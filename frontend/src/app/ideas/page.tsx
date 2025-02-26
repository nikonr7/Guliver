'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { supabase } from '@/lib/supabase';
import { Header } from '@/components/Header';
import Link from 'next/link';
import { ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline';
import { IdeaDetail } from '@/components/IdeaDetail';

interface Idea {
  id: string;
  title: string;
  selftext: string;
  analysis: string;
  url: string;
  score: number;
  subreddit: string;
  created_at: string;
  similarity: number;
  is_saved?: boolean;
}

export default function IdeasPage() {
  const [ideas, setIdeas] = useState<Idea[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const { user } = useAuth();
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [expandedIdea, setExpandedIdea] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState<number>(0);

  useEffect(() => {
    if (user) {
      fetchIdeas();
    }
  }, [user]);

  const fetchIdeas = async () => {
    try {
      setIsLoading(true);
      
      // Get all posts from reddit_posts table
      const { data: allPosts, error: postsError, count } = await supabase
        .from('reddit_posts')
        .select('*', { count: 'exact' })
        .order('created_at', { ascending: false });

      if (postsError) throw postsError;
      
      // Get saved posts from history
      const { data: history, error: historyError } = await supabase
        .from('history')
        .select('post_id')
        .eq('user_id', user?.id);

      if (historyError) throw historyError;
      
      // Create a set of saved post IDs for quick lookup
      const savedPostIds = new Set(history.map(item => item.post_id));
      
      // Transform the data and mark saved posts
      const transformedPosts = allPosts.map(post => ({
        ...post,
        similarity: 1.0, // Default similarity score
        is_saved: savedPostIds.has(post.id)
      }));
      
      // Extract unique categories (subreddits)
      const uniqueCategories = Array.from(new Set(transformedPosts.map(post => post.subreddit)));
      setCategories(uniqueCategories);
      
      setIdeas(transformedPosts);
      setTotalCount(count || transformedPosts.length);
    } catch (error) {
      console.error('Error fetching ideas:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle save/unsave
  const handleSaveToggle = () => {
    fetchIdeas();
  };

  // Filter ideas based on search query and category
  const filteredIdeas = ideas.filter(idea => {
    const matchesSearch = searchQuery === '' || 
      idea.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (idea.analysis && idea.analysis.toLowerCase().includes(searchQuery.toLowerCase()));
    
    const matchesCategory = selectedCategory === '' || idea.subreddit === selectedCategory;
    
    return matchesSearch && matchesCategory;
  });

  // Function to categorize ideas
  const categorizeIdea = (idea: Idea) => {
    // This is a simple categorization based on content
    // You can implement more sophisticated categorization logic
    if (idea.title.toLowerCase().includes('looking for') || 
        idea.title.toLowerCase().includes('need') || 
        idea.title.toLowerCase().includes('searching')) {
      return 'Looking for solution';
    } else if (idea.title.toLowerCase().includes('alternative') || 
               idea.title.toLowerCase().includes('instead of')) {
      return 'Seeking alternative';
    } else if (idea.title.toLowerCase().includes('help') || 
               idea.title.toLowerCase().includes('advice')) {
      return 'Seeking advice';
    } else {
      return 'General discussion';
    }
  };

  const toggleExpand = (ideaId: string) => {
    if (expandedIdea === ideaId) {
      setExpandedIdea(null);
    } else {
      setExpandedIdea(ideaId);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">A curated list of users looking for SaaS solutions</h1>
              <p className="text-gray-600 mt-2">{totalCount}+ leads found and counting!</p>
            </div>
          </div>
          
          {/* Search and filter section */}
          <div className="mb-8 flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative rounded-md shadow-sm">
                <input
                  type="text"
                  className="block w-full rounded-md border-0 py-3 pl-4 pr-10 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm sm:leading-6"
                  placeholder="Sign in to search the database..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 text-gray-400">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                  </svg>
                </div>
              </div>
            </div>
            <div className="w-full md:w-auto">
              <select
                className="block w-full rounded-md border-0 py-3 pl-4 pr-10 text-gray-900 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm sm:leading-6"
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
              >
                <option value="">All Categories</option>
                {categories.map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>
            </div>
            <button
              className="px-4 py-3 bg-gray-500 text-white rounded-md hover:bg-gray-600 transition-colors"
              onClick={() => fetchIdeas()}
            >
              Search
            </button>
          </div>
          
          {/* Table header */}
          <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 sm:rounded-lg bg-white">
            <div className="grid grid-cols-12 border-b border-gray-200 bg-gray-50 text-sm font-medium text-gray-500">
              <div className="col-span-6 px-6 py-3 text-left">Opportunity</div>
              <div className="col-span-2 px-6 py-3 text-left">Date</div>
              <div className="col-span-3 px-6 py-3 text-left">Category</div>
              <div className="col-span-1 px-6 py-3 text-left"></div>
            </div>
            
            {isLoading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              </div>
            ) : filteredIdeas.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-500 text-lg">No ideas found matching your criteria.</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-200 bg-white">
                {filteredIdeas.map((idea) => (
                  <div key={idea.id} className="grid grid-cols-12">
                    <div className="col-span-6 px-6 py-4">
                      <div className="text-sm font-medium text-gray-900 line-clamp-2">
                        {idea.is_saved && (
                          <span className="inline-flex items-center rounded-full bg-green-50 px-2 py-1 text-xs font-medium text-green-700 ring-1 ring-inset ring-green-600/20 mr-2">
                            Saved
                          </span>
                        )}
                        {idea.title}
                      </div>
                    </div>
                    <div className="col-span-2 px-6 py-4 text-sm text-gray-500">
                      {new Date(idea.created_at).toLocaleDateString()}
                    </div>
                    <div className="col-span-3 px-6 py-4">
                      <span className="inline-flex items-center rounded-md bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700 ring-1 ring-inset ring-blue-700/10">
                        {idea.subreddit}
                      </span>
                    </div>
                    <div 
                      className="col-span-1 px-6 py-4 text-right cursor-pointer"
                      onClick={() => toggleExpand(idea.id)}
                    >
                      {expandedIdea === idea.id ? (
                        <ChevronUpIcon className="h-5 w-5 text-gray-400" />
                      ) : (
                        <ChevronDownIcon className="h-5 w-5 text-gray-400" />
                      )}
                    </div>
                    
                    {/* Expanded detail view */}
                    {expandedIdea === idea.id && (
                      <IdeaDetail
                        id={idea.id}
                        title={idea.title}
                        selftext={idea.selftext}
                        analysis={idea.analysis}
                        url={idea.url}
                        score={idea.score}
                        subreddit={idea.subreddit}
                        created_at={idea.created_at}
                        isOpen={expandedIdea === idea.id}
                        onToggle={() => toggleExpand(idea.id)}
                        is_saved={idea.is_saved}
                        onSaveToggle={handleSaveToggle}
                      />
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
} 