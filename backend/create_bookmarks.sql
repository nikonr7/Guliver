-- Create a table for storing post history
create table if not exists history (
    id uuid default gen_random_uuid() primary key,
    user_id uuid references auth.users not null,
    post_id text references reddit_posts(id) not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    notes text,
    -- Add a unique constraint to prevent duplicate history entries
    unique(user_id, post_id)
);

-- Create an index on user_id for better query performance
create index if not exists idx_history_user_id on history(user_id);

-- Create an index on post_id for better query performance
create index if not exists idx_history_post_id on history(post_id);

-- Enable Row Level Security (RLS)
alter table history enable row level security;

-- Create a policy that allows users to view only their own history
create policy "Users can view own history"
on history
for select
to authenticated
using (auth.uid() = user_id);

-- Create a policy that allows users to insert their own history
create policy "Users can insert own history"
on history
for insert
to authenticated
with check (auth.uid() = user_id);

-- Create a policy that allows users to delete from their own history
create policy "Users can delete from own history"
on history
for delete
to authenticated
using (auth.uid() = user_id);

-- Create a policy that allows users to update their own history
create policy "Users can update own history"
on history
for update
to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id); 