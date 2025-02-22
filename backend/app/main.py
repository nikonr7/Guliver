from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from .api.routes import search, analysis, subreddit
from .utils.logging import print_banner, print_step, print_success

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

def main():
    """Main function to run the FastAPI server."""
    print_banner()
    print_step("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main() 