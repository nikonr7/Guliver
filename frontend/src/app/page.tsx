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
}

export default function Home() {
  const [searchResults, setSearchResults] = useState<Post[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentTimeframe, setCurrentTimeframe] = useState<string>('');

  const handleProblemSearch = async (subreddit: string, timeframe: string) => {
    setIsLoading(true);
    setCurrentTimeframe(timeframe);
    
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

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1">
            <SearchPanel 
              onProblemSearch={handleProblemSearch}
              isLoading={isLoading} 
            />
          </div>
          <div className="lg:col-span-2">
            <ResultsPanel 
              results={searchResults} 
              isLoading={isLoading}
              isLoadingMore={false}
              onLoadMore={() => {}}
              hasMore={false}
              isProblemSearch={true}
              timeframe={currentTimeframe}
            />
          </div>
        </div>
      </main>
    </div>
  );
}
