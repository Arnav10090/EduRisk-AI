"""
EduRisk AI Backend - Main Application Entry Point
"""

from fastapi import FastAPI
import os
import logging
from dotenv import load_dotenv
from backend.config import get_config
from backend.api.router import configure_cors, configure_middleware, include_routes
from backend.middleware import configure_logging
from backend.middleware.api_key_auth import ApiKeyMiddleware
from backend.middleware.query_profiler import QueryProfilerMiddleware

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure structured logging (Requirement 22.5, 22.6)
log_level = os.getenv("LOG_LEVEL", "INFO")
json_format = os.getenv("LOG_JSON_FORMAT", "True").lower() == "true"
configure_logging(log_level=log_level, json_format=json_format)

# Get application configuration
config = get_config()

# Create FastAPI application
app = FastAPI(
    title="EduRisk AI - Placement Risk Intelligence",
    description="AI-powered placement risk assessment for education loan lenders",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS middleware
configure_cors(app, config.cors_origins)

# Configure query profiler in DEBUG mode (Requirement 26.7, Task 11.2)
debug_mode = os.getenv("DEBUG", "False").lower() == "true"
if debug_mode:
    app.add_middleware(QueryProfilerMiddleware)
    logger.info("✅ Query profiling enabled (DEBUG=True)")

# Configure API key authentication middleware (Requirement 2)
app.add_middleware(ApiKeyMiddleware)

# Configure other middleware (logging, exception handling, rate limiting)
configure_middleware(app, config)

# Include all API routes
include_routes(app)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": "EduRisk AI API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "True").lower() == "true",
    )
