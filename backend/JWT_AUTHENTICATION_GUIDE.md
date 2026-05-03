# JWT Authentication Guide for EduRisk AI

## Overview

This guide explains how to use JWT (JSON Web Token) authentication to protect API routes in the EduRisk AI backend.

**Requirements**: 7.3.1, 7.3.2, 7.3.3, 7.3.4

## Quick Start

### 1. Import the Dependency

```python
from backend.routes.auth import get_current_user
```

### 2. Add to Route Handler

```python
from fastapi import APIRouter, Depends

@router.get("/protected-endpoint")
async def my_protected_route(
    current_user: dict = Depends(get_current_user)
):
    """
    This route requires a valid JWT token.
    
    Args:
        current_user: Authenticated user information (injected from JWT)
    """
    username = current_user['username']
    email = current_user['email']
    
    return {"message": f"Hello {username}!"}
```

### 3. Client Usage

```bash
# 1. Login to get JWT token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Response: {"access_token": "eyJhbGc...", "token_type": "bearer"}

# 2. Use token in protected requests
curl http://localhost:8000/api/students \
  -H "Authorization: Bearer eyJhbGc..."
```

## How It Works

### JWT Dependency Function

The `get_current_user()` function is defined in `backend/routes/auth.py`:

```python
async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Dependency to extract and validate current user from JWT token.
    
    Requirements:
        - 7.3.1: Create get_current_user() dependency function
        - 7.3.2: Extract and validate JWT from Authorization header
        - 7.3.3: Return user information from JWT payload
        - 7.3.4: Raise 401 exception for invalid/expired tokens
    """
    # Verify token
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Extract username
    username = payload.get("sub")
    
    # Return user info
    return {
        "username": user["username"],
        "email": user.get("email"),
        "full_name": user.get("full_name")
    }
```

### What It Does

1. **Extracts JWT** from `Authorization: Bearer <token>` header (Requirement 7.3.2)
2. **Validates token** signature and expiration using `verify_token()` (Requirement 7.3.2)
3. **Returns user info** from JWT payload if valid (Requirement 7.3.3)
4. **Raises 401** if token is invalid or expired (Requirement 7.3.4)

## Protected Routes

The following routes are protected with JWT authentication:

### Student Routes (`backend/routes/students.py`)
- `GET /api/students` - List all students
- `GET /api/students/{student_id}` - Get student detail
- `GET /api/students/{student_id}/predictions` - Get prediction history

### Prediction Routes (`backend/routes/predict.py`)
- `POST /api/predict` - Create single prediction
- `POST /api/batch-score` - Create batch predictions

### Alert Routes (`backend/routes/alerts.py`)
- `GET /api/alerts` - Get high-risk alerts

### Explanation Routes (`backend/routes/explain.py`)
- `GET /api/explain/{student_id}` - Get SHAP explanation

## Public Routes

These routes do NOT require JWT authentication:

- `GET /api/health` - Health check
- `POST /api/auth/login` - Login to get JWT
- `POST /api/auth/refresh` - Refresh JWT token
- `GET /docs` - API documentation
- `GET /redoc` - Alternative API documentation
- `GET /openapi.json` - OpenAPI schema

## Using User Information

The `current_user` dictionary contains:

```python
{
    "username": "admin",           # Username from JWT 'sub' claim
    "email": "admin@edurisk.ai",   # Email from JWT payload
    "full_name": "Admin User"      # Full name from JWT payload
}
```

### Example: Logging User Actions

```python
@router.post("/predict")
async def predict_single(
    student_data: StudentInput,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    logger.info(f"User '{current_user['username']}' creating prediction")
    
    # Use username in audit logs
    result = await prediction_service.predict_student(
        student_data=student_data,
        db=db,
        performed_by=current_user['username']  # Track who made the prediction
    )
    
    return result
```

## Error Handling

### Missing Token

**Request:**
```bash
curl http://localhost:8000/api/students
```

**Response:**
```json
{
  "detail": "Not authenticated"
}
```
**Status Code:** 401

### Invalid Token

**Request:**
```bash
curl http://localhost:8000/api/students \
  -H "Authorization: Bearer invalid_token"
```

**Response:**
```json
{
  "detail": "Invalid or expired token"
}
```
**Status Code:** 401

### Expired Token

**Request:**
```bash
curl http://localhost:8000/api/students \
  -H "Authorization: Bearer <expired_token>"
```

**Response:**
```json
{
  "detail": "Invalid or expired token"
}
```
**Status Code:** 401

**Solution:** Use `/api/auth/refresh` to get a new token, or login again.

## Testing Protected Routes

### Unit Test Example

```python
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_protected_route_requires_jwt():
    """Test that protected route rejects requests without JWT"""
    response = client.get("/api/students")
    assert response.status_code == 401

def test_protected_route_with_valid_jwt():
    """Test that protected route accepts valid JWT"""
    # Login to get token
    login_response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    token = login_response.json()["access_token"]
    
    # Use token
    response = client.get(
        "/api/students",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
```

## Security Best Practices

1. **Always use HTTPS** in production to prevent token interception
2. **Store tokens securely** on the client (httpOnly cookies or secure storage)
3. **Set strong SECRET_KEY** in environment variables (never commit to git)
4. **Token expiration** is set to 24 hours (configurable in `backend/core/security.py`)
5. **Refresh tokens** before they expire using `/api/auth/refresh`
6. **Never log tokens** or passwords (enforced in security module)

## Configuration

### Environment Variables

```bash
# .env
SECRET_KEY=your_very_strong_secret_key_here_change_in_production
ALGORITHM=HS256
```

### Token Expiration

Default: 24 hours

To change, modify `ACCESS_TOKEN_EXPIRE_HOURS` in `backend/core/security.py`:

```python
ACCESS_TOKEN_EXPIRE_HOURS = 24  # Change to desired hours
```

## Troubleshooting

### "Not authenticated" error

**Cause:** Missing `Authorization` header

**Solution:** Include `Authorization: Bearer <token>` header in request

### "Invalid or expired token" error

**Causes:**
1. Token signature is invalid (wrong SECRET_KEY)
2. Token has expired (> 24 hours old)
3. Token format is malformed

**Solutions:**
1. Verify SECRET_KEY matches between token creation and validation
2. Login again to get a new token
3. Use `/api/auth/refresh` to renew token before expiration

### Token works in Postman but not in code

**Cause:** Missing "Bearer " prefix

**Solution:** Ensure token is sent as `Bearer <token>`, not just `<token>`

```python
# ✅ Correct
headers = {"Authorization": f"Bearer {token}"}

# ❌ Wrong
headers = {"Authorization": token}
```

## Additional Resources

- **JWT Specification**: https://jwt.io/
- **FastAPI Security**: https://fastapi.tiangolo.com/tutorial/security/
- **OAuth2 Password Flow**: https://oauth.net/2/grant-types/password/

## Summary

To protect a route with JWT authentication:

1. Import `get_current_user` from `backend.routes.auth`
2. Add `current_user: dict = Depends(get_current_user)` to route parameters
3. Use `current_user['username']` to access authenticated user information
4. FastAPI automatically handles token validation and 401 errors

**That's it!** The dependency handles all the complexity of JWT extraction, validation, and error handling.
