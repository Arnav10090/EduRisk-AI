/**
 * Middleware to protect routes requiring authentication.
 * 
 * This middleware checks for authentication tokens and redirects
 * unauthenticated users to the login page when accessing protected routes.
 * 
 * Requirements: 24.7
 */
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Public routes that don't require authentication.
 */
const PUBLIC_ROUTES = ['/login', '/'];

/**
 * Protected routes that require authentication.
 * Users without valid tokens will be redirected to /login.
 */
const PROTECTED_ROUTES = ['/dashboard', '/alerts', '/student'];

/**
 * Middleware function to protect routes.
 * 
 * Checks for authentication token in localStorage (via cookie or header).
 * Redirects unauthenticated users to /login when accessing protected routes.
 * 
 * Requirements: 24.7
 * 
 * @param request - Next.js request object
 * @returns Next.js response (redirect or continue)
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public routes without authentication
  if (PUBLIC_ROUTES.includes(pathname)) {
    return NextResponse.next();
  }

  // Check if the current route is protected
  const isProtectedRoute = PROTECTED_ROUTES.some(route => pathname.startsWith(route));

  if (isProtectedRoute) {
    // Check for authentication token
    // Note: Since we're using localStorage, we can't directly access it in middleware
    // Instead, we check for a cookie that should be set alongside localStorage
    const token = request.cookies.get('edurisk_auth_token')?.value;
    
    // Also check Authorization header as fallback
    const authHeader = request.headers.get('authorization');
    const hasToken = token || authHeader;

    if (!hasToken) {
      // Redirect to login if not authenticated
      const loginUrl = new URL('/login', request.url);
      // Add redirect parameter to return to original page after login
      loginUrl.searchParams.set('redirect', pathname);
      return NextResponse.redirect(loginUrl);
    }
  }

  return NextResponse.next();
}

/**
 * Middleware configuration.
 * 
 * Applies middleware to all routes except:
 * - API routes
 * - Static files (_next/static)
 * - Images (_next/image)
 * - Favicon
 */
export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
