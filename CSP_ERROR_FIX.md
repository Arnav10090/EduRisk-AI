# CSP (Content Security Policy) Error Fix

## Error Description

When refreshing the login page, you're seeing this error in the browser console:

```
Refused to load the script 'http://localhost:3000/_next/static/chunks/...' 
because it violates the following Content Security Policy directive: "script-src 'self'"
```

## Root Cause

The Next.js configuration had overly restrictive Content Security Policy (CSP) headers that were blocking Next.js's own scripts from loading. This is a common issue when CSP is configured without accounting for Next.js's dynamic script loading in development mode.

## Solution Applied

I've updated `frontend/next.config.js` to:
1. **Disable CSP in development mode** (no restrictions)
2. **Keep CSP enabled in production** with proper permissions

### Changes Made

```javascript
async headers() {
  const isDevelopment = process.env.NODE_ENV === 'development';
  
  if (isDevelopment) {
    // No CSP restrictions in development
    return [];
  }
  
  // Production CSP with proper permissions
  return [
    {
      source: '/:path*',
      headers: [
        {
          key: 'Content-Security-Policy',
          value: "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; ...",
        },
      ],
    },
  ];
},
```

## How to Apply the Fix

### Option 1: Rebuild Frontend Container (Recommended)

```bash
# Stop the frontend
docker-compose stop frontend

# Rebuild with the updated configuration
docker-compose build frontend

# Start the frontend
docker-compose up -d frontend

# Verify it's running
docker-compose ps frontend
```

**Note**: This will take 5-10 minutes to rebuild.

### Option 2: Quick Browser Fix (Temporary)

While the rebuild is running, you can try these browser-side fixes:

1. **Clear browser cache**:
   - Press `Ctrl+Shift+Delete` (Windows) or `Cmd+Shift+Delete` (Mac)
   - Select "Cached images and files"
   - Click "Clear data"

2. **Hard refresh**:
   - Press `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)

3. **Disable CSP in browser** (Chrome DevTools):
   - Open DevTools (F12)
   - Go to Settings (F1)
   - Search for "Disable Content Security Policy"
   - Check the box
   - Refresh the page

## Testing After Fix

1. **Navigate to**: http://localhost:3000/login
2. **Verify**: No CSP errors in browser console
3. **Login** with `admin` / `admin123`
4. **Verify**: Dashboard loads successfully

## Why This Happened

The original CSP configuration was:
```javascript
"script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
```

This was missing:
- ✅ `default-src` directive
- ✅ `connect-src` for API calls
- ✅ `img-src`, `font-src` for assets
- ✅ Development mode exception

Next.js in development mode uses:
- Dynamic script loading
- Hot module replacement (HMR)
- WebSocket connections
- Inline scripts for hydration

All of these were being blocked by the restrictive CSP.

## Production Considerations

For production deployment, you should:

1. **Use nonces** for inline scripts:
   ```javascript
   script-src 'self' 'nonce-{random}'
   ```

2. **Restrict connect-src** to your actual API domain:
   ```javascript
   connect-src 'self' https://api.yourdomain.com
   ```

3. **Remove unsafe-eval** if possible:
   ```javascript
   script-src 'self' 'unsafe-inline'
   ```

4. **Add report-uri** for CSP violations:
   ```javascript
   report-uri /api/csp-report
   ```

## Alternative: Run Frontend Outside Docker

If rebuilding takes too long, you can run the frontend directly:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (if not done)
npm install

# Run development server
npm run dev
```

Then access at http://localhost:3000 (not through Docker).

This will pick up the configuration changes immediately without rebuilding.

## Summary

**Problem**: CSP blocking Next.js scripts  
**Root Cause**: Overly restrictive CSP headers  
**Solution**: Disable CSP in development mode  
**Action Required**: Rebuild frontend container  
**Time**: 5-10 minutes  
**Alternative**: Run frontend with `npm run dev`

---

**Status**: ✅ Configuration fixed, awaiting rebuild  
**Impact**: Fixes CSP errors and allows login page to work  
**Files Modified**: `frontend/next.config.js`
