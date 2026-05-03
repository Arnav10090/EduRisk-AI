"""
API Router and Middleware Configuration

This module configures the main API router with all endpoint routes
and middleware stack including CORS, request logging, error handling,
and rate limiting.

Feature: edurisk-ai-placement-intelligence
Requirements: 21.1, 21.2, 21.3, 21.4, 21.5, 22.1, 22.2, 22.3, 22.4, 22.5, 22.6
"""

from fastapi import APIRouter
from fastapi.middleware.cors import CORSMiddleware
import logging

# Import middleware components
from backend.middleware import (
    ErrorHandlingMiddleware,
    RequestLoggingMiddleware,
    configure_logging
)

# Configure structured logging
configure_logging(log_level="INFO", json_format=True)

logger = logging.getLogger(__name__)

# Create main API router
api_router = APIRouter(prefix="/api")


def configure_cors(app, cors_origins: list):
    """
    Configure CORS middleware with specified origins.
    
    Args:
        app: FastAPI application instance
        cors_origins: List of allowed origins
        
    Requirements: 21.1, 21.2, 21.5, 22.1, 22.2, 22.3, 22.4
    """
    # Log warning if wildcard detected
    if "*" in cors_origins:
        logger.warning(
            "⚠️ SECURITY WARNING: CORS configured with wildcard (*). "
            "This allows requests from ANY origin and should NEVER be used in production!"
        )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Accept", "X-API-Key"],
    )
    logger.info(f"CORS configured with origins: {cors_origins}")


def configure_middleware(app, config=None):
    """
    Configure all middleware in the correct order.
    
    Order matters: Exception handling should be outermost,
    then logging, then rate limiting, then CORS.
    
    Args:
        app: FastAPI application instance
        config: Configuration object (optional, for rate limiting)
        
    Requirements: 21.3, 21.4, 22.1, 22.2, 22.3, 22.4, 22.5, 22.6, 23.1, 23.2, 23.3, 23.4, 23.5, 23.6
    """
    # Add exception handling middleware (outermost)
    # Requirement 22.1, 22.2, 22.3, 22.4: Comprehensive error handling
    app.add_middleware(ErrorHandlingMiddleware)
    logger.info("Error handling middleware configured")
    
    # Add request logging middleware
    # Requirement 22.6: Log all API requests with method, path, status, response time
    app.add_middleware(RequestLoggingMiddleware)
    logger.info("Request logging middleware configured")
    
    # Add rate limiting middleware if config provided
    if config:
        from backend.middleware.rate_limit import RateLimitMiddleware
        import os
        
        # Get rate limiting configuration from environment
        enabled = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
        predict_limit = int(os.getenv("RATE_LIMIT_PREDICT_PER_MINUTE", "100"))
        batch_limit = int(os.getenv("RATE_LIMIT_BATCH_PER_MINUTE", "10"))
        get_limit = int(os.getenv("RATE_LIMIT_GET_PER_MINUTE", "300"))
        
        app.add_middleware(
            RateLimitMiddleware,
            redis_url=config.redis_url,
            enabled=enabled,
            predict_limit=predict_limit,
            batch_limit=batch_limit,
            get_limit=get_limit
        )
        logger.info("Rate limiting middleware configured")
    
    logger.info("All middleware configured successfully")


def include_routes(app):
    """
    Include all route modules in the API router.
    
    Args:
        app: FastAPI application instance
    """
    # Import route modules
    from backend.routes import predict, explain, alerts, students, health, auth, predictions
    
    # Include routers
    api_router.include_router(auth.router, tags=["Authentication"])
    api_router.include_router(predict.router, tags=["Predictions"])
    api_router.include_router(predictions.router, tags=["Predictions"])  # SHAP retrieval endpoint
    api_router.include_router(explain.router, tags=["Explanations"])
    api_router.include_router(alerts.router, tags=["Alerts"])
    api_router.include_router(students.router, tags=["Students"])
    api_router.include_router(health.router, tags=["Health"])
    
    # Include API router in app
    app.include_router(api_router)
    
    logger.info("All routes included successfully")
