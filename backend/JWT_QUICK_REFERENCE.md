# JWT Authentication Quick Reference

## Protect a Route (3 Steps)

### 1. Import
```python
from backend.routes.auth import get_current_user
```

### 2. Add Dependency
```python
@router.get("/my-endpoint")
async def my_route(
    current_user: dict = Depends(get_current_user)  # Add this
):
```

### 3. Use User Info
```python
username = current_user['username']
email = current_user['email']
full_name = current_user['full_name']
```

## Client Usage

### Get Token
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Use Token
```bash
curl http://localhost:8000/api/students \
  -H "Authorization: Bearer <your_token_here>"
```

## Protected Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/api/students` | GET | List students |
| `/api/students/{id}` | GET | Get student detail |
| `/api/students/{id}/predictions` | GET | Get prediction history |
| `/api/predict` | POST | Create prediction |
| `/api/batch-score` | POST | Batch predictions |
| `/api/alerts` | GET | Get alerts |
| `/api/explain/{id}` | GET | Get SHAP explanation |

## Public Routes (No JWT)

| Route | Method | Description |
|-------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/auth/login` | POST | Login |
| `/api/auth/refresh` | POST | Refresh token |
| `/docs` | GET | API docs |

## Error Responses

| Error | Status | Cause |
|-------|--------|-------|
| "Not authenticated" | 401 | Missing Authorization header |
| "Invalid or expired token" | 401 | Bad token or expired |

## Test Users

| Username | Password |
|----------|----------|
| admin | admin123 |
| demo | demo123 |

## Full Documentation

See `backend/JWT_AUTHENTICATION_GUIDE.md` for complete guide.
