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
}

export function ResultsPanel({ results, isLoading }: ResultsPanelProps) {
  const getRedditUrl = (url: string) => {
    // If the URL starts with 'http', it's already a full URL
    if (url.startsWith('http')) {
      return url;
    }
    // If it starts with '/r/', add the Reddit domain
    if (url.startsWith('/r/')) {
      return `https://reddit.com${url}`;
    }
    // Fallback: construct the full URL
    return `https://reddit.com/r/${url}`;
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="space-y-2">
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              <div className="h-20 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-500 text-center">No results found. Try a different search query.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {results.map((post) => (
        <div key={post.id} className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-lg font-semibold text-gray-900">{post.title}</h3>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">r/{post.subreddit}</span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                {(post.similarity * 100).toFixed(1)}% match
              </span>
            </div>
          </div>
          
          {post.selftext && (
            <p className="text-gray-600 text-sm mb-4 line-clamp-3">{post.selftext}</p>
          )}
          
          {post.analysis && (
            <div className="mt-4 p-4 bg-blue-50 rounded-md">
              <h4 className="text-sm font-medium text-blue-900 mb-2">Analysis</h4>
              <p className="text-sm text-blue-700">{post.analysis}</p>
            </div>
          )}
          
          <div className="mt-4 flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">
                Score: {post.score}
              </span>
            </div>
            <a
              href={getRedditUrl(post.url)}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              View on Reddit →
            </a>
          </div>
        </div>
      ))}
    </div>
  );
} 