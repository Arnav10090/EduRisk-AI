"""
EduRisk AI Backend - Authentication Routes

This module provides JWT OAuth2 authentication endpoints for user login
and token refresh.

Requirements: 20.1, 20.2, 20.3, 20.6, 20.7, 20.8
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
import logging

from backend.core.security import (
    create_access_token,
    verify_token,
    verify_password,
    get_password_hash
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# Request/Response Models
class TokenResponse(BaseModel):
    """
    OAuth2 token response model.
    
    Requirements: 20.3
    """
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    """
    Login request model with username and password.
    
    Requirements: 20.2, 20.3
    """
    username: str
    password: str


# Mock user database (for MVP - replace with real database in production)
# These seeded accounts are intentional hackathon/demo credentials so judges
# can access the product immediately without a signup flow.
# In production, this should query the users table in PostgreSQL.
MOCK_USERS = {
    "admin": {
        "username": "admin",
        "hashed_password": get_password_hash("admin123"),  # Demo password: admin123
        "email": "admin@edurisk.ai",
        "full_name": "Admin User"
    },
    "demo": {
        "username": "demo",
        "hashed_password": get_password_hash("demo@1234"),  # Demo password: demo@1234
        "email": "demo@edurisk.ai",
        "full_name": "Demo User"
    }
}


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    Authenticate user credentials against database.
    
    Args:
        username: Username to authenticate
        password: Plain text password to verify
    
    Returns:
        User dictionary if authentication successful, None otherwise
    
    Requirements: 20.2, 20.4, 20.10
    
    Security Notes:
        - Uses constant-time password comparison to prevent timing attacks
        - Does NOT log passwords or hashes (Requirement 20.10)
    """
    # Look up user in mock database
    user = MOCK_USERS.get(username)
    
    if not user:
        logger.debug(f"Authentication failed: user '{username}' not found")
        return None
    
    # Verify password using bcrypt
    if not verify_password(password, user["hashed_password"]):
        logger.debug(f"Authentication failed: invalid password for user '{username}'")
        return None
    
    logger.info(f"User '{username}' authenticated successfully")
    return user


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    """
    Authenticate user and return JWT access token.
    
    Implements OAuth2 Password Flow with JWT token generation.
    
    Args:
        login_data: Username and password credentials
    
    Returns:
        TokenResponse with access_token and token_type="bearer"
    
    Raises:
        HTTPException 401: Invalid credentials
    
    Requirements: 20.1, 20.2, 20.3, 20.4, 20.8, 20.10
    
    Example:
        POST /api/auth/login
        {
            "username": "admin",
            "password": "admin123"
        }
        
        Response:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer"
        }
    """
    # Authenticate user credentials (Requirement 20.2, 20.4)
    user = authenticate_user(login_data.username, login_data.password)
    
    if not user:
        # Return 401 with generic message (Requirement 20.8)
        # Don't reveal whether username or password was wrong (security best practice)
        logger.warning(f"Failed login attempt for username: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",  # Generic message per Requirement 20.8
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create JWT access token (Requirement 20.1, 20.3, 20.4, 20.5)
    access_token = create_access_token(
        data={
            "sub": user["username"],  # Subject claim (username)
            "email": user.get("email"),
            "full_name": user.get("full_name")
        }
    )
    
    logger.info(f"JWT token issued for user: {user['username']}")
    
    # Return token response (Requirement 20.3)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer"
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token: str = Depends(oauth2_scheme)):
    """
    Refresh JWT access token.
    
    Validates the provided token and issues a new one with extended expiration.
    
    Args:
        token: Current JWT access token from Authorization header
    
    Returns:
        TokenResponse with new access_token and token_type="bearer"
    
    Raises:
        HTTPException 401: Invalid or expired token
    
    Requirements: 20.6, 20.8, 20.9
    
    Example:
        POST /api/auth/refresh
        Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
        
        Response:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer"
        }
    """
    # Verify current token (Requirement 20.8, 20.9)
    payload = verify_token(token)
    
    if not payload:
        # Return 401 for invalid/expired token (Requirement 20.8)
        logger.warning("Token refresh failed: invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract username from token payload
    username = payload.get("sub")
    if not username:
        logger.warning("Token refresh failed: missing subject claim")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify user still exists
    user = MOCK_USERS.get(username)
    if not user:
        logger.warning(f"Token refresh failed: user '{username}' not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new JWT access token (Requirement 20.6)
    new_access_token = create_access_token(
        data={
            "sub": user["username"],
            "email": user.get("email"),
            "full_name": user.get("full_name")
        }
    )
    
    logger.info(f"JWT token refreshed for user: {username}")
    
    # Return new token response
    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer"
    )


# Dependency for protected routes (to be used in other route modules)
async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Dependency to extract and validate current user from JWT token.
    
    Use this as a dependency in protected route handlers to require authentication.
    
    Args:
        token: JWT access token from Authorization header
    
    Returns:
        User dictionary with username, email, full_name
    
    Raises:
        HTTPException 401: Invalid or expired token
    
    Requirements: 20.7, 20.8, 20.9
    
    Example:
        @router.get("/protected")
        async def protected_route(current_user: dict = Depends(get_current_user)):
            return {"message": f"Hello {current_user['username']}"}
    """
    # Verify token (Requirement 20.8, 20.9)
    payload = verify_token(token)
    
    if not payload:
        logger.warning("Authentication failed: invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract username from token
    username = payload.get("sub")
    if not username:
        logger.warning("Authentication failed: missing subject claim in token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify user exists
    user = MOCK_USERS.get(username)
    if not user:
        logger.warning(f"Authentication failed: user '{username}' not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Return user info (without password hash)
    return {
        "username": user["username"],
        "email": user.get("email"),
        "full_name": user.get("full_name")
    }
