"""
Test script for bias audit functionality.

This script tests the bias audit on all three placement models
(3m, 6m, 12m) to ensure comprehensive fairness testing.

Feature: edurisk-ai-placement-intelligence
"""

import numpy as np
import pandas as pd
from pathlib import Path
import joblib
from sklearn.model_selection import train_test_split

from ml.pipeline.bias_audit import (
    run_bias_audit,
    save_bias_report,
    generate_synthetic_sensitive_features
)
from ml.pipeline.feature_engineering import FeatureEngineer


def test_all_models():
    """
    Test bias audit on all three placement models.
    """
    print("=" * 70)
    print("Testing Bias Audit on All Placement Models")
    print("=" * 70)
    
    # Load test data
    print("\nLoading test data...")
    data_path = Path('ml/data/synthetic/students.csv')
    
    if not data_path.exists():
        print(f"\n❌ Error: Test data not found at {data_path}")
        return False
    
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} records")
    
    # Generate synthetic sensitive features
    print("\nGenerating synthetic demographic features...")
    sensitive_features = generate_synthetic_sensitive_features(
        n_samples=len(df),
        random_seed=42
    )
    
    # Prepare features
    print("\nPreparing features...")
    feature_engineer = FeatureEngineer()
    
    X_list = []
    for idx, row in df.iterrows():
        student_data = row.to_dict()
        features = feature_engineer.transform(student_data)
        X_list.append(features[0])
    
    X = np.array(X_list)
    
    # Test each model
    models_to_test = [
        ('placement_model_3m', 'placed_3m'),
        ('placement_model_6m', 'placed_6m'),
        ('placement_model_12m', 'placed_12m')
    ]
    
    all_reports = []
    
    for model_name, label_col in models_to_test:
        print(f"\n{'='*70}")
        print(f"Testing {model_name}")
        print(f"{'='*70}")
        
        # Split data
        _, X_test, _, y_test, _, sensitive_test = train_test_split(
            X, df[label_col].values, sensitive_features,
            test_size=0.2,
            stratify=df[label_col].values,
            random_state=42
        )
        
        print(f"Test set size: {len(X_test)} samples")
        
        # Load model
        model_path = Path(f'ml/models/{model_name}.pkl')
        
        if not model_path.exists():
            print(f"\n⚠️  Warning: Model not found at {model_path}")
            print(f"Skipping {model_name}")
            continue
        
        print(f"Loading model from {model_path}...")
        model = joblib.load(model_path)
        
        # Run bias audit
        try:
            report = run_bias_audit(
                model=model,
                X_test=X_test,
                y_test=y_test,
                sensitive_features=sensitive_test,
                model_name=model_name,
                bias_threshold=0.1
            )
            
            # Save report
            report_path = save_bias_report(report, output_dir='ml/reports')
            
            all_reports.append({
                'model': model_name,
                'report': report,
                'path': report_path
            })
            
        except Exception as e:
            print(f"\n❌ Error testing {model_name}: {e}")
            return False
    
    # Summary
    print("\n" + "=" * 70)
    print("Bias Audit Summary")
    print("=" * 70)
    
    for item in all_reports:
        report = item['report']
        status = "⚠️  BIASED" if report.is_biased else "✓ PASSED"
        print(f"\n{item['model']}:")
        print(f"  Status: {status}")
        print(f"  Demographic Parity Difference: {report.demographic_parity_difference:.4f}")
        print(f"  Equalized Odds Difference: {report.equalized_odds_difference:.4f}")
        print(f"  Report: {item['path']}")
    
    print("\n" + "=" * 70)
    print("✓ All bias audits completed successfully!")
    print("=" * 70)
    
    return True


def test_bias_threshold():
    """
    Test that bias flagging works correctly when threshold is exceeded.
    """
    print("\n" + "=" * 70)
    print("Testing Bias Threshold Flagging")
    print("=" * 70)
    
    # This is a unit test to verify the BiasReport correctly flags bias
    from ml.pipeline.bias_audit import BiasReport
    
    # Test case 1: Below threshold (should pass)
    report1 = BiasReport(
        model_name='test_model_pass',
        demographic_parity_diff=0.05,
        equalized_odds_diff=0.03,
        metrics_by_gender={'Male': {'accuracy': 0.8, 'selection_rate': 0.7}},
        metrics_by_region={'North': {'accuracy': 0.8, 'selection_rate': 0.7}},
        bias_threshold=0.1
    )
    
    assert not report1.is_biased, "Report should not be flagged as biased"
    print("✓ Test 1 passed: Model with DPD=0.05 correctly marked as PASSED")
    
    # Test case 2: Above threshold (should fail)
    report2 = BiasReport(
        model_name='test_model_fail',
        demographic_parity_diff=0.15,
        equalized_odds_diff=0.12,
        metrics_by_gender={'Male': {'accuracy': 0.8, 'selection_rate': 0.7}},
        metrics_by_region={'North': {'accuracy': 0.8, 'selection_rate': 0.7}},
        bias_threshold=0.1
    )
    
    assert report2.is_biased, "Report should be flagged as biased"
    print("✓ Test 2 passed: Model with DPD=0.15 correctly marked as BIASED")
    
    # Test case 3: Exactly at threshold (should pass)
    report3 = BiasReport(
        model_name='test_model_boundary',
        demographic_parity_diff=0.1,
        equalized_odds_diff=0.08,
        metrics_by_gender={'Male': {'accuracy': 0.8, 'selection_rate': 0.7}},
        metrics_by_region={'North': {'accuracy': 0.8, 'selection_rate': 0.7}},
        bias_threshold=0.1
    )
    
    assert not report3.is_biased, "Report at threshold should not be flagged"
    print("✓ Test 3 passed: Model with DPD=0.10 (at threshold) correctly marked as PASSED")
    
    print("\n✓ All threshold tests passed!")
    
    return True


def main():
    """
    Run all bias audit tests.
    """
    print("\n" + "=" * 70)
    print("EduRisk AI - Bias Audit Test Suite")
    print("=" * 70)
    
    # Test 1: Threshold flagging logic
    if not test_bias_threshold():
        print("\n❌ Threshold tests failed!")
        return
    
    # Test 2: All models
    if not test_all_models():
        print("\n❌ Model tests failed!")
        return
    
    print("\n" + "=" * 70)
    print("✓ All tests passed successfully!")
    print("=" * 70)


if __name__ == '__main__':
    main()
