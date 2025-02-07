import os
import requests
from openai import AsyncOpenAI
from supabase import create_client, Client
from dotenv import load_dotenv
import time
from tqdm import tqdm
from colorama import init, Fore, Style
import sys
import asyncio
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import aiohttp
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
from datetime import datetime, timedelta, timezone

# Initialize FastAPI app
app = FastAPI(title="Guliver API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize colorama
init()

def print_step(message):
    """Print a step with formatting."""
    print(f"\n{Fore.BLUE}➜ {message}{Style.RESET_ALL}")

def print_success(message):
    """Print a success message with formatting."""
    print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")

def print_error(message):
    """Print an error message with formatting."""
    print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")

def loading_spinner(message):
    """Display a loading spinner with a message."""
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    i = 0
    while True:
        sys.stdout.write(f'\r{Fore.YELLOW}{spinner[i]}{Style.RESET_ALL} {message}')
        sys.stdout.flush()
        time.sleep(0.1)
        i = (i + 1) % len(spinner)

# Load environment variables from .env
load_dotenv()

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Initialize Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Test Supabase connection at startup
try:
    print_step("Initializing Supabase client...")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Test the connection
    print_step("Testing Supabase connection...")
    test = supabase.table("reddit_posts").select("id").limit(1).execute()
    print_success("Successfully connected to Supabase")
except Exception as e:
    print_error(f"Failed to initialize Supabase: {str(e)}")
    print(f"{Fore.RED}Please check your Supabase credentials and connection.{Style.RESET_ALL}")
    sys.exit(1)  # Exit if we can't connect to Supabase

# Reddit API credentials
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = 'MarketResearchBot/1.0'

def get_reddit_token():
    """Get Reddit API access token."""
    print_step("Getting Reddit API token...")
    auth = requests.auth.HTTPBasicAuth(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
    data = {
        'grant_type': 'client_credentials',
    }
    headers = {
        'User-Agent': REDDIT_USER_AGENT
    }
    
    try:
        response = requests.post(
            'https://www.reddit.com/api/v1/access_token',
            auth=auth,
            data=data,
            headers=headers
        )
        
        if response.status_code == 200:
            print_success("Successfully obtained Reddit API token")
            return response.json()['access_token']
        else:
            print_error(f"Failed to get Reddit token. Status code: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Error getting Reddit token: {e}")
        return None

async def fetch_posts_async(subreddit: str, size: int = 10) -> List[Dict]:
    """Async version of fetching posts."""
    print_step(f"Fetching posts from r/{subreddit}...")
    token = get_reddit_token()
    if not token:
        return []
    
    headers = {
        'User-Agent': REDDIT_USER_AGENT,
        'Authorization': f'Bearer {token}'
    }
    
    url = f"https://oauth.reddit.com/r/{subreddit}/hot"
    params = {
        'limit': size
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    posts = data['data']['children']
                    print_success(f"Successfully fetched {len(posts)} posts from r/{subreddit}")
                    return [post['data'] for post in posts]
                else:
                    print_error(f"Failed to fetch posts. Status code: {response.status}")
                    return []
    except Exception as e:
        print_error(f"Error fetching posts: {e}")
        return []

async def analyze_text(text: str) -> str:
    """Analyze text using AI to extract market problems or startup ideas."""
    print_step("Analyzing post")
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "system", "content": """You are an expert market research analyst and startup advisor. 
Your task is to analyze discussions and identify:
1. Clear market opportunities and gaps
2. Specific user pain points and problems
3. Potential startup ideas or business solutions
4. Market size indicators and trends
5. Competitive landscape insights

Be precise, practical, and focus on actionable insights."""},
                {"role": "user", "content": f"Analyze this Reddit post and extract valuable market insights:\n\n{text}"}
            ],
            max_tokens=500,
            temperature=0.6
        )
        analysis = response.choices[0].message.content.strip()
        print_success("Analysis completed successfully")
        return analysis
    except Exception as e:
        print_error(f"Error during analysis: {e}")
        return ""

async def check_existing_analysis_async(post_id: str) -> tuple[bool, str]:
    """Async version of checking existing analysis."""
    try:
        print_step(f"Checking post: {post_id}")
        
        # Query the database (remove await as Supabase operations are not async)
        result = supabase.table("reddit_posts").select("*").eq("id", post_id).execute()
        
        # Check if we got any data back
        if result.data and len(result.data) > 0:
            post_data = result.data[0]
            if post_data.get('analysis'):
                print_success("✓")
                return True, post_data['analysis']
            else:
                print_success("✓")
                return True, ""
        else:
            print_success("✓")
            return False, ""
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False, ""

async def generate_embedding(text: str) -> List[float]:
    """Generate embedding for text using advanced text embedding model."""
    print_step("Generating embedding...")
    try:
        response = await client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        print_success("Successfully generated embedding")
        return response.data[0].embedding
    except Exception as e:
        print_error(f"Error generating embedding: {e}")
        return []

async def semantic_search_with_offset(
    query: str,
    subreddit: str,
    match_threshold: float = 0.7,
    limit: int = 10,
    seen_ids: set = None
) -> List[Dict[str, Any]]:
    """Enhanced semantic search that can skip already seen posts."""
    try:
        query_embedding = await generate_embedding(query)
        if not query_embedding:
            return []

        # Get more results than needed to account for filtering
        results = supabase.rpc(
            'match_posts',
            {
                'query_embedding': query_embedding,
                'match_threshold': match_threshold,
                'match_count': limit * 3  # Get extra to allow for filtering
            }
        ).execute()

        if not results.data:
            return []

        # Filter by subreddit and unseen posts
        filtered_results = []
        seen_ids = seen_ids or set()
        
        for post in results.data:
            if post['subreddit'].lower() == subreddit.lower() and post['id'] not in seen_ids:
                filtered_results.append(post)
                if len(filtered_results) >= limit:
                    break

        filtered_results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
        return filtered_results[:limit]
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return []

async def batch_generate_embeddings(texts: List[str], batch_size: int = 20) -> List[List[float]]:
    """Generate embeddings for multiple texts in batches."""
    print_step(f"Generating embeddings for {len(texts)} texts in batches of {batch_size}...")
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        try:
            print(f"{Fore.YELLOW}Processing batch of {len(batch)} texts{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}First text in batch (truncated): {batch[0][:100]}...{Style.RESET_ALL}")
            
            response = await client.embeddings.create(
                model="text-embedding-ada-002",
                input=batch
            )
            
            print(f"{Fore.YELLOW}Got response with {len(response.data)} embeddings{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}First embedding length: {len(response.data[0].embedding)}{Style.RESET_ALL}")
            
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
            print_success(f"Processed batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
        except Exception as e:
            print_error(f"Error in batch {i//batch_size + 1}: {e}")
            # Print full exception details
            import traceback
            print(f"{Fore.RED}Full error: {traceback.format_exc()}{Style.RESET_ALL}")
            # Fill with empty embeddings for failed batch
            all_embeddings.extend([[] for _ in batch])
    
    print(f"{Fore.YELLOW}Total embeddings generated: {len(all_embeddings)}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Number of non-empty embeddings: {sum(1 for e in all_embeddings if e)}{Style.RESET_ALL}")
    
    return all_embeddings

async def store_post_with_embedding(post: dict, embedding: List[float], analysis: str = None):
    """Store post with its embedding, optionally including analysis."""
    try:
        print_step(f"Storing: {post.get('title')[:50]}...")
        
        # Convert Unix timestamp to ISO format
        created_at = datetime.fromtimestamp(post.get('created_utc'), tz=timezone.utc).isoformat()
        
        # Prepare the data
        data = {
            "id": post.get('id'),
            "title": post.get('title'),
            "selftext": post.get('selftext', ''),
            "analysis": analysis,
            "subreddit": post.get('subreddit'),
            "url": post.get('url'),
            "score": post.get('score'),
            "embedding": embedding,
            "created_at": created_at
        }
        
        # Use upsert to handle both insert and update
        result = supabase.table("reddit_posts").upsert(data).execute()
        
        if result.data:
            print_success("✓")
            return True
        else:
            print_error("✗")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

async def update_post_analysis(post_id: str, analysis: str):
    """Update the analysis of an existing post."""
    try:
        result = supabase.table("reddit_posts").update({"analysis": analysis}).eq("id", post_id).execute()
        if isinstance(result, dict) and result.get('data'):
            print_success(f"Updated analysis for post {post_id}")
            return True
        return False
    except Exception as e:
        print_error(f"Error updating analysis: {e}")
        return False

async def process_subreddit_posts(subreddit: str, post_limit: int) -> int:
    """Process posts from a single subreddit."""
    successful_posts = 0
    
    print_step(f"Processing r/{subreddit}...")
    posts = await fetch_posts_async(subreddit, size=post_limit)
    
    if not posts:
        print_error(f"No posts found in r/{subreddit}")
        return 0
    
    print_success(f"Found {len(posts)} posts")
    
    # Process posts one by one
    for post in posts:
        # Check if post exists
        exists, existing_analysis = await check_existing_analysis_async(post.get('id'))
        if exists:
            successful_posts += 1
            continue
        
        # Generate embedding
        content = post.get('title', '') + "\n" + post.get('selftext', '')
        embedding = await generate_embedding(content)
        
        if not embedding:
            continue
        
        # Store post with embedding
        if await store_post_with_embedding(post, embedding):
            successful_posts += 1
    
    return successful_posts

async def fetch_and_filter_posts(subreddits: List[str], post_limit: int = 100):
    """Fetch and process posts from multiple subreddits."""
    print_step(f"Processing {len(subreddits)} subreddits...")
    
    total_successful = 0
    for subreddit in subreddits:
        successful = await process_subreddit_posts(subreddit, post_limit)
        total_successful += successful
        
        print(f"\n{Fore.GREEN}r/{subreddit}: {successful} posts processed{Style.RESET_ALL}")
    
    print(f"\n{Fore.GREEN}Total processed: {total_successful}{Style.RESET_ALL}")
    return total_successful

async def fetch_posts_by_timeframe(subreddit: str, timeframe: str = 'week', size: int = 100) -> List[Dict]:
    """Fetch posts from a subreddit within a specific timeframe."""
    print_step(f"Fetching posts from r/{subreddit} for the last {timeframe}...")
    token = get_reddit_token()
    if not token:
        return []
    
    headers = {
        'User-Agent': REDDIT_USER_AGENT,
        'Authorization': f'Bearer {token}'
    }

    # Instead of combining all keywords in one query, we'll search for each keyword separately
    all_posts = []
    seen_ids = set()

    for keyword in PROBLEM_KEYWORDS:
        print_step(f"Searching for keyword: {keyword}")
        try:
            url = f"https://oauth.reddit.com/r/{subreddit}/search"
            params = {
                'q': keyword,  # Search one keyword at a time
                'restrict_sr': 'true',
                'sort': 'new',
                'limit': size,
                't': timeframe,
                'type': 'link'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        posts = data['data']['children']
                        
                        # Add new unique posts
                        for post in posts:
                            post_data = post['data']
                            if post_data['id'] not in seen_ids:
                                seen_ids.add(post_data['id'])
                                all_posts.append(post_data)
                                print_success(f"Found post with keyword '{keyword}': {post_data['title'][:100]}")
                    else:
                        print_error(f"Failed to fetch posts for keyword '{keyword}'. Status code: {response.status}")
        except Exception as e:
            print_error(f"Error fetching posts for keyword '{keyword}': {e}")
        
        # Add a small delay between requests to avoid rate limiting
        await asyncio.sleep(0.5)
    
    # Calculate timestamp for the timeframe
    now = datetime.now()
    if timeframe == 'week':
        start_time = now - timedelta(days=7)
    elif timeframe == 'month':
        start_time = now - timedelta(days=30)
    elif timeframe == 'year':
        start_time = now - timedelta(days=365)
    else:
        print_error(f"Invalid timeframe: {timeframe}")
        return []

    # Filter by timestamp
    filtered_posts = [
        post for post in all_posts 
        if datetime.fromtimestamp(post['created_utc']) >= start_time
    ]
    
    print_success(f"Successfully fetched {len(filtered_posts)} unique posts from r/{subreddit}")
    return filtered_posts

# Update fetch_comments_async to get all comments
async def fetch_comments_async(post_id: str) -> List[Dict]:
    """Fetch all comments for a post."""
    token = get_reddit_token()
    if not token:
        return []
    
    headers = {
        'User-Agent': REDDIT_USER_AGENT,
        'Authorization': f'Bearer {token}'
    }
    
    url = f"https://oauth.reddit.com/comments/{post_id}"
    params = {
        'sort': 'top',
        'depth': 1  # Get only top-level comments
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if len(data) > 1:  # Reddit returns [post_data, comments_data]
                        comments = data[1]['data']['children']
                        return [
                            comment['data']['body'] 
                            for comment in comments 
                            if comment['kind'] == 't1' and len(comment['data']['body']) > 50  # Filter short comments
                        ]
                return []
    except Exception as e:
        print_error(f"Error fetching comments: {e}")
        return []

# Update analyze_post_with_comments to analyze all comments
async def analyze_post_with_comments(post: dict) -> str:
    """Analyze post content together with all its comments."""
    print_step("Fetching comments...")
    comments = await fetch_comments_async(post['id'])
    
    # Combine post content with comments
    full_content = f"POST TITLE: {post['title']}\n\nPOST CONTENT: {post['selftext']}\n\n"
    if comments:
        full_content += "COMMENTS:\n"
        for i, comment in enumerate(comments, 1):
            full_content += f"\nComment {i}:\n{comment}\n"
    
    print_step("Analyzing post and comments...")
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "system", "content": """You are an expert market research analyst and startup advisor. 
Analyze both the main post and its comments to identify:
1. Clear market opportunities and gaps
2. Specific user pain points and problems
3. Potential startup ideas or business solutions
4. Market size indicators and trends
5. Competitive landscape insights
6. Additional insights from comment discussions

Focus on actionable insights and note when comments provide additional context or validation to the main post's points."""},
                {"role": "user", "content": f"Analyze this Reddit post and its comments to extract valuable market insights:\n\n{full_content}"}
            ],
            max_tokens=1000,  # Increased for more comments
            temperature=0.6
        )
        analysis = response.choices[0].message.content.strip()
        print_success("Analysis completed successfully")
        return analysis
    except Exception as e:
        print_error(f"Error during analysis: {e}")
        return ""

async def smart_analysis_pipeline(
    query: str, 
    subreddit: str = None, 
    min_similarity: float = 0.7, 
    max_posts: int = 5, 
    analyze_count: int = None,
    comment_limit: int = 5
):
    """Smart pipeline that uses embeddings first, then advanced AI only for relevant posts."""
    print_step(f"Starting smart analysis for query: {query}")
    if subreddit:
        print_step(f"Searching in r/{subreddit}")
    
    # First, fetch and store new posts to ensure fresh data
    print_step(f"Fetching new posts from r/{subreddit}...")
    await process_subreddit_posts(subreddit, 100)  # Fetch 100 posts to have a good pool
    
    # Find similar posts using vector search
    similar_posts = await semantic_search_with_offset(query, subreddit, min_similarity, max_posts)
    if not similar_posts:
        print_error("No similar posts found")
        return []
    
    print_success(f"Found {len(similar_posts)} relevant posts")
    
    # If analyze_count is specified, only analyze that many posts
    posts_to_analyze = similar_posts[:analyze_count] if analyze_count else similar_posts
    
    # Analyze relevant posts that haven't been analyzed yet
    for i, post in enumerate(posts_to_analyze):
        if not post.get('analysis'):
            print_step(f"Analyzing post {i+1}/{len(posts_to_analyze)}: {post['title'][:100]}...")
            analysis = await analyze_post_with_comments(post)
            if analysis:
                await update_post_analysis(post['id'], analysis)
                post['analysis'] = analysis
                print_success(f"Analysis completed for post {post['id']}")
    
    return similar_posts

async def main_async():
    """Async version of main function."""
    while True:
        print_step("Starting Market Research Bot")
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}Choose operation:{Style.RESET_ALL}")
        print("1. Fetch and process new posts")
        print("2. Search and analyze")
        choice = input(f"{Fore.GREEN}> {Style.RESET_ALL}").strip()
        
        if choice == "1":
            subreddits = get_user_subreddits()
            post_limit = get_post_limit()
            
            try:
                successful_posts = await fetch_and_filter_posts(subreddits, post_limit)
                print(f"\n{Fore.CYAN}Summary:{Style.RESET_ALL}")
                print(f"Total posts successfully processed: {successful_posts}")
            except Exception as e:
                print_error(f"An error occurred: {str(e)}")
                import traceback
                print(f"{Fore.RED}Full error: {traceback.format_exc()}{Style.RESET_ALL}")
        
        elif choice == "2":
            print(f"\n{Fore.CYAN}Enter search query:{Style.RESET_ALL}")
            query = input(f"{Fore.GREEN}> {Style.RESET_ALL}").strip()
            
            if query:
                try:
                    print(f"\n{Fore.CYAN}Enter subreddit to search in (press Enter to search all):{Style.RESET_ALL}")
                    subreddit = input(f"{Fore.GREEN}> {Style.RESET_ALL}").strip()
                    
                    threshold = float(input(f"{Fore.GREEN}Enter similarity threshold (0.0-1.0, default: 0.7): {Style.RESET_ALL}").strip() or "0.7")
                    
                    print(f"\n{Fore.CYAN}How many posts to analyze? (default: all matched posts):{Style.RESET_ALL}")
                    analyze_input = input(f"{Fore.GREEN}> {Style.RESET_ALL}").strip()
                    analyze_count = int(analyze_input) if analyze_input else None
                    
                    print(f"\n{Fore.CYAN}How many top comments to analyze per post? (default: 5):{Style.RESET_ALL}")
                    comment_input = input(f"{Fore.GREEN}> {Style.RESET_ALL}").strip()
                    comment_limit = int(comment_input) if comment_input else 5
                    
                    results = await smart_analysis_pipeline(
                        query, 
                        subreddit if subreddit else None, 
                        threshold,
                        max_posts=10,  # Show more results
                        analyze_count=analyze_count,
                        comment_limit=comment_limit
                    )
                    
                    if results:
                        print(f"\n{Fore.CYAN}Found {len(results)} relevant posts{Style.RESET_ALL}")
                        for idx, post in enumerate(results, 1):
                            print(f"\n{Fore.YELLOW}Match {idx} (Similarity: {post['similarity']:.2f}){Style.RESET_ALL}")
                            print(f"Subreddit: r/{post['subreddit']}")
                            print(f"Title: {post['title']}")
                            if post['analysis']:
                                print(f"{Fore.GREEN}Analysis (including comments):{Style.RESET_ALL}")
                                print(post['analysis'])
                            elif idx <= (analyze_count or len(results)):
                                print(f"{Fore.YELLOW}Analysis pending...{Style.RESET_ALL}")
                            else:
                                print(f"{Fore.YELLOW}Not selected for analysis{Style.RESET_ALL}")
                    else:
                        print_error("No relevant posts found")
                except ValueError:
                    print_error("Please enter a valid number")
                except Exception as e:
                    print_error(f"An error occurred: {str(e)}")
            else:
                print_error("Please enter a valid search query")
        
        else:
            print_error("Invalid choice")
        
        print(f"\n{Fore.CYAN}Continue? (y/n){Style.RESET_ALL}")
        if input(f"{Fore.GREEN}> {Style.RESET_ALL}").strip().lower() != 'y':
            break

def print_banner():
    """Print a welcome banner for the application."""
    banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║                Reddit Market Research Tool                  ║
║           Search, Analyze, and Extract Insights            ║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)

def main():
    """Main function to run the FastAPI server."""
    print_banner()
    print(f"{Fore.CYAN}Starting FastAPI server...{Style.RESET_ALL}")
    uvicorn.run(app, host="0.0.0.0", port=8000)

def validate_subreddit(subreddit: str) -> bool:
    """Validate if a subreddit exists."""
    print_step(f"Validating r/{subreddit}...")
    
    headers = {
        'User-Agent': REDDIT_USER_AGENT
    }
    
    url = f"https://www.reddit.com/r/{subreddit}/about.json"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if not data.get('data'):
                print_error(f"r/{subreddit} does not exist")
                return False
            if data['data'].get('over18', False):
                print_error(f"r/{subreddit} is NSFW and will be skipped")
                return False
            print_success(f"r/{subreddit} exists and is valid")
            return True
        else:
            print_error(f"r/{subreddit} does not exist or is private")
            return False
    except Exception as e:
        print_error(f"Error validating r/{subreddit}: {e}")
        return False

def get_user_subreddits():
    """Get and validate user input subreddits."""
    print(f"\n{Fore.CYAN}Enter subreddits to analyze (comma-separated, press enter when done){Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Example: startups, Entrepreneur, smallbusiness{Style.RESET_ALL}")
    
    while True:
        subreddits_input = input(f"{Fore.GREEN}> {Style.RESET_ALL}").strip()
        
        if not subreddits_input:
            # Use default subreddits if no input
            default_subreddits = ["startups", "Entrepreneur", "smallbusiness", "SideProject"]
            print(f"{Fore.YELLOW}Using default subreddits: {', '.join(default_subreddits)}{Style.RESET_ALL}")
            return default_subreddits
        
        # Split and clean input
        subreddits = [s.strip() for s in subreddits_input.split(',') if s.strip()]
        
        if not subreddits:
            print_error("Please enter at least one subreddit")
            continue
        
        # Validate each subreddit
        valid_subreddits = []
        for subreddit in subreddits:
            if validate_subreddit(subreddit):
                valid_subreddits.append(subreddit)
        
        if valid_subreddits:
            return valid_subreddits
        else:
            print_error("No valid subreddits entered. Please try again.")

def get_post_limit():
    """Get number of posts to analyze per subreddit."""
    print(f"\n{Fore.CYAN}How many posts to analyze per subreddit? (1-100, default: 10){Style.RESET_ALL}")
    
    while True:
        try:
            limit_input = input(f"{Fore.GREEN}> {Style.RESET_ALL}").strip()
            
            if not limit_input:
                return 10
            
            limit = int(limit_input)
            if 1 <= limit <= 100:
                if limit > 25:
                    print(f"{Fore.YELLOW}Warning: Processing {limit} posts may take some time and use more API calls{Style.RESET_ALL}")
                return limit
            else:
                print_error("Please enter a number between 1 and 100")
        except ValueError:
            print_error("Please enter a valid number")

async def unified_subreddit_search(
    query: str,
    subreddit: str,
    match_threshold: float = 0.7,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Unified function to search and fetch posts from a specific subreddit.
    Combines historical database search with fresh Reddit data.
    """
    print_step(f"Searching in r/{subreddit} for: {query[:50]}...")
    
    try:
        # First, get the most recent post we have for this subreddit
        latest_post = supabase.table("reddit_posts") \
            .select("created_at") \
            .eq("subreddit", subreddit) \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()
        
        # Perform semantic search on all existing data
        search_results = await semantic_search_with_offset(query, subreddit, match_threshold, limit)
        
        # Always fetch some new posts to keep the database fresh
        print_step(f"Fetching new posts from r/{subreddit}...")
        new_posts = await process_subreddit_posts(subreddit, limit * 2)  # Fetch extra to ensure enough data
        
        if new_posts > 0:
            # Perform semantic search again including new data
            updated_results = await semantic_search_with_offset(query, subreddit, match_threshold, limit)
            
            # If we got better (more relevant) results, use them
            if updated_results and (not search_results or 
                updated_results[0].get('similarity', 0) > search_results[0].get('similarity', 0)):
                search_results = updated_results
            
            print_success(f"Added {new_posts} new posts to the database")
        
        if search_results:
            # Sort results by similarity score
            search_results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
        
        return search_results
    except Exception as e:
        print_error(f"Error in unified search: {str(e)}")
        return []

async def interactive_subreddit_search():
    """Interactive function for searching within a specific subreddit."""
    print(f"\n{Fore.CYAN}Enter the subreddit you want to search in:{Style.RESET_ALL}")
    while True:
        subreddit = input(f"{Fore.GREEN}Subreddit > {Style.RESET_ALL}").strip()
        if validate_subreddit(subreddit):
            break
        print_error("Please enter a valid subreddit name")
    
    print(f"\n{Fore.CYAN}Enter your search query:{Style.RESET_ALL}")
    query = input(f"{Fore.GREEN}Search > {Style.RESET_ALL}").strip()
    
    if not query:
        print_error("Search query cannot be empty")
        return
    
    print_step("Searching...")
    results = await unified_subreddit_search(query, subreddit)
    
    if not results:
        print_error("No results found")
        return
    
    print_success(f"\nFound {len(results)} results:")
    for i, post in enumerate(results, 1):
        print(f"\n{Fore.CYAN}Result {i}:{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Title:{Style.RESET_ALL} {post['title']}")
        if post.get('analysis'):
            print(f"{Fore.YELLOW}Analysis:{Style.RESET_ALL} {post['analysis'][:200]}...")
        print(f"{Fore.YELLOW}Similarity Score:{Style.RESET_ALL} {post.get('similarity', 0):.2f}")
        print(f"{Fore.YELLOW}URL:{Style.RESET_ALL} https://reddit.com{post.get('url', '')}")

async def check_and_update_subreddit(subreddit: str, default_limit: int = 100) -> bool:
    """Check if we have posts for the subreddit and fetch new ones if needed."""
    try:
        print_step(f"Checking existing posts for r/{subreddit}...")
        
        # Get our most recent post for this subreddit
        latest_post = supabase.table("reddit_posts") \
            .select("created_at") \
            .eq("subreddit", subreddit) \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()
        
        existing_count = supabase.table("reddit_posts") \
            .select("id", count="exact") \
            .eq("subreddit", subreddit) \
            .execute()
        
        count = existing_count.count if existing_count else 0
        print_success(f"Found {count} existing posts in database")
        
        # Always fetch new posts to ensure we have the latest
        print_step(f"Fetching new posts from r/{subreddit}...")
        new_posts = await process_subreddit_posts(subreddit, default_limit)
        
        if new_posts > 0:
            print_success(f"Added {new_posts} new posts to the database")
        else:
            print_success("Database is up to date")
        
        return True
    except Exception as e:
        print_error(f"Error updating subreddit: {str(e)}")
        return False

async def new_interactive_workflow():
    """New streamlined workflow for fetching and searching."""
    print_banner()
    
    # Step 1: Choose subreddit
    print(f"\n{Fore.CYAN}Enter the subreddit you want to analyze:{Style.RESET_ALL}")
    while True:
        subreddit = input(f"{Fore.GREEN}Subreddit > {Style.RESET_ALL}").strip()
        if validate_subreddit(subreddit):
            break
        print_error("Please enter a valid subreddit name")
    
    # Step 2: Check and update posts
    success = await check_and_update_subreddit(subreddit)
    if not success:
        return
    
    # Step 3: Get search query and analyze
    while True:
        print(f"\n{Fore.CYAN}Enter your search query (or 'exit' to quit):{Style.RESET_ALL}")
        query = input(f"{Fore.GREEN}Search > {Style.RESET_ALL}").strip()
        
        if query.lower() == 'exit':
            break
        
        if not query:
            print_error("Search query cannot be empty")
            continue
        
        # Keep track of seen posts for this search query
        seen_post_ids = set()
        
        while True:  # Loop for finding more results
            # Perform search excluding seen posts
            results = await semantic_search_with_offset(
                query, 
                subreddit, 
                match_threshold=0.7, 
                limit=10,
                seen_ids=seen_post_ids
            )
            
            if results:
                print_success(f"\nFound {len(results)} more relevant posts:")
                for i, post in enumerate(results, len(seen_post_ids) + 1):
                    print(f"\n{Fore.CYAN}Result {i}:{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}Title:{Style.RESET_ALL} {post['title']}")
                    print(f"{Fore.YELLOW}Similarity Score:{Style.RESET_ALL} {post.get('similarity', 0):.2f}")
                    
                    # Analyze with AI if not already analyzed
                    if not post.get('analysis'):
                        print(f"{Fore.YELLOW}Analyzing...{Style.RESET_ALL}")
                        analysis = await analyze_post_with_comments(post)
                        if analysis:
                            await update_post_analysis(post['id'], analysis)
                            post['analysis'] = analysis
                    
                    if post.get('analysis'):
                        print(f"{Fore.GREEN}Analysis:{Style.RESET_ALL}")
                        print(post['analysis'])
                    
                    print(f"{Fore.YELLOW}URL:{Style.RESET_ALL} https://reddit.com{post.get('url', '')}")
                    
                    # Add to seen posts
                    seen_post_ids.add(post['id'])
                
                # Ask if user wants to see more results
                print(f"\n{Fore.CYAN}Would you like to see more results? (y/n){Style.RESET_ALL}")
                if input(f"{Fore.GREEN}> {Style.RESET_ALL}").strip().lower() != 'y':
                    break
            else:
                print_error("No more relevant posts found")
                break

# API Models
class SearchRequest(BaseModel):
    query: str
    subreddit: str
    match_threshold: float = 0.7
    limit: int = 5

class AnalysisRequest(BaseModel):
    text: str

# Additional API Models
class BatchProcessRequest(BaseModel):
    subreddits: List[str]
    post_limit: int = 10

class SmartAnalysisRequest(BaseModel):
    query: str
    subreddit: str
    min_similarity: float = 0.7
    max_posts: int = 5
    analyze_count: Optional[int] = None
    comment_limit: int = 5

class SubredditValidationResponse(BaseModel):
    is_valid: bool
    message: str

class ProblemAnalysisRequest(BaseModel):
    subreddit: str
    timeframe: str = 'week'  # 'week', 'month', or 'year'
    min_score: int = 5  # Minimum score threshold

# Add new database model for search history
class SearchHistory(BaseModel):
    subreddit: str
    timeframe: str
    last_search_time: datetime
    last_post_time: datetime

async def get_last_search(subreddit: str, timeframe: str) -> Optional[Dict]:
    """Get the last search results for this subreddit and timeframe."""
    try:
        result = supabase.table("search_history")\
            .select("*")\
            .eq("subreddit", subreddit)\
            .eq("timeframe", timeframe)\
            .order("last_search_time", desc=True)\
            .limit(1)\
            .execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    except Exception as e:
        print_error(f"Error getting last search: {e}")
        return None

async def update_search_history(subreddit: str, timeframe: str, last_post_time: datetime):
    """Update search history with new timestamp."""
    try:
        now = datetime.now(timezone.utc)
        
        # First try to get existing record
        existing = supabase.table("search_history")\
            .select("*")\
            .eq("subreddit", subreddit)\
            .eq("timeframe", timeframe)\
            .execute()
        
        data = {
            "subreddit": subreddit,
            "timeframe": timeframe,
            "last_search_time": now.isoformat(),
            "last_post_time": last_post_time.replace(tzinfo=timezone.utc).isoformat()
        }
        
        if existing.data and len(existing.data) > 0:
            # Update existing record
            result = supabase.table("search_history")\
                .update(data)\
                .eq("subreddit", subreddit)\
                .eq("timeframe", timeframe)\
                .execute()
        else:
            # Insert new record
            result = supabase.table("search_history")\
                .insert(data)\
                .execute()
        
        print_success(f"Updated search history for r/{subreddit}")
        return result
    except Exception as e:
        print_error(f"Error updating search history: {e}")
        return None

async def get_analyzed_posts(subreddit: str, since_time: datetime) -> List[Dict]:
    """Get already analyzed posts from database."""
    try:
        result = supabase.table("reddit_posts")\
            .select("*")\
            .eq("subreddit", subreddit)\
            .gte("created_at", since_time.isoformat())\
            .not_.is_("analysis", "null")\
            .order("score", desc=True)\
            .execute()
        
        return result.data if result.data else []
    except Exception as e:
        print_error(f"Error getting analyzed posts: {e}")
        return []

# API Routes
@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/search")
async def search(request: SearchRequest):
    try:
        # Use smart_analysis_pipeline instead of unified_subreddit_search
        results = await smart_analysis_pipeline(
            query=request.query,
            subreddit=request.subreddit,
            min_similarity=request.match_threshold,
            max_posts=request.limit,
            analyze_count=request.limit,  # Analyze all returned posts
            comment_limit=5
        )
        
        if not results:
            return {"status": "success", "data": []}
            
        print_success(f"Returning {len(results)} analyzed posts")
        return {"status": "success", "data": results}
    except Exception as e:
        print_error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def analyze(request: AnalysisRequest):
    try:
        analysis = await analyze_text(request.text)
        return {"status": "success", "analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/subreddit/{subreddit}/posts")
async def get_subreddit_posts(
    subreddit: str,
    limit: int = Query(default=10, le=100)
):
    try:
        posts = await fetch_posts_async(subreddit, limit)
        return {"status": "success", "data": posts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/smart-analysis")
async def smart_analysis(request: SmartAnalysisRequest):
    """Full smart analysis pipeline including comments and AI analysis."""
    try:
        results = await smart_analysis_pipeline(
            query=request.query,
            subreddit=request.subreddit,
            min_similarity=request.min_similarity,
            max_posts=request.max_posts,
            analyze_count=request.analyze_count,
            comment_limit=request.comment_limit
        )
        return {"status": "success", "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/batch-process")
async def batch_process(request: BatchProcessRequest):
    """Process multiple subreddits and store posts with embeddings."""
    try:
        results = await fetch_and_filter_posts(
            subreddits=request.subreddits,
            post_limit=request.post_limit
        )
        return {"status": "success", "processed_count": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/validate-subreddit/{subreddit}")
async def validate_subreddit_endpoint(subreddit: str) -> SubredditValidationResponse:
    """Validate if a subreddit exists and is accessible."""
    is_valid = validate_subreddit(subreddit)
    message = f"r/{subreddit} is valid" if is_valid else f"r/{subreddit} is invalid or inaccessible"
    return SubredditValidationResponse(is_valid=is_valid, message=message)

@app.post("/api/analyze-with-comments")
async def analyze_with_comments(post_id: str, comment_limit: int = 5):
    """Analyze a post together with its top comments."""
    try:
        # First get the post from database
        post = supabase.table("reddit_posts").select("*").eq("id", post_id).execute()
        if not post.data:
            raise HTTPException(status_code=404, detail="Post not found")
        
        analysis = await analyze_post_with_comments(post.data[0], comment_limit)
        if analysis:
            # Update the analysis in database
            await update_post_analysis(post_id, analysis)
            return {"status": "success", "analysis": analysis}
        else:
            raise HTTPException(status_code=500, detail="Analysis failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/subreddit/{subreddit}/stats")
async def get_subreddit_stats(subreddit: str):
    """Get statistics about stored posts for a subreddit."""
    try:
        stats = supabase.table("reddit_posts")\
            .select("*", count="exact")\
            .eq("subreddit", subreddit)\
            .execute()
        
        return {
            "status": "success",
            "stats": {
                "total_posts": stats.count,
                "subreddit": subreddit
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add new function for keyword-based search
PROBLEM_KEYWORDS = [
    "need tool for", "need software for", "looking for tool", "looking for app",
    "recommend tool", "recommend software", "any tools for", "any apps for",
    "frustrated with", "tired of manually", "hate doing", "waste time",
    "wasting time", "takes forever to", "pain point", "pain in the",
    "annoying process", "automate this", "efficiency", "productivity",
    "automation", "workflow", "business needs", "company requires",
    "enterprise solution", "scale our", "manage multiple", "track all",
    "monitor our", "integrate with", "data entry", "manual process",
    "repetitive tasks", "time consuming", "complex workflow",
    "communication gap", "coordination", "collaboration", "solution for",
    "struggle with", "difficult to", "can't figure out", "need to improve",
    "optimize", "streamline", "simplify", "how to solve", "help managing",
    "better way to", "alternative to"
]

async def search_problem_posts(subreddit: str, timeframe: str = 'week', min_score: int = 1) -> List[Dict]:
    """Search for posts containing problem-related keywords within the specified timeframe."""
    print_step(f"Searching for problem-related posts in r/{subreddit}...")
    
    # Fetch posts for the timeframe
    posts = await fetch_posts_by_timeframe(subreddit, timeframe)
    if not posts:
        return []
    
    # Filter posts by score and keywords
    filtered_posts = []
    for post in posts:
        if post['score'] >= min_score:  # Only include posts with minimum score
            text = f"{post['title'].lower()} {post['selftext'].lower()}"
            matching_keywords = [
                keyword for keyword in PROBLEM_KEYWORDS 
                if keyword.lower() in text
            ]
            if matching_keywords:
                print_success(f"Found post with {post['score']} votes and keywords {matching_keywords}: {post['title'][:100]}...")
                filtered_posts.append(post)
    
    # Sort posts by score in descending order
    filtered_posts.sort(key=lambda x: x['score'], reverse=True)
    print_success(f"Found {len(filtered_posts)} posts containing problem-related keywords (min score: {min_score})")
    return filtered_posts

async def analyze_problem_posts(subreddit: str, timeframe: str = 'week') -> List[Dict]:
    """Main function to find and analyze problem-related posts."""
    # Find posts with problem-related keywords
    posts = await search_problem_posts(subreddit, timeframe)
    if not posts:
        return []
    
    # Analyze each post with all its comments
    analyzed_posts = []
    for post in posts:
        analysis = await analyze_post_with_comments(post)
        if analysis:
            post['analysis'] = analysis
            analyzed_posts.append(post)
    
    return analyzed_posts

@app.post("/api/analyze-problems")
async def analyze_problems(request: ProblemAnalysisRequest):
    """Analyze problem-related posts in a subreddit."""
    try:
        if request.timeframe not in ['week', 'month', 'year']:
            raise HTTPException(status_code=400, detail="Invalid timeframe. Must be 'week', 'month', or 'year'")
        
        # Calculate the time range we need
        now = datetime.now(timezone.utc)
        if request.timeframe == 'week':
            start_time = now - timedelta(days=7)
        elif request.timeframe == 'month':
            start_time = now - timedelta(days=30)
        else:  # year
            start_time = now - timedelta(days=365)
        
        # Check if we have a recent search
        last_search = await get_last_search(request.subreddit, request.timeframe)
        existing_posts = []
        needs_new_search = True
        
        if last_search:
            last_search_time = datetime.fromisoformat(last_search['last_search_time'])
            last_post_time = datetime.fromisoformat(last_search['last_post_time'])
            
            # Ensure timezone awareness
            if last_search_time.tzinfo is None:
                last_search_time = last_search_time.replace(tzinfo=timezone.utc)
            if last_post_time.tzinfo is None:
                last_post_time = last_post_time.replace(tzinfo=timezone.utc)
            
            # Get existing analyzed posts
            print_step("Checking for existing analyzed posts...")
            existing_posts = await get_analyzed_posts(request.subreddit, start_time)
            
            if existing_posts:
                print_success(f"Found {len(existing_posts)} existing analyzed posts")
                
                # If the last search was very recent, we might not need a new search
                if now - last_search_time < timedelta(hours=24):
                    needs_new_search = False
                    print_step("Last search was recent, using cached results")
                else:
                    # We have some results but need to search for newer posts
                    print_step(f"Found previous search from {last_search_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                    print_step("Will search for new posts since last search")
                    start_time = last_post_time
            else:
                print_step("No existing analyzed posts found, will perform full search")
        
        new_posts = []
        if needs_new_search:
            # Search for new posts
            print_step(f"Searching for new posts since {start_time.strftime('%Y-%m-%d %H:%M:%S %Z')}...")
            filtered_posts = await search_problem_posts(request.subreddit, request.timeframe, request.min_score)
            
            if filtered_posts:
                # Filter out posts we already have
                existing_ids = {post['id'] for post in existing_posts}
                new_posts = [post for post in filtered_posts if post['id'] not in existing_ids]
                
                if new_posts:
                    print_step(f"Found {len(new_posts)} new problem-related posts to analyze")
                    newest_post_time = None
                    
                    # Store and analyze each filtered post
                    for post in new_posts:
                        # Generate embedding for the post
                        content = f"{post['title']}\n{post['selftext']}"
                        embedding = await generate_embedding(content)
                        
                        if embedding:
                            # Store the post and analyze it immediately
                            success = await store_post_with_embedding(post, embedding)
                            if success:
                                print_success(f"Stored post: {post['title'][:100]}")
                                
                                # Analyze the post
                                analysis = await analyze_post_with_comments(post)
                                if analysis:
                                    # Update the stored post with the analysis
                                    await update_post_analysis(post['id'], analysis)
                                    post['analysis'] = analysis
                                    existing_posts.append(post)
                                    print_success(f"Analyzed post: {post['title'][:100]}")
                                
                                # Track the newest post time
                                post_time = datetime.fromtimestamp(post['created_utc'], tz=timezone.utc)
                                if newest_post_time is None or post_time > newest_post_time:
                                    newest_post_time = post_time
                    
                    # Update search history with the newest post time
                    if newest_post_time:
                        await update_search_history(request.subreddit, request.timeframe, newest_post_time)
                else:
                    print_step("No new problem-related posts found that weren't already analyzed")
        
        # Combine and sort all posts by score
        all_posts = sorted(
            existing_posts, 
            key=lambda x: x.get('score', 0), 
            reverse=True
        )
        
        if not all_posts:
            print_step("No posts found matching the criteria")
        else:
            print_success(f"Returning {len(all_posts)} total posts")
            
        return {
            "status": "success",
            "timeframe": request.timeframe,
            "subreddit": request.subreddit,
            "min_score": request.min_score,
            "post_count": len(all_posts),
            "data": all_posts,
            "source": "mixed" if existing_posts and new_posts else "new" if new_posts else "cache"
        }
    except Exception as e:
        print_error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    main() 