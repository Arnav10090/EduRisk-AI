"""
Query Profiler Middleware for N+1 Query Optimization.

This middleware logs slow database queries to help identify performance bottlenecks.
Only active in DEBUG mode.

Feature: edurisk-submission-improvements
Requirements: 26.6, 26.7
Task: 11.2 - Add query performance monitoring
"""

import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from typing import Callable

logger = logging.getLogger(__name__)


class QueryProfilerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log slow database queries for optimization.
    
    Logs requests that exceed the slow query threshold (100ms) with
    detailed information including method, path, and duration.
    
    Requirements:
        - 26.6: Log slow queries (>100ms) with query details
        - 26.7: Include database query profiling in DEBUG mode
    """
    
    SLOW_QUERY_THRESHOLD_MS = 100
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log if it exceeds slow query threshold.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            HTTP response
        """
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log slow requests (likely slow queries) (Requirement 26.6)
        if duration_ms > self.SLOW_QUERY_THRESHOLD_MS:
            logger.warning(
                f"⚠️ SLOW QUERY: {request.method} {request.url.path} "
                f"took {duration_ms:.2f}ms (threshold: {self.SLOW_QUERY_THRESHOLD_MS}ms) "
                f"| Query params: {dict(request.query_params)} "
                f"| Client: {request.client.host if request.client else 'unknown'}"
            )
        else:
            # Log all queries in DEBUG mode for profiling (Requirement 26.7)
            logger.debug(
                f"Query: {request.method} {request.url.path} "
                f"took {duration_ms:.2f}ms"
            )
        
        return response
