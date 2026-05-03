"""
Response schemas for prediction API endpoints.

Implements Pydantic v2 schemas for prediction responses, batch scoring,
and SHAP explanations.

Validates Requirements: 8.5, 9.5, 10.3
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class RiskDriver(BaseModel):
    """
    Nested model representing a single risk driver from SHAP analysis.
    
    Contains feature name, SHAP value, and direction of contribution.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "feature": "internship_score",
                "value": 0.34,
                "direction": "positive"
            }
        }
    )
    
    feature: str = Field(
        ...,
        description="Feature name from the ML model"
    )
    
    value: float = Field(
        ...,
        description="SHAP value indicating feature contribution to prediction"
    )
    
    direction: str = Field(
        ...,
        pattern="^(positive|negative)$",
        description="Direction of contribution: 'positive' or 'negative'"
    )


class NextBestAction(BaseModel):
    """
    Nested model representing a recommended intervention action.
    
    Contains action type, title, description, and priority level.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "skill_up",
                "title": "Skill-Up Recommendation",
                "description": "Enroll in Engineering-specific certification courses to improve job market readiness",
                "priority": "high"
            }
        }
    )
    
    type: str = Field(
        ...,
        description="Action type (skill_up, internship, resume, mock_interview, recruiter_match)"
    )
    
    title: str = Field(
        ...,
        description="Short title for the recommended action"
    )
    
    description: str = Field(
        ...,
        description="Detailed description of the recommended action"
    )
    
    priority: str = Field(
        ...,
        pattern="^(low|medium|high)$",
        description="Priority level: 'low', 'medium', or 'high'"
    )


class PredictionResponse(BaseModel):
    """
    Complete prediction response for a single student.
    
    Contains all placement probabilities, risk scores, salary estimates,
    SHAP explanations, AI summary, and recommended actions.
    
    Validates Requirement: 8.5
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "550e8400-e29b-41d4-a716-446655440000",
                "prediction_id": "660e8400-e29b-41d4-a716-446655440001",
                "prob_placed_3m": 0.7845,
                "prob_placed_6m": 0.8923,
                "prob_placed_12m": 0.9456,
                "placement_label": "placed_3m",
                "risk_score": 25,
                "risk_level": "low",
                "salary_min": 6.50,
                "salary_max": 9.50,
                "salary_confidence": 37.50,
                "emi_affordability": 0.35,
                "top_risk_drivers": [
                    {
                        "feature": "internship_score",
                        "value": 0.34,
                        "direction": "positive"
                    },
                    {
                        "feature": "institute_tier_1",
                        "value": 0.22,
                        "direction": "positive"
                    }
                ],
                "ai_summary": "Low risk student with strong internship experience and tier-1 institute background. Placement within 3 months is highly probable.",
                "next_best_actions": [
                    {
                        "type": "recruiter_match",
                        "title": "Recruiter Matches Available",
                        "description": "3 active recruiters hiring Engineering graduates",
                        "priority": "low"
                    }
                ],
                "alert_triggered": False
            }
        }
    )
    
    # Identifiers
    student_id: UUID = Field(
        ...,
        description="Unique identifier for the student"
    )

    name: str = Field(
        ...,
        description="Student full name"
    )
    
    prediction_id: UUID = Field(
        ...,
        description="Unique identifier for this prediction record"
    )
    
    # Placement probabilities
    prob_placed_3m: Decimal = Field(
        ...,
        ge=0,
        le=1,
        description="Probability of placement within 3 months (0.0000 to 1.0000)"
    )
    
    prob_placed_6m: Decimal = Field(
        ...,
        ge=0,
        le=1,
        description="Probability of placement within 6 months (0.0000 to 1.0000)"
    )
    
    prob_placed_12m: Decimal = Field(
        ...,
        ge=0,
        le=1,
        description="Probability of placement within 12 months (0.0000 to 1.0000)"
    )
    
    placement_label: str = Field(
        ...,
        description="Predicted placement timeline: 'placed_3m', 'placed_6m', 'placed_12m', or 'high_risk'"
    )
    
    # Risk assessment
    risk_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Composite risk score from 0 (lowest risk) to 100 (highest risk)"
    )
    
    risk_level: str = Field(
        ...,
        pattern="^(low|medium|high)$",
        description="Risk level classification: 'low', 'medium', or 'high'"
    )
    
    # Salary estimates
    salary_min: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Minimum predicted salary in LPA (Lakhs Per Annum)"
    )
    
    salary_max: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Maximum predicted salary in LPA (Lakhs Per Annum)"
    )
    
    salary_confidence: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Salary prediction confidence as percentage"
    )
    
    # EMI affordability
    emi_affordability: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Ratio of monthly EMI to predicted monthly salary"
    )
    
    # Explainability
    top_risk_drivers: List[RiskDriver] = Field(
        ...,
        description="Top 5 features driving the risk prediction (from SHAP analysis)"
    )
    
    ai_summary: str = Field(
        ...,
        description="Natural language summary of risk assessment generated by LLM"
    )
    
    # Recommendations
    next_best_actions: List[NextBestAction] = Field(
        ...,
        description="Recommended interventions to improve student outcomes"
    )
    
    # Alert status
    alert_triggered: bool = Field(
        ...,
        description="Whether this prediction triggered a high-risk alert"
    )


class BatchScoreResponse(BaseModel):
    """
    Response for batch scoring of multiple students.
    
    Contains array of individual prediction results and aggregate summary statistics.
    
    Validates Requirement: 9.5
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "results": [
                    {
                        "student_id": "550e8400-e29b-41d4-a716-446655440000",
                        "prediction_id": "660e8400-e29b-41d4-a716-446655440001",
                        "prob_placed_3m": 0.7845,
                        "prob_placed_6m": 0.8923,
                        "prob_placed_12m": 0.9456,
                        "placement_label": "placed_3m",
                        "risk_score": 25,
                        "risk_level": "low",
                        "salary_min": 6.50,
                        "salary_max": 9.50,
                        "salary_confidence": 37.50,
                        "emi_affordability": 0.35,
                        "top_risk_drivers": [],
                        "ai_summary": "Low risk student",
                        "next_best_actions": [],
                        "alert_triggered": False
                    }
                ],
                "summary": {
                    "high_risk_count": 12,
                    "medium_risk_count": 45,
                    "low_risk_count": 143
                }
            }
        }
    )
    
    results: List[PredictionResponse] = Field(
        ...,
        description="Array of prediction results for each student in the batch"
    )
    
    summary: Dict[str, int] = Field(
        ...,
        description="Aggregate statistics: high_risk_count, medium_risk_count, low_risk_count"
    )


class ShapExplanationResponse(BaseModel):
    """
    Detailed SHAP explanation for a student's prediction.
    
    Contains complete SHAP values dictionary, base value, prediction probability,
    and waterfall data for visualization.
    
    Validates Requirement: 10.3
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "550e8400-e29b-41d4-a716-446655440000",
                "shap_values": {
                    "internship_score": 0.34,
                    "institute_tier_1": 0.22,
                    "cgpa_normalized": 0.11,
                    "job_demand_score": -0.09,
                    "course_type_encoded": -0.17
                },
                "base_value": 0.45,
                "prediction": 0.78,
                "waterfall_data": [
                    {
                        "feature": "base_value",
                        "value": 0.45,
                        "cumulative": 0.45
                    },
                    {
                        "feature": "internship_score",
                        "value": 0.34,
                        "cumulative": 0.79
                    },
                    {
                        "feature": "institute_tier_1",
                        "value": 0.22,
                        "cumulative": 1.01
                    }
                ]
            }
        }
    )
    
    student_id: UUID = Field(
        ...,
        description="Unique identifier for the student"
    )
    
    shap_values: Dict[str, float] = Field(
        ...,
        description="Dictionary mapping feature names to their SHAP values"
    )
    
    base_value: float = Field(
        ...,
        description="Model baseline prediction value on training data"
    )
    
    prediction: float = Field(
        ...,
        ge=0,
        le=1,
        description="Final prediction probability (base_value + sum of SHAP values)"
    )
    
    waterfall_data: List[Dict[str, Any]] = Field(
        ...,
        description="Array of objects for waterfall visualization with feature, value, and cumulative fields"
    )
