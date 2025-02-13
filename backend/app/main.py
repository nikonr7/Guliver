from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import json
from .api.routes import search, analysis, subreddit
from .utils.logging import print_banner, print_step
from .utils.task_manager import get_task, remove_task

# Initialize FastAPI app
app = FastAPI(title="Guliver API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(analysis.router, prefix="/api", tags=["analysis"])
app.include_router(subreddit.router, prefix="/api/subreddit", tags=["subreddit"])

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}


async def event_generator(task_id: str):
    try:
        current_task = get_task(task_id)
        if current_task.done():
            task_results = await current_task
            task_results_to_json = json.dumps(task_results)
            yield f"data: {task_results_to_json}\n\n"
            
    except Exception as e:
        pass
    finally:
        remove_task(task_id)

@app.get("/events/{task_id}")
async def task_events(task_id: str):
    return StreamingResponse(event_generator(task_id), media_type="text/event-stream")

def main():
    """Main function to run the FastAPI server."""
    print_banner()
    print_step("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main() 