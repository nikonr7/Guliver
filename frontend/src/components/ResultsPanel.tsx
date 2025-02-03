interface Post {
  id: string;
  title: string;
  selftext: string;
  analysis: string;
  url: string;
  score: number;
  subreddit: string;
  similarity: number;
}

interface ResultsPanelProps {
  results: Post[];
  isLoading: boolean;
  isLoadingMore: boolean;
  onLoadMore: () => void;
  hasMore: boolean;
}

export function ResultsPanel({ results, isLoading, isLoadingMore, onLoadMore, hasMore }: ResultsPanelProps) {
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

  const formatAnalysis = (analysis: string) => {
    // Split the analysis into sections based on numbered points
    const sections = analysis.split(/(?=\d+\.\s)/).filter(Boolean);
    
    return sections.map((section, index) => {
      // Extract the title and content
      const [title, ...content] = section.split(':');
      const contentText = content.join(':').trim(); // Rejoin in case there were colons in the content
      
      return {
        title: title.trim(),
        content: contentText
      };
    });
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="space-y-4">
          <div className="w-full h-2 bg-gray-200 rounded overflow-hidden">
            <div className="h-full bg-blue-600 rounded animate-pulse w-3/4"></div>
          </div>
          <div className="animate-pulse space-y-6">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="space-y-3 border border-gray-100 rounded-lg p-4">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                <div className="h-20 bg-gray-200 rounded"></div>
                <div className="h-4 bg-gray-200 rounded w-1/4"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center">
          <p className="text-gray-500 mb-2">No results found</p>
          <p className="text-sm text-gray-400">Try:</p>
          <ul className="text-sm text-gray-400 mt-2 space-y-1">
            <li>• Using different keywords</li>
            <li>• Being more specific in your query</li>
            <li>• Checking if the subreddit name is correct</li>
          </ul>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-4 p-4 bg-white rounded-lg shadow">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Search Results</h2>
        <p className="text-sm text-gray-600">
          Found {results.length} relevant posts. Results are sorted by relevance to your query.
        </p>
      </div>

      <div className="space-y-4">
        {results.map((post) => (
          <article key={post.id} className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow">
            <header className="flex justify-between items-start mb-3">
              <h3 className="text-lg font-semibold text-gray-900 hover:text-blue-600">
                <a href={getRedditUrl(post.url)} target="_blank" rel="noopener noreferrer">
                  {post.title}
                </a>
              </h3>
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-gray-500">r/{post.subreddit}</span>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  {(post.similarity * 100).toFixed(1)}% match
                </span>
              </div>
            </header>
            
            {post.selftext && (
              <div className="mb-4">
                <p className="text-gray-600 text-sm line-clamp-3">{post.selftext}</p>
                {post.selftext.length > 250 && (
                  <button 
                    onClick={() => window.open(getRedditUrl(post.url), '_blank')}
                    className="text-sm text-blue-600 hover:text-blue-800 mt-1"
                  >
                    Read more →
                  </button>
                )}
              </div>
            )}
            
            {post.analysis && (
              <div className="mt-4 p-4 bg-blue-50 rounded-md">
                <div className="flex items-center mb-3">
                  <svg className="w-5 h-5 text-blue-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z" />
                  </svg>
                  <h4 className="text-sm font-semibold text-blue-900">AI Analysis</h4>
                </div>
                <div className="space-y-4">
                  {formatAnalysis(post.analysis).map((section, index) => (
                    <div key={index} className="border-l-2 border-blue-200 pl-4">
                      <h5 className="text-sm font-medium text-blue-800 mb-1">
                        {section.title}
                      </h5>
                      <p className="text-sm text-blue-700 leading-relaxed">
                        {section.content}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            <footer className="mt-4 flex justify-between items-center pt-3 border-t border-gray-100">
              <div className="flex items-center space-x-4">
                <span className="inline-flex items-center text-sm text-gray-500">
                  <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z" />
                  </svg>
                  {formatScore(post.score)}
                </span>
              </div>
              <a
                href={getRedditUrl(post.url)}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                View Discussion
                <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>
            </footer>
          </article>
        ))}
      </div>
      
      {hasMore && (
        <div className="flex justify-center mt-6">
          <button
            onClick={onLoadMore}
            disabled={isLoadingMore}
            className={`inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
              isLoadingMore ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            {isLoadingMore ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                <span>Loading more results...</span>
              </>
            ) : (
              <>
                <span>Load More Results</span>
                <svg className="ml-2 w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
} 