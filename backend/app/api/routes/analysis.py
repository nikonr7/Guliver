import time
import asyncio
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, BackgroundTasks
from ...models.schemas import AnalysisRequest, ProblemAnalysisRequest
from ...services.openai_service import analyze_text, analyze_post_with_comments
from ...services.search_service import analyze_problem_posts
from ...services.supabase_service import (
    get_last_search,
    get_analyzed_posts,
    update_search_history,
    update_post_analysis
)
from ...config import supabase  # Add this import for supabase client
from ...utils.task_manager import task_manager
from ...utils.logging import print_step, print_success, print_error

router = APIRouter()

@router.post("/analyze")
async def analyze(request: AnalysisRequest):
    try:
        analysis = await analyze_text(request.text)
        return {"status": "success", "analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-with-comments")
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

@router.post("/analyze-problems")
async def analyze_problems(request: ProblemAnalysisRequest, background_tasks: BackgroundTasks):
    """Analyze problem-related posts in a subreddit."""
    # Generate a unique task ID
    task_id = str(int(time.time() * 1000))  # millisecond timestamp as ID
    print_step(f"Creating new search task with ID: {task_id}")
    
    # Initialize task in task manager
    await task_manager.add_task(task_id, "system", request.dict())
    
    async def search_task():
        try:
            if request.timeframe not in ['week', 'month', 'year']:
                raise HTTPException(status_code=400, detail="Invalid timeframe")
            
            # Calculate the time range
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
                try:
                    # Get the timestamp strings from the search history
                    last_search_time_str = last_search['last_search_time']
                    last_post_time_str = last_search['last_post_time']
                    
                    # Parse PostgreSQL ISO 8601 timestamps
                    # Format: YYYY-MM-DD"T"HH24:MI:SS.MSOF
                    def parse_timestamp(ts_str: str) -> datetime:
                        try:
                            # Try parsing with milliseconds
                            dt = datetime.strptime(ts_str, '%Y-%m-%dT%H:%M:%S.%f+00:00')
                        except ValueError:
                            # Try without milliseconds
                            dt = datetime.strptime(ts_str, '%Y-%m-%dT%H:%M:%S+00:00')
                        return dt.replace(tzinfo=timezone.utc)
                    
                    last_search_time = parse_timestamp(last_search_time_str)
                    last_post_time = parse_timestamp(last_post_time_str)
                    
                    # Check if cache is fresh (less than 24 hours old)
                    if now - last_search_time < timedelta(hours=24):
                        needs_new_search = False
                        print_step("Last search was recent, using cached results")
                    
                except (ValueError, KeyError) as e:
                    print_error(f"Error parsing timestamps: {str(e)}")
                    # Explicitly invalidate cache on timestamp parsing error
                    last_search_time = now
                    last_post_time = now
                    needs_new_search = True
                
                # Get existing analyzed posts regardless of cache freshness
                print_step("Checking for existing analyzed posts...")
                existing_posts = await get_analyzed_posts(request.subreddit, start_time)
                if existing_posts:
                    print_success(f"Found {len(existing_posts)} existing analyzed posts")
                else:
                    print_step("No existing posts found in cache")
            
            new_posts = []
            if needs_new_search:
                print_step(f"Searching for new problem-related posts in r/{request.subreddit}...")
                try:
                    new_posts = await analyze_problem_posts(
                        request.subreddit, 
                        request.timeframe,
                        request.min_score
                    )
                    
                    # Always update search history after a new search
                    newest_post_time = now
                    if new_posts:
                        # If we found posts, use the newest post time
                        newest_post_time = max(
                            datetime.fromtimestamp(post.get('created_utc', 0), tz=timezone.utc)
                            for post in new_posts
                        )
                        print_success(f"Found and analyzed {len(new_posts)} new problem-related posts")
                    else:
                        print_step("No new problem-related posts found")
                    
                    # Update search history regardless of whether posts were found
                    await update_search_history(request.subreddit, request.timeframe, newest_post_time)
                    
                except Exception as e:
                    print_error(f"Error during problem search: {str(e)}")
                    # Continue with existing posts if available
                    pass

            # Combine and sort all posts by score
            all_posts = sorted(
                existing_posts + new_posts, 
                key=lambda x: x.get('score', 0), 
                reverse=True
            )
            
            if not all_posts:
                print_step("No posts found (neither in cache nor from new search)")
            
            # Update task with results
            task_manager.update_task_status(task_id, 'completed')
            return {
                "status": "success",
                "task_id": task_id,
                "timeframe": request.timeframe,
                "subreddit": request.subreddit,
                "min_score": request.min_score,
                "post_count": len(all_posts),
                "data": all_posts,
                "source": "mixed" if existing_posts and new_posts else "new" if new_posts else "cache",
                "cache_used": not needs_new_search,
                "cache_stats": {
                    "cached_posts_count": len(existing_posts),
                    "new_posts_count": len(new_posts)
                }
            }
        except Exception as e:
            print_error(f"Error in search task {task_id}: {str(e)}")
            task_manager.update_task_status(task_id, 'failed', str(e))
            raise

    # Create and store the task
    task = asyncio.create_task(search_task())
    task_manager.register_task(task_id, task)
    print_success(f"Task {task_id} created and stored")
    
    return {
        "status": "success",
        "task_id": task_id,
        "message": "Search started"
    }

@router.get("/analyze-problems/{task_id}/status")
async def get_search_status(task_id: str):
    """Get the status of a search task."""
    print_step(f"Checking status of task {task_id}")
    task_info = task_manager.get_task_status(task_id)
    
    if not task_info:
        raise HTTPException(status_code=404, detail="Search task not found")
    
    if task_id in task_manager.active_tasks:
        task = task_manager.active_tasks[task_id]
        if task.done():
            try:
                result = await task
                task_manager.update_task_status(task_id, 'completed')
                print_success(f"Task {task_id} completed")
                return result
            except asyncio.CancelledError:
                return {"status": "cancelled", "task_id": task_id}
            except Exception as e:
                task_manager.update_task_status(task_id, 'failed', str(e))
                return {"status": "error", "task_id": task_id, "error": str(e)}
        else:
            return {"status": "running", "task_id": task_id}
    else:
        # Task exists but is not active (completed, failed, or cancelled)
        return {
            "status": task_info['status'],
            "task_id": task_id,
            "error": task_info.get('error'),
            "result": task_info.get('result')
        }

@router.post("/analyze-problems/stop/{task_id}")
async def stop_search(task_id: str):
    """Stop an ongoing search task."""
    print_step(f"Received stop request for task {task_id}")
    task_info = task_manager.get_task_status(task_id)
    
    if not task_info:
        raise HTTPException(status_code=404, detail="Search task not found")
    
    await task_manager.cancel_task(task_id)
    return {"status": "cancelled", "task_id": task_id} 