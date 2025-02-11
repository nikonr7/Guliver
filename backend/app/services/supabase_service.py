from typing import List, Dict, Optional
from datetime import datetime, timezone
from ..config import supabase
from ..utils.logging import print_step, print_success, print_error

async def store_post_with_embedding(post: dict, embedding: List[float], analysis: str = None) -> bool:
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

async def update_post_analysis(post_id: str, analysis: str) -> bool:
    """Update the analysis of an existing post."""
    try:
        result = supabase.table("reddit_posts").update({"analysis": analysis}).eq("id", post_id).execute()
        if result.data:
            print_success(f"Updated analysis for post {post_id}")
            return True
        return False
    except Exception as e:
        print_error(f"Error updating analysis: {e}")
        return False

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

async def update_search_history(subreddit: str, timeframe: str, last_post_time: datetime) -> bool:
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
        return True
    except Exception as e:
        print_error(f"Error updating search history: {e}")
        return False

async def semantic_search_with_offset(
    query: str,
    subreddit: str,
    match_threshold: float = 0.7,
    limit: int = 10,
    seen_ids: set = None
) -> List[Dict]:
    """Enhanced semantic search that can skip already seen posts."""
    from .openai_service import generate_embedding  # Import here to avoid circular dependency
    
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