from fastapi import APIRouter, HTTPException, Query
from ...models.schemas import BatchProcessRequest, SubredditValidationResponse
from ...services.reddit import validate_subreddit, fetch_posts_async
from ...services.search_service import fetch_and_filter_posts
from ...config import supabase
from ...utils.logging import print_step, print_success, print_error

router = APIRouter()

@router.get("/validate/{subreddit}")
async def validate_subreddit_endpoint(subreddit: str) -> SubredditValidationResponse:
    """Validate if a subreddit exists and is accessible."""
    is_valid = validate_subreddit(subreddit)
    message = f"r/{subreddit} is valid" if is_valid else f"r/{subreddit} is invalid or inaccessible"
    return SubredditValidationResponse(is_valid=is_valid, message=message)

@router.get("/{subreddit}/posts")
async def get_subreddit_posts(
    subreddit: str,
    limit: int = Query(default=10, le=100)
):
    try:
        posts = await fetch_posts_async(subreddit, limit)
        return {"status": "success", "data": posts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-process")
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

@router.get("/{subreddit}/stats")
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