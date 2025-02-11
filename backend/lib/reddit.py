from typing import Dict, List
from datetime import datetime, timedelta 
import requests
import aiohttp
import asyncio
from .constants import *
from .log_utils import *


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