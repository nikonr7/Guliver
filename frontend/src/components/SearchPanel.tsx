import { useState } from 'react';

interface SearchPanelProps {
  onSearch: (query: string, subreddit: string) => void;
  onProblemSearch: (subreddit: string, timeframe: string) => void;
  isLoading: boolean;
}

export function SearchPanel({ onSearch, onProblemSearch, isLoading }: SearchPanelProps) {
  const [query, setQuery] = useState('');
  const [subreddit, setSubreddit] = useState('');
  const [showHelp, setShowHelp] = useState(false);
  const [searchMode, setSearchMode] = useState<'regular' | 'problem'>('regular');
  const [timeframe, setTimeframe] = useState('week');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (subreddit.trim()) {
      if (searchMode === 'regular' && query.trim()) {
        onSearch(query.trim(), subreddit.trim());
      } else if (searchMode === 'problem') {
        onProblemSearch(subreddit.trim(), timeframe);
      }
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-900">Search Posts</h2>
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
          <h3 className="text-sm font-medium text-blue-900 mb-2">How to use the search:</h3>
          <ul className="text-sm text-blue-800 space-y-2">
            <li>• Enter a subreddit name without "r/" (e.g., "technology", "startups")</li>
            <li>• Choose between Regular Search or Problem Search mode</li>
            <li>• Problem Search: Finds posts discussing problems, pain points, and needs</li>
            <li>• Regular Search: Search with your own query</li>
          </ul>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex gap-4 mb-4">
          <button
            type="button"
            onClick={() => setSearchMode('regular')}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
              searchMode === 'regular'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Regular Search
          </button>
          <button
            type="button"
            onClick={() => setSearchMode('problem')}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
              searchMode === 'problem'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Problem Search
          </button>
        </div>

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
            placeholder="technology"
            required
          />
          <p className="mt-1 text-xs text-gray-500">Popular: technology, startups, programming</p>
        </div>

        {searchMode === 'regular' ? (
          <div>
            <div className="flex justify-between items-center mb-1">
              <label htmlFor="query" className="block text-sm font-medium text-gray-700">
                Search Query
              </label>
              <span className="text-xs text-gray-500">Be specific for better results</span>
            </div>
            <input
              type="text"
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 placeholder-gray-400"
              placeholder="What are the biggest challenges in starting a SaaS business?"
              required
            />
            <p className="mt-1 text-xs text-gray-500">Try asking specific questions or describing your interests</p>
          </div>
        ) : (
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
              Find posts discussing problems, pain points, and user needs from the selected time period
            </p>
          </div>
        )}

        <button
          type="submit"
          disabled={isLoading || !subreddit.trim() || (searchMode === 'regular' && !query.trim())}
          className={`w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors ${
            isLoading || !subreddit.trim() || (searchMode === 'regular' && !query.trim())
              ? 'opacity-50 cursor-not-allowed'
              : ''
          }`}
        >
          {isLoading ? (
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              <span>Searching...</span>
            </div>
          ) : (
            searchMode === 'regular' ? 'Search Reddit' : 'Find Problems'
          )}
        </button>
      </form>
    </div>
  );
} 