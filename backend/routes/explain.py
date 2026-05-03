"""
SHAP Explanation API endpoint.

Implements GET /api/explain/{student_id} endpoint for retrieving
detailed SHAP explanations for student predictions.

Feature: edurisk-ai-placement-intelligence
Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6
"""

from fastapi import APIRouter, Depends, HTTPException, status, Path as PathParam
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from uuid import UUID
import logging

from backend.db.session import get_db
from backend.models.prediction import Prediction
from backend.schemas.prediction import ShapExplanationResponse
from backend.services.audit_logger import AuditLogger
from backend.routes.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/explain/{student_id}", response_model=ShapExplanationResponse, status_code=status.HTTP_200_OK)
async def get_explanation(
    student_id: UUID = PathParam(..., description="Student UUID"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieve detailed SHAP explanation for a student's most recent prediction.
    
    **Protected Route**: Requires valid JWT token in Authorization header.
    
    This endpoint returns the complete SHAP values dictionary, base value,
    prediction probability, and waterfall data structure for visualization.
    Logs the EXPLAIN action to the audit trail for compliance tracking.
    
    Args:
        student_id: UUID of the student
        db: Database session (injected)
        current_user: Authenticated user information (injected from JWT)
        
    Returns:
        ShapExplanationResponse with SHAP values and waterfall data
        
    Raises:
        HTTPException 401: Invalid or expired JWT token
        HTTPException 404: No prediction found for student
        HTTPException 500: Internal server error
        
    Requirements:
        - 6.2: Log EXPLAIN action to audit trail
        - 6.2.1: Import AuditLogger
        - 6.2.2: Call await AuditLogger.log_explain()
        - 6.2.3: Pass student_id, prediction_id, and performed_by="api_user"
        - 6.2.4: Commit audit log entry to database
        - 7.3.1: Use get_current_user() dependency for JWT authentication
        - 7.3.2: Extract and validate JWT from Authorization header
        - 7.3.3: Return user information from JWT payload
        - 7.3.4: Raise 401 exception for invalid/expired tokens
        - 10.1: Accept student UUID via GET /api/explain/{student_id}
        - 10.2: Retrieve most recent prediction for student
        - 10.3: Return ShapExplanationResponse with SHAP values
        - 10.4: Format waterfall data structure for visualization
        - 10.5: Return HTTP 404 if student not found
        - 10.6: Complete within 1 second
    """
    try:
        logger.info(f"User '{current_user['username']}' retrieving SHAP explanation for student: {student_id}")
        
        # Query most recent prediction for student (Requirement 10.2)
        query = (
            select(Prediction)
            .where(Prediction.student_id == student_id)
            .order_by(desc(Prediction.created_at))
            .limit(1)
        )
        
        result = await db.execute(query)
        prediction = result.scalar_one_or_none()
        
        # Return 404 if no prediction found (Requirement 10.5)
        if prediction is None:
            logger.warning(f"No prediction found for student: {student_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No prediction found for student {student_id}"
            )
        
        # Extract SHAP values from prediction
        shap_values = prediction.shap_values
        
        # Calculate base value and prediction
        # Base value is typically stored in SHAP values or we use a default
        base_value = shap_values.get("base_value", 0.5)
        
        # Calculate prediction as base_value + sum of SHAP values
        # (excluding base_value if it's in the dict)
        shap_sum = sum(
            float(v) for k, v in shap_values.items() 
            if k != "base_value"
        )
        prediction_value = base_value + shap_sum
        
        # Format waterfall data for visualization (Requirement 10.4)
        waterfall_data = []
        
        # Start with base value
        waterfall_data.append({
            "feature": "base_value",
            "value": base_value,
            "cumulative": base_value
        })
        
        # Sort SHAP values by absolute value (descending) for better visualization
        sorted_shap = sorted(
            [(k, v) for k, v in shap_values.items() if k != "base_value"],
            key=lambda x: abs(float(x[1])),
            reverse=True
        )
        
        # Build waterfall with cumulative values
        cumulative = base_value
        for feature, value in sorted_shap:
            cumulative += float(value)
            waterfall_data.append({
                "feature": feature,
                "value": float(value),
                "cumulative": cumulative
            })
        
        logger.info(
            f"SHAP explanation retrieved for student: {student_id} - "
            f"Prediction: {prediction_value:.4f}"
        )
        
        # Log EXPLAIN action to audit trail (Requirement 6.2)
        await AuditLogger.log_explain(
            db=db,
            student_id=student_id,
            prediction_id=prediction.id,
            performed_by=current_user['username']  # Use authenticated username
        )
        
        # Commit audit log entry to database (Requirement 6.2.4)
        await db.commit()
        
        return ShapExplanationResponse(
            student_id=student_id,
            shap_values={k: float(v) for k, v in shap_values.items() if k != "base_value"},
            base_value=base_value,
            prediction=prediction_value,
            waterfall_data=waterfall_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving SHAP explanation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve SHAP explanation: {str(e)}"
        )
