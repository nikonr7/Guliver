from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SearchRequest(BaseModel):
    query: str
    subreddit: str
    match_threshold: float = 0.7
    limit: int = 5

class AnalysisRequest(BaseModel):
    text: str

class BatchProcessRequest(BaseModel):
    subreddits: List[str]
    post_limit: int = 10

class SmartAnalysisRequest(BaseModel):
    query: str
    subreddit: str
    min_similarity: float = 0.7
    max_posts: int = 5
    analyze_count: Optional[int] = None
    comment_limit: int = 5

class SubredditValidationResponse(BaseModel):
    is_valid: bool
    message: str

class ProblemAnalysisRequest(BaseModel):
    subreddit: str
    timeframe: str = 'week'  # 'week', 'month', or 'year'
    min_score: int = 5  # Minimum score threshold

class SearchHistory(BaseModel):
    subreddit: str
    timeframe: str
    last_search_time: datetime
    last_post_time: datetime 