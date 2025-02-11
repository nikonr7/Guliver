from fastapi import APIRouter, HTTPException
from ...models.schemas import SearchRequest, SmartAnalysisRequest
from ...services.search_service import smart_analysis_pipeline
from ...utils.logging import print_step, print_success, print_error

router = APIRouter()

@router.post("/search")
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

@router.post("/smart-analysis")
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