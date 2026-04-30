"""
Salary Estimation Module for EduRisk AI

This module loads a trained Ridge regression model and predicts salary ranges
with confidence intervals for students.

Feature: edurisk-ai-placement-intelligence
Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""

from pathlib import Path
from typing import Optional
import json
import numpy as np
import joblib
from dataclasses import dataclass


@dataclass
class SalaryPrediction:
    """
    Container for salary prediction results.
    
    Attributes:
        predicted: Predicted salary in LPA (Lakhs Per Annum)
        salary_min: Minimum salary in confidence interval (LPA)
        salary_max: Maximum salary in confidence interval (LPA)
        confidence: Confidence interval width as percentage of predicted salary
    """
    predicted: float
    salary_min: float
    salary_max: float
    confidence: float


class SalaryEstimator:
    """
    Loads trained Ridge regression model and predicts salary ranges.
    
    This class manages a Ridge regression pipeline (StandardScaler + Ridge)
    and calculates confidence intervals using residual standard deviation
    from training.
    
    Requirements:
        - 2.1: Predict min, max, and confidence percentage
        - 2.2: Express salaries in LPA with 2 decimal precision
        - 2.3: Calculate salary_min as predicted - 1.5 * std
        - 2.4: Calculate salary_max as predicted + 1.5 * std
        - 2.5: Calculate confidence as interval width percentage
    """
    
    def __init__(self, model_path: Path):
        """
        Initialize SalaryEstimator by loading model from disk.
        
        Args:
            model_path: Path to the salary model pickle file
            
        Raises:
            FileNotFoundError: If model file is not found
            Exception: If model cannot be loaded
        """
        self.model_path = Path(model_path)
        
        # Load the Ridge regression pipeline (Requirement 2.6)
        self.model = self._load_model()
        
        # Load standard deviation of residuals from training
        self.std_residuals = self._load_std_residuals()
    
    def _load_model(self):
        """
        Load the pickled Ridge regression pipeline from disk.
        
        Returns:
            Loaded model pipeline (StandardScaler + Ridge)
            
        Raises:
            FileNotFoundError: If model file doesn't exist
        """
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        
        try:
            model = joblib.load(self.model_path)
            return model
        except Exception as e:
            raise Exception(f"Failed to load model from {self.model_path}: {e}")
    
    def _load_std_residuals(self) -> float:
        """
        Load standard deviation of residuals from salary_metrics.json.
        
        This value is computed during training and represents the typical
        prediction error, used to calculate confidence intervals.
        
        Returns:
            Standard deviation of residuals
            
        Raises:
            FileNotFoundError: If metrics file not found
            KeyError: If std_residuals not in metrics file
        """
        # Metrics file is in the same directory as the model
        metrics_path = self.model_path.parent / 'salary_metrics.json'
        
        if not metrics_path.exists():
            raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
        
        try:
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
                return float(metrics['std_residuals'])
        except KeyError:
            raise KeyError("'std_residuals' not found in salary_metrics.json")
        except Exception as e:
            raise Exception(f"Failed to load metrics from {metrics_path}: {e}")
    
    def predict(self, features: np.ndarray) -> SalaryPrediction:
        """
        Predict salary range in LPA.
        
        Args:
            features: Feature vector from FeatureEngineer, shape (1, 16)
            
        Returns:
            SalaryPrediction with predicted, min, max, and confidence
            
        Raises:
            ValueError: If feature vector has incorrect shape
            
        Requirements:
            - 2.1: Predict min, max, and confidence percentage
            - 2.2: Express salaries in LPA with 2 decimal precision
            - 2.3: Calculate salary_min as predicted - 1.5 * std
            - 2.4: Calculate salary_max as predicted + 1.5 * std
            - 2.5: Calculate confidence as interval width percentage
        """
        # Validate feature vector shape
        if features.shape[0] != 1:
            raise ValueError(f"Expected features with shape (1, n_features), got {features.shape}")
        
        # Get predicted salary from model (Requirement 2.1)
        predicted_raw = self.model.predict(features)[0]
        predicted = round(float(predicted_raw), 2)  # Requirement 2.2: 2 decimal precision
        
        # Calculate confidence interval using 1.5 * std formula
        # (Requirements 2.3, 2.4)
        interval_width = 1.5 * self.std_residuals
        salary_min = round(predicted - interval_width, 2)  # Requirement 2.2
        salary_max = round(predicted + interval_width, 2)  # Requirement 2.2
        
        # Ensure salary_min is non-negative (salaries can't be negative)
        salary_min = max(0.0, salary_min)
        
        # Calculate confidence as percentage (Requirement 2.5)
        # Formula: ((max - min) / predicted) * 100
        if predicted > 0:
            confidence = round(((salary_max - salary_min) / predicted) * 100, 2)
        else:
            # Edge case: if predicted is 0 or negative, set confidence to 100%
            confidence = 100.0
        
        return SalaryPrediction(
            predicted=predicted,
            salary_min=salary_min,
            salary_max=salary_max,
            confidence=confidence
        )
