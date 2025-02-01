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
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')  # Use service role key instead of anon key
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

def check_existing_analysis(post_id: str) -> tuple[bool, str]:
    """Check if post already exists in database and return its analysis if found."""
    try:
        print(f"{Fore.BLUE}Checking database for post ID: {post_id}{Style.RESET_ALL}")
        response = supabase.table("reddit_posts").select("*").eq("id", post_id).execute()
        
        # Debug print
        print(f"{Fore.YELLOW}Database response: {response}{Style.RESET_ALL}")
        
        if isinstance(response, dict) and response.get('data'):
            if len(response['data']) > 0:
                print_success(f"Found existing post in database: {post_id}")
                return True, response['data'][0]['analysis']
        return False, ""
    except Exception as e:
        print_error(f"Error checking existing analysis: {e}")
        return False, ""

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
        
        # Debug print
        print(f"{Fore.YELLOW}Attempting to insert data for post ID: {post.get('id')}{Style.RESET_ALL}")
        
        # Insert into the reddit_posts table
        result = supabase.table("reddit_posts").insert(data).execute()
        
        # Check for errors in the response
        if isinstance(result, dict):
            if result.get('data') and isinstance(result['data'], list):
                print_success(f"Successfully stored post {post.get('id')} in Supabase")
                return True
            elif result.get('data') and isinstance(result['data'], dict) and result['data'].get('message'):
                print_error(f"Supabase error: {result['data']['message']}")
                return False
        
        print_error(f"Unexpected response format from Supabase: {result}")
        return False
        
    except Exception as e:
        print_error(f"Error storing to Supabase: {e}")
        return False

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
    print(f"\n{Fore.CYAN}How many posts to analyze per subreddit? (1-25, default: 3){Style.RESET_ALL}")
    
    while True:
        try:
            limit_input = input(f"{Fore.GREEN}> {Style.RESET_ALL}").strip()
            
            if not limit_input:
                return 3
            
            limit = int(limit_input)
            if 1 <= limit <= 25:
                return limit
            else:
                print_error("Please enter a number between 1 and 25")
        except ValueError:
            print_error("Please enter a valid number")

def process_post(post: dict) -> bool:
    """Process a single post - either fetch existing analysis or create new one."""
    content = post.get('title', '')
    if post.get('selftext'):
        content += "\n\n" + post.get('selftext')
    
    if not content:
        print_error("Post has no content to analyze.")
        return False

    # Check if post already exists in database
    exists, existing_analysis = check_existing_analysis(post.get('id'))
    if exists:
        print_success("Found existing analysis in database")
        print(f"\n{Fore.GREEN}Existing Analysis:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{existing_analysis}{Style.RESET_ALL}")
        return True
    
    # If not exists, analyze and store
    analysis = analyze_text(content)
    if analysis:
        print(f"\n{Fore.GREEN}Analysis Results:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{analysis}{Style.RESET_ALL}")
        # Store directly without checking again
        store_to_supabase(post, analysis)
        return True
    
    return False

def main():
    while True:
        print_step("Starting Market Research Bot")
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        
        # Get subreddits from user
        subreddits = get_user_subreddits()
        
        # Get post limit from user
        post_limit = get_post_limit()
        
        total_posts = 0
        successful_analyses = 0
        cached_analyses = 0
        
        for subreddit in subreddits:
            print(f"\n{Fore.CYAN}Processing r/{subreddit}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'-'*50}{Style.RESET_ALL}")
            
            posts = fetch_posts(subreddit, size=post_limit)
            
            if not posts:
                print_error(f"No posts found in r/{subreddit}")
                continue
            
            for post in posts:
                total_posts += 1
                print(f"\n{Fore.YELLOW}Post {total_posts}:{Style.RESET_ALL}")
                print(f"Title: {post.get('title')[:100]}...")
                
                # Check if post exists in database
                exists, existing_analysis = check_existing_analysis(post.get('id'))
                if exists:
                    cached_analyses += 1
                    print(f"\n{Fore.GREEN}Existing Analysis:{Style.RESET_ALL}")
                    print(f"{Fore.WHITE}{existing_analysis}{Style.RESET_ALL}")
                    successful_analyses += 1
                else:
                    # Only analyze if not in cache
                    analysis = analyze_text(post.get('title', '') + "\n\n" + post.get('selftext', ''))
                    if analysis:
                        print(f"\n{Fore.GREEN}Analysis Results:{Style.RESET_ALL}")
                        print(f"{Fore.WHITE}{analysis}{Style.RESET_ALL}")
                        store_to_supabase(post, analysis)
                        successful_analyses += 1
            
            print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        
        # Print summary
        print(f"\n{Fore.CYAN}Summary:{Style.RESET_ALL}")
        print(f"Total posts processed: {total_posts}")
        print(f"Successful analyses: {successful_analyses}")
        print(f"Cached analyses: {cached_analyses}")
        print(f"New analyses: {successful_analyses - cached_analyses}")
        if total_posts > 0:
            print(f"Success rate: {(successful_analyses/total_posts)*100:.1f}%")
        else:
            print("Success rate: N/A (no posts processed)")
        
        print(f"\n{Fore.CYAN}Starting new analysis...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        print() # Add a blank line for better readability

if __name__ == "__main__":
    main() 