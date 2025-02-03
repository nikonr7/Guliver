'use client';

import { useState } from 'react';
import { SearchPanel } from '@/components/SearchPanel';
import { ResultsPanel } from '@/components/ResultsPanel';
import { Header } from '@/components/Header';

export default function Home() {
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSearch = async (query: string, subreddit: string) => {
    setIsLoading(true);
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
      }
    } catch (error) {
      console.error('Search failed:', error);
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
            <SearchPanel onSearch={handleSearch} isLoading={isLoading} />
          </div>
          <div className="lg:col-span-2">
            <ResultsPanel results={searchResults} isLoading={isLoading} />
          </div>
        </div>
      </main>
    </div>
  );
}
