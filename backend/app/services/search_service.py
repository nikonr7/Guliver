from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
from ..utils.logging import print_step, print_success, print_error
from .reddit import fetch_posts_async, fetch_posts_by_timeframe
from .openai_service import analyze_post_with_comments, generate_embedding
from .supabase_service import (
    store_post_with_embedding,
    update_post_analysis,
    get_analyzed_posts,
    get_last_search,
    update_search_history,
    semantic_search_with_offset
)

async def process_subreddit_posts(subreddit: str, post_limit: int) -> int:
    """Process posts from a single subreddit."""
    successful_posts = 0
    
    print_step(f"Processing r/{subreddit}...")
    posts = await fetch_posts_async(subreddit, size=post_limit)
    
    if not posts:
        print_error(f"No posts found in r/{subreddit}")
        return 0
    
    print_success(f"Found {len(posts)} posts")
    
    # Process posts one by one
    for post in posts:
        # Check if post exists and has analysis
        exists = await get_analyzed_posts(subreddit, datetime.fromtimestamp(post['created_utc']))
        if exists:
            successful_posts += 1
            continue
        
        # Generate embedding
        content = post.get('title', '') + "\n" + post.get('selftext', '')
        embedding = await generate_embedding(content)
        
        if not embedding:
            continue
        
        # Store post with embedding
        if await store_post_with_embedding(post, embedding):
            successful_posts += 1
    
    return successful_posts

async def fetch_and_filter_posts(subreddits: List[str], post_limit: int = 100) -> int:
    """Fetch and process posts from multiple subreddits."""
    print_step(f"Processing {len(subreddits)} subreddits...")
    
    total_successful = 0
    for subreddit in subreddits:
        successful = await process_subreddit_posts(subreddit, post_limit)
        total_successful += successful
        
        print(f"\nProcessed {successful} posts from r/{subreddit}")
    
    print(f"\nTotal processed: {total_successful}")
    return total_successful

async def smart_analysis_pipeline(
    query: str, 
    subreddit: str = None, 
    min_similarity: float = 0.7, 
    max_posts: int = 5, 
    analyze_count: Optional[int] = None,
    comment_limit: int = 5
) -> List[Dict]:
    """Smart pipeline that uses embeddings first, then advanced AI only for relevant posts."""
    print_step(f"Starting smart analysis for query: {query}")
    if subreddit:
        print_step(f"Searching in r/{subreddit}")
    
    # First, fetch and store new posts to ensure fresh data
    print_step(f"Fetching new posts from r/{subreddit}...")
    await process_subreddit_posts(subreddit, 100)  # Fetch 100 posts to have a good pool
    
    # Find similar posts using vector search
    similar_posts = await semantic_search_with_offset(query, subreddit, min_similarity, max_posts)
    if not similar_posts:
        print_error("No similar posts found")
        return []
    
    print_success(f"Found {len(similar_posts)} relevant posts")
    
    # If analyze_count is specified, only analyze that many posts
    posts_to_analyze = similar_posts[:analyze_count] if analyze_count else similar_posts
    
    # Analyze relevant posts that haven't been analyzed yet
    for i, post in enumerate(posts_to_analyze):
        if not post.get('analysis'):
            print_step(f"Analyzing post {i+1}/{len(posts_to_analyze)}: {post['title'][:100]}...")
            analysis = await analyze_post_with_comments(post)
            if analysis:
                await update_post_analysis(post['id'], analysis)
                post['analysis'] = analysis
                print_success(f"Analysis completed for post {post['id']}")
    
    return similar_posts

async def analyze_problem_posts(subreddit: str, timeframe: str = 'week', min_score: int = 5) -> List[Dict]:
    """Find and analyze problem-related posts."""
    try:
        # Find posts with problem-related keywords
        posts = await fetch_posts_by_timeframe(subreddit, timeframe)
        if not posts:
            print_step(f"No posts found in r/{subreddit} for timeframe: {timeframe}")
            return []
        
        # Filter by score
        scored_posts = [post for post in posts if post['score'] >= min_score]
        if not scored_posts:
            print_step(f"No posts found with score >= {min_score}")
            return []
        
        # Analyze each post with all its comments
        analyzed_posts = []
        for post in scored_posts:
            try:
                print_step(f"Analyzing post: {post['title'][:100]}...")
                analysis = await analyze_post_with_comments(post)
                if analysis:
                    post['analysis'] = analysis
                    # Generate embedding for the post content
                    content = post['title'] + "\n" + post.get('selftext', '')
                    embedding = await generate_embedding(content)
                    if embedding:
                        # Store the post with analysis and embedding
                        if await store_post_with_embedding(post, embedding, analysis):
                            analyzed_posts.append(post)
                            print_success(f"Stored post with analysis: {post['id']}")
                    else:
                        print_error(f"Failed to generate embedding for post: {post['id']}")
            except Exception as e:
                print_error(f"Error processing post {post.get('id')}: {str(e)}")
                continue
        
        return analyzed_posts
    except Exception as e:
        print_error(f"Error in analyze_problem_posts: {str(e)}")
        return [] 