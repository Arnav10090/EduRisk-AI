"""
Unit tests for SHAP Explainability Module

Feature: edurisk-ai-placement-intelligence
Tests for Requirements: 5.1, 5.2, 5.3, 5.5
"""

import pytest
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.explain import ShapExplainer, ShapExplanation
from pipeline.predict import PlacementPredictor


def test_shap_explainer_initialization():
    """Test that ShapExplainer initializes with a model."""
    model_dir = Path(__file__).parent.parent / 'models'
    
    if not model_dir.exists():
        pytest.skip("Model directory not found - run training first")
    
    try:
        predictor = PlacementPredictor(model_dir)
        explainer = ShapExplainer(predictor.model_3m)
        
        assert explainer.model is not None
        assert explainer.explainer is not None
    except FileNotFoundError:
        pytest.skip("Models not found - run training first")


def test_shap_values_completeness():
    """
    Test that SHAP values are computed for all features.
    
    Requirement 5.1: Compute SHAP values for all input features
    """
    model_dir = Path(__file__).parent.parent / 'models'
    
    if not model_dir.exists():
        pytest.skip("Model directory not found - run training first")
    
    try:
        predictor = PlacementPredictor(model_dir)
        explainer = ShapExplainer(predictor.model_3m)
        
        # Create dummy feature vector (16 features)
        features = np.random.rand(1, 16)
        feature_names = [
            "cgpa_normalized", "internship_score", "employer_type_score",
            "certifications", "institute_tier_1", "institute_tier_2",
            "institute_tier_3", "course_type_encoded", "placement_rate_3m",
            "placement_rate_6m", "salary_benchmark", "job_demand_score",
            "region_job_density", "macro_hiring_index", "skill_gap_score",
            "emi_stress_ratio"
        ]
        
        explanation = explainer.explain(features, feature_names)
        
        # Verify all features have SHAP values
        assert len(explanation.shap_values) == 16
        for feature_name in feature_names:
            assert feature_name in explanation.shap_values
            assert isinstance(explanation.shap_values[feature_name], float)
        
    except FileNotFoundError:
        pytest.skip("Models not found - run training first")


def test_top_drivers_selection():
    """
    Test that top 5 risk drivers are selected correctly.
    
    Requirements:
        - 5.3: Identify top 5 risk drivers by absolute SHAP value
        - 5.5: Store with feature name, SHAP value, and direction
    """
    model_dir = Path(__file__).parent.parent / 'models'
    
    if not model_dir.exists():
        pytest.skip("Model directory not found - run training first")
    
    try:
        predictor = PlacementPredictor(model_dir)
        explainer = ShapExplainer(predictor.model_3m)
        
        # Create dummy feature vector
        features = np.random.rand(1, 16)
        feature_names = [
            "cgpa_normalized", "internship_score", "employer_type_score",
            "certifications", "institute_tier_1", "institute_tier_2",
            "institute_tier_3", "course_type_encoded", "placement_rate_3m",
            "placement_rate_6m", "salary_benchmark", "job_demand_score",
            "region_job_density", "macro_hiring_index", "skill_gap_score",
            "emi_stress_ratio"
        ]
        
        explanation = explainer.explain(features, feature_names)
        
        # Verify top drivers structure
        assert len(explanation.top_drivers) == 5
        
        for driver in explanation.top_drivers:
            assert "feature" in driver
            assert "value" in driver
            assert "direction" in driver
            assert driver["direction"] in ["positive", "negative"]
            assert isinstance(driver["value"], float)
        
        # Verify drivers are sorted by absolute value
        abs_values = [abs(driver["value"]) for driver in explanation.top_drivers]
        assert abs_values == sorted(abs_values, reverse=True)
        
    except FileNotFoundError:
        pytest.skip("Models not found - run training first")


def test_shap_direction_assignment():
    """
    Test that SHAP value direction is correctly assigned.
    
    Requirement 5.5: Store direction (positive/negative)
    """
    model_dir = Path(__file__).parent.parent / 'models'
    
    if not model_dir.exists():
        pytest.skip("Model directory not found - run training first")
    
    try:
        predictor = PlacementPredictor(model_dir)
        explainer = ShapExplainer(predictor.model_3m)
        
        # Test with mock SHAP values
        shap_values = {
            "feature_a": 0.5,
            "feature_b": -0.3,
            "feature_c": 0.2,
            "feature_d": -0.1,
            "feature_e": 0.4,
            "feature_f": 0.05
        }
        
        top_drivers = explainer.select_top_drivers(shap_values)
        
        # Verify direction matches sign
        for driver in top_drivers:
            if driver["value"] > 0:
                assert driver["direction"] == "positive"
            else:
                assert driver["direction"] == "negative"
        
    except FileNotFoundError:
        pytest.skip("Models not found - run training first")


def test_base_value_included():
    """
    Test that base_value is included in explanation.
    
    Requirement 5.5: Include base_value in explanation output
    """
    model_dir = Path(__file__).parent.parent / 'models'
    
    if not model_dir.exists():
        pytest.skip("Model directory not found - run training first")
    
    try:
        predictor = PlacementPredictor(model_dir)
        explainer = ShapExplainer(predictor.model_3m)
        
        features = np.random.rand(1, 16)
        feature_names = [
            "cgpa_normalized", "internship_score", "employer_type_score",
            "certifications", "institute_tier_1", "institute_tier_2",
            "institute_tier_3", "course_type_encoded", "placement_rate_3m",
            "placement_rate_6m", "salary_benchmark", "job_demand_score",
            "region_job_density", "macro_hiring_index", "skill_gap_score",
            "emi_stress_ratio"
        ]
        
        explanation = explainer.explain(features, feature_names)
        
        # Verify base_value exists and is a float
        assert hasattr(explanation, 'base_value')
        assert isinstance(explanation.base_value, float)
        
        # Verify prediction is base_value + sum of SHAP values
        expected_prediction = explanation.base_value + sum(explanation.shap_values.values())
        assert abs(explanation.prediction - expected_prediction) < 1e-6
        
    except FileNotFoundError:
        pytest.skip("Models not found - run training first")


def test_feature_name_mismatch_raises_error():
    """Test that mismatched feature names raise ValueError."""
    model_dir = Path(__file__).parent.parent / 'models'
    
    if not model_dir.exists():
        pytest.skip("Model directory not found - run training first")
    
    try:
        predictor = PlacementPredictor(model_dir)
        explainer = ShapExplainer(predictor.model_3m)
        
        features = np.random.rand(1, 16)
        # Provide wrong number of feature names
        feature_names = ["feature_1", "feature_2"]
        
        with pytest.raises(ValueError, match="Feature names length"):
            explainer.explain(features, feature_names)
        
    except FileNotFoundError:
        pytest.skip("Models not found - run training first")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
