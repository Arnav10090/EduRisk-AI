"""
Prediction API endpoints for single and batch student scoring.

Implements POST /api/predict and POST /api/batch-score endpoints.

Feature: edurisk-ai-placement-intelligence
Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import asyncio
import logging

from backend.db.session import get_db
from backend.schemas.student import StudentInput, BatchScoreRequest
from backend.schemas.prediction import PredictionResponse, BatchScoreResponse
from backend.services.prediction_service import PredictionService
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
        llm_service = LLMService(config.anthropic_api_key)
        
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
    prediction_service: PredictionService = Depends(get_prediction_service)
):
    """
    Generate placement risk prediction for a single student.
    
    This endpoint accepts a student profile and returns a comprehensive
    risk assessment including placement probabilities, risk scores,
    salary estimates, SHAP explanations, AI summary, and recommended actions.
    
    Args:
        student_data: Validated student input data
        db: Database session (injected)
        prediction_service: Prediction service instance (injected)
        
    Returns:
        PredictionResponse with complete prediction results
        
    Raises:
        HTTPException 422: Validation error in input data
        HTTPException 500: Internal server error during prediction
        
    Requirements:
        - 8.1: Accept Student_Profile via POST /api/predict
        - 8.2: Create student record in database
        - 8.3: Invoke all ML components in sequence
        - 8.4: Store complete prediction in database
        - 8.5: Return PredictionResponse
        - 8.6: Complete within 5 seconds for 95% of requests
        - 8.7: Return HTTP 500 with descriptive error on failure
    """
    try:
        logger.info(f"Processing prediction request for student: {student_data.name}")
        
        # Generate prediction using service
        result = await prediction_service.predict_student(
            student_data=student_data,
            db=db,
            performed_by="api_user"
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


@router.post("/batch-score", response_model=BatchScoreResponse, status_code=status.HTTP_200_OK)
async def predict_batch(
    batch_request: BatchScoreRequest,
    db: AsyncSession = Depends(get_db),
    prediction_service: PredictionService = Depends(get_prediction_service)
):
    """
    Generate placement risk predictions for multiple students in parallel.
    
    This endpoint accepts an array of student profiles (max 500) and returns
    predictions for all students along with aggregate summary statistics.
    
    Args:
        batch_request: Batch request containing array of student profiles
        db: Database session (injected)
        prediction_service: Prediction service instance (injected)
        
    Returns:
        BatchScoreResponse with array of predictions and summary statistics
        
    Raises:
        HTTPException 400: Batch size exceeds 500 students
        HTTPException 422: Validation error in input data
        HTTPException 500: Internal server error during batch processing
        
    Requirements:
        - 9.1: Accept array of Student_Profile objects
        - 9.2: Reject batches > 500 students with HTTP 400
        - 9.3: Process each student using same pipeline as single predictions
        - 9.4: Process predictions in parallel with asyncio.gather()
        - 9.5: Return BatchScoreResponse with results array and summary
        - 9.6: Include high_risk_count, medium_risk_count, low_risk_count in summary
        - 9.7: Complete within 60 seconds for batches of 500 students
    """
    try:
        students = batch_request.students
        
        # Validate batch size (Requirement 9.2)
        if len(students) > 500:
            logger.warning(f"Batch size {len(students)} exceeds maximum of 500")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batch size cannot exceed 500 students. Received {len(students)} students."
            )
        
        logger.info(f"Processing batch prediction request for {len(students)} students")
        
        # Process all predictions in parallel (Requirement 9.4)
        prediction_tasks = [
            prediction_service.predict_student(
                student_data=student,
                db=db,
                performed_by="api_user"
            )
            for student in students
        ]
        
        results = await asyncio.gather(*prediction_tasks, return_exceptions=True)
        
        # Separate successful predictions from errors
        successful_predictions: List[PredictionResponse] = []
        errors = []
        
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing student {idx}: {str(result)}")
                errors.append({"index": idx, "error": str(result)})
            else:
                successful_predictions.append(result)
        
        # If all predictions failed, return error
        if not successful_predictions:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="All predictions failed. Check logs for details."
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
