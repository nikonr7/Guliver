import React, { useEffect, useState } from 'react';

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

interface ResultsPanelProps {
  results: Post[];
  isLoading: boolean;
  isLoadingMore: boolean;
  onLoadMore: () => void;
  hasMore: boolean;
  isProblemSearch?: boolean;
  timeframe?: string;
}

export function ResultsPanel({ 
  results, 
  isLoading, 
  isLoadingMore, 
  onLoadMore, 
  hasMore, 
  isProblemSearch,
  timeframe 
}: ResultsPanelProps) {
  const [currentLoadingMessage, setCurrentLoadingMessage] = useState(0);

  const loadingMessages = isProblemSearch ? [
    "Fetching recent posts...",
    "Scanning for problem discussions...",
    "Finding pain points and needs...",
    "Starting AI analysis (this takes a few minutes)...",
    "Analyzing posts and all comments with AI...",
    "Extracting actionable insights...",
    "Finalizing results..."
  ] : [
    "Fetching fresh posts...",
    "Performing semantic search...",
    "Finding most relevant discussions...",
    "Starting AI analysis (this takes 2-3 minutes)...",
    "Analyzing post 1/5...",
    "Analyzing post 2/5...",
    "Analyzing post 3/5...",
    "Analyzing post 4/5...",
    "Analyzing post 5/5...",
    "Finalizing results..."
  ];

  // Effect to cycle through loading messages
  useEffect(() => {
    if (!isLoading) {
      setCurrentLoadingMessage(0);
      return;
    }

    const interval = setInterval(() => {
      setCurrentLoadingMessage((prev) => {
        if (prev < loadingMessages.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, isProblemSearch ? 4000 : 3000);

    return () => clearInterval(interval);
  }, [isLoading, loadingMessages.length, isProblemSearch]);

  const getRedditUrl = (url: string) => {
    if (url.startsWith('http')) {
      return url;
    }
    if (url.startsWith('/r/')) {
      return `https://reddit.com${url}`;
    }
    return `https://reddit.com/r/${url}`;
  };

  const formatScore = (score: number) => {
    if (score >= 1000000) {
      return `${(score / 1000000).toFixed(1)}M`;
    }
    if (score >= 1000) {
      return `${(score / 1000).toFixed(1)}K`;
    }
    return score.toString();
  };

  const formatAnalysis = (analysis: string, postId: string) => {
    // Split the analysis into sections based on numbered points
    const sections = analysis.split(/(?=\d+\.\s)/).filter(Boolean);
    
    return sections.map((section, index) => {
      // Extract the title and content
      const [title, ...content] = section.split(':');
      const contentText = content.join(':').trim(); // Rejoin in case there were colons in the content
      
      return {
        id: `${postId}-section-${index}`,
        title: title.trim(),
        content: contentText
      };
    });
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex flex-col items-center justify-center space-y-4">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-gray-600">{loadingMessages[currentLoadingMessage]}</p>
        </div>
      </div>
    );
  }

  if (!results.length) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-center text-gray-600">No results found. Try adjusting your search criteria.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {isProblemSearch && timeframe && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="text-blue-800 font-medium mb-2">Problem Search Results</h3>
          <p className="text-blue-600 text-sm">
            Showing problems and pain points discussed in the last {timeframe === 'week' ? 'week' : timeframe === 'month' ? 'month' : 'year'}
          </p>
          <p className="text-blue-600 text-sm mt-1">
            Sorted by community votes (minimum 5 votes)
          </p>
        </div>
      )}

      {/* Sort posts by score before mapping */}
      {[...results]
        .sort((a, b) => b.score - a.score)
        // Remove duplicates based on ID and score combination
        .filter((post, index, self) => 
          index === self.findIndex((p) => p.id === post.id && p.score === post.score)
        )
        .map((post, index) => (
        <div key={`post-${post.id}-${index}`} className="bg-white rounded-lg shadow p-6">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-medium bg-green-100 text-green-800">
                  {formatScore(post.score)} votes
                </span>
                <span className="text-sm text-gray-500">r/{post.subreddit}</span>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-1">{post.title}</h3>
              {post.selftext && (
                <div className="mt-2 text-sm text-gray-600 line-clamp-3">
                  {post.selftext}
                </div>
              )}
            </div>
            <a
              href={getRedditUrl(post.url)}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-shrink-0 text-blue-600 hover:text-blue-800 text-sm"
            >
              View on Reddit →
            </a>
          </div>

          {post.analysis && (
            <div className="mt-4 space-y-4">
              <h4 className="font-medium text-gray-900">Analysis</h4>
              <div className="space-y-3">
                {formatAnalysis(post.analysis, post.id).map((section) => (
                  <div key={section.id} className="text-sm">
                    <div className="font-medium text-gray-800">{section.title}</div>
                    <div className="mt-1 text-gray-600">{section.content}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}

      {hasMore && (
        <div className="flex justify-center">
          <button
            onClick={onLoadMore}
            disabled={isLoadingMore}
            className={`px-6 py-2 text-sm font-medium text-blue-600 bg-white border border-blue-300 rounded-md shadow-sm hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
              isLoadingMore ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            {isLoadingMore ? 'Loading...' : 'Load More Results'}
          </button>
        </div>
      )}
    </div>
  );
} 