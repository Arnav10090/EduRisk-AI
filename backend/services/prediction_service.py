"""
Prediction Service for EduRisk AI

This module orchestrates the complete prediction pipeline, coordinating
feature engineering, ML model inference, risk calculation, SHAP explanation,
LLM summary generation, and action recommendations.

Feature: edurisk-ai-placement-intelligence
Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""

from typing import Dict, Any, Optional
from pathlib import Path
from decimal import Decimal
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ml.pipeline.feature_engineering import FeatureEngineer
from ml.pipeline.predict import PlacementPredictor
from ml.pipeline.salary_model import SalaryEstimator
from ml.pipeline.explain import ShapExplainer
from .llm_service import LLMService
from .risk_calculator import calculate_risk_score, assign_risk_level, calculate_emi_affordability
from .action_recommender import generate_actions
from .audit_logger import AuditLogger
from .alert_service import AlertService
from ..models.student import Student
from ..models.prediction import Prediction
from ..schemas.student import StudentInput
from ..schemas.prediction import PredictionResponse, RiskDriver, NextBestAction


class PredictionService:
    """
    Orchestrates the complete prediction pipeline for student risk assessment.
    
    This service coordinates all ML components and business logic to generate
    comprehensive placement risk predictions including:
    - Placement timeline probabilities (3/6/12 months)
    - Salary range estimates
    - Risk scores and levels
    - EMI affordability assessment
    - SHAP-based explanations
    - AI-generated summaries
    - Personalized action recommendations
    
    Requirements:
        - 8.1: Accept Student_Profile via POST /api/predict
        - 8.2: Create student record in database
        - 8.3: Invoke all ML components in sequence
        - 8.4: Store complete prediction in database
        - 8.5: Return comprehensive prediction response
    """
    
    def __init__(
        self,
        feature_engineer: FeatureEngineer,
        placement_predictor: PlacementPredictor,
        salary_estimator: SalaryEstimator,
        llm_service: LLMService,
        model_dir: Path
    ):
        """
        Initialize PredictionService with all ML components.
        
        Args:
            feature_engineer: Feature engineering pipeline
            placement_predictor: Placement probability predictor
            salary_estimator: Salary range estimator
            llm_service: LLM service for AI summaries
            model_dir: Path to ML model directory for SHAP explainer
        """
        self.feature_engineer = feature_engineer
        self.placement_predictor = placement_predictor
        self.salary_estimator = salary_estimator
        self.llm_service = llm_service
        
        # Initialize SHAP explainer with the 3-month model
        # (We use 3m model for explanations as it's the primary risk indicator)
        self.shap_explainer = ShapExplainer(placement_predictor.model_3m)
        
        # Initialize alert service for high-risk notifications (Requirement 32.2)
        self.alert_service = AlertService()
    
    async def predict_student(
        self,
        student_data: StudentInput,
        db: AsyncSession,
        performed_by: Optional[str] = "system",
        compute_shap: bool = True
    ) -> PredictionResponse:
        """
        Generate complete prediction for a student.
        
        This method orchestrates the entire prediction pipeline:
        1. Create student record in database
        2. Transform features using feature engineering
        3. Get placement predictions (3/6/12 months)
        4. Get salary prediction with confidence interval
        5. Compute risk score and level
        6. Compute EMI affordability
        7. Generate SHAP explanation (optional, can be skipped for batch requests)
        8. Generate AI summary (async)
        9. Generate next-best action recommendations
        10. Store prediction in database
        11. Log audit entry
        12. Return complete response
        
        Args:
            student_data: Validated student input data
            db: Async database session
            performed_by: User or system identifier for audit logging
            compute_shap: Whether to compute SHAP values (default True, set False for batch)
            
        Returns:
            PredictionResponse with all prediction results
            
        Raises:
            Exception: If any component fails during prediction
            
        Requirements:
            - 8.1: Accept Student_Profile in JSON format
            - 8.2: Create student record in students table
            - 8.3: Invoke all ML components in sequence
            - 8.4: Store complete prediction in predictions table
            - 8.5: Return JSON response with all fields
            - 27.2: Support skipping SHAP computation for batch requests
        """
        # Step 1: Create student record (Requirement 8.2)
        student = await self._create_student_record(student_data, db)
        
        # Step 2: Transform features
        student_dict = self._student_to_dict(student_data)
        features = self.feature_engineer.transform(student_dict)
        feature_names = self.feature_engineer.get_feature_names()
        
        # Step 3: Get placement predictions (Requirement 8.3)
        placement_pred = self.placement_predictor.predict(features)
        model_version = self.placement_predictor.get_model_version()
        
        # Step 4: Get salary prediction (Requirement 8.3)
        salary_pred = self.salary_estimator.predict(features)
        
        # Step 5: Compute risk score and level (Requirement 8.3)
        risk_score = calculate_risk_score(
            placement_pred.prob_3m,
            placement_pred.prob_6m,
            placement_pred.prob_12m
        )
        risk_level = assign_risk_level(risk_score)
        
        # Step 6: Compute EMI affordability (Requirement 8.3)
        emi_affordability = None
        if student_data.loan_emi and salary_pred.predicted:
            emi_affordability = calculate_emi_affordability(
                float(student_data.loan_emi),
                salary_pred.predicted
            )
        
        # Step 7: Generate SHAP explanation (Requirement 8.3, optional for batch - Requirement 27.2)
        if compute_shap:
            shap_explanation = self.shap_explainer.explain(features, feature_names)
            shap_values = shap_explanation.shap_values
            top_risk_drivers = shap_explanation.top_drivers
        else:
            # For batch requests, set SHAP values to empty/null (Requirement 27.3)
            shap_values = {}
            top_risk_drivers = []
        
        # Step 8: Generate AI summary (Requirement 8.3)
        ai_summary = await self._generate_ai_summary(
            student_dict,
            placement_pred,
            risk_score,
            risk_level,
            top_risk_drivers
        )
        
        # Step 9: Generate next-best actions (Requirement 8.3)
        actions = self._generate_actions(
            risk_level,
            risk_score,
            top_risk_drivers,
            student_dict,
            placement_pred
        )
        
        # Step 10: Determine if alert should be triggered
        # Alert triggered if risk_level is "high" OR emi_affordability > 0.5
        alert_triggered = (
            risk_level == "high" or
            (emi_affordability is not None and emi_affordability > 0.5)
        )
        
        # Step 11: Store prediction in database (Requirement 8.4)
        prediction = await self._create_prediction_record(
            student_id=student.id,
            model_version=model_version,
            placement_pred=placement_pred,
            salary_pred=salary_pred,
            risk_score=risk_score,
            risk_level=risk_level,
            emi_affordability=emi_affordability,
            shap_values=shap_values,
            top_risk_drivers=top_risk_drivers,
            ai_summary=ai_summary,
            next_best_actions=actions,
            alert_triggered=alert_triggered,
            db=db
        )
        
        # Step 12: Log audit entry using AuditLogger service
        await AuditLogger.log_predict(
            db=db,
            student_id=student.id,
            prediction_id=prediction.id,
            model_version=model_version,
            risk_level=risk_level,
            risk_score=risk_score,
            alert_triggered=alert_triggered,
            performed_by=performed_by
        )
        
        # Step 13: Trigger alert for high-risk students (Requirement 32.2)
        if risk_level == "high":
            await self.alert_service.send_high_risk_alert(
                student=student,
                prediction=prediction,
                db=db,
                performed_by=performed_by
            )
        
        # Step 14: Return complete response (Requirement 8.5)
        return self._build_response(
            student_id=student.id,
            prediction_id=prediction.id,
            placement_pred=placement_pred,
            salary_pred=salary_pred,
            risk_score=risk_score,
            risk_level=risk_level,
            emi_affordability=emi_affordability,
            top_risk_drivers=top_risk_drivers,
            ai_summary=ai_summary,
            next_best_actions=actions,
            alert_triggered=alert_triggered
        )
    
    async def _create_student_record(
        self,
        student_data: StudentInput,
        db: AsyncSession
    ) -> Student:
        """
        Create a new student record in the database.
        
        Args:
            student_data: Validated student input
            db: Database session
            
        Returns:
            Created Student ORM object
            
        Requirement 8.2: Create student record in students table
        """
        student = Student(
            name=student_data.name,
            course_type=student_data.course_type,
            institute_name=student_data.institute_name,
            institute_tier=student_data.institute_tier,
            cgpa=student_data.cgpa,
            cgpa_scale=student_data.cgpa_scale,
            year_of_grad=student_data.year_of_grad,
            internship_count=student_data.internship_count,
            internship_months=student_data.internship_months,
            internship_employer_type=student_data.internship_employer_type,
            certifications=student_data.certifications,
            region=student_data.region,
            loan_amount=student_data.loan_amount,
            loan_emi=student_data.loan_emi
        )
        
        db.add(student)
        await db.flush()  # Flush to get the generated ID
        await db.refresh(student)  # Refresh to load all fields
        
        return student
    
    async def _create_prediction_record(
        self,
        student_id: UUID,
        model_version: str,
        placement_pred,
        salary_pred,
        risk_score: int,
        risk_level: str,
        emi_affordability: Optional[float],
        shap_values: Dict[str, float],
        top_risk_drivers: list,
        ai_summary: str,
        next_best_actions: list,
        alert_triggered: bool,
        db: AsyncSession
    ) -> Prediction:
        """
        Create a new prediction record in the database.
        
        Args:
            student_id: Student UUID
            model_version: ML model version string
            placement_pred: PlacementPrediction object
            salary_pred: SalaryPrediction object
            risk_score: Computed risk score
            risk_level: Assigned risk level
            emi_affordability: EMI affordability ratio
            shap_values: Complete SHAP values dictionary
            top_risk_drivers: Top 5 risk drivers
            ai_summary: LLM-generated summary
            next_best_actions: Recommended actions
            alert_triggered: Whether alert was triggered
            db: Database session
            
        Returns:
            Created Prediction ORM object
            
        Requirement 8.4: Store complete prediction in predictions table
        """
        prediction = Prediction(
            student_id=student_id,
            model_version=model_version,
            prob_placed_3m=Decimal(str(placement_pred.prob_3m)),
            prob_placed_6m=Decimal(str(placement_pred.prob_6m)),
            prob_placed_12m=Decimal(str(placement_pred.prob_12m)),
            placement_label=placement_pred.label,
            risk_score=risk_score,
            risk_level=risk_level,
            salary_min=Decimal(str(salary_pred.salary_min)) if salary_pred.salary_min else None,
            salary_max=Decimal(str(salary_pred.salary_max)) if salary_pred.salary_max else None,
            salary_confidence=Decimal(str(salary_pred.confidence)) if salary_pred.confidence else None,
            emi_affordability=Decimal(str(emi_affordability)) if emi_affordability else None,
            shap_values=shap_values,
            top_risk_drivers=top_risk_drivers,
            ai_summary=ai_summary,
            next_best_actions=next_best_actions,
            alert_triggered=alert_triggered
        )
        
        db.add(prediction)
        await db.flush()
        await db.refresh(prediction)
        
        return prediction
    
    def _student_to_dict(self, student_data: StudentInput) -> Dict[str, Any]:
        """
        Convert StudentInput to dictionary for feature engineering.
        
        Args:
            student_data: Validated student input
            
        Returns:
            Dictionary with student data
        """
        return {
            "name": student_data.name,
            "course_type": student_data.course_type,
            "institute_name": student_data.institute_name,
            "institute_tier": student_data.institute_tier,
            "cgpa": float(student_data.cgpa) if student_data.cgpa else 0.0,
            "cgpa_scale": float(student_data.cgpa_scale),
            "year_of_grad": student_data.year_of_grad,
            "internship_count": student_data.internship_count,
            "internship_months": student_data.internship_months,
            "internship_employer_type": student_data.internship_employer_type,
            "certifications": student_data.certifications,
            "region": student_data.region,
            "loan_amount": float(student_data.loan_amount) if student_data.loan_amount else 0.0,
            "loan_emi": float(student_data.loan_emi) if student_data.loan_emi else 0.0
        }
    
    async def _generate_ai_summary(
        self,
        student_dict: Dict[str, Any],
        placement_pred,
        risk_score: int,
        risk_level: str,
        top_risk_drivers: list
    ) -> str:
        """
        Generate AI-powered risk summary using LLM service.
        
        Args:
            student_dict: Student data dictionary
            placement_pred: PlacementPrediction object
            risk_score: Computed risk score
            risk_level: Assigned risk level
            top_risk_drivers: Top 5 risk drivers
            
        Returns:
            Natural language summary or fallback message
            
        Requirement 8.3: Invoke LLM_Summarizer
        """
        student_data_for_llm = {
            "course_type": student_dict["course_type"],
            "institute_tier": student_dict["institute_tier"],
            "cgpa": student_dict["cgpa"],
            "internship_count": student_dict["internship_count"]
        }
        
        prediction_data_for_llm = {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "prob_placed_3m": placement_pred.prob_3m,
            "prob_placed_6m": placement_pred.prob_6m,
            "prob_placed_12m": placement_pred.prob_12m
        }
        
        return await self.llm_service.generate_summary(
            student_data_for_llm,
            prediction_data_for_llm,
            top_risk_drivers
        )
    
    def _generate_actions(
        self,
        risk_level: str,
        risk_score: int,
        top_risk_drivers: list,
        student_dict: Dict[str, Any],
        placement_pred
    ) -> list:
        """
        Generate next-best action recommendations.
        
        Args:
            risk_level: Assigned risk level
            risk_score: Computed risk score
            top_risk_drivers: Top 5 risk drivers
            student_dict: Student data dictionary
            placement_pred: PlacementPrediction object
            
        Returns:
            List of action dictionaries
            
        Requirement 8.3: Invoke Action_Recommender
        """
        placement_probs = {
            "prob_3m": placement_pred.prob_3m,
            "prob_6m": placement_pred.prob_6m,
            "prob_12m": placement_pred.prob_12m
        }
        
        return generate_actions(
            risk_level=risk_level,
            risk_score=risk_score,
            shap_drivers=top_risk_drivers,
            student_data=student_dict,
            placement_probs=placement_probs
        )
    
    def _build_response(
        self,
        student_id: UUID,
        prediction_id: UUID,
        placement_pred,
        salary_pred,
        risk_score: int,
        risk_level: str,
        emi_affordability: Optional[float],
        top_risk_drivers: list,
        ai_summary: str,
        next_best_actions: list,
        alert_triggered: bool
    ) -> PredictionResponse:
        """
        Build the complete prediction response.
        
        Args:
            student_id: Student UUID
            prediction_id: Prediction UUID
            placement_pred: PlacementPrediction object
            salary_pred: SalaryPrediction object
            risk_score: Computed risk score
            risk_level: Assigned risk level
            emi_affordability: EMI affordability ratio
            top_risk_drivers: Top 5 risk drivers
            ai_summary: LLM-generated summary
            next_best_actions: Recommended actions
            alert_triggered: Whether alert was triggered
            
        Returns:
            PredictionResponse object
            
        Requirement 8.5: Return JSON response with all fields
        """
        # Convert top_risk_drivers to RiskDriver objects
        risk_drivers = [
            RiskDriver(
                feature=driver["feature"],
                value=driver["value"],
                direction=driver["direction"]
            )
            for driver in top_risk_drivers
        ]
        
        # Convert next_best_actions to NextBestAction objects
        actions = [
            NextBestAction(
                type=action["type"],
                title=action["title"],
                description=action["description"],
                priority=action["priority"]
            )
            for action in next_best_actions
        ]
        
        return PredictionResponse(
            student_id=student_id,
            prediction_id=prediction_id,
            prob_placed_3m=Decimal(str(placement_pred.prob_3m)),
            prob_placed_6m=Decimal(str(placement_pred.prob_6m)),
            prob_placed_12m=Decimal(str(placement_pred.prob_12m)),
            placement_label=placement_pred.label,
            risk_score=risk_score,
            risk_level=risk_level,
            salary_min=Decimal(str(salary_pred.salary_min)) if salary_pred.salary_min else None,
            salary_max=Decimal(str(salary_pred.salary_max)) if salary_pred.salary_max else None,
            salary_confidence=Decimal(str(salary_pred.confidence)) if salary_pred.confidence else None,
            emi_affordability=Decimal(str(emi_affordability)) if emi_affordability else None,
            top_risk_drivers=risk_drivers,
            ai_summary=ai_summary,
            next_best_actions=actions,
            alert_triggered=alert_triggered
        )
