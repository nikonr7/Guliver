from supabase import create_client
from datetime import datetime, timezone
from typing import List, Optional, Dict
from backend.lib.log_utils import *
from backend.lib.constants import *


class SupabaseConn:
  _connection_instance = None

  def __new__(cls):
    if cls._connection_instance == None:
      cls._connection_instance = super().__new__(cls)
      try:
        print_step("Initializing Supabase client...")
        cls._connection_instance = create_client(SUPABASE_URL, SUPABASE_KEY)

      except Exception as e:
        print_error(f"Failed to initialize Supabase: {str(e)}")
        sys.exit(1)
    return cls._connection_instance
  

async def store_post_with_embedding(post: dict, embedding: List[float], analysis: str = None):
    """Store post with its embedding, optionally including analysis."""
    supabase=SupabaseConn()
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
    supabase = SupabaseConn()
    
    try:
        result = supabase.table("reddit_posts").update({"analysis": analysis}).eq("id", post_id).execute()
        if isinstance(result, dict) and result.get('data'):
            print_success(f"Updated analysis for post {post_id}")
            return True
        return False
    except Exception as e:
        print_error(f"Error updating analysis: {e}")
        return False
    
async def get_last_search(subreddit: str, timeframe: str) -> Optional[Dict]:
    """Get the last search results for this subreddit and timeframe."""
    supabase = SupabaseConn()
    
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
    
async def get_analyzed_posts(subreddit: str, since_time: datetime) -> List[Dict]:
    """Get already analyzed posts from database."""
    supabase = SupabaseConn()
    
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
    
async def update_search_history(subreddit: str, timeframe: str, last_post_time: datetime):
    """Update search history with new timestamp."""
    supabase = SupabaseConn()
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