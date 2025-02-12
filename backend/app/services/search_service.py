from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
from ..utils.logging import print_step, print_success, print_error
from .reddit import fetch_posts_async, fetch_posts_by_timeframe, fetch_comments_async
from .openai_service import analyze_post_with_comments, generate_embedding, analyze_posts_batch
from .supabase_service import (
    store_post_with_embedding,
    update_post_analysis,
    get_analyzed_posts,
    get_last_search,
    update_search_history,
    semantic_search_with_offset
)
import asyncio
from ..utils.task_manager import task_manager

async def process_subreddit_posts(subreddit: str, post_limit: int) -> int:
    """Process posts from a single subreddit."""
    print_step(f"Processing r/{subreddit}...")
    posts = await fetch_posts_async(subreddit, size=post_limit)
    
    if not posts:
        print_error(f"No posts found in r/{subreddit}")
        return 0
    
    print_success(f"Found {len(posts)} posts")
    
    # Process posts in parallel
    async def process_single_post(post):
        try:
            # Check if post exists and has analysis
            exists = await get_analyzed_posts(subreddit, datetime.fromtimestamp(post['created_utc']))
            if exists:
                return True
            
            # Generate embedding and store post in parallel
            content = post.get('title', '') + "\n" + post.get('selftext', '')
            embedding = await generate_embedding(content)
            
            if not embedding:
                return False
            
            # Store post with embedding
            return await store_post_with_embedding(post, embedding)
        except Exception as e:
            print_error(f"Error processing post {post.get('id')}: {str(e)}")
            return False
    
    # Process all posts concurrently
    results = await asyncio.gather(*[process_single_post(post) for post in posts])
    successful_posts = sum(1 for result in results if result)
    
    return successful_posts

async def fetch_and_filter_posts(subreddits: List[str], post_limit: int = 100) -> int:
    """Fetch and process posts from multiple subreddits in parallel."""
    print_step(f"Processing {len(subreddits)} subreddits in parallel...")
    
    # Process all subreddits concurrently
    results = await asyncio.gather(
        *[process_subreddit_posts(subreddit, post_limit) for subreddit in subreddits]
    )
    
    # Sum up the successful posts from all subreddits
    total_successful = sum(results)
    
    for subreddit, successful in zip(subreddits, results):
        print(f"Processed {successful} posts from r/{subreddit}")
    
    print(f"\nTotal processed: {total_successful}")
    return total_successful

async def smart_analysis_pipeline(
    query: str, 
    subreddit: str = None, 
    min_similarity: float = 0.7, 
    max_posts: int = 5, 
    analyze_count: Optional[int] = None,
    comment_limit: int = 5,
    batch_size: int = 5,
    user_id: Optional[str] = None,
    task_id: Optional[str] = None
) -> List[Dict]:
    """Smart pipeline that uses embeddings first, then advanced AI only for relevant posts."""
    try:
        print_step(f"Starting smart analysis for query: {query}")
        if subreddit:
            print_step(f"Searching in r/{subreddit}")
        
        await _update_task_status(task_id, 'processing')
        similar_posts = await _fetch_and_search_posts(query, subreddit, min_similarity, max_posts)
        
        if not similar_posts:
            return []
        
        posts_to_analyze = _get_posts_to_analyze(similar_posts, analyze_count)
        await _process_posts_analysis(posts_to_analyze, batch_size)
        
        return similar_posts
    except Exception as e:
        print_error(f"Error in smart analysis pipeline: {str(e)}")
        await _update_task_status(task_id, 'failed', str(e))
        raise

async def _update_task_status(task_id: Optional[str], status: str, error: str = None) -> None:
    """Update task status if task_id is provided."""
    if task_id:
        task_manager.update_task_status(task_id, status, error)

async def _fetch_and_search_posts(
    query: str,
    subreddit: Optional[str],
    min_similarity: float,
    max_posts: int
) -> List[Dict]:
    """Fetch new posts and search for similar ones."""
    print_step(f"Fetching new posts...")
    
    # Generate query embedding in parallel with post fetching
    query_embedding_task = generate_embedding(query)
    
    if subreddit:
        # Single subreddit search
        posts_task = process_subreddit_posts(subreddit, 100)
        # Wait for both tasks
        query_embedding, _ = await asyncio.gather(query_embedding_task, posts_task)
        similar_posts = await semantic_search_with_offset(query, subreddit, min_similarity, max_posts, query_embedding)
    else:
        # Multi-subreddit search
        default_subreddits = ["startups", "Entrepreneur", "SaaS"]
        posts_task = fetch_and_filter_posts(default_subreddits, 100)
        # Wait for both tasks
        query_embedding, _ = await asyncio.gather(query_embedding_task, posts_task)
        similar_posts = await semantic_search_with_offset(query, None, min_similarity, max_posts, query_embedding)
    
    if not similar_posts:
        print_error("No similar posts found")
        return []
    
    print_success(f"Found {len(similar_posts)} relevant posts")
    return similar_posts

def _get_posts_to_analyze(posts: List[Dict], analyze_count: Optional[int]) -> List[Dict]:
    """Get subset of posts that need analysis."""
    return posts[:analyze_count] if analyze_count else posts

async def _process_posts_analysis(posts: List[Dict], batch_size: int) -> None:
    """Process posts analysis in parallel batches."""
    posts_needing_analysis = [post for post in posts if not post.get('analysis')]
    if not posts_needing_analysis:
        return

    # Fetch comments and generate embeddings for all posts in parallel
    async def prepare_post(post):
        comments_task = fetch_comments_async(post['id'])
        content = post['title'] + "\n" + post.get('selftext', '')
        embedding_task = generate_embedding(content)
        
        post['comments'], post['embedding'] = await asyncio.gather(comments_task, embedding_task)
        return post
    
    print_step(f"Preparing {len(posts_needing_analysis)} posts (fetching comments and generating embeddings)...")
    prepared_posts = await asyncio.gather(*[prepare_post(post) for post in posts_needing_analysis])
    
    # Filter out posts where embedding generation failed
    valid_posts = [post for post in prepared_posts if post.get('embedding')]
    
    if not valid_posts:
        print_error("No valid posts to analyze after preparation")
        return
    
    # Process in batches
    batches = [valid_posts[i:i + batch_size] for i in range(0, len(valid_posts), batch_size)]
    print_step(f"Analyzing {len(valid_posts)} posts in {len(batches)} batches...")
    
    # Process each batch in parallel and store results immediately
    async def process_batch(batch):
        analyses = await analyze_posts_batch(batch, batch_size)
        # Store results for this batch immediately
        store_tasks = []
        for post, analysis in zip(batch, analyses):
            if analysis:
                store_tasks.append(
                    store_post_with_embedding(post, post['embedding'], analysis)
                )
                post['analysis'] = analysis
        
        if store_tasks:
            results = await asyncio.gather(*store_tasks)
            successful = sum(1 for r in results if r)
            print_success(f"Stored {successful}/{len(store_tasks)} posts from batch")
    
    # Process all batches concurrently
    await asyncio.gather(*[process_batch(batch) for batch in batches])

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
        
        # Process posts in parallel
        async def process_post(post):
            try:
                print_step(f"Processing post: {post['title'][:100]}...")
                
                # Fetch comments and generate embedding in parallel
                comments_task = fetch_comments_async(post['id'])
                content = post['title'] + "\n" + post.get('selftext', '')
                embedding_task = generate_embedding(content)
                
                # Wait for both tasks to complete
                post['comments'], embedding = await asyncio.gather(comments_task, embedding_task)
                
                if not embedding:
                    return None
                
                # Analyze post with comments
                analysis = await analyze_post_with_comments(post)
                if not analysis:
                    return None
                
                post['analysis'] = analysis
                
                # Store post with analysis and embedding
                if await store_post_with_embedding(post, embedding, analysis):
                    print_success(f"Stored post with analysis: {post['id']}")
                    return post
                
                return None
            except Exception as e:
                print_error(f"Error processing post {post.get('id')}: {str(e)}")
                return None
        
        # Process all posts concurrently
        results = await asyncio.gather(*[process_post(post) for post in scored_posts])
        analyzed_posts = [post for post in results if post is not None]
        
        return analyzed_posts
    except Exception as e:
        print_error(f"Error in analyze_problem_posts: {str(e)}")
        return [] 