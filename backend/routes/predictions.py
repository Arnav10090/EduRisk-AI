"""
Predictions API endpoints for retrieving prediction data.

Implements GET /api/predictions/{id}/shap endpoint for async SHAP retrieval.

Feature: edurisk-ai-placement-intelligence
Requirements: 27.4
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import logging

from backend.db.session import get_db
from backend.models.prediction import Prediction
from backend.schemas.prediction import ShapExplanationResponse
from backend.routes.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/predictions/{prediction_id}/shap", response_model=ShapExplanationResponse, status_code=status.HTTP_200_OK)
async def get_shap_values(
    prediction_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieve SHAP explanation values for a prediction.
    
    **Protected Route**: Requires valid JWT token in Authorization header.
    
    This endpoint retrieves SHAP values that were computed asynchronously
    after a batch prediction request. If SHAP values are not yet available,
    returns HTTP 404.
    
    Args:
        prediction_id: UUID of the prediction record
        db: Database session (injected)
        current_user: Authenticated user information (injected from JWT)
        
    Returns:
        ShapExplanationResponse with SHAP values and waterfall data
        
    Raises:
        HTTPException 404: Prediction not found or SHAP values not yet computed
        HTTPException 401: Invalid or expired JWT token
        
    Requirements:
        - 27.4.1: Create GET /api/predictions/{id}/shap endpoint
        - 27.4.2: Return SHAP values once computed
        - 27.4.3: Return 404 if SHAP values not yet available
    """
    try:
        logger.info(f"User '{current_user['username']}' requesting SHAP values for prediction {prediction_id}")
        
        # Query prediction record
        stmt = select(Prediction).where(Prediction.id == prediction_id)
        result = await db.execute(stmt)
        prediction = result.scalar_one_or_none()
        
        # Check if prediction exists
        if not prediction:
            logger.warning(f"Prediction {prediction_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prediction {prediction_id} not found"
            )
        
        # Check if SHAP values are available (Requirement 27.4.3)
        if not prediction.shap_values or len(prediction.shap_values) == 0:
            logger.info(f"SHAP values not yet available for prediction {prediction_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SHAP values are still being computed. Please try again in a few moments."
            )
        
        # Calculate base value and prediction from SHAP values
        # Base value is typically the mean prediction on training data
        # For simplicity, we'll use 0.5 as a reasonable baseline
        base_value = 0.5
        
        # Sum SHAP values to get prediction offset
        shap_sum = sum(prediction.shap_values.values())
        prediction_value = base_value + shap_sum
        
        # Clamp prediction to [0, 1] range
        prediction_value = max(0.0, min(1.0, prediction_value))
        
        # Build waterfall data for visualization (Requirement 27.4.2)
        waterfall_data = [
            {
                "feature": "base_value",
                "value": base_value,
                "cumulative": base_value
            }
        ]
        
        cumulative = base_value
        # Sort SHAP values by absolute value (descending) for better visualization
        sorted_shap = sorted(
            prediction.shap_values.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        for feature, value in sorted_shap:
            cumulative += value
            waterfall_data.append({
                "feature": feature,
                "value": value,
                "cumulative": cumulative
            })
        
        logger.info(f"SHAP values retrieved successfully for prediction {prediction_id}")
        
        # Return SHAP explanation response (Requirement 27.4.2)
        return ShapExplanationResponse(
            student_id=prediction.student_id,
            shap_values=prediction.shap_values,
            base_value=base_value,
            prediction=prediction_value,
            waterfall_data=waterfall_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving SHAP values for prediction {prediction_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve SHAP values: {str(e)}"
        )
