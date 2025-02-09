'use client';

import { useState, useRef, useEffect } from 'react';
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
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const clearPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  };

  const startPolling = (taskId: string) => {
    clearPolling();
    
    const pollStatus = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/analyze-problems/${taskId}/status`);
        const data = await response.json();
        console.log('Poll response:', data);

        if (data.status === 'success' && data.data) {
          setSearchResults(data.data);
          setIsLoading(false);
          setCurrentTaskId(null);
          clearPolling();
        } else if (data.status === 'cancelled' || data.status === 'error') {
          setIsLoading(false);
          setCurrentTaskId(null);
          clearPolling();
        }
      } catch (error) {
        console.error('Error polling status:', error);
        setIsLoading(false);
        setCurrentTaskId(null);
        clearPolling();
      }
    };

    pollIntervalRef.current = setInterval(pollStatus, 1000);
  };

  const handleStopSearch = async () => {
    console.log('Stop search called, current task ID:', currentTaskId);
    if (currentTaskId) {
      try {
        // First abort the fetch request
        if (abortControllerRef.current) {
          abortControllerRef.current.abort();
          abortControllerRef.current = null;
        }

        // Stop polling
        clearPolling();

        // Then tell the backend to stop the task
        const stopResponse = await fetch(`http://localhost:8000/api/analyze-problems/stop/${currentTaskId}`, {
          method: 'POST'
        });
        const stopData = await stopResponse.json();
        console.log('Stop response:', stopData);
      } catch (error) {
        console.error('Error stopping search:', error);
      } finally {
        setIsLoading(false);
        setCurrentTaskId(null);
      }
    } else {
      console.log('No task ID available to stop');
      setIsLoading(false);
    }
  };

  const handleProblemSearch = async (subreddit: string, timeframe: string) => {
    // Abort any existing search
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    if (currentTaskId) {
      await handleStopSearch();
    }

    // Create new AbortController for this search
    abortControllerRef.current = new AbortController();
    setIsLoading(true);
    setCurrentTimeframe(timeframe);
    setSearchResults([]); // Clear previous results
    
    try {
      console.log('Starting new search...');
      const response = await fetch('http://localhost:8000/api/analyze-problems', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          subreddit,
          timeframe
        }),
        signal: abortControllerRef.current.signal
      });
      
      const data = await response.json();
      console.log('Search response:', data);
      
      if (data.status === 'success' && data.task_id) {
        console.log('Setting task ID:', data.task_id);
        setCurrentTaskId(data.task_id);
        startPolling(data.task_id);
      } else {
        console.log('Search response not successful:', data);
        setIsLoading(false);
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Search was stopped');
      } else {
        console.error('Problem search failed:', error);
      }
      setIsLoading(false);
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearPolling();
      if (currentTaskId) {
        handleStopSearch();
      }
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1">
            <SearchPanel 
              onProblemSearch={handleProblemSearch}
              onStopSearch={handleStopSearch}
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
