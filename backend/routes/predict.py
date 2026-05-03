"""
Prediction API endpoints for single and batch student scoring.

Implements POST /api/predict and POST /api/batch-score endpoints.

Feature: edurisk-ai-placement-intelligence
Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 27.1, 27.2, 27.3, 27.4, 27.5, 27.6, 27.7
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import asyncio
import logging
import time

from backend.db.session import get_db
from backend.schemas.student import StudentInput, BatchScoreRequest
from backend.schemas.prediction import PredictionResponse, BatchScoreResponse
from backend.services.prediction_service import PredictionService
from backend.routes.auth import get_current_user
from backend.config import get_config
from pathlib import Path

from ml.pipeline.feature_engineering import FeatureEngineer
from ml.pipeline.predict import PlacementPredictor
from ml.pipeline.salary_model import SalaryEstimator
from backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize ML components (singleton pattern)
_prediction_service = None


def get_prediction_service() -> PredictionService:
    """
    Get or create PredictionService singleton.
    
    Loads ML models on first call and caches for subsequent requests.
    """
    global _prediction_service
    
    if _prediction_service is None:
        config = get_config()
        model_dir = Path(config.ml_model_path)
        
        # Initialize ML components
        feature_engineer = FeatureEngineer()
        placement_predictor = PlacementPredictor(model_dir)
        salary_estimator = SalaryEstimator(model_dir / "salary_model.pkl")
        
        # Initialize LLM service with configured provider
        llm_api_key = config.llm_api_key or config.anthropic_api_key or ""
        llm_service = LLMService(
            api_key=llm_api_key,
            provider=config.llm_provider
        )
        
        # Create prediction service
        _prediction_service = PredictionService(
            feature_engineer=feature_engineer,
            placement_predictor=placement_predictor,
            salary_estimator=salary_estimator,
            llm_service=llm_service,
            model_dir=model_dir
        )
        
        logger.info("PredictionService initialized successfully")
    
    return _prediction_service


@router.post("/predict", response_model=PredictionResponse, status_code=status.HTTP_200_OK)
async def predict_single(
    student_data: StudentInput,
    db: AsyncSession = Depends(get_db),
    prediction_service: PredictionService = Depends(get_prediction_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate placement risk prediction for a single student.
    
    **Protected Route**: Requires valid JWT token in Authorization header.
    
    This endpoint accepts a student profile and returns a comprehensive
    risk assessment including placement probabilities, risk scores,
    salary estimates, SHAP explanations, AI summary, and recommended actions.
    
    Args:
        student_data: Validated student input data
        db: Database session (injected)
        prediction_service: Prediction service instance (injected)
        current_user: Authenticated user information (injected from JWT)
        
    Returns:
        PredictionResponse with complete prediction results
        
    Raises:
        HTTPException 401: Invalid or expired JWT token
        HTTPException 422: Validation error in input data
        HTTPException 500: Internal server error during prediction
        
    Requirements:
        - 7.3.1: Use get_current_user() dependency for JWT authentication
        - 7.3.2: Extract and validate JWT from Authorization header
        - 7.3.3: Return user information from JWT payload
        - 7.3.4: Raise 401 exception for invalid/expired tokens
        - 8.1: Accept Student_Profile via POST /api/predict
        - 8.2: Create student record in database
        - 8.3: Invoke all ML components in sequence
        - 8.4: Store complete prediction in database
        - 8.5: Return PredictionResponse
        - 8.6: Complete within 5 seconds for 95% of requests
        - 8.7: Return HTTP 500 with descriptive error on failure
    """
    try:
        logger.info(f"User '{current_user['username']}' processing prediction request for student: {student_data.name}")
        
        # Generate prediction using service
        result = await prediction_service.predict_student(
            student_data=student_data,
            db=db,
            performed_by=current_user['username']  # Use authenticated username
        )
        
        logger.info(
            f"Prediction completed for student: {result.student_id} - "
            f"Risk Level: {result.risk_level}, Risk Score: {result.risk_score}"
        )
        
        return result
        
    except ValueError as e:
        logger.error(f"Validation error in prediction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing prediction: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate prediction: {str(e)}"
        )


async def compute_shap_values_background(prediction_id: str, student_data: dict, prediction_service: PredictionService):
    """
    Background task to compute SHAP values for a prediction.
    
    This function runs asynchronously after the initial prediction response
    is returned to avoid timeout issues with large batches.
    
    Args:
        prediction_id: UUID of the prediction record
        student_data: Dictionary with student data for feature engineering
        prediction_service: PredictionService instance
        
    Requirements:
        - 27.1: Compute SHAP values asynchronously using BackgroundTasks
        - 27.6: Log SHAP computation time separately from prediction time
        - 27.7: Handle SHAP computation failures gracefully
    """
    from backend.db.session import get_async_session
    from uuid import UUID
    
    start_time = time.time()
    
    try:
        logger.info(f"Starting background SHAP computation for prediction {prediction_id}")
        
        # Transform features
        features = prediction_service.feature_engineer.transform(student_data)
        feature_names = prediction_service.feature_engineer.get_feature_names()
        
        # Compute SHAP explanation
        shap_explanation = prediction_service.shap_explainer.explain(features, feature_names)
        
        # Update prediction record with SHAP values
        async with get_async_session() as db:
            from sqlalchemy import select, update
            from backend.models.prediction import Prediction
            
            stmt = (
                update(Prediction)
                .where(Prediction.id == UUID(prediction_id))
                .values(
                    shap_values=shap_explanation.shap_values,
                    top_risk_drivers=shap_explanation.top_drivers
                )
            )
            await db.execute(stmt)
            await db.commit()
        
        elapsed_time = time.time() - start_time
        logger.info(
            f"SHAP computation completed for prediction {prediction_id} "
            f"in {elapsed_time:.2f} seconds"
        )
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(
            f"SHAP computation failed for prediction {prediction_id} "
            f"after {elapsed_time:.2f} seconds: {str(e)}",
            exc_info=True
        )
        # Don't raise - graceful degradation (Requirement 27.7)


@router.post("/batch-score", response_model=BatchScoreResponse, status_code=status.HTTP_200_OK)
async def predict_batch(
    batch_request: BatchScoreRequest,
    background_tasks: BackgroundTasks,
    prediction_service: PredictionService = Depends(get_prediction_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate placement risk predictions for multiple students in parallel.
    
    **Protected Route**: Requires valid JWT token in Authorization header.
    
    This endpoint accepts an array of student profiles (max 500) and returns
    predictions for all students along with aggregate summary statistics.
    
    SHAP values are computed asynchronously in the background to avoid timeouts.
    Initial response returns predictions with shap_values set to null.
    Use GET /api/predictions/{id}/shap to retrieve SHAP values once computed.
    
    Each student is processed with an independent database session to prevent
    race conditions and session corruption during concurrent processing.
    
    Args:
        batch_request: Batch request containing array of student profiles
        background_tasks: FastAPI background tasks for async SHAP computation
        prediction_service: Prediction service instance (injected)
        current_user: Authenticated user information (injected from JWT)
        
    Returns:
        BatchScoreResponse with array of predictions and summary statistics
        
    Raises:
        HTTPException 400: Batch size exceeds 500 students
        HTTPException 401: Invalid or expired JWT token
        HTTPException 422: Validation error in input data
        HTTPException 500: Internal server error during batch processing
        
    Requirements:
        - 7.3.1: Use get_current_user() dependency for JWT authentication
        - 7.3.2: Extract and validate JWT from Authorization header
        - 7.3.3: Return user information from JWT payload
        - 7.3.4: Raise 401 exception for invalid/expired tokens
        - 9.1: Accept array of Student_Profile objects
        - 9.2: Reject batches > 500 students with HTTP 400
        - 9.3: Process each student using same pipeline as single predictions
        - 9.4: Process predictions in parallel with asyncio.gather()
        - 9.5: Return BatchScoreResponse with results array and summary
        - 9.6: Include high_risk_count, medium_risk_count, low_risk_count in summary
        - 9.7: Complete within 60 seconds for batches of 500 students
        - Requirement 9.1: Create separate database session for each student
        - Requirement 9.2: Do not share session across concurrent predictions
        - Requirement 9.3: Use asyncio.gather() for parallel processing
        - Requirement 9.4: Return success=False for failed items without affecting others
        - Requirement 9.5: Return success=True with prediction data for successful items
        - Requirement 9.6: Close each session after processing
        - 27.1: Compute SHAP values asynchronously using BackgroundTasks
        - 27.2: Return prediction results immediately without SHAP values
        - 27.3: Set shap_values to null in initial response
        - 27.5: Complete POST /api/batch-score in under 5 seconds for 100 students
    """
    from backend.db.session import get_async_session
    
    try:
        students = batch_request.students
        
        # Validate batch size (Requirement 9.2)
        if len(students) > 500:
            logger.warning(f"User '{current_user['username']}' attempted batch size {len(students)} exceeds maximum of 500")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batch size cannot exceed 500 students. Received {len(students)} students."
            )
        
        logger.info(f"User '{current_user['username']}' processing batch prediction request for {len(students)} students")
        
        async def process_student(student_data: StudentInput, index: int) -> dict:
            """
            Process a single student with independent database session.
            
            Each student gets its own database session to prevent race conditions
            and session corruption during concurrent processing.
            
            SHAP values are NOT computed during initial processing to avoid timeouts.
            They will be computed asynchronously in background tasks.
            
            Args:
                student_data: Student input data
                index: Student index in batch (for error reporting)
                
            Returns:
                dict with success status and either prediction or error
                
            Requirements:
                - 9.1: Create separate database session for each student
                - 9.2: Do not share session across concurrent predictions
                - 9.4: Return success=False for failures without affecting others
                - 9.5: Return success=True with prediction data for successes
                - 9.6: Close session after processing
                - 27.2: Skip SHAP computation during initial batch processing
            """
            # Create independent session for this student (Requirement 9.1, 9.2)
            async with get_async_session() as db:
                try:
                    # Process prediction with independent session, skip SHAP (Requirement 27.2)
                    result = await prediction_service.predict_student(
                        student_data=student_data,
                        db=db,
                        performed_by=current_user['username'],
                        compute_shap=False  # Skip SHAP for batch requests
                    )
                    # Session is automatically committed and closed (Requirement 9.6)
                    
                    # Schedule background SHAP computation (Requirement 27.1)
                    student_dict = prediction_service._student_to_dict(student_data)
                    background_tasks.add_task(
                        compute_shap_values_background,
                        str(result.prediction_id),
                        student_dict,
                        prediction_service
                    )
                    
                    # Return success result (Requirement 9.5)
                    return {
                        "success": True,
                        "student_name": student_data.name,
                        "prediction": result
                    }
                except Exception as e:
                    # Session is automatically rolled back and closed (Requirement 9.6)
                    logger.error(f"Error processing student {index} ({student_data.name}): {str(e)}")
                    
                    # Return failure result without affecting other students (Requirement 9.4)
                    return {
                        "success": False,
                        "student_name": student_data.name,
                        "error": str(e),
                        "index": index
                    }
        
        # Process all students in parallel with independent sessions (Requirement 9.3)
        results = await asyncio.gather(
            *[process_student(student, idx) for idx, student in enumerate(students)],
            return_exceptions=False  # Exceptions are handled in process_student
        )
        
        # Separate successful predictions from errors
        successful_predictions: List[PredictionResponse] = []
        errors = []
        
        for result in results:
            if result["success"]:
                successful_predictions.append(result["prediction"])
            else:
                errors.append({
                    "index": result["index"],
                    "student_name": result["student_name"],
                    "error": result["error"]
                })
        
        # If all predictions failed, return error
        if not successful_predictions:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"All {len(students)} predictions failed. Check logs for details."
            )
        
        # Calculate summary statistics (Requirement 9.6)
        high_risk_count = sum(1 for p in successful_predictions if p.risk_level == "high")
        medium_risk_count = sum(1 for p in successful_predictions if p.risk_level == "medium")
        low_risk_count = sum(1 for p in successful_predictions if p.risk_level == "low")
        
        summary = {
            "high_risk_count": high_risk_count,
            "medium_risk_count": medium_risk_count,
            "low_risk_count": low_risk_count
        }
        
        logger.info(
            f"Batch prediction completed: {len(successful_predictions)} successful, "
            f"{len(errors)} errors - Summary: {summary}"
        )
        
        # Log errors if any
        if errors:
            logger.warning(f"Batch processing had {len(errors)} errors: {errors}")
        
        return BatchScoreResponse(
            results=successful_predictions,
            summary=summary
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error in batch prediction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing batch prediction: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process batch prediction: {str(e)}"
        )
