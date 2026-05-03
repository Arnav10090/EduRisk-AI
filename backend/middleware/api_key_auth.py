"""
API Key Authentication Middleware

This middleware enforces API key authentication on protected endpoints.
Public endpoints (health checks, documentation) are accessible without authentication.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8
"""

import os
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce API key authentication on protected endpoints.
    
    Public endpoints (no auth required):
    - /api/health
    - /api/auth/login
    - /api/auth/refresh
    - /docs
    - /redoc
    - /openapi.json
    - /
    
    Protected endpoints (require X-API-Key header):
    - All other /api/* endpoints
    """
    
    PUBLIC_PATHS = {
        "/api/health",
        "/api/auth/login",
        "/api/auth/refresh",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/"
    }
    
    def __init__(self, app):
        super().__init__(app)
        self.api_key = os.getenv("API_KEY")
        
        if not self.api_key:
            logger.warning("API_KEY not configured - authentication disabled")
    
    async def dispatch(self, request: Request, call_next):
        """
        Process each request and enforce API key authentication.
        
        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler
            
        Returns:
            Response from the next handler or 401 error
            
        Raises:
            HTTPException: 401 if authentication fails
        """
        # Skip authentication for public endpoints
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)
        
        # Skip authentication if API_KEY not configured
        if not self.api_key:
            return await call_next(request)
        
        # Check for X-API-Key header
        provided_key = request.headers.get("X-API-Key")
        
        if not provided_key:
            client_ip = self._get_client_ip(request)
            logger.warning(f"Missing API key from {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing API key. Include X-API-Key header in your request."}
            )
        
        if provided_key != self.api_key:
            client_ip = self._get_client_ip(request)
            logger.warning(f"Invalid API key from {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid API key"}
            )
        
        # Authentication successful
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address for logging purposes.
        
        Checks X-Forwarded-For header first (for proxy/load balancer scenarios),
        then falls back to direct client IP.
        
        Args:
            request: The incoming HTTP request
            
        Returns:
            Client IP address as string
        """
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
