/**
 * Authentication utilities for EduRisk AI frontend.
 * 
 * Provides functions for user authentication, token management, and logout.
 * 
 * Requirements: 23.3, 23.4, 24.1, 24.2
 */

const TOKEN_KEY = 'edurisk_auth_token';
const USER_KEY = 'edurisk_user';

interface AuthTokens {
  access_token: string;
  token_type: string;
}

interface User {
  username: string;
  email?: string;
  full_name?: string;
}

/**
 * Store JWT token securely in localStorage.
 * 
 * @param token - JWT access token
 * 
 * Requirements: 23.4, 24.1
 */
export function setToken(token: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(TOKEN_KEY, token);
    
    // Also set a cookie for middleware access (Requirement 24.7)
    // Note: This is a simple cookie, not httpOnly, but it's only used for route protection
    // The actual token is stored in localStorage
    document.cookie = `edurisk_auth_token=${token}; path=/; max-age=86400; SameSite=Strict`;
  }
}

/**
 * Retrieve stored JWT token.
 * 
 * @returns JWT token or null if not found
 * 
 * Requirements: 24.2
 */
export function getToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem(TOKEN_KEY);
  }
  return null;
}

/**
 * Clear stored JWT token and user data.
 * 
 * Requirements: 24.2
 */
export function clearToken(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    
    // Also clear the cookie (Requirement 24.7)
    document.cookie = 'edurisk_auth_token=; path=/; max-age=0; SameSite=Strict';
  }
}

/**
 * Store user information.
 * 
 * @param user - User data to store
 */
export function setUser(user: User): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
}

/**
 * Retrieve stored user information.
 * 
 * @returns User data or null if not found
 */
export function getUser(): User | null {
  if (typeof window !== 'undefined') {
    const userData = localStorage.getItem(USER_KEY);
    if (userData) {
      try {
        return JSON.parse(userData);
      } catch {
        return null;
      }
    }
  }
  return null;
}

/**
 * Authenticate user with username and password.
 * 
 * Calls POST /api/auth/login and stores the JWT token on success.
 * 
 * @param username - User's username
 * @param password - User's password
 * @throws Error if authentication fails
 * 
 * Requirements: 23.3, 23.4
 * 
 * @example
 * try {
 *   await login('admin', 'admin123');
 *   // Redirect to dashboard
 * } catch (error) {
 *   // Display error message
 * }
 */
export async function login(username: string, password: string): Promise<void> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  
  try {
    const response = await fetch(`${apiUrl}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      // Handle authentication failure (Requirement 23.3)
      if (response.status === 401) {
        throw new Error('Invalid username or password');
      }
      throw new Error('Login failed. Please try again.');
    }

    const data: AuthTokens = await response.json();
    
    // Store JWT token (Requirement 23.4, 24.1)
    setToken(data.access_token);
    
    // Store user info (username for now, can be expanded later)
    setUser({ username });
    
  } catch (error) {
    // Re-throw with user-friendly message (Requirement 23.3)
    if (error instanceof Error) {
      throw error;
    }
    throw new Error('Network error. Please check your connection.');
  }
}

/**
 * Log out the current user.
 * 
 * Clears stored tokens and user data, then redirects to login page.
 * 
 * Requirements: 24.4
 */
export function logout(): void {
  clearToken();
  
  // Redirect to login page
  if (typeof window !== 'undefined') {
    window.location.href = '/login';
  }
}

/**
 * Check if user is authenticated.
 * 
 * @returns true if user has a valid token stored
 */
export function isAuthenticated(): boolean {
  return getToken() !== null;
}

/**
 * Create API client with automatic token injection and 401 handling.
 * 
 * This function wraps fetch() to automatically:
 * - Add Authorization: Bearer {token} header to all requests
 * - Handle 401 responses by clearing tokens and redirecting to login
 * 
 * @param endpoint - API endpoint path (e.g., '/api/students')
 * @param options - Fetch options (method, body, headers, etc.)
 * @returns Promise resolving to Response object
 * @throws Error if request is unauthorized
 * 
 * Requirements: 24.2, 24.3
 * 
 * @example
 * // GET request
 * const response = await apiClient('/api/students');
 * const students = await response.json();
 * 
 * @example
 * // POST request
 * const response = await apiClient('/api/predict', {
 *   method: 'POST',
 *   body: JSON.stringify(studentData),
 * });
 */
export async function apiClient(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = getToken();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  // Merge existing headers from options
  if (options.headers) {
    const existingHeaders = new Headers(options.headers);
    existingHeaders.forEach((value, key) => {
      headers[key] = value;
    });
  }

  // Add Authorization header if token exists (Requirement 24.2)
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${apiUrl}${endpoint}`, {
    ...options,
    headers,
  });

  // Handle 401 Unauthorized (Requirement 24.3)
  if (response.status === 401) {
    clearToken();
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
    throw new Error('Unauthorized');
  }

  return response;
}
