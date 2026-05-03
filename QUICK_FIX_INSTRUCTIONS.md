# Quick Fix Instructions - Authentication Error

## The Problem

You're getting **401 Unauthorized** errors because:
1. The backend requires JWT authentication for `/api/students` and `/api/alerts`
2. The frontend dashboard wasn't including authentication tokens in requests
3. You need to login first before accessing the dashboard

## The Solution (2 Options)

### Option 1: Use the Login Page (Quickest - No Rebuild Needed!)

**This works with the current running containers:**

1. **Navigate to the login page**: http://localhost:3000/login

2. **Login with these credentials**:
   - Username: `admin`
   - Password: `admin123`

3. **After login**, you'll be redirected to the dashboard and it should work!

**Why this works**: The login page is already implemented and working. It will:
- Authenticate you with the backend
- Store a JWT token in your browser
- The token will be used for subsequent API requests

---

### Option 2: Rebuild Frontend (Applies the Code Fixes)

**If you want the automatic redirect to login page:**

The code fixes I made will:
- Automatically redirect unauthenticated users to `/login`
- Use the proper `apiClient()` function that includes JWT tokens

**To apply these fixes:**

```bash
# Stop the frontend
docker-compose stop frontend

# Rebuild the frontend image (this will take 5-10 minutes)
docker-compose build frontend

# Start the frontend
docker-compose up -d frontend
```

**After rebuild:**
- Navigate to http://localhost:3000
- You'll be automatically redirected to `/login`
- Login with `admin` / `admin123`
- You'll be redirected to `/dashboard` with working data

---

## Testing the Fix

### Step 1: Clear Browser Data (Important!)
```javascript
// Open browser console (F12) and run:
localStorage.clear();
```

### Step 2: Navigate to Login
Go to: http://localhost:3000/login

### Step 3: Login
- Username: `admin`
- Password: `admin123`

### Step 4: Verify Dashboard Works
- Should see student data loading
- No 401 errors in console
- API requests should show `Authorization: Bearer <token>` header

---

## Default User Accounts

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | Admin User |
| `demo` | `demo123` | Demo User |

---

## Troubleshooting

### Still getting 401 errors after login?

1. **Clear browser storage**:
   ```javascript
   // In browser console (F12)
   localStorage.clear();
   location.reload();
   ```

2. **Check if backend is running**:
   ```bash
   docker-compose ps backend
   ```

3. **Check backend logs**:
   ```bash
   docker-compose logs backend --tail 50
   ```

### Can't access login page?

1. **Check if frontend is running**:
   ```bash
   docker-compose ps frontend
   ```

2. **Restart frontend**:
   ```bash
   docker-compose restart frontend
   ```

3. **Check frontend logs**:
   ```bash
   docker-compose logs frontend --tail 50
   ```

### CORS errors still appearing?

1. **Verify CORS configuration** in `.env`:
   ```bash
   CORS_ORIGINS=http://localhost:3000,http://localhost:3001
   ```

2. **Restart backend** if you changed CORS:
   ```bash
   docker-compose restart backend
   ```

---

## What I Fixed

### Files Modified:

1. **`frontend/app/page.tsx`**
   - Added authentication check
   - Redirects to `/login` if not authenticated
   - Redirects to `/dashboard` if authenticated

2. **`frontend/app/dashboard/page.tsx`**
   - Added authentication check on page load
   - Replaced `fetch()` with `apiClient()` 
   - `apiClient()` automatically includes JWT token

3. **Already Working:**
   - `frontend/app/login/page.tsx` - Login page (already implemented)
   - `frontend/lib/auth.ts` - Authentication utilities (already implemented)
   - `backend/routes/auth.py` - Login endpoint (already implemented)

---

## Quick Command Reference

```bash
# Check all services status
docker-compose ps

# View logs for a service
docker-compose logs frontend --tail 50
docker-compose logs backend --tail 50

# Restart a service
docker-compose restart frontend
docker-compose restart backend

# Rebuild and restart frontend
docker-compose stop frontend
docker-compose build frontend
docker-compose up -d frontend

# Stop all services
docker-compose down

# Start all services
docker-compose up -d
```

---

## Recommended Next Steps

1. ✅ **Try Option 1 first** (just login at http://localhost:3000/login)
2. ⏳ **If you want automatic redirects**, use Option 2 (rebuild frontend)
3. 🔒 **For production**, set `API_KEY` in `.env` for additional security
4. 📝 **Review** `AUTHENTICATION_FIX_GUIDE.md` for detailed explanation

---

**Status**: ✅ Code fixes applied, ready to test  
**Quickest Solution**: Go to http://localhost:3000/login and login with `admin`/`admin123`  
**Best Solution**: Rebuild frontend to get automatic redirects
