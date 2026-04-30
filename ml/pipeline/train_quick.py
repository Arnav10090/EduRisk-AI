"""
Quick Model Training Pipeline for EduRisk AI

This script trains models with reasonable default hyperparameters
for faster training during development/testing.

Feature: edurisk-ai-placement-intelligence
Requirements: 1.3, 2.6, 15.1, 15.2, 15.3
"""

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from pathlib import Path
import joblib
import json
from datetime import datetime
from typing import Dict, Tuple
import warnings
warnings.filterwarnings('ignore')

from ml.pipeline.feature_engineering import FeatureEngineer


def train_placement_models(data_path: str, model_dir: Path) -> Dict:
    """Train all three placement models with default hyperparameters."""
    print('Training Placement Models...')
    print('=' * 60)
    
    # Load data
    df = pd.read_csv(data_path)
    print(f'Loaded {len(df)} records')
    
    # Generate features
    feature_engineer = FeatureEngineer()
    X_list = []
    for idx, row in df.iterrows():
        features = feature_engineer.transform(row.to_dict())
        X_list.append(features[0])
    
    X = np.array(X_list)
    print(f'Feature matrix shape: {X.shape}')
    
    # Train models for each time window
    metrics = {}
    for window, label_col in [('3m', 'placed_3m'), ('6m', 'placed_6m'), ('12m', 'placed_12m')]:
        print(f'\nTraining {window} model...')
        
        y = df[label_col].values
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, stratify=y, random_state=42
        )
        
        # Use reasonable default hyperparameters
        model = xgb.XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            use_label_encoder=False,
            eval_metric='auc',
            random_state=42
        )
        
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        metrics[window] = {
            'auc_roc': float(roc_auc_score(y_test, y_pred_proba)),
            'f1': float(f1_score(y_test, y_pred)),
            'precision': float(precision_score(y_test, y_pred)),
            'recall': float(recall_score(y_test, y_pred))
        }
        
        print(f'  AUC-ROC: {metrics[window]["auc_roc"]:.4f}')
        print(f'  F1: {metrics[window]["f1"]:.4f}')
        
        # Save model
        model_path = model_dir / f'placement_model_{window}.pkl'
        joblib.dump(model, model_path)
        print(f'  ✓ Saved to {model_path}')
    
    return metrics


def train_salary_model(data_path: str, model_dir: Path) -> Dict:
    """Train salary model with Ridge regression."""
    print('\nTraining Salary Model...')
    print('=' * 60)
    
    # Load data
    df = pd.read_csv(data_path)
    df_placed = df[df['salary_lpa'].notna() & (df['salary_lpa'] > 0)].copy()
    print(f'Loaded {len(df_placed)} placed students with salary data')
    
    # Generate features
    feature_engineer = FeatureEngineer()
    X_list = []
    for idx, row in df_placed.iterrows():
        features = feature_engineer.transform(row.to_dict())
        X_list.append(features[0])
    
    X = np.array(X_list)
    y = df_placed['salary_lpa'].values
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Create pipeline
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('model', Ridge(alpha=1.0, random_state=42))
    ])
    
    pipeline.fit(X_train, y_train)
    
    # Evaluate
    y_pred = pipeline.predict(X_test)
    residuals = y_test - y_pred
    
    metrics = {
        'mae': float(mean_absolute_error(y_test, y_pred)),
        'rmse': float(np.sqrt(mean_squared_error(y_test, y_pred))),
        'r2': float(r2_score(y_test, y_pred)),
        'std_residuals': float(np.std(residuals))
    }
    
    print(f'  MAE: {metrics["mae"]:.2f} LPA')
    print(f'  RMSE: {metrics["rmse"]:.2f} LPA')
    print(f'  R²: {metrics["r2"]:.4f}')
    
    # Save model
    model_path = model_dir / 'salary_model.pkl'
    joblib.dump(pipeline, model_path)
    print(f'  ✓ Saved to {model_path}')
    
    return metrics


def generate_version_metadata(placement_metrics: Dict, salary_metrics: Dict, model_dir: Path):
    """Generate version.json metadata file."""
    print('\nGenerating Version Metadata...')
    print('=' * 60)
    
    metadata = {
        'version': '1.0.0',
        'training_date': datetime.now().isoformat(),
        'models': {
            'placement_3m': {
                'type': 'XGBoostClassifier',
                'file': 'placement_model_3m.pkl',
                'metrics': placement_metrics['3m']
            },
            'placement_6m': {
                'type': 'XGBoostClassifier',
                'file': 'placement_model_6m.pkl',
                'metrics': placement_metrics['6m']
            },
            'placement_12m': {
                'type': 'XGBoostClassifier',
                'file': 'placement_model_12m.pkl',
                'metrics': placement_metrics['12m']
            },
            'salary': {
                'type': 'Ridge',
                'file': 'salary_model.pkl',
                'metrics': salary_metrics
            }
        },
        'feature_engineering': {
            'n_features': 16,
            'feature_names_file': 'feature_names.json'
        },
        'training_config': {
            'data_source': 'synthetic',
            'n_records': 5000,
            'train_test_split': 0.8,
            'random_seed': 42
        }
    }
    
    version_path = model_dir / 'version.json'
    with open(version_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f'  ✓ Saved to {version_path}')
    print(f'  Version: {metadata["version"]}')
    print(f'  Training Date: {metadata["training_date"]}')
    
    return metadata


def main():
    """Main training function."""
    print('=' * 70)
    print('EduRisk AI - Quick Model Training Pipeline')
    print('=' * 70)
    print()
    
    data_path = 'ml/data/synthetic/students.csv'
    model_dir = Path('ml/models')
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Train placement models
    placement_metrics = train_placement_models(data_path, model_dir)
    
    # Train salary model
    salary_metrics = train_salary_model(data_path, model_dir)
    
    # Generate version metadata
    metadata = generate_version_metadata(placement_metrics, salary_metrics, model_dir)
    
    # Save all metrics
    metrics_path = model_dir / 'training_metrics.json'
    with open(metrics_path, 'w') as f:
        json.dump({
            'placement': placement_metrics,
            'salary': salary_metrics
        }, f, indent=2)
    print(f'\n✓ All metrics saved to {metrics_path}')
    
    # Final summary
    print('\n' + '=' * 70)
    print('✓ TRAINING COMPLETE!')
    print('=' * 70)
    print('\nModel Performance Summary:')
    print('\nPlacement Models:')
    for window in ['3m', '6m', '12m']:
        m = placement_metrics[window]
        print(f'  {window.upper()}:')
        print(f'    - AUC-ROC: {m["auc_roc"]:.4f}')
        print(f'    - F1 Score: {m["f1"]:.4f}')
    
    print('\nSalary Model:')
    print(f'  - MAE: {salary_metrics["mae"]:.2f} LPA')
    print(f'  - RMSE: {salary_metrics["rmse"]:.2f} LPA')
    print(f'  - R²: {salary_metrics["r2"]:.4f}')
    
    print('\nGenerated Files:')
    print('  - ml/models/placement_model_3m.pkl')
    print('  - ml/models/placement_model_6m.pkl')
    print('  - ml/models/placement_model_12m.pkl')
    print('  - ml/models/salary_model.pkl')
    print('  - ml/models/version.json')
    print('  - ml/models/training_metrics.json')
    print('\n' + '=' * 70)


if __name__ == '__main__':
    main()
