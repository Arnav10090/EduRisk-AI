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
from sqlalchemy.orm import joinedload, selectinload
from typing import List, Optional
from decimal import Decimal
import logging

from backend.db.session import get_db
from backend.models.student import Student
from backend.models.prediction import Prediction
from backend.routes.auth import get_current_user
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


class StudentDetailResponse(BaseModel):
    """Response model for student detail with complete prediction data."""
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
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    salary_confidence: Optional[Decimal] = None
    emi_affordability: Optional[Decimal] = None
    shap_values: Optional[dict] = None
    top_risk_drivers: Optional[List[dict]] = None
    ai_summary: Optional[str] = None
    next_best_actions: Optional[List[dict]] = None
    alert_triggered: Optional[bool] = None
    prediction_created_at: Optional[str] = None


class PredictionHistoryEntry(BaseModel):
    """Response model for prediction history entry."""
    prediction_id: str
    risk_score: int
    risk_level: str
    created_at: str


@router.get("/students", response_model=StudentListResponse, status_code=status.HTTP_200_OK)
async def list_students(
    search: Optional[str] = Query(default=None, description="Search by student name (case-insensitive)"),
    sort: str = Query(default="created_at", description="Sort column (risk_score, name, course_type, institute_tier, created_at)"),
    order: str = Query(default="desc", description="Sort order (asc or desc)"),
    limit: int = Query(default=20, ge=1, le=500, description="Maximum number of students to return"),
    offset: int = Query(default=0, ge=0, description="Number of students to skip for pagination"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieve list of all students with their latest predictions.
    
    **Protected Route**: Requires valid JWT token in Authorization header.
    
    This endpoint supports search, sorting, and pagination for viewing
    the complete student portfolio with risk assessments.
    
    Args:
        search: Optional name search filter (case-insensitive partial match)
        sort: Column to sort by (risk_score, name, course_type, institute_tier, created_at)
        order: Sort order (asc or desc)
        limit: Maximum number of results (default 20, max 500)
        offset: Pagination offset (default 0)
        db: Database session (injected)
        current_user: Authenticated user information (injected from JWT)
        
    Returns:
        StudentListResponse with array of students and total count
        
    Raises:
        HTTPException 401: Invalid or expired JWT token
        HTTPException 500: Internal server error
        
    Requirements:
        - 7.3.1: Use get_current_user() dependency for JWT authentication
        - 7.3.2: Extract and validate JWT from Authorization header
        - 7.3.3: Return user information from JWT payload
        - 7.3.4: Raise 401 exception for invalid/expired tokens
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
            f"User '{current_user['username']}' listing students with search={search}, sort={sort}, order={order}, "
            f"limit={limit}, offset={offset}"
        )
        
        # Build query with eager loading to avoid N+1 pattern (Requirement 26.1, 26.2)
        # Use joinedload() to fetch students with their predictions in a single query
        query = select(Student).options(joinedload(Student.predictions))
        
        # Apply search filter (Requirement 12.2)
        if search:
            search_pattern = f"%{search}%"
            query = query.where(Student.name.ilike(search_pattern))
        
        # Apply sorting (Requirements 12.3, 12.4)
        # Note: When sorting by prediction fields, we need to join with predictions
        if sort == "risk_score":
            # For risk_score sorting, we need to join with the latest prediction
            # Use a subquery to get the latest prediction per student
            latest_prediction_subquery = (
                select(
                    Prediction.student_id,
                    func.max(Prediction.created_at).label("max_created_at")
                )
                .group_by(Prediction.student_id)
                .subquery()
            )
            
            query = (
                query
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
        
        # Execute query with eager loading (Requirement 26.1, 26.4)
        result = await db.execute(query)
        students = result.unique().scalars().all()
        
        # Format response (Requirement 12.7)
        # Predictions are already loaded via joinedload(), no additional queries needed
        students_response = []
        for student in students:
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
            
            # Get latest prediction from already-loaded predictions (no N+1 query)
            if student.predictions:
                latest_prediction = max(student.predictions, key=lambda p: p.created_at)
                student_data.prediction_id = str(latest_prediction.id)
                student_data.risk_score = latest_prediction.risk_score
                student_data.risk_level = latest_prediction.risk_level
                student_data.prob_placed_3m = latest_prediction.prob_placed_3m
                student_data.prob_placed_6m = latest_prediction.prob_placed_6m
                student_data.prob_placed_12m = latest_prediction.prob_placed_12m
                student_data.alert_triggered = latest_prediction.alert_triggered
                student_data.prediction_created_at = latest_prediction.created_at.isoformat()
            
            students_response.append(student_data)
        
        logger.info(
            f"Retrieved {len(students_response)} students (total: {total_count}) "
            f"with search={search}, sort={sort} using optimized query"
        )
        
        return StudentListResponse(
            students=students_response,
            total_count=total_count
        )
        
    except Exception as e:
        logger.error(f"Error listing students: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve students: {str(e)}"
        )


@router.get("/students/{student_id}", response_model=StudentDetailResponse, status_code=status.HTTP_200_OK)
async def get_student_detail(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieve detailed information for a specific student with their latest prediction.
    
    **Protected Route**: Requires valid JWT token in Authorization header.
    
    This endpoint returns complete student data including all prediction fields
    needed for the student detail page (SHAP values, AI summary, actions, etc.).
    
    Args:
        student_id: UUID of the student
        db: Database session (injected)
        current_user: Authenticated user information (injected from JWT)
        
    Returns:
        StudentDetailResponse with complete student and prediction data
        
    Raises:
        HTTPException 401: Invalid or expired JWT token
        HTTPException 404: Student not found
        HTTPException 500: Internal server error
        
    Requirements:
        - 7.3.1: Use get_current_user() dependency for JWT authentication
        - 7.3.2: Extract and validate JWT from Authorization header
        - 7.3.3: Return user information from JWT payload
        - 7.3.4: Raise 401 exception for invalid/expired tokens
    """
    try:
        logger.info(f"User '{current_user['username']}' fetching detail for student {student_id}")
        
        # Query student with eager loading of predictions (Requirement 26.1)
        student_query = (
            select(Student)
            .options(joinedload(Student.predictions))
            .where(Student.id == student_id)
        )
        student_result = await db.execute(student_query)
        student = student_result.unique().scalar_one_or_none()
        
        if not student:
            logger.warning(f"Student {student_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with ID {student_id} not found"
            )
        
        # Get latest prediction from already-loaded predictions (no additional query)
        prediction = None
        if student.predictions:
            prediction = max(student.predictions, key=lambda p: p.created_at)
        
        # Build response
        response = StudentDetailResponse(
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
            response.prediction_id = str(prediction.id)
            response.risk_score = prediction.risk_score
            response.risk_level = prediction.risk_level
            response.prob_placed_3m = prediction.prob_placed_3m
            response.prob_placed_6m = prediction.prob_placed_6m
            response.prob_placed_12m = prediction.prob_placed_12m
            response.salary_min = prediction.salary_min
            response.salary_max = prediction.salary_max
            response.salary_confidence = prediction.salary_confidence
            response.emi_affordability = prediction.emi_affordability
            response.shap_values = prediction.shap_values
            response.top_risk_drivers = prediction.top_risk_drivers
            response.ai_summary = prediction.ai_summary
            response.next_best_actions = prediction.next_best_actions
            response.alert_triggered = prediction.alert_triggered
            response.prediction_created_at = prediction.created_at.isoformat()
        
        logger.info(f"Retrieved detail for student {student_id} using optimized query")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching student detail: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve student detail: {str(e)}"
        )


@router.get("/students/{student_id}/predictions", response_model=List[PredictionHistoryEntry], status_code=status.HTTP_200_OK)
async def get_student_predictions(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieve prediction history for a specific student.
    
    **Protected Route**: Requires valid JWT token in Authorization header.
    
    This endpoint returns all predictions for a student, ordered by date descending,
    for display in the audit trail timeline.
    
    Args:
        student_id: UUID of the student
        db: Database session (injected)
        current_user: Authenticated user information (injected from JWT)
        
    Returns:
        List of PredictionHistoryEntry objects
        
    Raises:
        HTTPException 401: Invalid or expired JWT token
        HTTPException 404: Student not found
        HTTPException 500: Internal server error
        
    Requirements:
        - 7.3.1: Use get_current_user() dependency for JWT authentication
        - 7.3.2: Extract and validate JWT from Authorization header
        - 7.3.3: Return user information from JWT payload
        - 7.3.4: Raise 401 exception for invalid/expired tokens
    """
    try:
        logger.info(f"User '{current_user['username']}' fetching prediction history for student {student_id}")
        
        # Verify student exists
        student_query = select(Student).where(Student.id == student_id)
        student_result = await db.execute(student_query)
        student = student_result.scalar_one_or_none()
        
        if not student:
            logger.warning(f"Student {student_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with ID {student_id} not found"
            )
        
        # Query all predictions for student
        predictions_query = (
            select(Prediction)
            .where(Prediction.student_id == student_id)
            .order_by(desc(Prediction.created_at))
        )
        predictions_result = await db.execute(predictions_query)
        predictions = predictions_result.scalars().all()
        
        # Format response
        history = [
            PredictionHistoryEntry(
                prediction_id=str(pred.id),
                risk_score=pred.risk_score,
                risk_level=pred.risk_level,
                created_at=pred.created_at.isoformat()
            )
            for pred in predictions
        ]
        
        logger.info(f"Retrieved {len(history)} predictions for student {student_id}")
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching prediction history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve prediction history: {str(e)}"
        )


class DashboardHeatmapResponse(BaseModel):
    """Response model for dashboard heatmap data."""
    students: List[StudentWithPrediction]
    high_risk_count: int
    total_students: int


@router.get("/dashboard/heatmap", response_model=DashboardHeatmapResponse, status_code=status.HTTP_200_OK)
async def get_dashboard_heatmap(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get dashboard heatmap data with optimized queries.
    
    **Protected Route**: Requires valid JWT token in Authorization header.
    
    This endpoint executes at most 2 database queries to fetch all data needed
    for the dashboard heatmap visualization.
    
    Args:
        db: Database session (injected)
        current_user: Authenticated user information (injected from JWT)
        
    Returns:
        DashboardHeatmapResponse with students and high-risk count
        
    Raises:
        HTTPException 401: Invalid or expired JWT token
        HTTPException 500: Internal server error
        
    Requirements:
        - 26.4: Execute at most 2 database queries for dashboard heatmap
        - 26.1: Use joinedload() to avoid N+1 queries
    """
    try:
        logger.info(f"User '{current_user['username']}' fetching dashboard heatmap")
        
        # Query 1: Get all students with their predictions using joinedload (Requirement 26.1, 26.4)
        students_query = (
            select(Student)
            .options(joinedload(Student.predictions))
            .order_by(desc(Student.created_at))
        )
        students_result = await db.execute(students_query)
        students = students_result.unique().scalars().all()
        
        # Query 2: Get high-risk alert count (Requirement 26.4)
        high_risk_query = (
            select(func.count())
            .select_from(Prediction)
            .where(Prediction.risk_level == "high")
        )
        high_risk_result = await db.execute(high_risk_query)
        high_risk_count = high_risk_result.scalar()
        
        # Format response - predictions already loaded, no N+1 queries
        students_response = []
        for student in students:
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
            
            # Get latest prediction from already-loaded predictions
            if student.predictions:
                latest_prediction = max(student.predictions, key=lambda p: p.created_at)
                student_data.prediction_id = str(latest_prediction.id)
                student_data.risk_score = latest_prediction.risk_score
                student_data.risk_level = latest_prediction.risk_level
                student_data.prob_placed_3m = latest_prediction.prob_placed_3m
                student_data.prob_placed_6m = latest_prediction.prob_placed_6m
                student_data.prob_placed_12m = latest_prediction.prob_placed_12m
                student_data.alert_triggered = latest_prediction.alert_triggered
                student_data.prediction_created_at = latest_prediction.created_at.isoformat()
            
            students_response.append(student_data)
        
        logger.info(
            f"Dashboard heatmap loaded with 2 queries: {len(students_response)} students, "
            f"{high_risk_count} high-risk alerts"
        )
        
        return DashboardHeatmapResponse(
            students=students_response,
            high_risk_count=high_risk_count,
            total_students=len(students_response)
        )
        
    except Exception as e:
        logger.error(f"Error fetching dashboard heatmap: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dashboard heatmap: {str(e)}"
        )

