# Authentication Fix Guide

## Problem Summary

When accessing the dashboard at `http://localhost:3000/dashboard`, you're getting:
1. **CORS errors** in the browser console
2. **401 Unauthorized** errors when fetching students data
3. **Failed to fetch** errors

## Root Cause

The application has JWT authentication enabled, but the dashboard page was:
1. Not checking if the user is authenticated
2. Not including the JWT token in API requests
3. Using plain `fetch()` instead of the authenticated `apiClient()` function

## Solution Applied

I've fixed three files to implement proper authentication flow:

### 1. Fixed `frontend/app/page.tsx`
**Change**: Root page now checks authentication before redirecting
- If authenticated → redirect to `/dashboard`
- If not authenticated → redirect to `/login`

### 2. Fixed `frontend/app/dashboard/page.tsx`
**Changes**:
- Added authentication check on page load
- Replaced `fetch()` with `apiClient()` for all API calls
- `apiClient()` automatically includes JWT token in Authorization header

### 3. Already Exists: `frontend/app/login/page.tsx`
- Login page is already implemented
- Default credentials:
  - Username: `admin` / Password: `admin123`
  - Username: `demo` / Password: `demo123`

## How to Apply the Fix

### Option 1: Rebuild Frontend Container (Recommended)

```bash
# Stop the frontend container
docker-compose stop frontend

# Rebuild the frontend image with the updated code
docker-compose build frontend

# Start the frontend container
docker-compose up -d frontend

# Check logs to verify it started successfully
docker-compose logs -f frontend
```

### Option 2: Quick Test Without Docker

If you want to test the changes immediately without rebuilding:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (if not already done)
npm install

# Run the development server
npm run dev
```

Then access the application at `http://localhost:3000` (not through Docker).

## Testing the Fix

1. **Navigate to** `http://localhost:3000`
   - Should redirect to `/login` page

2. **Login with credentials**:
   - Username: `admin`
   - Password: `admin123`

3. **After successful login**:
   - Should redirect to `/dashboard`
   - Dashboard should load student data successfully
   - No more 401 Unauthorized errors

4. **Verify in browser console**:
   - No CORS errors
   - API requests include `Authorization: Bearer <token>` header
   - Successful 200 responses from `/api/students` and `/api/alerts`

## Authentication Flow

```
User visits http://localhost:3000
         ↓
Check if authenticated (JWT token in localStorage)
         ↓
    ┌────┴────┐
    NO       YES
    ↓         ↓
/login    /dashboard
    ↓         ↓
Enter credentials    Fetch data with JWT token
    ↓         ↓
POST /api/auth/login    GET /api/students (with Authorization header)
    ↓         ↓
Store JWT token    Display dashboard
    ↓
Redirect to /dashboard
```

## API Endpoints Authentication Status

| Endpoint | Authentication Required | Notes |
|----------|------------------------|-------|
| `GET /` | No | Root endpoint |
| `GET /api/health` | No | Public health check |
| `POST /api/auth/login` | No | Login endpoint |
| `POST /api/auth/refresh` | No | Token refresh |
| `GET /api/students` | **YES** | Requires JWT token |
| `GET /api/alerts` | **YES** | Requires JWT token |
| `POST /api/predict` | **YES** | Requires JWT token |
| `POST /api/batch-score` | **YES** | Requires JWT token |
| `GET /docs` | No | API documentation |
| `GET /redoc` | No | API documentation |

## Default User Credentials

The backend has two mock users configured:

### Admin User
- **Username**: `admin`
- **Password**: `admin123`
- **Email**: `admin@edurisk.ai`
- **Full Name**: Admin User

### Demo User
- **Username**: `demo`
- **Password**: `demo123`
- **Email**: `demo@edurisk.ai`
- **Full Name**: Demo User

**Note**: These are mock users stored in memory. In production, you should:
1. Replace with a real user database
2. Use strong, unique passwords
3. Implement password reset functionality
4. Add user management features

## Troubleshooting

### Issue: Still getting 401 errors after login

**Solution**:
1. Clear browser localStorage: `localStorage.clear()` in browser console
2. Clear browser cookies
3. Refresh the page
4. Try logging in again

### Issue: CORS errors persist

**Check**:
1. Backend CORS configuration in `.env`:
   ```bash
   CORS_ORIGINS=http://localhost:3000,http://localhost:3001
   ```
2. Restart backend if you changed CORS settings:
   ```bash
   docker-compose restart backend
   ```

### Issue: Frontend not picking up code changes

**Solution**:
```bash
# Rebuild the frontend image
docker-compose build frontend
docker-compose up -d frontend
```

### Issue: "Invalid username or password"

**Check**:
1. Using correct credentials: `admin` / `admin123`
2. Backend is running: `docker-compose ps backend`
3. Backend logs: `docker-compose logs backend`

## Security Notes

### Current Setup (Development)
- JWT tokens stored in localStorage (accessible to JavaScript)
- Mock users with hardcoded passwords
- API_KEY authentication disabled (not set in .env)
- DEBUG mode enabled

### Production Recommendations
1. **Set API_KEY** in `.env` for API key authentication layer
2. **Disable DEBUG mode**: `DEBUG=False`
3. **Use httpOnly cookies** for JWT tokens (more secure than localStorage)
4. **Implement real user database** with PostgreSQL users table
5. **Use strong SECRET_KEY** for JWT signing
6. **Enable HTTPS** for all communications
7. **Implement rate limiting** on login endpoint
8. **Add password complexity requirements**
9. **Implement account lockout** after failed login attempts
10. **Add audit logging** for authentication events

## Files Modified

1. ✅ `frontend/app/page.tsx` - Added authentication check before redirect
2. ✅ `frontend/app/dashboard/page.tsx` - Use apiClient() with JWT tokens
3. ℹ️ `frontend/lib/auth.ts` - Already has apiClient() function (no changes needed)
4. ℹ️ `frontend/app/login/page.tsx` - Already implemented (no changes needed)

## Next Steps

1. **Rebuild frontend container** to apply the fixes
2. **Test the login flow** with admin/admin123
3. **Verify dashboard loads** without errors
4. **Optional**: Set API_KEY in `.env` for additional security layer
5. **Optional**: Implement user management features for production

---

**Status**: ✅ Code fixes applied, awaiting frontend container rebuild  
**Impact**: Fixes 401 Unauthorized errors and enables proper authentication flow  
**Breaking Changes**: None - existing functionality preserved, authentication now works correctly
