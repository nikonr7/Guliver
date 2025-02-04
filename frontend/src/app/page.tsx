'use client';

import { useState } from 'react';
import { SearchPanel } from '@/components/SearchPanel';
import { ResultsPanel } from '@/components/ResultsPanel';
import { Header } from '@/components/Header';

interface Post {
  id: string;
  title: string;
  selftext: string;
  analysis: string;
  url: string;
  score: number;
  subreddit: string;
  similarity?: number;  // Optional for problem search
}

export default function Home() {
  const [searchResults, setSearchResults] = useState<Post[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [currentQuery, setCurrentQuery] = useState('');
  const [currentSubreddit, setCurrentSubreddit] = useState('');
  const [seenPostIds, setSeenPostIds] = useState<Set<string>>(new Set());
  const [isProblemSearch, setIsProblemSearch] = useState(false);
  const [currentTimeframe, setCurrentTimeframe] = useState<string>('');

  const handleSearch = async (query: string, subreddit: string) => {
    setIsLoading(true);
    setCurrentQuery(query);
    setCurrentSubreddit(subreddit);
    setSeenPostIds(new Set());
    setIsProblemSearch(false);
    
    try {
      const response = await fetch('http://localhost:8000/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          subreddit,
          match_threshold: 0.7,
          limit: 10
        }),
      });
      
      const data = await response.json();
      if (data.status === 'success') {
        setSearchResults(data.data);
        setSeenPostIds(new Set(data.data.map((post: Post) => post.id)));
      }
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleProblemSearch = async (subreddit: string, timeframe: string) => {
    setIsLoading(true);
    setCurrentSubreddit(subreddit);
    setCurrentTimeframe(timeframe);
    setCurrentQuery('');
    setSeenPostIds(new Set());
    setIsProblemSearch(true);
    
    try {
      const response = await fetch('http://localhost:8000/api/analyze-problems', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          subreddit,
          timeframe
        }),
      });
      
      const data = await response.json();
      if (data.status === 'success') {
        setSearchResults(data.data);
      }
    } catch (error) {
      console.error('Problem search failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoadMore = async () => {
    if (!currentSubreddit) return;
    if (isProblemSearch) return; // No load more for problem search currently
    
    setIsLoadingMore(true);
    try {
      const response = await fetch('http://localhost:8000/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: currentQuery,
          subreddit: currentSubreddit,
          match_threshold: 0.7,
          limit: 10,
          seen_ids: Array.from(seenPostIds)
        }),
      });
      
      const data = await response.json();
      if (data.status === 'success' && data.data.length > 0) {
        const newPosts = data.data as Post[];
        setSearchResults([...searchResults, ...newPosts]);
        setSeenPostIds(new Set([...Array.from(seenPostIds), ...newPosts.map((post: Post) => post.id)]));
      }
    } catch (error) {
      console.error('Load more failed:', error);
    } finally {
      setIsLoadingMore(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1">
            <SearchPanel 
              onSearch={handleSearch} 
              onProblemSearch={handleProblemSearch}
              isLoading={isLoading} 
            />
          </div>
          <div className="lg:col-span-2">
            <ResultsPanel 
              results={searchResults} 
              isLoading={isLoading}
              isLoadingMore={isLoadingMore}
              onLoadMore={handleLoadMore}
              hasMore={!isProblemSearch && searchResults.length > 0}
              isProblemSearch={isProblemSearch}
              timeframe={currentTimeframe}
            />
          </div>
        </div>
      </main>
    </div>
  );
}
