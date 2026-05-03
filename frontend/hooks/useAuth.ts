/**
 * React hook for accessing authentication state.
 * 
 * Provides centralized access to authentication state, user information,
 * and authentication actions (login, logout).
 * 
 * Requirements: 24.6
 */
'use client';

import { useState, useEffect } from 'react';
import { getToken, getUser, logout as authLogout } from '@/lib/auth';

interface User {
  username: string;
  email?: string;
  full_name?: string;
}

interface UseAuthReturn {
  /** Current authenticated user, or null if not authenticated */
  user: User | null;
  /** Whether authentication state is being loaded */
  loading: boolean;
  /** Whether user is currently authenticated */
  isAuthenticated: boolean;
  /** Function to log out the current user */
  logout: () => void;
}

/**
 * Hook for accessing authentication state and actions.
 * 
 * This hook provides:
 * - Current user information
 * - Authentication status
 * - Loading state during initialization
 * - Logout function
 * 
 * Requirements: 24.6
 * 
 * @returns Authentication state and actions
 * 
 * @example
 * function MyComponent() {
 *   const { user, isAuthenticated, logout } = useAuth();
 *   
 *   if (!isAuthenticated) {
 *     return <div>Please log in</div>;
 *   }
 *   
 *   return (
 *     <div>
 *       <p>Welcome, {user?.username}!</p>
 *       <button onClick={logout}>Logout</button>
 *     </div>
 *   );
 * }
 */
export function useAuth(): UseAuthReturn {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Check for stored token and user on mount
    const token = getToken();
    const storedUser = getUser();

    if (token && storedUser) {
      setUser(storedUser);
      setIsAuthenticated(true);
    } else {
      setUser(null);
      setIsAuthenticated(false);
    }

    setLoading(false);
  }, []);

  const logout = () => {
    authLogout();
    setUser(null);
    setIsAuthenticated(false);
  };

  return {
    user,
    loading,
    isAuthenticated,
    logout,
  };
}
