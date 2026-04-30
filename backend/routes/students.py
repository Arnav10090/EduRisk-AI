"""
Student List API endpoint.

Implements GET /api/students endpoint for viewing all students
with their latest predictions.

Feature: edurisk-ai-placement-intelligence
Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, or_
from typing import List, Optional
from decimal import Decimal
import logging

from backend.db.session import get_db
from backend.models.student import Student
from backend.models.prediction import Prediction
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class StudentWithPrediction(BaseModel):
    """Response model for student with latest prediction."""
    student_id: str
    name: str
    course_type: str
    institute_name: Optional[str]
    institute_tier: int
    cgpa: Optional[Decimal]
    year_of_grad: int
    created_at: str
    
    # Latest prediction fields (optional if no prediction exists)
    prediction_id: Optional[str] = None
    risk_score: Optional[int] = None
    risk_level: Optional[str] = None
    prob_placed_3m: Optional[Decimal] = None
    prob_placed_6m: Optional[Decimal] = None
    prob_placed_12m: Optional[Decimal] = None
    alert_triggered: Optional[bool] = None
    prediction_created_at: Optional[str] = None


class StudentListResponse(BaseModel):
    """Response model for student list with pagination."""
    students: List[StudentWithPrediction]
    total_count: int


@router.get("/students", response_model=StudentListResponse, status_code=status.HTTP_200_OK)
async def list_students(
    search: Optional[str] = Query(default=None, description="Search by student name (case-insensitive)"),
    sort: str = Query(default="created_at", description="Sort column (risk_score, name, course_type, institute_tier, created_at)"),
    order: str = Query(default="desc", description="Sort order (asc or desc)"),
    limit: int = Query(default=20, ge=1, le=500, description="Maximum number of students to return"),
    offset: int = Query(default=0, ge=0, description="Number of students to skip for pagination"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve list of all students with their latest predictions.
    
    This endpoint supports search, sorting, and pagination for viewing
    the complete student portfolio with risk assessments.
    
    Args:
        search: Optional name search filter (case-insensitive partial match)
        sort: Column to sort by (risk_score, name, course_type, institute_tier, created_at)
        order: Sort order (asc or desc)
        limit: Maximum number of results (default 20, max 500)
        offset: Pagination offset (default 0)
        db: Database session (injected)
        
    Returns:
        StudentListResponse with array of students and total count
        
    Raises:
        HTTPException 500: Internal server error
        
    Requirements:
        - 12.1: Accept optional query parameters: search, sort, order, limit, offset
        - 12.2: Filter students by name using case-insensitive partial matching
        - 12.3: Sort by specified column (risk_score, name, course_type, institute_tier, created_at)
        - 12.4: Sort in descending order when order="desc", otherwise ascending
        - 12.5: Support pagination with limit (default 20) and offset (default 0)
        - 12.6: Join with predictions table to include latest prediction
        - 12.7: Return array of students and total_count
    """
    try:
        logger.info(
            f"Listing students with search={search}, sort={sort}, order={order}, "
            f"limit={limit}, offset={offset}"
        )
        
        # Subquery to get latest prediction for each student (Requirement 12.6)
        latest_prediction_subquery = (
            select(
                Prediction.student_id,
                func.max(Prediction.created_at).label("max_created_at")
            )
            .group_by(Prediction.student_id)
            .subquery()
        )
        
        # Main query with left join to get students with their latest prediction
        query = (
            select(Student, Prediction)
            .outerjoin(
                latest_prediction_subquery,
                Student.id == latest_prediction_subquery.c.student_id
            )
            .outerjoin(
                Prediction,
                (Prediction.student_id == Student.id) &
                (Prediction.created_at == latest_prediction_subquery.c.max_created_at)
            )
        )
        
        # Apply search filter (Requirement 12.2)
        if search:
            search_pattern = f"%{search}%"
            query = query.where(Student.name.ilike(search_pattern))
        
        # Apply sorting (Requirements 12.3, 12.4)
        sort_column = Student.created_at  # Default
        
        if sort == "risk_score":
            sort_column = Prediction.risk_score
        elif sort == "name":
            sort_column = Student.name
        elif sort == "course_type":
            sort_column = Student.course_type
        elif sort == "institute_tier":
            sort_column = Student.institute_tier
        elif sort == "created_at":
            sort_column = Student.created_at
        else:
            logger.warning(f"Invalid sort column '{sort}', defaulting to 'created_at'")
            sort_column = Student.created_at
        
        # Apply sort order
        if order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        # Get total count before pagination (Requirement 12.7)
        count_query = select(func.count()).select_from(Student)
        if search:
            search_pattern = f"%{search}%"
            count_query = count_query.where(Student.name.ilike(search_pattern))
        
        count_result = await db.execute(count_query)
        total_count = count_result.scalar()
        
        # Apply pagination (Requirement 12.5)
        query = query.limit(limit).offset(offset)
        
        # Execute query
        result = await db.execute(query)
        rows = result.all()
        
        # Format response (Requirement 12.7)
        students = []
        for student, prediction in rows:
            student_data = StudentWithPrediction(
                student_id=str(student.id),
                name=student.name,
                course_type=student.course_type,
                institute_name=student.institute_name,
                institute_tier=student.institute_tier,
                cgpa=student.cgpa,
                year_of_grad=student.year_of_grad,
                created_at=student.created_at.isoformat()
            )
            
            # Add prediction data if available
            if prediction:
                student_data.prediction_id = str(prediction.id)
                student_data.risk_score = prediction.risk_score
                student_data.risk_level = prediction.risk_level
                student_data.prob_placed_3m = prediction.prob_placed_3m
                student_data.prob_placed_6m = prediction.prob_placed_6m
                student_data.prob_placed_12m = prediction.prob_placed_12m
                student_data.alert_triggered = prediction.alert_triggered
                student_data.prediction_created_at = prediction.created_at.isoformat()
            
            students.append(student_data)
        
        logger.info(
            f"Retrieved {len(students)} students (total: {total_count}) "
            f"with search={search}, sort={sort}"
        )
        
        return StudentListResponse(
            students=students,
            total_count=total_count
        )
        
    except Exception as e:
        logger.error(f"Error listing students: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve students: {str(e)}"
        )
