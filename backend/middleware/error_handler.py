"""
Error Handling Middleware and Custom Exceptions

This module provides comprehensive error handling with custom exception types
and consistent JSON error responses.

Feature: edurisk-ai-placement-intelligence
Requirements: 22.1, 22.2, 22.3, 22.4, 22.5, 22.6
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Dict, Any
import logging
import traceback
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


# Custom Exception Classes
class EduRiskException(Exception):
    """Base exception for EduRisk AI application"""
    def __init__(self, message: str, status_code: int = 500, details: Dict[str, Any] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(EduRiskException):
    """Exception for validation errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, status_code=422, details=details)


class DatabaseError(EduRiskException):
    """Exception for database operation errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, status_code=503, details=details)


class ModelError(EduRiskException):
    """Exception for ML model errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, status_code=500, details=details)


class ExternalServiceError(EduRiskException):
    """Exception for external service failures (e.g., Claude API)"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, status_code=503, details=details)


class NotFoundError(EduRiskException):
    """Exception for resource not found errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, status_code=404, details=details)


class InternalServerError(EduRiskException):
    """Exception for internal server errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, status_code=500, details=details)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive error handling middleware that catches all exceptions
    and returns consistent JSON error responses.
    
    Requirements: 22.1, 22.2, 22.3, 22.4
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        try:
            response = await call_next(request)
            return response
            
        except EduRiskException as e:
            # Handle custom application exceptions
            logger.error(
                f"Application error: {e.message}",
                extra={
                    "error_type": type(e).__name__,
                    "status_code": e.status_code,
                    "path": request.url.path,
                    "method": request.method,
                    "details": e.details,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                exc_info=True
            )
            
            # Check DEBUG mode from environment (Requirement 5.2.1, 5.2.2)
            import os
            debug_mode = os.getenv("DEBUG", "False").lower() == "true"
            
            # Build error response
            error_content = {
                "error": type(e).__name__,
                "message": e.message,
                "details": e.details,
                "path": request.url.path,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Include stack trace only in DEBUG mode (Requirement 5.2.2)
            if debug_mode:
                error_content["debug_info"] = {
                    "stack_trace": traceback.format_exc()
                }
            
            return JSONResponse(
                status_code=e.status_code,
                content=error_content
            )
            
        except RequestValidationError as e:
            # Handle Pydantic validation errors (HTTP 422)
            error_details = []
            for error in e.errors():
                error_details.append({
                    "field": ".".join(str(loc) for loc in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"]
                })
            
            logger.warning(
                f"Validation error: {len(error_details)} field(s) failed validation",
                extra={
                    "error_type": "RequestValidationError",
                    "path": request.url.path,
                    "method": request.method,
                    "validation_errors": error_details,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "error": "ValidationError",
                    "message": "Request validation failed",
                    "details": error_details,
                    "path": request.url.path,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
        except ValueError as e:
            # Handle value errors (typically validation-related)
            logger.error(
                f"Value error: {str(e)}",
                extra={
                    "error_type": "ValueError",
                    "path": request.url.path,
                    "method": request.method,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                exc_info=True
            )
            
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "ValueError",
                    "message": str(e),
                    "path": request.url.path,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
        except Exception as e:
            # Handle all other unhandled exceptions
            # Requirement 22.1: Log full stack trace with ERROR level
            stack_trace = traceback.format_exc()
            
            logger.error(
                f"Unhandled exception: {str(e)}",
                extra={
                    "error_type": type(e).__name__,
                    "path": request.url.path,
                    "method": request.method,
                    "stack_trace": stack_trace,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                exc_info=True
            )
            
            # Check DEBUG mode from environment (Requirement 5.2.1, 5.2.2)
            import os
            debug_mode = os.getenv("DEBUG", "False").lower() == "true"
            
            # Build error response
            error_content = {
                "error": "InternalServerError",
                "message": "An unexpected error occurred. Please try again later.",
                "path": request.url.path,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Include stack trace only in DEBUG mode (Requirement 5.2.2)
            if debug_mode:
                error_content["debug_info"] = {
                    "exception_type": type(e).__name__,
                    "exception_message": str(e),
                    "stack_trace": stack_trace
                }
            
            # Don't expose internal error details in production (Requirement 5.2.3)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_content
            )


def create_error_response(
    error_type: str,
    message: str,
    status_code: int = 500,
    details: Dict[str, Any] = None
) -> JSONResponse:
    """
    Helper function to create consistent error responses.
    
    Args:
        error_type: Type of error (e.g., "ValidationError", "DatabaseError")
        message: Human-readable error message
        status_code: HTTP status code
        details: Additional error details
        
    Returns:
        JSONResponse with consistent error format
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "error": error_type,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )
