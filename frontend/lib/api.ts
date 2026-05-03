/**
 * API client utilities for EduRisk AI frontend.
 * 
 * Provides a centralized API client with automatic JWT token injection
 * and 401 error handling.
 * 
 * Requirements: 24.2, 24.3
 */

import { apiClient as authApiClient } from './auth';

/**
 * API client with automatic token injection and error handling.
 * 
 * This is a re-export of the apiClient from auth.ts for convenience.
 * All API requests should use this client to ensure proper authentication.
 * 
 * Features:
 * - Automatically attaches Authorization: Bearer {token} header
 * - Handles 401 responses by clearing tokens and redirecting to /login
 * - Provides consistent error handling across the application
 * 
 * Requirements: 24.2, 24.3
 * 
 * @example
 * import { apiClient } from '@/lib/api';
 * 
 * // GET request
 * const response = await apiClient('/api/students');
 * const students = await response.json();
 * 
 * // POST request
 * const response = await apiClient('/api/predict', {
 *   method: 'POST',
 *   body: JSON.stringify(data),
 * });
 */
export const apiClient = authApiClient;

/**
 * Helper function to handle API responses with JSON parsing.
 * 
 * @param endpoint - API endpoint path
 * @param options - Fetch options
 * @returns Promise resolving to parsed JSON data
 * @throws Error if response is not ok
 */
export async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await apiClient(endpoint, options);
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `API request failed: ${response.status}`);
  }
  
  return response.json();
}

/**
 * Helper function for GET requests.
 * 
 * @param endpoint - API endpoint path
 * @returns Promise resolving to parsed JSON data
 */
export async function get<T>(endpoint: string): Promise<T> {
  return apiRequest<T>(endpoint, { method: 'GET' });
}

/**
 * Helper function for POST requests.
 * 
 * @param endpoint - API endpoint path
 * @param data - Request body data
 * @returns Promise resolving to parsed JSON data
 */
export async function post<T>(endpoint: string, data: any): Promise<T> {
  return apiRequest<T>(endpoint, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Helper function for PUT requests.
 * 
 * @param endpoint - API endpoint path
 * @param data - Request body data
 * @returns Promise resolving to parsed JSON data
 */
export async function put<T>(endpoint: string, data: any): Promise<T> {
  return apiRequest<T>(endpoint, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

/**
 * Helper function for DELETE requests.
 * 
 * @param endpoint - API endpoint path
 * @returns Promise resolving to parsed JSON data
 */
export async function del<T>(endpoint: string): Promise<T> {
  return apiRequest<T>(endpoint, { method: 'DELETE' });
}
