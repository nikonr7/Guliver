'use client';

import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { usePathname } from 'next/navigation';

export function Header() {
  const { user, signOut } = useAuth();
  const pathname = usePathname();

  const handleLogout = async () => {
    try {
      await signOut();
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };

  const isActive = (path: string) => {
    return pathname === path ? 'text-blue-600' : 'text-gray-600 hover:text-gray-900';
  };

  return (
    <header className="bg-white shadow">
      <div className="container mx-auto px-4 py-6">
        <div className="flex justify-between items-center">
          <div className="flex items-center">
            <h1 className="text-2xl font-bold text-gray-900">Reddit Analysis Cabinet</h1>
          </div>
          <div className="flex items-center space-x-6">
            <nav className="flex space-x-4">
              <Link 
                href="/dashboard" 
                className={`${isActive('/dashboard')} px-3 py-2 rounded-md text-sm font-medium`}
              >
                Search
              </Link>
              <Link 
                href="/history" 
                className={`${isActive('/history')} px-3 py-2 rounded-md text-sm font-medium`}
              >
                History
              </Link>
              <Link 
                href="/ideas" 
                className={`${isActive('/ideas')} px-3 py-2 rounded-md text-sm font-medium`}
              >
                Ideas
              </Link>
              <Link 
                href="/analytics" 
                className={`${isActive('/analytics')} px-3 py-2 rounded-md text-sm font-medium`}
              >
                Analytics
              </Link>
            </nav>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">{user?.email}</span>
              <button
                onClick={handleLogout}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
} 