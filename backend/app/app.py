from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta, timezone
from fastapi import BackgroundTasks
from typing import Dict
from dotenv import load_dotenv
from backend.lib.types import *
from backend.lib.reddit import *
from backend.lib.gpt import *
from backend.lib.supabase import *
from backend.lib.log_utils import *
from backend.lib.utils import cancel_task
import asyncio
import uvicorn

app = FastAPI(title="Guliver API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

active_tasks: Dict[str, asyncio.Task] = {}

def run_server():
    """Main function to run the FastAPI server."""
    print_banner()
    print(f"{Fore.CYAN}Starting FastAPI server...{Style.RESET_ALL}")
    uvicorn.run(app, host="0.0.0.0", port=8000)


# API Routes
@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/search")
async def search(request: SearchRequest):
    try:
        # Use smart_analysis_pipeline instead of unified_subreddit_search
        results = await smart_analysis_pipeline(
            query=request.query,
            subreddit=request.subreddit,
            min_similarity=request.match_threshold,
            max_posts=request.limit,
            analyze_count=request.limit,  # Analyze all returned posts
            comment_limit=5
        )
        
        if not results:
            return {"status": "success", "data": []}
            
        print_success(f"Returning {len(results)} analyzed posts")
        return {"status": "success", "data": results}
    except Exception as e:
        print_error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def analyze(request: AnalysisRequest):
    try:
        analysis = await analyze_text(request.text)
        return {"status": "success", "analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/subreddit/{subreddit}/posts")
async def get_subreddit_posts(
    subreddit: str,
    limit: int = Query(default=10, le=100)
):
    try:
        posts = await fetch_posts_async(subreddit, limit)
        return {"status": "success", "data": posts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/smart-analysis")
async def smart_analysis(request: SmartAnalysisRequest):
    """Full smart analysis pipeline including comments and AI analysis."""
    try:
        results = await smart_analysis_pipeline(
            query=request.query,
            subreddit=request.subreddit,
            min_similarity=request.min_similarity,
            max_posts=request.max_posts,
            analyze_count=request.analyze_count,
            comment_limit=request.comment_limit
        )
        return {"status": "success", "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/batch-process")
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

@app.get("/api/validate-subreddit/{subreddit}")
async def validate_subreddit_endpoint(subreddit: str) -> SubredditValidationResponse:
    """Validate if a subreddit exists and is accessible."""
    is_valid = validate_subreddit(subreddit)
    message = f"r/{subreddit} is valid" if is_valid else f"r/{subreddit} is invalid or inaccessible"
    return SubredditValidationResponse(is_valid=is_valid, message=message)

@app.post("/api/analyze-with-comments")
async def analyze_with_comments(post_id: str, comment_limit: int = 5):
    """Analyze a post together with its top comments."""
    supabase = SupabaseConn()
    
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

@app.get("/api/subreddit/{subreddit}/stats")
async def get_subreddit_stats(subreddit: str):
    """Get statistics about stored posts for a subreddit."""
    supabase = SupabaseConn
    
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


@app.post("/api/analyze-problems")
async def analyze_problems(request: ProblemAnalysisRequest, background_tasks: BackgroundTasks):
    """Analyze problem-related posts in a subreddit."""
    # Generate a unique task ID
    task_id = str(int(time.time() * 1000))  # millisecond timestamp as ID
    print_step(f"Creating new search task with ID: {task_id}")
    
    async def search_task():
        try:
            if request.timeframe not in ['week', 'month', 'year']:
                raise HTTPException(status_code=400, detail="Invalid timeframe. Must be 'week', 'month', or 'year'")
            
            # Calculate the time range we need
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
                last_search_time = datetime.fromisoformat(last_search['last_search_time'])
                last_post_time = datetime.fromisoformat(last_search['last_post_time'])
                
                # Ensure timezone awareness
                if last_search_time.tzinfo is None:
                    last_search_time = last_search_time.replace(tzinfo=timezone.utc)
                if last_post_time.tzinfo is None:
                    last_post_time = last_post_time.replace(tzinfo=timezone.utc)
                
                # Get existing analyzed posts
                print_step("Checking for existing analyzed posts...")
                existing_posts = await get_analyzed_posts(request.subreddit, start_time)
                
                if existing_posts:
                    print_success(f"Found {len(existing_posts)} existing analyzed posts")
                    
                    # If the last search was very recent, we might not need a new search
                    if now - last_search_time < timedelta(hours=24):
                        needs_new_search = False
                        print_step("Last search was recent, using cached results")
                    else:
                        # We have some results but need to search for newer posts
                        print_step(f"Found previous search from {last_search_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                        print_step("Will search for new posts since last search")
                        start_time = last_post_time
                else:
                    print_step("No existing analyzed posts found, will perform full search")

            new_posts = []
            newest_post_time = None
            
            if needs_new_search:
                print_step(f"Searching for new problem-related posts in r/{request.subreddit}...")
                try:
                    # Pass min_score to analyze_problem_posts
                    new_posts = await analyze_problem_posts(
                        request.subreddit, 
                        request.timeframe,
                        request.min_score
                    )
                    if new_posts:
                        newest_post_time = max(
                            datetime.fromtimestamp(post.get('created_utc', 0), tz=timezone.utc)
                            for post in new_posts
                        )
                        print_success(f"Found and analyzed {len(new_posts)} new problem-related posts")
                        
                        # Store the analyzed posts
                        for post in new_posts:
                            if post.get('analysis'):
                                await update_post_analysis(post['id'], post['analysis'])
                                print_success(f"Analysis stored for post {post['id']}")
                        
                        # Update search history with the newest post time
                        if newest_post_time:
                            await update_search_history(request.subreddit, request.timeframe, newest_post_time)
                    else:
                        print_step("No new problem-related posts found that weren't already analyzed")
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
                print_step("No posts found matching the criteria")
            else:
                print_success(f"Returning {len(all_posts)} total posts")
                
            result = {
                "status": "success",
                "task_id": task_id,
                "timeframe": request.timeframe,
                "subreddit": request.subreddit,
                "min_score": request.min_score,
                "post_count": len(all_posts),
                "data": all_posts,
                "source": "mixed" if existing_posts and new_posts else "new" if new_posts else "cache"
            }
            return result
        except asyncio.CancelledError:
            print_step(f"Search task {task_id} was cancelled")
            raise
        except Exception as e:
            print_error(f"Error in search task {task_id}: {str(e)}")
            raise

    # Create and store the task
    task = asyncio.create_task(search_task())
    active_tasks[task_id] = task
    print_success(f"Task {task_id} created and stored")
    
    try:
        # Return immediately with task ID
        return {
            "status": "success",
            "task_id": task_id,
            "message": "Search started"
        }
    except Exception as e:
        print_error(f"Error starting task {task_id}: {str(e)}")
        active_tasks.pop(task_id, None)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analyze-problems/{task_id}/status")
async def get_search_status(task_id: str):
    """Get the status of a search task."""
    print_step(f"Checking status of task {task_id}")
    if task_id in active_tasks:
        task = active_tasks[task_id]
        if task.done():
            try:
                result = await task
                # Only remove the task after successfully getting the result
                active_tasks.pop(task_id, None)
                print_success(f"Task {task_id} completed and cleaned up")
                return result
            except asyncio.CancelledError:
                active_tasks.pop(task_id, None)
                return {"status": "cancelled", "task_id": task_id}
            except Exception as e:
                active_tasks.pop(task_id, None)
                return {"status": "error", "task_id": task_id, "error": str(e)}
        else:
            return {"status": "running", "task_id": task_id}
    else:
        raise HTTPException(status_code=404, detail="Search task not found")

@app.post("/api/analyze-problems/stop/{task_id}")
async def stop_search(task_id: str):
    """Stop an ongoing search task."""
    print_step(f"Received stop request for task {task_id}")
    if task_id in active_tasks:
        await cancel_task(task_id)
        return {"status": "cancelled", "task_id": task_id}
    else:
        print_error(f"Task {task_id} not found")
        raise HTTPException(status_code=404, detail="Search task not found")