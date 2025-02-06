-- Drop existing policies if any
drop policy if exists "Enable all operations for authenticated users" on reddit_posts;

-- Create a policy that allows all operations for all users (since we're using service role key)
create policy "Allow all operations for service role"
on reddit_posts
for all
using (true)
with check (true);

-- Enable RLS on the table (if not already enabled)
alter table reddit_posts enable row level security;

-- Grant necessary permissions
grant all on reddit_posts to service_role;
grant all on reddit_posts to authenticated;
grant all on reddit_posts to anon; 