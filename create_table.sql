-- Create a table for storing Reddit posts and their analysis
create table if not exists reddit_posts (
    id text primary key,
    title text not null,
    selftext text,
    analysis text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    subreddit text,
    url text,
    score integer
);

-- Create an index on created_at for better query performance
create index if not exists idx_reddit_posts_created_at on reddit_posts(created_at);

-- Enable Row Level Security (RLS)
alter table reddit_posts enable row level security;

-- Create a policy that allows all operations for authenticated users
create policy "Enable all operations for authenticated users"
on reddit_posts
for all
to authenticated
using (true)
with check (true); 