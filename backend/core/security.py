"""
EduRisk AI Backend - Security Utilities

This module provides JWT token generation/verification and password hashing
for OAuth2 authentication.

Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 20.8, 20.9, 20.10
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import bcrypt
import logging

logger = logging.getLogger(__name__)

# JWT configuration from environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key_here_change_in_production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS = 24  # Requirement 20.5: Set JWT expiration to 24 hours


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with the provided data.
    
    The token is signed with SECRET_KEY from environment variables and
    expires after 24 hours by default (Requirement 20.5).
    
    Args:
        data: Dictionary containing claims to encode in the JWT
              (e.g., {"sub": "username", "user_id": "123"})
        expires_delta: Optional custom expiration timedelta.
                      Defaults to 24 hours if not provided.
    
    Returns:
        Encoded JWT token string
    
    Requirements: 20.2, 20.4, 20.5, 20.10
    
    Example:
        >>> token = create_access_token({"sub": "john_doe", "user_id": "123"})
        >>> print(token)
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
    
    Security Notes:
        - Tokens are signed with SECRET_KEY to prevent tampering
        - Tokens include expiration time (exp claim) for automatic invalidation
        - Do NOT log the generated token (Requirement 20.10)
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    
    # Encode JWT with SECRET_KEY
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    # Log token creation without exposing the token itself (Requirement 20.10)
    logger.info(f"Access token created for subject: {data.get('sub', 'unknown')}")
    
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT access token.
    
    Validates the token signature and expiration time. Returns the decoded
    payload if valid, or None if invalid/expired.
    
    Args:
        token: JWT token string to verify
    
    Returns:
        Dictionary containing the decoded token payload if valid,
        None if the token is invalid or expired
    
    Requirements: 20.8, 20.9, 20.10
    
    Example:
        >>> token = create_access_token({"sub": "john_doe"})
        >>> payload = verify_token(token)
        >>> print(payload["sub"])
        'john_doe'
        
        >>> invalid_token = "invalid.jwt.token"
        >>> payload = verify_token(invalid_token)
        >>> print(payload)
        None
    
    Security Notes:
        - Verifies token signature using SECRET_KEY
        - Automatically checks expiration time (exp claim)
        - Returns None for any validation failure
        - Does NOT log the token itself (Requirement 20.10)
    """
    try:
        # Decode and verify JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Extract subject (username) for logging
        username = payload.get("sub")
        if username:
            logger.debug(f"Token verified successfully for user: {username}")
        
        return payload
        
    except JWTError as e:
        # Log verification failure without exposing the token
        logger.warning(f"Token verification failed: {type(e).__name__}")
        return None
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"Unexpected error during token verification: {type(e).__name__}")
        return None


def get_password_hash(password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    
    Uses bcrypt directly for secure password hashing.
    The resulting hash includes salt and can be safely stored in the database.
    
    Args:
        password: Plain text password to hash
    
    Returns:
        Bcrypt password hash string
    
    Requirements: 20.10
    
    Example:
        >>> hashed = get_password_hash("my_secure_password")
        >>> print(hashed)
        '$2b$12$...'  # Bcrypt hash with salt
    
    Security Notes:
        - Uses bcrypt algorithm (industry standard)
        - Automatically generates unique salt for each password
        - Hash includes algorithm, cost factor, salt, and hash
        - Do NOT log the password or hash (Requirement 20.10)
    """
    # Hash password without logging it (Requirement 20.10)
    # Convert password to bytes and hash with bcrypt
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    
    logger.debug("Password hashed successfully")
    
    # Return as string for database storage
    return hashed_password.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a bcrypt hash.
    
    Uses constant-time comparison to prevent timing attacks.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hash to compare against
    
    Returns:
        True if the password matches the hash, False otherwise
    
    Requirements: 20.2, 20.10
    
    Example:
        >>> hashed = get_password_hash("my_password")
        >>> verify_password("my_password", hashed)
        True
        >>> verify_password("wrong_password", hashed)
        False
    
    Security Notes:
        - Uses constant-time comparison to prevent timing attacks
        - Do NOT log passwords or hashes (Requirement 20.10)
        - Returns False for any verification failure
    """
    try:
        # Verify password without logging it (Requirement 20.10)
        # Convert both to bytes for bcrypt
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        
        is_valid = bcrypt.checkpw(password_bytes, hashed_bytes)
        
        if is_valid:
            logger.debug("Password verification successful")
        else:
            logger.debug("Password verification failed: incorrect password")
        
        return is_valid
        
    except Exception as e:
        # Log verification failure without exposing password details
        logger.warning(f"Password verification error: {type(e).__name__}")
        return False


def get_token_expiration_time() -> int:
    """
    Get the token expiration time in hours.
    
    Returns:
        Number of hours until token expiration (24 hours)
    
    Requirements: 20.5
    """
    return ACCESS_TOKEN_EXPIRE_HOURS


# Warn if SECRET_KEY is using default value
if SECRET_KEY == "your_secret_key_here_change_in_production":
    logger.warning(
        "SECRET_KEY is using default value! "
        "Set a strong SECRET_KEY in environment variables for production."
    )
