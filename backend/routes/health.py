"""
System Health Check API endpoint.

Implements GET /api/health endpoint for monitoring service availability.

Feature: edurisk-ai-placement-intelligence
Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6
"""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pathlib import Path
import logging
from datetime import datetime

from backend.db.session import get_db
from backend.config import get_config
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthCheckResponse(BaseModel):
    """Response model for health check."""
    status: str
    timestamp: str
    database: str
    ml_models: str
    model_version: str


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(
    db: AsyncSession = Depends(get_db)
):
    """
    Perform system health check.
    
    This endpoint verifies database connectivity and ML model availability
    to ensure the system is operational.
    
    Args:
        db: Database session (injected)
        
    Returns:
        JSON response with health status and component details
        
    Status Codes:
        - 200: All checks passed (status="ok")
        - 503: One or more checks failed (status="degraded")
        
    Requirements:
        - 13.1: Expose GET /api/health endpoint
        - 13.2: Verify database connectivity
        - 13.3: Verify ML model files exist
        - 13.4: Return HTTP 200 with status "ok" if all checks pass
        - 13.5: Return HTTP 503 with status "degraded" if any check fails
        - 13.6: Complete within 3 seconds
    """
    health_status = "ok"
    database_status = "disconnected"
    ml_models_status = "unavailable"
    model_version = "unknown"
    
    try:
        # Check database connectivity (Requirement 13.2)
        try:
            await db.execute(text("SELECT 1"))
            database_status = "connected"
            logger.debug("Database health check passed")
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            database_status = "disconnected"
            health_status = "degraded"
        
        # Check ML model availability (Requirement 13.3)
        try:
            config = get_config()
            model_dir = Path(config.ml_model_path)
            
            # Check if required model files exist
            required_models = [
                "placement_model_3m.pkl",
                "placement_model_6m.pkl",
                "placement_model_12m.pkl",
                "salary_model.pkl"
            ]
            
            all_models_exist = all(
                (model_dir / model_file).exists()
                for model_file in required_models
            )
            
            if all_models_exist:
                ml_models_status = "available"
                logger.debug("ML models health check passed")
                
                # Try to read model version
                version_file = model_dir / "version.json"
                if version_file.exists():
                    import json
                    with open(version_file, 'r') as f:
                        version_data = json.load(f)
                        model_version = version_data.get("version", "unknown")
            else:
                logger.error("One or more ML model files are missing")
                ml_models_status = "unavailable"
                health_status = "degraded"
                
        except Exception as e:
            logger.error(f"ML models health check failed: {str(e)}")
            ml_models_status = "unavailable"
            health_status = "degraded"
        
        # Prepare response
        response_data = HealthCheckResponse(
            status=health_status,
            timestamp=datetime.utcnow().isoformat(),
            database=database_status,
            ml_models=ml_models_status,
            model_version=model_version
        )
        
        # Return appropriate status code (Requirements 13.4, 13.5)
        if health_status == "ok":
            logger.info("Health check passed: all systems operational")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=response_data.model_dump()
            )
        else:
            logger.warning(f"Health check degraded: database={database_status}, ml_models={ml_models_status}")
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=response_data.model_dump()
            )
            
    except Exception as e:
        logger.error(f"Health check failed with exception: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "degraded",
                "timestamp": datetime.utcnow().isoformat(),
                "database": database_status,
                "ml_models": ml_models_status,
                "model_version": model_version,
                "error": str(e)
            }
        )
