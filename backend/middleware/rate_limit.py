"""
Rate Limiting Middleware

This module implements Redis-backed rate limiting for API endpoints.
Different rate limits are applied based on HTTP method and endpoint path.

Feature: edurisk-ai-placement-intelligence
Requirements: 23.1, 23.2, 23.3, 23.4, 23.5, 23.6
"""

import time
import logging
from typing import Callable, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Redis-backed rate limiting middleware.
    
    Implements per-IP rate limiting with different limits for different endpoints:
    - POST /api/predict: 100 requests per minute
    - POST /api/batch-score: 10 requests per minute
    - GET requests: 300 requests per minute
    
    Returns HTTP 429 when rate limit is exceeded.
    Adds X-RateLimit-* headers to all responses.
    
    Requirements: 23.1, 23.2, 23.3, 23.4, 23.5, 23.6
    """
    
    def __init__(
        self,
        app,
        redis_url: Optional[str] = None,
        enabled: bool = True,
        predict_limit: int = 100,
        batch_limit: int = 10,
        get_limit: int = 300
    ):
        """
        Initialize rate limiting middleware.
        
        Args:
            app: FastAPI application instance
            redis_url: Redis connection URL (e.g., "redis://localhost:6379/0")
            enabled: Whether rate limiting is enabled
            predict_limit: Rate limit for POST /api/predict (requests per minute)
            batch_limit: Rate limit for POST /api/batch-score (requests per minute)
            get_limit: Rate limit for GET requests (requests per minute)
        """
        super().__init__(app)
        self.enabled = enabled
        self.predict_limit = predict_limit
        self.batch_limit = batch_limit
        self.get_limit = get_limit
        
        # Initialize Redis connection if enabled
        self.redis_client: Optional[redis.Redis] = None
        if self.enabled and redis_url:
            try:
                self.redis_client = redis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                logger.info(f"Rate limiting enabled with Redis at {redis_url}")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                logger.warning("Rate limiting will be disabled")
                self.enabled = False
        else:
            if self.enabled:
                logger.warning("Rate limiting enabled but no Redis URL provided - disabling")
                self.enabled = False
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process request with rate limiting.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            HTTP response with rate limit headers
        """
        # Skip rate limiting if disabled or Redis not available
        if not self.enabled or not self.redis_client:
            return await call_next(request)
        
        # Get client IP address
        client_ip = self._get_client_ip(request)
        
        # Determine rate limit based on endpoint
        limit, window = self._get_rate_limit(request)
        
        # Check rate limit
        try:
            allowed, remaining, reset_time = await self._check_rate_limit(
                client_ip, request.method, request.url.path, limit, window
            )
            
            # Create response
            if allowed:
                response = await call_next(request)
            else:
                # Rate limit exceeded - return 429
                retry_after = int(reset_time - time.time())
                response = JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate Limit Exceeded",
                        "detail": f"Too many requests. Please try again in {retry_after} seconds.",
                        "retry_after": retry_after
                    }
                )
            
            # Add rate limit headers to response
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
            response.headers["X-RateLimit-Reset"] = str(int(reset_time))
            
            return response
            
        except Exception as e:
            # If rate limiting fails, log error and allow request through
            logger.error(f"Rate limiting error: {e}", exc_info=True)
            return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request.
        
        Checks X-Forwarded-For header first (for proxied requests),
        then falls back to direct client IP.
        
        Args:
            request: HTTP request
            
        Returns:
            Client IP address as string
        """
        # Check X-Forwarded-For header (for requests behind proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, take the first one
            return forwarded_for.split(",")[0].strip()
        
        # Fall back to direct client IP
        if request.client:
            return request.client.host
        
        # Default fallback
        return "unknown"
    
    def _get_rate_limit(self, request: Request) -> tuple[int, int]:
        """
        Determine rate limit for the request.
        
        Args:
            request: HTTP request
            
        Returns:
            Tuple of (limit, window_seconds)
            - limit: Maximum number of requests allowed
            - window_seconds: Time window in seconds (always 60 for per-minute limits)
        """
        method = request.method.upper()
        path = request.url.path
        
        # POST /api/predict: 100 requests per minute
        if method == "POST" and path == "/api/predict":
            return self.predict_limit, 60
        
        # POST /api/batch-score: 10 requests per minute
        if method == "POST" and path == "/api/batch-score":
            return self.batch_limit, 60
        
        # GET requests: 300 requests per minute
        if method == "GET":
            return self.get_limit, 60
        
        # Default for other requests (POST, PUT, DELETE): use predict limit
        return self.predict_limit, 60
    
    async def _check_rate_limit(
        self,
        client_ip: str,
        method: str,
        path: str,
        limit: int,
        window: int
    ) -> tuple[bool, int, float]:
        """
        Check if request is within rate limit using Redis.
        
        Uses sliding window counter algorithm with Redis.
        
        Args:
            client_ip: Client IP address
            method: HTTP method
            path: Request path
            limit: Maximum requests allowed in window
            window: Time window in seconds
            
        Returns:
            Tuple of (allowed, remaining, reset_time)
            - allowed: Whether request is allowed
            - remaining: Number of requests remaining in window
            - reset_time: Unix timestamp when the rate limit resets
        """
        # Create Redis key for this client/endpoint combination
        key = f"rate_limit:{client_ip}:{method}:{path}"
        
        # Get current time
        now = time.time()
        window_start = now - window
        
        # Use Redis pipeline for atomic operations
        pipe = self.redis_client.pipeline()
        
        # Remove old entries outside the current window
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Count requests in current window
        pipe.zcard(key)
        
        # Add current request with timestamp as score
        pipe.zadd(key, {str(now): now})
        
        # Set expiration on the key (window + 1 second buffer)
        pipe.expire(key, window + 1)
        
        # Execute pipeline
        results = await pipe.execute()
        
        # Get count of requests in current window (before adding current request)
        current_count = results[1]
        
        # Calculate remaining requests and reset time
        remaining = max(0, limit - current_count - 1)
        reset_time = now + window
        
        # Check if limit exceeded
        allowed = current_count < limit
        
        return allowed, remaining, reset_time
    
    async def close(self):
        """Close Redis connection when middleware is shut down."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")
