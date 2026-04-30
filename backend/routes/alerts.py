"""
High-Risk Student Alerts API endpoint.

Implements GET /api/alerts endpoint for retrieving high-risk students
requiring immediate attention.

Feature: edurisk-ai-placement-intelligence
Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, or_
from typing import List, Optional
from decimal import Decimal
import logging

from backend.db.session import get_db
from backend.models.prediction import Prediction
from backend.models.student import Student
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class AlertResponse(BaseModel):
    """Response model for individual alert."""
    student_id: str
    student_name: str
    course_type: str
    institute_tier: int
    risk_score: int
    risk_level: str
    emi_affordability: Optional[Decimal]
    top_risk_driver: str
    prediction_id: str
    created_at: str


@router.get("/alerts", response_model=List[AlertResponse], status_code=status.HTTP_200_OK)
async def get_alerts(
    threshold: str = Query(default="high", description="Risk threshold filter (high, medium, low)"),
    limit: int = Query(default=50, ge=1, le=500, description="Maximum number of alerts to return"),
    offset: int = Query(default=0, ge=0, description="Number of alerts to skip for pagination"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve list of high-risk students requiring immediate attention.
    
    This endpoint returns students filtered by risk threshold, sorted by
    risk score in descending order, with pagination support.
    
    Args:
        threshold: Risk level filter ("high", "medium", "low")
        limit: Maximum number of results (default 50, max 500)
        offset: Pagination offset (default 0)
        db: Database session (injected)
        
    Returns:
        List of AlertResponse objects with student and prediction details
        
    Raises:
        HTTPException 500: Internal server error
        
    Requirements:
        - 11.1: Accept optional query parameters: threshold, limit, offset
        - 11.2: Return students where risk_level="high" OR emi_affordability>0.5
        - 11.3: Default threshold to "high" when omitted
        - 11.4: Support pagination with limit (default 50) and offset (default 0)
        - 11.5: Sort by risk_score descending
        - 11.6: Include student name, course type, tier, risk score, level, EMI, top driver
        - 11.7: Complete within 2 seconds
    """
    try:
        logger.info(
            f"Retrieving alerts with threshold={threshold}, limit={limit}, offset={offset}"
        )
        
        # Build query with joins (Requirement 11.6)
        query = (
            select(Prediction, Student)
            .join(Student, Prediction.student_id == Student.id)
        )
        
        # Apply threshold filter (Requirements 11.2, 11.3)
        if threshold == "high":
            # High risk: risk_level="high" OR emi_affordability > 0.5
            query = query.where(
                or_(
                    Prediction.risk_level == "high",
                    Prediction.emi_affordability > Decimal("0.5")
                )
            )
        elif threshold == "medium":
            query = query.where(Prediction.risk_level == "medium")
        elif threshold == "low":
            query = query.where(Prediction.risk_level == "low")
        else:
            # Invalid threshold, default to high
            logger.warning(f"Invalid threshold '{threshold}', defaulting to 'high'")
            query = query.where(
                or_(
                    Prediction.risk_level == "high",
                    Prediction.emi_affordability > Decimal("0.5")
                )
            )
        
        # Sort by risk_score descending (Requirement 11.5)
        query = query.order_by(desc(Prediction.risk_score))
        
        # Apply pagination (Requirement 11.4)
        query = query.limit(limit).offset(offset)
        
        # Execute query
        result = await db.execute(query)
        rows = result.all()
        
        # Format response (Requirement 11.6)
        alerts = []
        for prediction, student in rows:
            # Extract top risk driver
            top_driver = "N/A"
            if prediction.top_risk_drivers and len(prediction.top_risk_drivers) > 0:
                top_driver = prediction.top_risk_drivers[0].get("feature", "N/A")
            
            alerts.append(AlertResponse(
                student_id=str(student.id),
                student_name=student.name,
                course_type=student.course_type,
                institute_tier=student.institute_tier,
                risk_score=prediction.risk_score,
                risk_level=prediction.risk_level,
                emi_affordability=prediction.emi_affordability,
                top_risk_driver=top_driver,
                prediction_id=str(prediction.id),
                created_at=prediction.created_at.isoformat()
            ))
        
        logger.info(f"Retrieved {len(alerts)} alerts for threshold={threshold}")
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error retrieving alerts: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve alerts: {str(e)}"
        )
