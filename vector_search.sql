-- Function to match posts based on embedding similarity
create or replace function match_posts(
    query_embedding vector(1536),
    match_threshold float,
    match_count int
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
    where 1 - (reddit_posts.embedding <=> query_embedding) > match_threshold
    order by reddit_posts.embedding <=> query_embedding
    limit match_count;
end;
$$; 