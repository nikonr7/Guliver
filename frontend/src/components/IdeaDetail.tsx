import { useState } from 'react';
import { SaveButton } from '@/components/SaveButton';

interface IdeaDetailProps {
  id: string;
  title: string;
  selftext?: string;
  analysis?: string;
  url?: string;
  score?: number;
  subreddit: string;
  created_at: string;
  isOpen: boolean;
  onToggle: () => void;
  is_saved?: boolean;
  onSaveToggle?: () => void;
}

export function IdeaDetail({
  id,
  title,
  selftext,
  analysis,
  url,
  score,
  subreddit,
  created_at,
  isOpen,
  onToggle,
  is_saved,
  onSaveToggle
}: IdeaDetailProps) {
  if (!isOpen) return null;

  return (
    <div className="col-span-12 bg-gray-50 p-4 rounded-b-lg border-t border-gray-200">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2">
          {selftext && (
            <div className="mb-4">
              <h3 className="text-sm font-medium text-gray-900 mb-2">Description</h3>
              <div className="bg-white p-3 rounded-md shadow-sm text-sm text-gray-700">
                {selftext}
              </div>
            </div>
          )}
          
          {analysis && (
            <div className="mb-4">
              <h3 className="text-sm font-medium text-gray-900 mb-2">Analysis</h3>
              <div className="bg-white p-3 rounded-md shadow-sm text-sm text-gray-700">
                {analysis}
              </div>
            </div>
          )}
        </div>
        
        <div className="md:col-span-1">
          <div className="bg-white p-4 rounded-md shadow-sm">
            <h3 className="text-sm font-medium text-gray-900 mb-3">Details</h3>
            
            <div className="space-y-3">
              <div>
                <p className="text-xs text-gray-500">Subreddit</p>
                <p className="text-sm text-gray-900">r/{subreddit}</p>
              </div>
              
              {score !== undefined && (
                <div>
                  <p className="text-xs text-gray-500">Score</p>
                  <p className="text-sm text-gray-900">{score}</p>
                </div>
              )}
              
              <div>
                <p className="text-xs text-gray-500">Date</p>
                <p className="text-sm text-gray-900">{new Date(created_at).toLocaleDateString()}</p>
              </div>
              
              <div>
                <p className="text-xs text-gray-500">Status</p>
                <p className="text-sm text-gray-900">
                  {is_saved ? (
                    <span className="inline-flex items-center text-green-700">
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4 mr-1">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clipRule="evenodd" />
                      </svg>
                      Saved to your history
                    </span>
                  ) : (
                    <span className="text-gray-500">Not saved</span>
                  )}
                </p>
              </div>
              
              <div className="pt-2 flex items-center justify-between">
                <SaveButton postId={id} onSaveToggle={onSaveToggle} />
                
                {url && (
                  <a
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-blue-600 hover:text-blue-800"
                  >
                    View original →
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 