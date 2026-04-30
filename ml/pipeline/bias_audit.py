"""
Bias Audit Module for EduRisk AI

This module provides post-hoc fairness testing using Fairlearn to compute
demographic parity metrics and identify potential bias in placement predictions.

Feature: edurisk-ai-placement-intelligence
Requirements: 29.1, 29.2, 29.3, 29.4, 29.5, 29.6
"""

import numpy as np
import pandas as pd
import xgboost as xgb
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import json
import warnings
warnings.filterwarnings('ignore')

try:
    from fairlearn.metrics import (
        MetricFrame,
        demographic_parity_difference,
        equalized_odds_difference,
        selection_rate
    )
    FAIRLEARN_AVAILABLE = True
except ImportError:
    FAIRLEARN_AVAILABLE = False
    print("Warning: Fairlearn not installed. Install with: pip install fairlearn")

from sklearn.metrics import accuracy_score


class BiasReport:
    """
    Container for bias audit results.
    
    Attributes:
        model_name: Name of the audited model
        timestamp: Audit timestamp
        demographic_parity_difference: Max difference in selection rates
        equalized_odds_difference: Max difference in error rates
        metrics_by_gender: Accuracy and selection rate by gender group
        metrics_by_region: Accuracy and selection rate by region group
        is_biased: Whether model exceeds bias threshold (>0.1)
        bias_threshold: Threshold for flagging bias
    """
    
    def __init__(
        self,
        model_name: str,
        demographic_parity_diff: float,
        equalized_odds_diff: float,
        metrics_by_gender: Dict,
        metrics_by_region: Dict,
        bias_threshold: float = 0.1
    ):
        self.model_name = model_name
        self.timestamp = datetime.now().isoformat()
        self.demographic_parity_difference = demographic_parity_diff
        self.equalized_odds_difference = equalized_odds_diff
        self.metrics_by_gender = metrics_by_gender
        self.metrics_by_region = metrics_by_region
        self.bias_threshold = bias_threshold
        self.is_biased = demographic_parity_diff > bias_threshold
    
    def to_dict(self) -> Dict:
        """Convert report to dictionary for JSON serialization."""
        return {
            'model_name': self.model_name,
            'timestamp': self.timestamp,
            'demographic_parity_difference': float(self.demographic_parity_difference),
            'equalized_odds_difference': float(self.equalized_odds_difference),
            'metrics_by_gender': self.metrics_by_gender,
            'metrics_by_region': self.metrics_by_region,
            'bias_threshold': float(self.bias_threshold),
            'is_biased': bool(self.is_biased),
            'bias_flag': 'POTENTIALLY BIASED' if self.is_biased else 'PASSED'
        }
    
    def __str__(self) -> str:
        """String representation of the report."""
        lines = [
            f"\n{'='*70}",
            f"Bias Audit Report: {self.model_name}",
            f"Timestamp: {self.timestamp}",
            f"{'='*70}",
            f"\nOverall Fairness Metrics:",
            f"  Demographic Parity Difference: {self.demographic_parity_difference:.4f}",
            f"  Equalized Odds Difference: {self.equalized_odds_difference:.4f}",
            f"  Bias Threshold: {self.bias_threshold}",
            f"  Status: {'⚠️  POTENTIALLY BIASED' if self.is_biased else '✓ PASSED'}",
            f"\nMetrics by Gender Group:",
        ]
        
        for group, metrics in self.metrics_by_gender.items():
            lines.append(f"  {group}:")
            lines.append(f"    - Accuracy: {metrics['accuracy']:.4f}")
            lines.append(f"    - Selection Rate: {metrics['selection_rate']:.4f}")
        
        lines.append(f"\nMetrics by Region Group:")
        for group, metrics in self.metrics_by_region.items():
            lines.append(f"  {group}:")
            lines.append(f"    - Accuracy: {metrics['accuracy']:.4f}")
            lines.append(f"    - Selection Rate: {metrics['selection_rate']:.4f}")
        
        lines.append(f"\n{'='*70}")
        
        if self.is_biased:
            lines.append(f"\n⚠️  WARNING: Model shows demographic parity difference > {self.bias_threshold}")
            lines.append(f"   This indicates potential bias in predictions across demographic groups.")
            lines.append(f"   Consider retraining with fairness constraints or adjusting decision thresholds.")
        
        return '\n'.join(lines)


def run_bias_audit(
    model: xgb.XGBClassifier,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    sensitive_features: pd.DataFrame,
    model_name: str = 'placement_model',
    bias_threshold: float = 0.1
) -> BiasReport:
    """
    Compute demographic parity metrics using Fairlearn.
    
    This function performs post-hoc fairness testing by computing accuracy
    and selection rate metrics grouped by sensitive demographic features
    (gender and region). It flags models where demographic parity difference
    exceeds the specified threshold.
    
    Args:
        model: Trained XGBoost model
        X_test: Test features (WITHOUT sensitive features)
        y_test: True labels
        sensitive_features: DataFrame with 'gender' and 'region' columns
        model_name: Name of the model being audited
        bias_threshold: Threshold for flagging bias (default 0.1)
        
    Returns:
        BiasReport with parity differences and metric breakdowns
        
    Raises:
        ImportError: If Fairlearn is not installed
        ValueError: If sensitive_features missing required columns
    """
    if not FAIRLEARN_AVAILABLE:
        raise ImportError(
            "Fairlearn is required for bias auditing. "
            "Install with: pip install fairlearn"
        )
    
    # Validate sensitive features
    required_columns = ['gender', 'region']
    missing_columns = [col for col in required_columns if col not in sensitive_features.columns]
    if missing_columns:
        raise ValueError(
            f"sensitive_features missing required columns: {missing_columns}. "
            f"Required: {required_columns}"
        )
    
    print(f"\n{'='*70}")
    print(f"Running Bias Audit: {model_name}")
    print(f"{'='*70}")
    
    # Generate predictions
    print("\nGenerating predictions...")
    y_pred = model.predict(X_test)
    
    # Compute demographic parity difference (Requirement 29.3)
    print("Computing demographic parity difference...")
    dpd = demographic_parity_difference(
        y_true=y_test,
        y_pred=y_pred,
        sensitive_features=sensitive_features['gender']
    )
    print(f"  Demographic Parity Difference (Gender): {dpd:.4f}")
    
    # Compute equalized odds difference
    print("Computing equalized odds difference...")
    eod = equalized_odds_difference(
        y_true=y_test,
        y_pred=y_pred,
        sensitive_features=sensitive_features['gender']
    )
    print(f"  Equalized Odds Difference (Gender): {eod:.4f}")
    
    # Compute metrics by gender group (Requirement 29.2)
    print("\nComputing metrics by gender group...")
    metrics_by_gender = _compute_group_metrics(
        y_test, y_pred, sensitive_features['gender']
    )
    
    # Compute metrics by region group (Requirement 29.2)
    print("Computing metrics by region group...")
    metrics_by_region = _compute_group_metrics(
        y_test, y_pred, sensitive_features['region']
    )
    
    # Create bias report
    report = BiasReport(
        model_name=model_name,
        demographic_parity_diff=dpd,
        equalized_odds_diff=eod,
        metrics_by_gender=metrics_by_gender,
        metrics_by_region=metrics_by_region,
        bias_threshold=bias_threshold
    )
    
    # Print report
    print(report)
    
    return report


def _compute_group_metrics(
    y_true: pd.Series,
    y_pred: np.ndarray,
    sensitive_feature: pd.Series
) -> Dict[str, Dict[str, float]]:
    """
    Compute accuracy and selection rate for each group.
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        sensitive_feature: Sensitive feature (e.g., gender or region)
        
    Returns:
        Dictionary mapping group names to metrics
    """
    # Create MetricFrame for accuracy
    mf_accuracy = MetricFrame(
        metrics=accuracy_score,
        y_true=y_true,
        y_pred=y_pred,
        sensitive_features=sensitive_feature
    )
    
    # Create MetricFrame for selection rate
    mf_selection = MetricFrame(
        metrics=selection_rate,
        y_true=y_true,
        y_pred=y_pred,
        sensitive_features=sensitive_feature
    )
    
    # Combine metrics by group
    group_metrics = {}
    for group in mf_accuracy.by_group.index:
        group_metrics[str(group)] = {
            'accuracy': float(mf_accuracy.by_group[group]),
            'selection_rate': float(mf_selection.by_group[group])
        }
    
    return group_metrics


def save_bias_report(
    report: BiasReport,
    output_dir: str = 'ml/reports'
) -> str:
    """
    Save bias audit report to JSON file with timestamp.
    
    Args:
        report: BiasReport to save
        output_dir: Output directory path
        
    Returns:
        Path to saved report file
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate filename with timestamp (Requirement 29.6)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'bias_audit_{report.model_name}_{timestamp}.json'
    output_file = output_path / filename
    
    # Save report as JSON
    with open(output_file, 'w') as f:
        json.dump(report.to_dict(), f, indent=2)
    
    print(f"\n✓ Bias audit report saved to: {output_file}")
    
    return str(output_file)


def generate_synthetic_sensitive_features(
    n_samples: int,
    random_seed: int = 42
) -> pd.DataFrame:
    """
    Generate synthetic demographic features for bias auditing.
    
    This function generates synthetic gender and region data for testing
    purposes when real demographic data is not available.
    
    Args:
        n_samples: Number of samples to generate
        random_seed: Random seed for reproducibility
        
    Returns:
        DataFrame with 'gender' and 'region' columns
    """
    np.random.seed(random_seed)
    
    # Generate gender (binary for simplicity)
    genders = np.random.choice(['Male', 'Female'], size=n_samples, p=[0.6, 0.4])
    
    # Generate region
    regions = np.random.choice(
        ['North', 'South', 'East', 'West', 'Central'],
        size=n_samples,
        p=[0.25, 0.30, 0.15, 0.20, 0.10]
    )
    
    return pd.DataFrame({
        'gender': genders,
        'region': regions
    })


def main():
    """
    Main function to run bias audit on trained models.
    
    This demonstrates how to use the bias audit functionality with
    trained placement models.
    """
    print("EduRisk AI - Bias Audit")
    print("=" * 70)
    
    # Check if Fairlearn is available
    if not FAIRLEARN_AVAILABLE:
        print("\n❌ Error: Fairlearn is not installed.")
        print("Install with: pip install fairlearn")
        return
    
    # Load test data
    print("\nLoading test data...")
    data_path = Path('ml/data/synthetic/students.csv')
    
    if not data_path.exists():
        print(f"\n❌ Error: Test data not found at {data_path}")
        print("Please run the data generation script first:")
        print("  python ml/data/generate_synthetic.py")
        return
    
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} records")
    
    # Generate synthetic sensitive features
    # Note: In production, these would come from actual data
    print("\nGenerating synthetic demographic features...")
    sensitive_features = generate_synthetic_sensitive_features(
        n_samples=len(df),
        random_seed=42
    )
    
    # Prepare features and labels
    print("\nPreparing features...")
    from ml.pipeline.feature_engineering import FeatureEngineer
    from sklearn.model_selection import train_test_split
    
    feature_engineer = FeatureEngineer()
    
    X_list = []
    for idx, row in df.iterrows():
        student_data = row.to_dict()
        features = feature_engineer.transform(student_data)
        X_list.append(features[0])
    
    X = np.array(X_list)
    
    # Split data (use same split as training)
    _, X_test, _, y_test_3m, _, sensitive_test = train_test_split(
        X, df['placed_3m'].values, sensitive_features,
        test_size=0.2,
        stratify=df['placed_3m'].values,
        random_state=42
    )
    
    print(f"Test set size: {len(X_test)} samples")
    
    # Load trained model
    model_path = Path('ml/models/placement_model_3m.pkl')
    
    if not model_path.exists():
        print(f"\n❌ Error: Model not found at {model_path}")
        print("Please train the model first:")
        print("  python ml/pipeline/train.py")
        return
    
    print(f"\nLoading model from {model_path}...")
    import joblib
    model = joblib.load(model_path)
    
    # Run bias audit (Requirements 29.1, 29.2, 29.3, 29.4, 29.5)
    report = run_bias_audit(
        model=model,
        X_test=X_test,
        y_test=y_test_3m,
        sensitive_features=sensitive_test,
        model_name='placement_model_3m',
        bias_threshold=0.1
    )
    
    # Save report (Requirement 29.6)
    save_bias_report(report, output_dir='ml/reports')
    
    print("\n" + "=" * 70)
    print("✓ Bias audit complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
