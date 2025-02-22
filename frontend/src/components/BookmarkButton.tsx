import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';
import { useAuth } from '@/contexts/AuthContext';
import { BookmarkIcon as BookmarkOutline } from '@heroicons/react/24/outline';
import { BookmarkIcon as BookmarkSolid } from '@heroicons/react/24/solid';

interface BookmarkButtonProps {
  postId: string;
}

export function BookmarkButton({ postId }: BookmarkButtonProps) {
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    checkBookmarkStatus();
  }, [postId]);

  const checkBookmarkStatus = async () => {
    if (!user) {
      setIsLoading(false);
      return;
    }

    try {
      const { data } = await supabase
        .from('bookmarks')
        .select('id')
        .eq('user_id', user.id)
        .eq('post_id', postId)
        .single();

      setIsBookmarked(!!data);
    } catch (error) {
      console.error('Error checking bookmark status:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleBookmark = async () => {
    if (!user) {
      // You might want to redirect to login or show a message
      return;
    }

    setIsLoading(true);

    try {
      if (isBookmarked) {
        // Remove bookmark
        await supabase
          .from('bookmarks')
          .delete()
          .eq('user_id', user.id)
          .eq('post_id', postId);
        setIsBookmarked(false);
      } else {
        // Add bookmark
        await supabase
          .from('bookmarks')
          .insert([
            {
              user_id: user.id,
              post_id: postId,
            },
          ]);
        setIsBookmarked(true);
      }
    } catch (error) {
      console.error('Error toggling bookmark:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (!user) return null;

  return (
    <button
      onClick={toggleBookmark}
      disabled={isLoading}
      className={`p-2 rounded-full hover:bg-gray-100 transition-colors ${
        isLoading ? 'opacity-50 cursor-not-allowed' : ''
      }`}
      aria-label={isBookmarked ? 'Remove from bookmarks' : 'Add to bookmarks'}
    >
      {isBookmarked ? (
        <BookmarkSolid className="h-5 w-5 text-blue-600" />
      ) : (
        <BookmarkOutline className="h-5 w-5 text-gray-600 hover:text-blue-600" />
      )}
    </button>
  );
} 