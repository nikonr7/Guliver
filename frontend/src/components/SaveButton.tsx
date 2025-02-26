import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';
import { useAuth } from '@/contexts/AuthContext';

interface SaveButtonProps {
  postId: string;
  onSaveToggle?: () => void;
}

export function SaveButton({ postId, onSaveToggle }: SaveButtonProps) {
  const [isSaved, setIsSaved] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    checkSaveStatus();
  }, [postId]);

  const checkSaveStatus = async () => {
    if (!user) {
      setIsLoading(false);
      return;
    }

    try {
      const { data } = await supabase
        .from('history')
        .select('id')
        .eq('user_id', user.id)
        .eq('post_id', postId)
        .single();

      setIsSaved(!!data);
    } catch (error) {
      console.error('Error checking save status:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleSave = async () => {
    if (!user) {
      return;
    }

    setIsLoading(true);

    try {
      if (isSaved) {
        // Remove from history
        await supabase
          .from('history')
          .delete()
          .eq('user_id', user.id)
          .eq('post_id', postId);
        setIsSaved(false);
      } else {
        // Add to history
        await supabase
          .from('history')
          .insert([
            {
              user_id: user.id,
              post_id: postId,
            },
          ]);
        setIsSaved(true);
      }
      
      // Call the callback function if provided
      if (onSaveToggle) {
        onSaveToggle();
      }
    } catch (error) {
      console.error('Error toggling save:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (!user) return null;

  return (
    <button
      onClick={toggleSave}
      disabled={isLoading}
      className={`inline-flex items-center px-4 py-2 text-sm font-medium rounded-md ${
        isSaved
          ? 'bg-blue-600 text-white hover:bg-blue-700'
          : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
      } transition-colors ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      {isLoading ? (
        <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-1"></div>
      ) : null}
      {isSaved ? 'Saved' : 'Save'}
    </button>
  );
} 