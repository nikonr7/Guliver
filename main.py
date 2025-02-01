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
    """Analyze text using OpenAI GPT-4 to extract market problems or startup ideas."""
    print_step("Analyzing post with GPT-4...")
    try:
        response = await client.chat.completions.create(
            model="gpt-4",
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
        print_error(f"Error during OpenAI analysis: {e}")
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
    """Generate embedding for text using OpenAI's text-embedding-ada-002."""
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

async def semantic_search(query: str, match_threshold: float = 0.7, limit: int = 5) -> List[Dict[str, Any]]:
    """Find most relevant posts using embedding similarity."""
    print_step(f"Searching: {query[:50]}...")
    try:
        query_embedding = await generate_embedding(query)
        if not query_embedding:
            return []

        # Remove await as Supabase RPC is not async
        results = supabase.rpc(
            'match_posts',
            {
                'query_embedding': query_embedding,
                'match_threshold': match_threshold,
                'match_count': limit
            }
        ).execute()

        if results.data:
            print_success(f"Found {len(results.data)} matches")
            return results.data
        return []
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
        
        # Prepare the data
        data = {
            "id": post.get('id'),
            "title": post.get('title'),
            "selftext": post.get('selftext', ''),
            "analysis": analysis,
            "subreddit": post.get('subreddit'),
            "url": post.get('url'),
            "score": post.get('score'),
            "embedding": embedding
        }
        
        # Use upsert to handle both insert and update (remove await)
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

async def smart_analysis_pipeline(query: str, min_similarity: float = 0.7, max_posts: int = 5):
    """Smart pipeline that uses embeddings first, then GPT-4 only for relevant posts."""
    print_step(f"Starting smart analysis for query: {query}")
    
    # 1. Get query embedding
    query_embedding = await generate_embedding(query)
    if not query_embedding:
        print_error("Failed to generate query embedding")
        return []
    
    # 2. Find similar posts using vector search
    similar_posts = await semantic_search(query, min_similarity, max_posts)
    if not similar_posts:
        print_error("No similar posts found")
        return []
    
    print_success(f"Found {len(similar_posts)} relevant posts")
    
    # 3. Analyze relevant posts that haven't been analyzed yet
    for post in similar_posts:
        if not post.get('analysis'):
            print_step(f"Analyzing post: {post['title'][:100]}...")
            analysis = await analyze_text(post['title'] + "\n" + post.get('selftext', ''))
            if analysis:
                await update_post_analysis(post['id'], analysis)
                post['analysis'] = analysis
    
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
                    threshold = float(input(f"{Fore.GREEN}Enter similarity threshold (0.0-1.0, default: 0.7): {Style.RESET_ALL}").strip() or "0.7")
                    results = await smart_analysis_pipeline(query, threshold)
                    
                    if results:
                        print(f"\n{Fore.CYAN}Found {len(results)} relevant posts{Style.RESET_ALL}")
                        for idx, post in enumerate(results, 1):
                            print(f"\n{Fore.YELLOW}Match {idx} (Similarity: {post['similarity']:.2f}):{Style.RESET_ALL}")
                            print(f"Title: {post['title']}")
                            if post['analysis']:
                                print(f"{Fore.GREEN}Analysis:{Style.RESET_ALL}")
                                print(post['analysis'])
                    else:
                        print_error("No relevant posts found")
                except Exception as e:
                    print_error(f"An error occurred: {str(e)}")
            else:
                print_error("Please enter a valid search query")
        
        else:
            print_error("Invalid choice")
        
        print(f"\n{Fore.CYAN}Continue? (y/n){Style.RESET_ALL}")
        if input(f"{Fore.GREEN}> {Style.RESET_ALL}").strip().lower() != 'y':
            break

def main():
    """Entry point that runs the async main function."""
    asyncio.run(main_async())

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

if __name__ == "__main__":
    main() 