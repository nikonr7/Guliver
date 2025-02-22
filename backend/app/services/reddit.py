import requests
import aiohttp
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
from ..config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
from ..utils.logging import print_step, print_success, print_error
from ..utils.constants import PROBLEM_KEYWORDS

def get_reddit_token() -> Optional[str]:
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

async def fetch_comments_async(post_id: str) -> List[str]:
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

    seen_ids = set()
    all_posts = []

    async def search_keyword(keyword: str):
        print_step(f"Searching for keyword: {keyword}")
        try:
            url = f"https://oauth.reddit.com/r/{subreddit}/search"
            params = {
                'q': keyword,
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
                        
                        keyword_posts = []
                        for post in posts:
                            post_data = post['data']
                            if post_data['id'] not in seen_ids:
                                seen_ids.add(post_data['id'])
                                keyword_posts.append(post_data)
                                print_success(f"Found post with keyword '{keyword}': {post_data['title'][:100]}")
                        return keyword_posts
                    else:
                        print_error(f"Failed to fetch posts for keyword '{keyword}'. Status code: {response.status}")
                        return []
        except Exception as e:
            print_error(f"Error fetching posts for keyword '{keyword}': {e}")
            return []

    # Search all keywords in parallel
    keyword_results = await asyncio.gather(*[
        search_keyword(keyword) for keyword in PROBLEM_KEYWORDS
    ])
    
    # Combine all results
    for posts in keyword_results:
        all_posts.extend(posts)
    
    # Filter by timeframe
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

    filtered_posts = [
        post for post in all_posts 
        if datetime.fromtimestamp(post['created_utc']) >= start_time
    ]
    
    print_success(f"Successfully fetched {len(filtered_posts)} unique posts from r/{subreddit}")
    return filtered_posts

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