import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from supabase import create_client, Client
from .utils.logging import print_step, print_success, print_error
import sys

# Load environment variables
load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Reddit API Configuration
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = 'MarketResearchBot/1.0'

# Supabase Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Initialize Supabase client
try:
    print_step("Initializing Supabase client...")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Test the connection
    print_step("Testing Supabase connection...")
    test = supabase.table("reddit_posts").select("id").limit(1).execute()
    print_success("Successfully connected to Supabase")
except Exception as e:
    print_error(f"Failed to initialize Supabase: {str(e)}")
    print(f"Please check your Supabase credentials and connection.")
    sys.exit(1)  # Exit if we can't connect to Supabase 