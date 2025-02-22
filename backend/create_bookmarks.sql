-- Create a table for storing bookmarked posts
create table if not exists bookmarks (
    id uuid default gen_random_uuid() primary key,
    user_id uuid references auth.users not null,
    post_id text references reddit_posts(id) not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    notes text,
    -- Add a unique constraint to prevent duplicate bookmarks
    unique(user_id, post_id)
);

-- Create an index on user_id for better query performance
create index if not exists idx_bookmarks_user_id on bookmarks(user_id);

-- Create an index on post_id for better query performance
create index if not exists idx_bookmarks_post_id on bookmarks(post_id);

-- Enable Row Level Security (RLS)
alter table bookmarks enable row level security;

-- Create a policy that allows users to view only their own bookmarks
create policy "Users can view own bookmarks"
on bookmarks
for select
to authenticated
using (auth.uid() = user_id);

-- Create a policy that allows users to insert their own bookmarks
create policy "Users can insert own bookmarks"
on bookmarks
for insert
to authenticated
with check (auth.uid() = user_id);

-- Create a policy that allows users to delete their own bookmarks
create policy "Users can delete own bookmarks"
on bookmarks
for delete
to authenticated
using (auth.uid() = user_id);

-- Create a policy that allows users to update their own bookmarks
create policy "Users can update own bookmarks"
on bookmarks
for update
to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id); 