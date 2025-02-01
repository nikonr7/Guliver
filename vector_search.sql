-- Function to match posts based on embedding similarity
create or replace function match_posts(
    query_embedding vector(1536),
    match_threshold float,
    match_count int,
    subreddit_filter text default null
)
returns table (
    id text,
    title text,
    selftext text,
    analysis text,
    subreddit text,
    url text,
    score integer,
    similarity float
)
language plpgsql
as $$
begin
    return query
    select
        reddit_posts.id,
        reddit_posts.title,
        reddit_posts.selftext,
        reddit_posts.analysis,
        reddit_posts.subreddit,
        reddit_posts.url,
        reddit_posts.score,
        1 - (reddit_posts.embedding <=> query_embedding) as similarity
    from reddit_posts
    where
        -- Apply subreddit filter only if provided
        (subreddit_filter is null or reddit_posts.subreddit = subreddit_filter)
        -- Only return posts that are more similar than the threshold
        and 1 - (reddit_posts.embedding <=> query_embedding) > match_threshold
    order by reddit_posts.embedding <=> query_embedding
    limit match_count;
end;
$$; 