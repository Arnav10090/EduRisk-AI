"""
Model Training Pipeline for EduRisk AI

This script trains XGBoost classifiers for placement prediction across
3 time windows (3m, 6m, 12m) with hyperparameter optimization using Optuna.

Feature: edurisk-ai-placement-intelligence
Requirements: 1.3
"""

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score
import optuna
from pathlib import Path
import joblib
import json
from typing import Dict, Tuple
import warnings
warnings.filterwarnings('ignore')

from ml.pipeline.feature_engineering import FeatureEngineer


class PlacementModelTrainer:
    """
    Trains XGBoost models for placement prediction.
    
    Implements:
    - 80/20 train-test split
    - 5-fold cross-validation
    - Hyperparameter tuning with Optuna (50 trials)
    - Model persistence and metrics logging
    """
    
    def __init__(
        self,
        data_path: str = 'ml/data/synthetic/students.csv',
        model_dir: str = 'ml/models',
        n_trials: int = 50,
        cv_folds: int = 5,
        random_seed: int = 42
    ):
        """
        Initialize trainer.
        
        Args:
            data_path: Path to training data CSV
            model_dir: Directory to save trained models
            n_trials: Number of Optuna trials for hyperparameter tuning
            cv_folds: Number of cross-validation folds
            random_seed: Random seed for reproducibility
        """
        self.data_path = data_path
        self.model_dir = Path(model_dir)
        self.n_trials = n_trials
        self.cv_folds = cv_folds
        self.random_seed = random_seed
        
        # Create model directory if it doesn't exist
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize feature engineer
        self.feature_engineer = FeatureEngineer()
        
        # Store training metrics
        self.metrics = {}
    
    def load_and_prepare_data(self) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """
        Load data and prepare features and labels.
        
        Returns:
            Tuple of (X_features, y_labels_dict)
            where y_labels_dict contains 'placed_3m', 'placed_6m', 'placed_12m'
        """
        print('Loading training data...')
        df = pd.read_csv(self.data_path)
        print(f'Loaded {len(df)} records')
        
        # Generate features for all students
        print('Generating features...')
        X_list = []
        for idx, row in df.iterrows():
            student_data = row.to_dict()
            features = self.feature_engineer.transform(student_data)
            X_list.append(features[0])  # Extract from (1, n_features) shape
        
        X = np.array(X_list)
        
        # Extract labels
        y_labels = {
            'placed_3m': df['placed_3m'].values,
            'placed_6m': df['placed_6m'].values,
            'placed_12m': df['placed_12m'].values
        }
        
        print(f'Feature matrix shape: {X.shape}')
        print(f'Label distributions:')
        for label_name, y in y_labels.items():
            print(f'  - {label_name}: {y.mean():.2%} positive')
        
        return X, y_labels
    
    def train_model(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        model_name: str
    ) -> Tuple[xgb.XGBClassifier, Dict[str, float]]:
        """
        Train a single XGBoost model with hyperparameter optimization.
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_test: Test features
            y_test: Test labels
            model_name: Name for the model (e.g., 'placement_model_3m')
            
        Returns:
            Tuple of (trained_model, metrics_dict)
        """
        print(f'\n{"="*60}')
        print(f'Training {model_name}')
        print(f'{"="*60}')
        
        # Define objective function for Optuna
        def objective(trial):
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 100, 500),
                'max_depth': trial.suggest_int('max_depth', 3, 7),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
                'subsample': trial.suggest_float('subsample', 0.7, 0.9),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.7, 0.9),
                'min_child_weight': trial.suggest_int('min_child_weight', 1, 5),
                'gamma': trial.suggest_float('gamma', 0, 0.2),
                'use_label_encoder': False,
                'eval_metric': 'auc',
                'random_state': self.random_seed
            }
            
            model = xgb.XGBClassifier(**params)
            
            # 5-fold cross-validation
            cv_scores = cross_val_score(
                model, X_train, y_train,
                cv=self.cv_folds,
                scoring='roc_auc',
                n_jobs=-1
            )
            
            return cv_scores.mean()
        
        # Run Optuna optimization
        print(f'Running hyperparameter optimization ({self.n_trials} trials)...')
        study = optuna.create_study(direction='maximize', study_name=model_name)
        study.optimize(objective, n_trials=self.n_trials, show_progress_bar=True)
        
        print(f'\nBest trial:')
        print(f'  - AUC-ROC (CV): {study.best_value:.4f}')
        print(f'  - Parameters: {study.best_params}')
        
        # Train final model with best parameters
        print('\nTraining final model with best parameters...')
        best_params = study.best_params
        best_params.update({
            'use_label_encoder': False,
            'eval_metric': 'auc',
            'random_state': self.random_seed
        })
        
        model = xgb.XGBClassifier(**best_params)
        model.fit(X_train, y_train)
        
        # Evaluate on test set
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        metrics = {
            'auc_roc': roc_auc_score(y_test, y_pred_proba),
            'f1': f1_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'cv_auc_mean': study.best_value,
            'best_params': best_params
        }
        
        print(f'\nTest Set Metrics:')
        print(f'  - AUC-ROC: {metrics["auc_roc"]:.4f}')
        print(f'  - F1 Score: {metrics["f1"]:.4f}')
        print(f'  - Precision: {metrics["precision"]:.4f}')
        print(f'  - Recall: {metrics["recall"]:.4f}')
        
        return model, metrics
    
    def train_all_models(self) -> Dict[str, Dict]:
        """
        Train all three placement models (3m, 6m, 12m).
        
        Returns:
            Dictionary of metrics for all models
        """
        # Load and prepare data
        X, y_labels = self.load_and_prepare_data()
        
        # 80/20 train-test split (stratified)
        print('\nSplitting data (80/20 train-test)...')
        
        all_metrics = {}
        
        # Train models for each time window
        for window, label_name in [('3m', 'placed_3m'), ('6m', 'placed_6m'), ('12m', 'placed_12m')]:
            y = y_labels[label_name]
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y,
                test_size=0.2,
                stratify=y,
                random_state=self.random_seed
            )
            
            print(f'\nTrain set: {len(X_train)} samples')
            print(f'Test set: {len(X_test)} samples')
            
            # Train model
            model_name = f'placement_model_{window}'
            model, metrics = self.train_model(
                X_train, y_train, X_test, y_test, model_name
            )
            
            # Save model
            model_path = self.model_dir / f'{model_name}.pkl'
            joblib.dump(model, model_path)
            print(f'\n✓ Model saved to {model_path}')
            
            # Store metrics
            all_metrics[window] = metrics
        
        self.metrics = all_metrics
        return all_metrics
    
    def save_metrics(self, output_path: str = None):
        """
        Save training metrics to JSON file.
        
        Args:
            output_path: Path to save metrics (default: model_dir/training_metrics.json)
        """
        if output_path is None:
            output_path = self.model_dir / 'training_metrics.json'
        
        # Convert numpy types to Python types for JSON serialization
        metrics_serializable = {}
        for window, metrics in self.metrics.items():
            metrics_serializable[window] = {
                'auc_roc': float(metrics['auc_roc']),
                'f1': float(metrics['f1']),
                'precision': float(metrics['precision']),
                'recall': float(metrics['recall']),
                'cv_auc_mean': float(metrics['cv_auc_mean']),
                'best_params': metrics['best_params']
            }
        
        with open(output_path, 'w') as f:
            json.dump(metrics_serializable, f, indent=2)
        
        print(f'\n✓ Metrics saved to {output_path}')


def main():
    """
    Main function to train all placement models.
    """
    print('EduRisk AI - Placement Model Training')
    print('=' * 60)
    
    # Initialize trainer
    trainer = PlacementModelTrainer(
        data_path='ml/data/synthetic/students.csv',
        model_dir='ml/models',
        n_trials=50,  # 50 trials for hyperparameter tuning
        cv_folds=5,   # 5-fold cross-validation
        random_seed=42
    )
    
    # Train all models
    metrics = trainer.train_all_models()
    
    # Save metrics
    trainer.save_metrics()
    
    print('\n' + '=' * 60)
    print('✓ Training complete!')
    print('=' * 60)
    print('\nSummary:')
    for window, m in metrics.items():
        print(f'\n{window.upper()} Model:')
        print(f'  - AUC-ROC: {m["auc_roc"]:.4f}')
        print(f'  - F1 Score: {m["f1"]:.4f}')
        print(f'  - Precision: {m["precision"]:.4f}')
        print(f'  - Recall: {m["recall"]:.4f}')


if __name__ == '__main__':
    main()
