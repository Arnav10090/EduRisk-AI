"""
Request Logging Middleware

This middleware logs all API requests with detailed context including
method, path, status code, and response time.

Feature: edurisk-ai-placement-intelligence
Requirements: 22.6
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import time
from backend.middleware.logging_config import RequestLogger

# Create logger instance
request_logger = RequestLogger("edurisk.api.requests")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging all API requests with timing information.
    
    Requirement 22.6: Log all API requests with INFO level including
    method, path, status code, and response time
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Record start time
        start_time = time.time()
        
        # Get client IP
        client_ip = request.client.host if request.client else None
        
        # Log request start
        request_logger.log_request_start(
            method=request.method,
            path=request.url.path,
            client_ip=client_ip
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Log request completion
        request_logger.log_request_complete(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            response_time=response_time,
            client_ip=client_ip
        )
        
        # Add response time header
        response.headers["X-Process-Time"] = f"{response_time:.3f}"
        
        return response
