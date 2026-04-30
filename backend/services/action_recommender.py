"""
Action recommendation engine for EduRisk AI.

This module provides rule-based logic to generate personalized intervention
recommendations (Next-Best Actions) to help students improve their placement
prospects based on their risk profile and SHAP feature attributions.
"""

from typing import List, Dict, Any, Optional


def generate_actions(
    risk_level: str,
    risk_score: int,
    shap_drivers: List[Dict[str, Any]],
    student_data: Dict[str, Any],
    placement_probs: Dict[str, float],
    internship_score: Optional[float] = None
) -> List[Dict[str, str]]:
    """
    Generate personalized next-best action recommendations based on risk profile.
    
    This function applies a rule-based engine to identify actionable interventions
    that can help improve a student's placement prospects. Rules are triggered
    based on risk indicators, SHAP feature attributions, and student profile data.
    
    Args:
        risk_level: Categorical risk level ("low", "medium", or "high")
        risk_score: Numeric risk score from 0 to 100
        shap_drivers: List of top SHAP risk drivers, each containing:
            - feature: Feature name
            - value: SHAP value (contribution to prediction)
            - direction: "positive" or "negative"
        student_data: Dictionary containing student profile fields:
            - course_type: Course type (e.g., "Engineering", "MBA")
            - institute_tier: Institute tier (1, 2, or 3)
            - internship_count: Number of internships
            - internship_months: Total months of internship experience
            - internship_employer_type: Type of employer
        placement_probs: Dictionary with placement probabilities:
            - prob_3m: 3-month placement probability
            - prob_6m: 6-month placement probability
            - prob_12m: 12-month placement probability
        internship_score: Pre-computed internship score (optional, will be
            calculated if not provided)
    
    Returns:
        List of action dictionaries, each containing:
            - type: Action type identifier
            - title: Short action title
            - description: Detailed action description
            - priority: Priority level ("high", "medium", or "low")
    
    Requirements:
        - 7.1: Generate list of Next_Best_Action recommendations
        - 7.2: Recommend "skill_up" when job_demand_score in bottom 3 SHAP features
        - 7.3: Recommend "internship" when count=0 or score<0.3 (high priority)
        - 7.4: Recommend "resume" when risk_score>60
        - 7.5: Recommend "mock_interview" when prob_3m<0.5 (high priority)
        - 7.6: Recommend "recruiter_match" when risk_level low/medium and tier<=2 (low priority)
        - 7.7: Store recommendations as JSONB array with type, title, description, priority
    
    Examples:
        >>> shap_drivers = [
        ...     {"feature": "cgpa_normalized", "value": -0.25, "direction": "negative"},
        ...     {"feature": "job_demand_score", "value": -0.18, "direction": "negative"},
        ...     {"feature": "internship_score", "value": -0.15, "direction": "negative"}
        ... ]
        >>> student_data = {
        ...     "course_type": "Engineering",
        ...     "institute_tier": 2,
        ...     "internship_count": 0,
        ...     "internship_months": 0,
        ...     "internship_employer_type": None
        ... }
        >>> placement_probs = {"prob_3m": 0.35, "prob_6m": 0.55, "prob_12m": 0.70}
        >>> actions = generate_actions("high", 72, shap_drivers, student_data, placement_probs)
        >>> len(actions) >= 3
        True
        >>> any(a["type"] == "skill_up" for a in actions)
        True
        >>> any(a["type"] == "internship" for a in actions)
        True
    """
    actions = []
    
    # Extract student profile fields
    course_type = student_data.get("course_type", "")
    institute_tier = student_data.get("institute_tier", 3)
    internship_count = student_data.get("internship_count", 0)
    internship_months = student_data.get("internship_months", 0)
    internship_employer_type = student_data.get("internship_employer_type")
    
    # Calculate internship score if not provided
    if internship_score is None:
        internship_score = _compute_internship_score(
            internship_count, internship_months, internship_employer_type
        )
    
    # Extract SHAP feature names for bottom 3 analysis
    shap_feature_names = [driver["feature"] for driver in shap_drivers]
    
    # Get bottom 3 SHAP features (those with most negative contribution)
    # Sort by SHAP value ascending (most negative first)
    sorted_drivers = sorted(shap_drivers, key=lambda x: x["value"])
    bottom_3_features = [driver["feature"] for driver in sorted_drivers[:3]]
    
    # Rule 1: Skill-Up Recommendation (Requirement 7.2)
    # Trigger when job_demand_score is among bottom 3 SHAP contributors
    if "job_demand_score" in bottom_3_features:
        priority = "high" if risk_level == "high" else "medium"
        actions.append({
            "type": "skill_up",
            "title": "Skill-Up Recommendation",
            "description": (
                f"Enroll in {course_type}-specific certification courses to improve "
                f"job market alignment. Low job demand score indicates a skill gap "
                f"in your field. Consider certifications in trending technologies "
                f"relevant to {course_type} roles."
            ),
            "priority": priority
        })
    
    # Rule 2: Internship / Project Experience (Requirement 7.3)
    # Trigger when internship_count is zero OR internship_score is below 0.3
    if internship_count == 0 or internship_score < 0.3:
        actions.append({
            "type": "internship",
            "title": "Internship / Project Experience",
            "description": (
                "Complete at least 1 industry internship or substantial project work. "
                f"Current internship experience ({internship_count} internships, "
                f"{internship_months} months) is below market expectations. "
                "Hands-on experience significantly improves placement prospects."
            ),
            "priority": "high"
        })
    
    # Rule 3: Resume Improvement (Requirement 7.4)
    # Trigger when risk_score exceeds 60
    if risk_score > 60:
        actions.append({
            "type": "resume",
            "title": "Resume Improvement",
            "description": (
                "Resume review and optimization recommended. High risk score suggests "
                "your profile may not be effectively showcased. Professional resume "
                "coaching can help highlight strengths and improve recruiter response rates."
            ),
            "priority": "medium"
        })
    
    # Rule 4: Mock Interview Coaching (Requirement 7.5)
    # Trigger when prob_placed_3m is below 0.5
    prob_3m = placement_probs.get("prob_3m", 0.0)
    if prob_3m < 0.5:
        actions.append({
            "type": "mock_interview",
            "title": "Mock Interview Coaching",
            "description": (
                f"3-month placement probability is {prob_3m:.0%}, below 50% threshold. "
                "Mock interview sessions with industry professionals can significantly "
                "improve interview performance and confidence. Focus on technical and "
                "behavioral interview preparation."
            ),
            "priority": "high"
        })
    
    # Rule 5: Recruiter Match (Requirement 7.6)
    # Trigger when risk_level is "low" or "medium" AND institute_tier is 1 or 2
    if risk_level in ["low", "medium"] and institute_tier <= 2:
        actions.append({
            "type": "recruiter_match",
            "title": "Recruiter Matches Available",
            "description": (
                f"3 active recruiters are currently hiring {course_type} graduates "
                f"from Tier-{institute_tier} institutes. Your profile matches their "
                "requirements. Connect with recruiters to explore immediate placement "
                "opportunities."
            ),
            "priority": "low"
        })
    
    return actions


def _compute_internship_score(
    internship_count: int,
    internship_months: int,
    internship_employer_type: Optional[str]
) -> float:
    """
    Compute internship score using weighted formula.
    
    This is a helper function that replicates the feature engineering logic
    for internship score calculation when it's not provided directly.
    
    Formula (from Requirement 17.2):
    internship_score = (count × 0.4) + (months/24 × 0.3) + (employer_score × 0.3)
    
    Args:
        internship_count: Number of internships
        internship_months: Total months of internship experience
        internship_employer_type: Type of employer (MNC, Startup, PSU, NGO, None)
    
    Returns:
        Internship score as float
    
    Examples:
        >>> _compute_internship_score(2, 6, "MNC")
        2.075
        >>> _compute_internship_score(0, 0, None)
        0.0
        >>> _compute_internship_score(1, 3, "Startup")
        1.3375
    """
    count_component = internship_count * 0.4
    months_component = (internship_months / 24.0) * 0.3
    employer_score = _get_employer_type_score(internship_employer_type)
    employer_component = employer_score * 0.3
    
    return count_component + months_component + employer_component


def _get_employer_type_score(employer_type: Optional[str]) -> float:
    """
    Map employer type to numeric score.
    
    Mapping (from Requirement 17.3):
    - MNC: 4
    - Startup: 3
    - PSU: 2
    - NGO: 1
    - None/null: 0
    
    Args:
        employer_type: Employer type string (case-insensitive)
    
    Returns:
        Numeric score for employer type
    
    Examples:
        >>> _get_employer_type_score("MNC")
        4.0
        >>> _get_employer_type_score("startup")
        3.0
        >>> _get_employer_type_score(None)
        0.0
        >>> _get_employer_type_score("Unknown")
        0.0
    """
    if employer_type is None:
        return 0.0
    
    employer_type_upper = employer_type.upper()
    
    employer_scores = {
        "MNC": 4.0,
        "STARTUP": 3.0,
        "PSU": 2.0,
        "NGO": 1.0
    }
    
    return employer_scores.get(employer_type_upper, 0.0)
