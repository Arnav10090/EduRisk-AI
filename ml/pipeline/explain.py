"""
SHAP Explainability Module for EduRisk AI

This module generates feature attributions using SHAP TreeExplainer to explain
placement prediction model outputs.

Feature: edurisk-ai-placement-intelligence
Requirements: 5.1, 5.2, 5.3, 5.5
"""

from typing import Dict, List, Any
import numpy as np
import shap
from dataclasses import dataclass


@dataclass
class ShapExplanation:
    """
    Container for SHAP explanation results.
    
    Attributes:
        shap_values: Dictionary mapping feature names to SHAP values
        base_value: Model baseline prediction on training data
        prediction: Final prediction (base_value + sum of SHAP values)
        top_drivers: List of top 5 risk drivers with feature, value, direction
    """
    shap_values: Dict[str, float]
    base_value: float
    prediction: float
    top_drivers: List[Dict[str, Any]]


class ShapExplainer:
    """
    Generates feature attributions using SHAP TreeExplainer.
    
    This class computes SHAP values for XGBoost model predictions to provide
    transparent, auditable explanations of which features drive risk scores.
    
    Requirements:
        - 5.1: Compute SHAP values for all input features
        - 5.2: Use TreeExplainer for exact SHAP values
        - 5.3: Identify top 5 risk drivers by absolute SHAP value
        - 5.5: Store top_risk_drivers with feature name, value, direction
    """
    
    def __init__(self, model):
        """
        Initialize TreeExplainer for the given XGBoost model.
        
        Args:
            model: Trained XGBoost classifier
            
        Requirement 5.2: Use TreeExplainer for XGBoost models
        """
        self.model = model
        # TreeExplainer provides exact SHAP values for tree-based models
        self.explainer = shap.TreeExplainer(model)
    
    def explain(self, features: np.ndarray, feature_names: List[str]) -> ShapExplanation:
        """
        Compute SHAP values for prediction.
        
        Args:
            features: Feature vector, shape (1, n_features)
            feature_names: Ordered list of feature names matching feature vector
            
        Returns:
            ShapExplanation with SHAP values dict, base_value, and top_drivers
            
        Raises:
            ValueError: If feature_names length doesn't match features shape
            
        Requirements:
            - 5.1: Compute SHAP values for all input features
            - 5.3: Identify top 5 risk drivers
            - 5.5: Include base_value in explanation output
        """
        # Validate inputs
        if len(feature_names) != features.shape[1]:
            raise ValueError(
                f"Feature names length ({len(feature_names)}) must match "
                f"features shape ({features.shape[1]})"
            )
        
        # Compute SHAP values (Requirement 5.1)
        # shap_values returns array of shape (1, n_features) for binary classification
        shap_values_array = self.explainer.shap_values(features)
        
        # Get base value (model baseline prediction on training data)
        # Requirement 5.5: Include base_value in explanation output
        base_value = float(self.explainer.expected_value)
        
        # Convert SHAP values array to dictionary (Requirement 5.1)
        # For binary classification, shap_values is shape (1, n_features)
        shap_values_dict = {}
        for i, feature_name in enumerate(feature_names):
            shap_values_dict[feature_name] = float(shap_values_array[0, i])
        
        # Calculate final prediction (base_value + sum of SHAP values)
        prediction = base_value + sum(shap_values_dict.values())
        
        # Select top 5 risk drivers (Requirement 5.3)
        top_drivers = self.select_top_drivers(shap_values_dict)
        
        return ShapExplanation(
            shap_values=shap_values_dict,
            base_value=base_value,
            prediction=prediction,
            top_drivers=top_drivers
        )
    
    def select_top_drivers(self, shap_values: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Select top 5 risk drivers by sorting features by absolute SHAP value.
        
        Args:
            shap_values: Dictionary mapping feature names to SHAP values
            
        Returns:
            List of top 5 drivers, each with:
                - feature: Feature name
                - value: SHAP value
                - direction: "positive" or "negative"
                
        Requirements:
            - 5.3: Identify top 5 risk drivers by absolute SHAP value
            - 5.5: Store with feature name, SHAP value, and direction
        """
        # Sort features by absolute SHAP value in descending order
        sorted_features = sorted(
            shap_values.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        # Take top 5 (Requirement 5.3)
        top_5 = sorted_features[:5]
        
        # Format as list of dictionaries (Requirement 5.5)
        top_drivers = []
        for feature_name, shap_value in top_5:
            top_drivers.append({
                "feature": feature_name,
                "value": float(shap_value),
                "direction": "positive" if shap_value > 0 else "negative"
            })
        
        return top_drivers
