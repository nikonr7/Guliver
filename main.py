import os
import requests
import openai
from supabase_py import create_client, Client
from dotenv import load_dotenv
import time
from tqdm import tqdm
from colorama import init, Fore, Style
import sys

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
openai.api_key = os.getenv('OPENAI_API_KEY')

# Initialize Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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

def fetch_posts(subreddit: str, size: int = 10):
    """Fetch posts from a subreddit using Reddit's API."""
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
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            posts = response.json()['data']['children']
            print_success(f"Successfully fetched {len(posts)} posts from r/{subreddit}")
            return [post['data'] for post in posts]
        else:
            print_error(f"Failed to fetch posts. Status code: {response.status_code}")
            return []
    except Exception as e:
        print_error(f"Error fetching posts: {e}")
        return []

def analyze_text(text: str) -> str:
    """Analyze text using OpenAI GPT-4 to extract market problems or startup ideas."""
    print_step("Analyzing post with GPT-4...")
    try:
        response = openai.ChatCompletion.create(
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

def store_to_supabase(post: dict, analysis: str):
    """Store the Reddit post and its analysis into Supabase."""
    print_step("Storing data in Supabase...")
    try:
        data = {
            "id": post.get('id'),
            "title": post.get('title'),
            "selftext": post.get('selftext', ''),
            "analysis": analysis,
            "subreddit": post.get('subreddit'),
            "url": post.get('url'),
            "score": post.get('score')
        }
        # Insert into the reddit_posts table
        result = supabase.table("reddit_posts").insert(data).execute()
        print_success(f"Successfully stored post {post.get('id')} in Supabase")
    except Exception as e:
        print_error(f"Error storing to Supabase: {e}")

def main():
    print_step("Starting Market Research Bot")
    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    
    # List of relevant subreddits for market research
    subreddits = [
        "startups",
        "Entrepreneur",
        "smallbusiness",
        "SideProject"
    ]
    
    total_posts = 0
    successful_analyses = 0
    
    for subreddit in subreddits:
        print(f"\n{Fore.CYAN}Processing r/{subreddit}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-'*50}{Style.RESET_ALL}")
        
        posts = fetch_posts(subreddit, size=3)
        
        for post in posts:
            total_posts += 1
            print(f"\n{Fore.YELLOW}Post {total_posts}:{Style.RESET_ALL}")
            print(f"Title: {post.get('title')[:100]}...")
            
            content = post.get('title', '')
            if post.get('selftext'):
                content += "\n\n" + post.get('selftext')
            
            if content:
                analysis = analyze_text(content)
                if analysis:
                    successful_analyses += 1
                    print(f"\n{Fore.GREEN}Analysis Results:{Style.RESET_ALL}")
                    print(f"{Fore.WHITE}{analysis}{Style.RESET_ALL}")
                    store_to_supabase(post, analysis)
            else:
                print_error("Post has no content to analyze.")
        
        print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    
    # Print summary
    print(f"\n{Fore.CYAN}Summary:{Style.RESET_ALL}")
    print(f"Total posts processed: {total_posts}")
    print(f"Successful analyses: {successful_analyses}")
    print(f"Success rate: {(successful_analyses/total_posts)*100:.1f}%")

if __name__ == "__main__":
    main() 