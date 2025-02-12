import { useState } from 'react';

interface SearchPanelProps {
  onProblemSearch: (subreddit: string, timeframe: string) => void;
  onStopSearch: () => void;
  isLoading: boolean;
}

export function SearchPanel({ onProblemSearch, onStopSearch, isLoading }: SearchPanelProps) {
  const [subreddit, setSubreddit] = useState('');
  const [showHelp, setShowHelp] = useState(false);
  const [timeframe, setTimeframe] = useState('week');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (subreddit.trim()) {
      onProblemSearch(subreddit.trim(), timeframe);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-900">Find Problems & Pain Points</h2>
        <button
          type="button"
          onClick={() => setShowHelp(!showHelp)}
          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
        >
          {showHelp ? 'Hide Help' : 'Show Help'}
        </button>
      </div>

      {showHelp && (
        <div className="mb-6 p-4 bg-blue-50 rounded-md">
          <h3 className="text-sm font-medium text-blue-900 mb-2">How it works:</h3>
          <ul className="text-sm text-blue-800 space-y-2">
            <li>• Enter a subreddit name without "r/" (e.g., "startups", "SaaS")</li>
            <li>• Choose a time period to analyze</li>
            <li>• We'll find posts discussing problems, pain points, and needs</li>
            <li>• Results are sorted by community votes (minimum 5 votes)</li>
          </ul>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <div className="flex justify-between items-center mb-1">
            <label htmlFor="subreddit" className="block text-sm font-medium text-gray-700">
              Subreddit
            </label>
            <span className="text-xs text-gray-500">Without "r/"</span>
          </div>
          <input
            type="text"
            id="subreddit"
            value={subreddit}
            onChange={(e) => setSubreddit(e.target.value.replace(/^r\//, ''))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 placeholder-gray-400"
            placeholder="startups"
            required
          />
          <p className="mt-1 text-xs text-gray-500">Popular: startups, SaaS, smallbusiness, entrepreneur</p>
        </div>

        <div>
          <label htmlFor="timeframe" className="block text-sm font-medium text-gray-700 mb-1">
            Time Period
          </label>
          <select
            id="timeframe"
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
          >
            <option value="week">Last Week</option>
            <option value="month">Last Month</option>
            <option value="year">Last Year</option>
          </select>
          <p className="mt-1 text-xs text-gray-500">
            Find problems and pain points discussed in the selected time period
          </p>
        </div>

        <div className="flex space-x-3">
          <button
            type="submit"
            disabled={isLoading || !subreddit.trim()}
            className={`flex-1 flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors ${
              isLoading || !subreddit.trim() ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            {isLoading ? (
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Searching...</span>
              </div>
            ) : (
              'Find Problems'
            )}
          </button>
          
          {isLoading && (
            <button
              type="button"
              onClick={onStopSearch}
              className="px-4 py-3 border border-red-300 rounded-md shadow-sm text-sm font-medium text-red-600 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
            >
              Stop
            </button>
          )}
        </div>
      </form>
    </div>
  );
} 