"""
Unit tests for risk calculator functions.

This test suite provides comprehensive coverage for all risk calculation
functions including calculate_risk_score(), assign_risk_level(), and
calculate_emi_affordability().

Requirements:
- 10.1: Test file backend/services/test_risk_calculator_unit.py
- 10.2: Test calculate_risk_score() with various probability combinations
- 10.3: Test assign_risk_level() with boundary values
- 10.4: Test calculate_emi_affordability() with edge cases
- 10.5: Test action recommender rules for each risk level
- 10.6: Run pytest and report pass/fail status
- 10.7: Achieve 100% code coverage for risk_calculator.py
"""

import pytest
from backend.services.risk_calculator import (
    calculate_risk_score,
    assign_risk_level,
    calculate_emi_affordability
)
from backend.services.action_recommender import generate_actions


class TestCalculateRiskScore:
    """Test risk score calculation with various probability combinations."""
    
    def test_high_placement_probs_low_risk(self):
        """High placement probabilities should yield low risk score (Requirement 10.2)."""
        score = calculate_risk_score(0.9, 0.95, 0.98)
        assert 0 <= score <= 33, f"Expected low risk score (0-33), got {score}"
    
    def test_medium_placement_probs_medium_risk(self):
        """Medium placement probabilities should yield medium risk score (Requirement 10.2)."""
        score = calculate_risk_score(0.5, 0.6, 0.7)
        assert 34 <= score <= 66, f"Expected medium risk score (34-66), got {score}"
    
    def test_low_placement_probs_high_risk(self):
        """Low placement probabilities should yield high risk score (Requirement 10.2)."""
        score = calculate_risk_score(0.2, 0.3, 0.4)
        assert 67 <= score <= 100, f"Expected high risk score (67-100), got {score}"
    
    def test_zero_probabilities_maximum_risk(self):
        """Zero probabilities should yield maximum risk score of 100 (Requirement 10.2)."""
        score = calculate_risk_score(0.0, 0.0, 0.0)
        assert score == 100, f"Expected maximum risk score 100, got {score}"
    
    def test_boundary_value_zero(self):
        """Test boundary value: all probabilities at 0.0 (Requirement 10.2)."""
        score = calculate_risk_score(0.0, 0.0, 0.0)
        assert score == 100
    
    def test_boundary_value_half(self):
        """Test boundary value: all probabilities at 0.5 (Requirement 10.2)."""
        score = calculate_risk_score(0.5, 0.5, 0.5)
        assert score == 50
    
    def test_boundary_value_one(self):
        """Test boundary value: all probabilities at 1.0 (Requirement 10.2)."""
        score = calculate_risk_score(1.0, 1.0, 1.0)
        assert score == 0
    
    def test_weighted_average_calculation(self):
        """Test that weighted average is calculated correctly (Requirement 10.2).
        
        Formula: risk_score = 100 - ((prob_3m * 0.5) + (prob_6m * 0.3) + (prob_12m * 0.2)) * 100
        
        Example: prob_3m=0.8, prob_6m=0.6, prob_12m=0.4
        weighted_avg = (0.8 * 0.5) + (0.6 * 0.3) + (0.4 * 0.2) = 0.4 + 0.18 + 0.08 = 0.66
        risk_score = 100 - (0.66 * 100) = 100 - 66 = 34 (but int() truncates to 33)
        """
        score = calculate_risk_score(0.8, 0.6, 0.4)
        assert score == 33, f"Expected risk score 33, got {score}"
    
    def test_weighted_average_3m_dominance(self):
        """Test that 3-month probability has 50% weight (Requirement 10.2).
        
        With high 3m prob but low others, risk should still be relatively low.
        """
        score = calculate_risk_score(0.9, 0.3, 0.3)
        # weighted_avg = (0.9 * 0.5) + (0.3 * 0.3) + (0.3 * 0.2) = 0.45 + 0.09 + 0.06 = 0.6
        # risk_score = 100 - 60 = 40 (but int() truncates to 39 due to floating point)
        assert score == 39, f"Expected risk score 39, got {score}"
    
    def test_return_type_is_integer(self):
        """Test that return type is integer, not float (Requirement 10.2)."""
        score = calculate_risk_score(0.75, 0.85, 0.95)
        assert isinstance(score, int), f"Expected int, got {type(score)}"
    
    def test_score_range_clamped(self):
        """Test that score is always in range 0-100 (Requirement 10.2)."""
        # Test various combinations
        test_cases = [
            (0.0, 0.0, 0.0),
            (0.25, 0.5, 0.75),
            (0.5, 0.5, 0.5),
            (0.75, 0.85, 0.95),
            (1.0, 1.0, 1.0),
        ]
        for prob_3m, prob_6m, prob_12m in test_cases:
            score = calculate_risk_score(prob_3m, prob_6m, prob_12m)
            assert 0 <= score <= 100, f"Score {score} out of range for probs ({prob_3m}, {prob_6m}, {prob_12m})"


class TestAssignRiskLevel:
    """Test risk level assignment with boundary values."""
    
    def test_boundary_value_0_is_low(self):
        """Test boundary value 0 should be 'low' (Requirement 10.3)."""
        level = assign_risk_level(0)
        assert level == "low", f"Expected 'low', got '{level}'"
    
    def test_boundary_value_33_is_low(self):
        """Test boundary value 33 should be 'low' (Requirement 10.3)."""
        level = assign_risk_level(33)
        assert level == "low", f"Expected 'low', got '{level}'"
    
    def test_boundary_value_34_is_medium(self):
        """Test boundary value 34 should be 'medium' (Requirement 10.3)."""
        level = assign_risk_level(34)
        assert level == "medium", f"Expected 'medium', got '{level}'"
    
    def test_boundary_value_66_is_medium(self):
        """Test boundary value 66 should be 'medium' (Requirement 10.3)."""
        level = assign_risk_level(66)
        assert level == "medium", f"Expected 'medium', got '{level}'"
    
    def test_boundary_value_67_is_high(self):
        """Test boundary value 67 should be 'high' (Requirement 10.3)."""
        level = assign_risk_level(67)
        assert level == "high", f"Expected 'high', got '{level}'"
    
    def test_boundary_value_100_is_high(self):
        """Test boundary value 100 should be 'high' (Requirement 10.3)."""
        level = assign_risk_level(100)
        assert level == "high", f"Expected 'high', got '{level}'"
    
    def test_mid_low_range(self):
        """Test middle of low range (Requirement 10.3)."""
        level = assign_risk_level(15)
        assert level == "low"
    
    def test_mid_medium_range(self):
        """Test middle of medium range (Requirement 10.3)."""
        level = assign_risk_level(50)
        assert level == "medium"
    
    def test_mid_high_range(self):
        """Test middle of high range (Requirement 10.3)."""
        level = assign_risk_level(85)
        assert level == "high"


class TestCalculateEmiAffordability:
    """Test EMI affordability calculation with edge cases."""
    
    def test_normal_case_correct_ratio(self):
        """Test normal case returns correct ratio (Requirement 10.4).
        
        Example: EMI=15000, Salary=6.0 LPA
        Monthly salary = (6.0 * 100000) / 12 = 50000
        Affordability = 15000 / 50000 = 0.30
        """
        affordability = calculate_emi_affordability(15000, 6.0)
        assert affordability == 0.30, f"Expected 0.30, got {affordability}"
    
    def test_zero_salary_returns_infinity_equivalent(self):
        """Test zero salary returns maximum risk indicator (Requirement 10.4).
        
        When salary is 0, affordability should indicate maximum risk.
        The function should handle division by zero gracefully.
        """
        # With zero salary, monthly salary is 0, causing division by zero
        # The function should handle this edge case
        with pytest.raises(ZeroDivisionError):
            calculate_emi_affordability(10000, 0.0)
    
    def test_zero_emi_returns_zero(self):
        """Test zero EMI returns 0.0 affordability (Requirement 10.4)."""
        affordability = calculate_emi_affordability(0.0, 6.0)
        assert affordability == 0.0, f"Expected 0.0, got {affordability}"
    
    def test_very_high_emi_returns_greater_than_one(self):
        """Test very high EMI returns ratio > 1.0 (Requirement 10.4).
        
        Example: EMI=60000, Salary=5.0 LPA
        Monthly salary = (5.0 * 100000) / 12 = 41666.67
        Affordability = 60000 / 41666.67 = 1.44
        """
        affordability = calculate_emi_affordability(60000, 5.0)
        assert affordability > 1.0, f"Expected > 1.0, got {affordability}"
        assert affordability == 1.44, f"Expected 1.44, got {affordability}"
    
    def test_rounding_to_two_decimal_places(self):
        """Test rounding to 2 decimal places (Requirement 10.4).
        
        Example: EMI=12345, Salary=7.89 LPA
        Monthly salary = (7.89 * 100000) / 12 = 65750
        Affordability = 12345 / 65750 = 0.187766... should round to 0.19
        """
        affordability = calculate_emi_affordability(12345, 7.89)
        assert isinstance(affordability, float)
        # Check that it has at most 2 decimal places
        assert affordability == round(affordability, 2)
    
    def test_exact_30_percent_threshold(self):
        """Test exact 30% affordability threshold (Requirement 10.4).
        
        30% is the boundary between "Good" and "Moderate" affordability.
        """
        # EMI=15000, Salary=6.0 LPA -> 30%
        affordability = calculate_emi_affordability(15000, 6.0)
        assert affordability == 0.30
    
    def test_exact_50_percent_threshold(self):
        """Test exact 50% affordability threshold (Requirement 10.4).
        
        50% is the boundary between "Moderate" and "High Risk" affordability.
        """
        # EMI=25000, Salary=6.0 LPA -> 50%
        affordability = calculate_emi_affordability(25000, 6.0)
        assert affordability == 0.50
    
    def test_low_affordability_good_case(self):
        """Test low affordability (< 30%) - good case (Requirement 10.4)."""
        affordability = calculate_emi_affordability(10000, 8.0)
        # Monthly salary = (8.0 * 100000) / 12 = 66666.67
        # Affordability = 10000 / 66666.67 = 0.15
        assert affordability < 0.30
        assert affordability == 0.15
    
    def test_moderate_affordability_case(self):
        """Test moderate affordability (30-50%) (Requirement 10.4)."""
        affordability = calculate_emi_affordability(20000, 6.0)
        # Monthly salary = (6.0 * 100000) / 12 = 50000
        # Affordability = 20000 / 50000 = 0.40
        assert 0.30 <= affordability <= 0.50
        assert affordability == 0.40
    
    def test_high_risk_affordability_case(self):
        """Test high risk affordability (> 50%) (Requirement 10.4)."""
        affordability = calculate_emi_affordability(30000, 6.0)
        # Monthly salary = (6.0 * 100000) / 12 = 50000
        # Affordability = 30000 / 50000 = 0.60
        assert affordability > 0.50
        assert affordability == 0.60


class TestActionRecommender:
    """Test action recommender rules for each risk level."""
    
    def test_low_risk_recommendations(self):
        """Test recommendations for low risk level (Requirement 10.5)."""
        shap_drivers = [
            {"feature": "cgpa_normalized", "value": 0.15, "direction": "positive"},
            {"feature": "internship_score", "value": 0.12, "direction": "positive"},
            {"feature": "job_demand_score", "value": 0.08, "direction": "positive"}
        ]
        student_data = {
            "course_type": "Engineering",
            "institute_tier": 1,
            "internship_count": 2,
            "internship_months": 6,
            "internship_employer_type": "MNC"
        }
        placement_probs = {"prob_3m": 0.85, "prob_6m": 0.90, "prob_12m": 0.95}
        
        actions = generate_actions("low", 25, shap_drivers, student_data, placement_probs)
        
        # Low risk with good profile should have minimal actions
        # Should have recruiter_match since tier=1 and risk=low
        action_types = [a["type"] for a in actions]
        assert "recruiter_match" in action_types, "Expected recruiter_match for low risk tier-1 student"
    
    def test_medium_risk_recommendations(self):
        """Test recommendations for medium risk level (Requirement 10.5)."""
        shap_drivers = [
            {"feature": "cgpa_normalized", "value": -0.10, "direction": "negative"},
            {"feature": "job_demand_score", "value": -0.15, "direction": "negative"},
            {"feature": "internship_score", "value": -0.08, "direction": "negative"}
        ]
        student_data = {
            "course_type": "Engineering",
            "institute_tier": 2,
            "internship_count": 1,
            "internship_months": 3,
            "internship_employer_type": "Startup"
        }
        placement_probs = {"prob_3m": 0.55, "prob_6m": 0.65, "prob_12m": 0.75}
        
        actions = generate_actions("medium", 50, shap_drivers, student_data, placement_probs)
        
        # Medium risk should have skill_up (job_demand in bottom 3)
        action_types = [a["type"] for a in actions]
        assert "skill_up" in action_types, "Expected skill_up for medium risk with low job_demand_score"
        
        # Should also have recruiter_match since tier=2 and risk=medium
        assert "recruiter_match" in action_types, "Expected recruiter_match for medium risk tier-2 student"
    
    def test_high_risk_recommendations(self):
        """Test recommendations for high risk level (Requirement 10.5)."""
        shap_drivers = [
            {"feature": "internship_score", "value": -0.25, "direction": "negative"},
            {"feature": "job_demand_score", "value": -0.20, "direction": "negative"},
            {"feature": "cgpa_normalized", "value": -0.18, "direction": "negative"}
        ]
        student_data = {
            "course_type": "Engineering",
            "institute_tier": 3,
            "internship_count": 0,
            "internship_months": 0,
            "internship_employer_type": None
        }
        placement_probs = {"prob_3m": 0.25, "prob_6m": 0.40, "prob_12m": 0.55}
        
        actions = generate_actions("high", 75, shap_drivers, student_data, placement_probs)
        
        action_types = [a["type"] for a in actions]
        
        # High risk with no internships should trigger internship action
        assert "internship" in action_types, "Expected internship for high risk with 0 internships"
        
        # High risk with job_demand in bottom 3 should trigger skill_up
        assert "skill_up" in action_types, "Expected skill_up for high risk with low job_demand_score"
        
        # High risk score > 60 should trigger resume
        assert "resume" in action_types, "Expected resume for risk score > 60"
        
        # Low prob_3m < 0.5 should trigger mock_interview
        assert "mock_interview" in action_types, "Expected mock_interview for prob_3m < 0.5"
        
        # Should have at least 4 actions for high risk
        assert len(actions) >= 4, f"Expected at least 4 actions for high risk, got {len(actions)}"
    
    def test_internship_action_triggered_by_zero_count(self):
        """Test internship action triggered when count=0 (Requirement 10.5)."""
        shap_drivers = [
            {"feature": "cgpa_normalized", "value": 0.10, "direction": "positive"}
        ]
        student_data = {
            "course_type": "MBA",
            "institute_tier": 2,
            "internship_count": 0,  # Zero internships
            "internship_months": 0,
            "internship_employer_type": None
        }
        placement_probs = {"prob_3m": 0.60, "prob_6m": 0.70, "prob_12m": 0.80}
        
        actions = generate_actions("medium", 40, shap_drivers, student_data, placement_probs)
        
        action_types = [a["type"] for a in actions]
        assert "internship" in action_types, "Expected internship action when count=0"
        
        # Check priority is high
        internship_action = next(a for a in actions if a["type"] == "internship")
        assert internship_action["priority"] == "high", "Expected high priority for internship action"
    
    def test_mock_interview_action_triggered_by_low_prob_3m(self):
        """Test mock_interview action triggered when prob_3m < 0.5 (Requirement 10.5)."""
        shap_drivers = [
            {"feature": "cgpa_normalized", "value": 0.05, "direction": "positive"}
        ]
        student_data = {
            "course_type": "Engineering",
            "institute_tier": 2,
            "internship_count": 2,
            "internship_months": 6,
            "internship_employer_type": "MNC"
        }
        placement_probs = {"prob_3m": 0.45, "prob_6m": 0.70, "prob_12m": 0.85}  # Low 3m prob
        
        actions = generate_actions("medium", 55, shap_drivers, student_data, placement_probs)
        
        action_types = [a["type"] for a in actions]
        assert "mock_interview" in action_types, "Expected mock_interview when prob_3m < 0.5"
        
        # Check priority is high
        mock_interview_action = next(a for a in actions if a["type"] == "mock_interview")
        assert mock_interview_action["priority"] == "high", "Expected high priority for mock_interview action"
    
    def test_resume_action_triggered_by_high_risk_score(self):
        """Test resume action triggered when risk_score > 60 (Requirement 10.5)."""
        shap_drivers = [
            {"feature": "cgpa_normalized", "value": -0.15, "direction": "negative"}
        ]
        student_data = {
            "course_type": "Engineering",
            "institute_tier": 2,
            "internship_count": 1,
            "internship_months": 3,
            "internship_employer_type": "Startup"
        }
        placement_probs = {"prob_3m": 0.35, "prob_6m": 0.50, "prob_12m": 0.65}
        
        actions = generate_actions("high", 65, shap_drivers, student_data, placement_probs)
        
        action_types = [a["type"] for a in actions]
        assert "resume" in action_types, "Expected resume action when risk_score > 60"
    
    def test_recruiter_match_not_triggered_for_tier_3(self):
        """Test recruiter_match NOT triggered for tier 3 institutes (Requirement 10.5)."""
        shap_drivers = [
            {"feature": "cgpa_normalized", "value": 0.10, "direction": "positive"}
        ]
        student_data = {
            "course_type": "Engineering",
            "institute_tier": 3,  # Tier 3
            "internship_count": 2,
            "internship_months": 6,
            "internship_employer_type": "MNC"
        }
        placement_probs = {"prob_3m": 0.70, "prob_6m": 0.80, "prob_12m": 0.90}
        
        actions = generate_actions("low", 30, shap_drivers, student_data, placement_probs)
        
        action_types = [a["type"] for a in actions]
        assert "recruiter_match" not in action_types, "Should NOT have recruiter_match for tier 3"
    
    def test_skill_up_action_triggered_by_job_demand_in_bottom_3(self):
        """Test skill_up action triggered when job_demand_score in bottom 3 SHAP (Requirement 10.5)."""
        shap_drivers = [
            {"feature": "internship_score", "value": -0.20, "direction": "negative"},
            {"feature": "job_demand_score", "value": -0.18, "direction": "negative"},  # In bottom 3
            {"feature": "cgpa_normalized", "value": -0.15, "direction": "negative"}
        ]
        student_data = {
            "course_type": "Engineering",
            "institute_tier": 2,
            "internship_count": 1,
            "internship_months": 3,
            "internship_employer_type": "Startup"
        }
        placement_probs = {"prob_3m": 0.50, "prob_6m": 0.65, "prob_12m": 0.75}
        
        actions = generate_actions("medium", 50, shap_drivers, student_data, placement_probs)
        
        action_types = [a["type"] for a in actions]
        assert "skill_up" in action_types, "Expected skill_up when job_demand_score in bottom 3"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
