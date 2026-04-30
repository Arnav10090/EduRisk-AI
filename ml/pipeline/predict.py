"""
Placement Prediction Module for EduRisk AI

This module loads trained XGBoost models and generates placement probability predictions
for 3-month, 6-month, and 12-month time windows.

Feature: edurisk-ai-placement-intelligence
Requirements: 1.1, 1.2, 1.3, 1.4, 1.6
"""

from pathlib import Path
from typing import Dict, Optional
import json
import numpy as np
import joblib
from dataclasses import dataclass


@dataclass
class PlacementPrediction:
    """
    Container for placement prediction results.
    
    Attributes:
        prob_3m: Probability of placement within 3 months (0.0-1.0)
        prob_6m: Probability of placement within 6 months (0.0-1.0)
        prob_12m: Probability of placement within 12 months (0.0-1.0)
        label: Placement timeline label ("placed_3m", "placed_6m", "placed_12m", "high_risk")
    """
    prob_3m: float
    prob_6m: float
    prob_12m: float
    label: str


class PlacementPredictor:
    """
    Loads trained XGBoost models and generates placement predictions.
    
    This class manages three separate XGBoost classifiers trained for different
    time windows (3, 6, and 12 months) and assigns placement labels based on
    probability thresholds.
    
    Requirements:
        - 1.1: Generate probability scores for 3/6/12 month windows
        - 1.2: Assign placement timeline label
        - 1.3: Use three separate XGBoost classifiers
        - 1.4: Output probabilities with 4 decimal precision
        - 1.6: Assign "high_risk" when all probabilities < 0.50
    """
    
    def __init__(self, model_dir: Path):
        """
        Initialize PlacementPredictor by loading models from disk.
        
        Args:
            model_dir: Path to directory containing model files
            
        Raises:
            FileNotFoundError: If model files are not found
            Exception: If models cannot be loaded
        """
        self.model_dir = Path(model_dir)
        
        # Load the three XGBoost models (Requirement 1.3)
        self.model_3m = self._load_model('placement_model_3m.pkl')
        self.model_6m = self._load_model('placement_model_6m.pkl')
        self.model_12m = self._load_model('placement_model_12m.pkl')
        
        # Load model version
        self._version = self._load_version()
    
    def _load_model(self, filename: str):
        """
        Load a pickled model from disk.
        
        Args:
            filename: Name of the model file
            
        Returns:
            Loaded model object
            
        Raises:
            FileNotFoundError: If model file doesn't exist
        """
        model_path = self.model_dir / filename
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        try:
            model = joblib.load(model_path)
            return model
        except Exception as e:
            raise Exception(f"Failed to load model from {model_path}: {e}")
    
    def _load_version(self) -> str:
        """
        Load model version from version.json file.
        
        Returns:
            Version string (e.g., "1.0.0")
            
        Requirement 15.2: Read Model_Version from version.json
        """
        version_path = self.model_dir / 'version.json'
        
        if not version_path.exists():
            # Requirement 15.4: Use "unknown" if version file missing
            return "unknown"
        
        try:
            with open(version_path, 'r') as f:
                version_data = json.load(f)
                return version_data.get('version', 'unknown')
        except Exception:
            return "unknown"
    
    def predict(self, features: np.ndarray) -> PlacementPrediction:
        """
        Generate placement predictions for all time windows.
        
        Args:
            features: Feature vector from FeatureEngineer, shape (1, 16)
            
        Returns:
            PlacementPrediction with probabilities and label
            
        Raises:
            ValueError: If feature vector has incorrect shape
            
        Requirements:
            - 1.1: Generate probability scores for 3/6/12 month windows
            - 1.2: Assign placement timeline label
            - 1.4: Output probabilities with 4 decimal precision
            - 1.6: Assign "high_risk" when all probabilities < 0.50
        """
        # Validate feature vector shape
        if features.shape[0] != 1:
            raise ValueError(f"Expected features with shape (1, n_features), got {features.shape}")
        
        # Get probability predictions from each model (Requirement 1.1)
        # XGBoost predict_proba returns [prob_class_0, prob_class_1]
        # We want probability of positive class (placed=1)
        prob_3m_raw = self.model_3m.predict_proba(features)[0, 1]
        prob_6m_raw = self.model_6m.predict_proba(features)[0, 1]
        prob_12m_raw = self.model_12m.predict_proba(features)[0, 1]
        
        # Round to 4 decimal places (Requirement 1.4)
        prob_3m = round(float(prob_3m_raw), 4)
        prob_6m = round(float(prob_6m_raw), 4)
        prob_12m = round(float(prob_12m_raw), 4)
        
        # Assign placement label based on thresholds (Requirements 1.2, 1.6)
        label = self._assign_label(prob_3m, prob_6m, prob_12m)
        
        return PlacementPrediction(
            prob_3m=prob_3m,
            prob_6m=prob_6m,
            prob_12m=prob_12m,
            label=label
        )
    
    def _assign_label(self, prob_3m: float, prob_6m: float, prob_12m: float) -> str:
        """
        Assign placement timeline label based on probability thresholds.
        
        Logic (Requirements 1.2, 1.6):
        - If prob_3m >= 0.50: "placed_3m"
        - Elif prob_6m >= 0.50: "placed_6m"
        - Elif prob_12m >= 0.50: "placed_12m"
        - Else: "high_risk"
        
        Args:
            prob_3m: 3-month placement probability
            prob_6m: 6-month placement probability
            prob_12m: 12-month placement probability
            
        Returns:
            Placement label string
        """
        if prob_3m >= 0.50:
            return "placed_3m"
        elif prob_6m >= 0.50:
            return "placed_6m"
        elif prob_12m >= 0.50:
            return "placed_12m"
        else:
            return "high_risk"
    
    def get_model_version(self) -> str:
        """
        Return semantic version string from version.json.
        
        Returns:
            Model version string (e.g., "1.0.0" or "unknown")
            
        Requirement 15.1: Record Model_Version in predictions
        """
        return self._version
