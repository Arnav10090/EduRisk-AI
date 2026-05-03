'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { login } from '@/lib/auth';

/**
 * Login Page Component
 * 
 * Provides secure login screen for user authentication.
 * 
 * Requirements: 23.1, 23.2, 23.3, 23.4, 23.5, 23.6, 23.7, 23.8
 * 
 * Features:
 * - Username and password input fields with validation
 * - Form validation (non-empty fields)
 * - User-friendly error messages
 * - JWT token storage on successful login
 * - Redirect to dashboard after authentication
 * - EduRisk AI branding and logo
 * - "Forgot Password" link (non-functional for MVP)
 */
export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('demo');
  const [password, setPassword] = useState('demo@1234');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validate inputs (Requirement 23.8)
    if (!username.trim() || !password.trim()) {
      setError('Please enter both username and password');
      return;
    }

    setLoading(true);

    try {
      // Attempt login (Requirement 23.3, 23.4, 23.5)
      await login(username, password);
      
      // Redirect to dashboard on success (Requirement 23.5)
      router.push('/dashboard');
    } catch (err) {
      // Display user-friendly error message (Requirement 23.3)
      setError(err instanceof Error ? err.message : 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-4">
          {/* Logo and Branding (Requirement 23.7) */}
          <div className="flex justify-center">
            <div className="text-4xl font-bold text-primary">EduRisk AI</div>
          </div>
          <CardTitle className="text-2xl text-center">Welcome Back</CardTitle>
          <CardDescription className="text-center">
            Sign in to access your student risk assessment dashboard
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Error Alert (Requirement 23.3) */}
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Username Field (Requirement 23.2) */}
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                placeholder="Enter your username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={loading}
                required
              />
            </div>

            {/* Password Field (Requirement 23.2) */}
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                required
              />
            </div>

            {/* Forgot Password Link (Requirement 23.6) */}
            <div className="text-right">
              <a href="#" className="text-sm text-primary hover:underline">
                Forgot password?
              </a>
            </div>

            {/* Submit Button */}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
