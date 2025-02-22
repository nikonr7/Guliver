'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { supabase } from '@/lib/supabase';
import { Header } from '@/components/Header';
import { SaveButton } from '@/components/SaveButton';

interface SavedPost {
  id: string;
  title: string;
  selftext: string;
  analysis: string;
  url: string;
  score: number;
  subreddit: string;
  created_at: string;
}

export default function HistoryPage() {
  const [savedPosts, setSavedPosts] = useState<SavedPost[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      fetchSavedPosts();
    }
  }, [user]);

  const fetchSavedPosts = async () => {
    try {
      const { data: history, error: historyError } = await supabase
        .from('history')
        .select(`
          post_id,
          created_at,
          reddit_posts (
            id,
            title,
            selftext,
            analysis,
            url,
            score,
            subreddit
          )
        `)
        .eq('user_id', user?.id)
        .order('created_at', { ascending: false });

      if (historyError) throw historyError;

      const posts = history
        .map((item) => ({
          ...item.reddit_posts,
          created_at: item.created_at,
        }))
        .filter((post): post is SavedPost => post !== null);

      setSavedPosts(posts);
    } catch (error) {
      console.error('Error fetching saved posts:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">History</h1>
          
          {isLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            </div>
          ) : savedPosts.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500 text-lg">You haven't saved any posts yet.</p>
            </div>
          ) : (
            <div className="space-y-6">
              {savedPosts.map((post) => (
                <div
                  key={post.id}
                  className="bg-white shadow rounded-lg overflow-hidden"
                >
                  <div className="p-6">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h2 className="text-xl font-semibold text-gray-900 mb-2">
                          {post.title}
                        </h2>
                        <p className="text-sm text-gray-500 mb-4">
                          Posted in r/{post.subreddit} • Score: {post.score}
                        </p>
                      </div>
                      <SaveButton postId={post.id} />
                    </div>
                    
                    {post.selftext && (
                      <div className="mt-4 text-gray-600">
                        <p>{post.selftext.length > 300 
                          ? `${post.selftext.substring(0, 300)}...` 
                          : post.selftext}
                        </p>
                      </div>
                    )}
                    
                    {post.analysis && (
                      <div className="mt-4 bg-gray-50 p-4 rounded-md">
                        <h3 className="text-sm font-medium text-gray-900 mb-2">
                          Analysis
                        </h3>
                        <p className="text-sm text-gray-600">{post.analysis}</p>
                      </div>
                    )}
                    
                    <div className="mt-4 flex justify-between items-center">
                      <a
                        href={post.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-blue-600 hover:text-blue-800"
                      >
                        View on Reddit →
                      </a>
                      <span className="text-sm text-gray-500">
                        Saved on {new Date(post.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
} 