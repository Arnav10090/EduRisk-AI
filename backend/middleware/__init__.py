"""
Middleware package for EduRisk AI Backend.

This package contains custom middleware components including:
- Rate limiting middleware
- Error handling middleware
- Request logging middleware
- Structured logging configuration
"""

from backend.middleware.rate_limit import RateLimitMiddleware
from backend.middleware.error_handler import (
    ErrorHandlingMiddleware,
    EduRiskException,
    ValidationError,
    DatabaseError,
    ModelError,
    ExternalServiceError,
    NotFoundError,
    InternalServerError,
    create_error_response
)
from backend.middleware.request_logging import RequestLoggingMiddleware
from backend.middleware.logging_config import (
    configure_logging,
    RequestLogger,
    request_logger
)

__all__ = [
    "RateLimitMiddleware",
    "ErrorHandlingMiddleware",
    "RequestLoggingMiddleware",
    "EduRiskException",
    "ValidationError",
    "DatabaseError",
    "ModelError",
    "ExternalServiceError",
    "NotFoundError",
    "InternalServerError",
    "create_error_response",
    "configure_logging",
    "RequestLogger",
    "request_logger"
]

