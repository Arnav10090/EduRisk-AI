"""
Salary Model Training for EduRisk AI

This script trains a Ridge regression model for salary prediction
with StandardScaler preprocessing.

Feature: edurisk-ai-placement-intelligence
Requirements: 2.6
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from pathlib import Path
import joblib
import json
from typing import Dict, Tuple
import warnings
warnings.filterwarnings('ignore')

from ml.pipeline.feature_engineering import FeatureEngineer


class SalaryModelTrainer:
    """
    Trains Ridge regression model for salary prediction.
    
    Implements:
    - StandardScaler preprocessing
    - Ridge regression with regularization
    - 80/20 train-test split
    - 5-fold cross-validation
    - Model persistence and metrics logging
    """
    
    def __init__(
        self,
        data_path: str = 'ml/data/synthetic/students.csv',
        model_dir: str = 'ml/models',
        cv_folds: int = 5,
        random_seed: int = 42
    ):
        """
        Initialize trainer.
        
        Args:
            data_path: Path to training data CSV
            model_dir: Directory to save trained model
            cv_folds: Number of cross-validation folds
            random_seed: Random seed for reproducibility
        """
        self.data_path = data_path
        self.model_dir = Path(model_dir)
        self.cv_folds = cv_folds
        self.random_seed = random_seed
        
        # Create model directory if it doesn't exist
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize feature engineer
        self.feature_engineer = FeatureEngineer()
        
        # Store training metrics
        self.metrics = {}
    
    def load_and_prepare_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load data and prepare features and salary labels.
        
        Only includes students who were placed (salary > 0).
        
        Returns:
            Tuple of (X_features, y_salary)
        """
        print('Loading training data...')
        df = pd.read_csv(self.data_path)
        print(f'Loaded {len(df)} records')
        
        # Filter to only placed students with salary data
        df_placed = df[df['salary_lpa'].notna() & (df['salary_lpa'] > 0)].copy()
        print(f'Filtered to {len(df_placed)} placed students with salary data')
        
        # Generate features for all placed students
        print('Generating features...')
        X_list = []
        for idx, row in df_placed.iterrows():
            student_data = row.to_dict()
            features = self.feature_engineer.transform(student_data)
            X_list.append(features[0])  # Extract from (1, n_features) shape
        
        X = np.array(X_list)
        y = df_placed['salary_lpa'].values
        
        print(f'Feature matrix shape: {X.shape}')
        print(f'Salary statistics:')
        print(f'  - Mean: {y.mean():.2f} LPA')
        print(f'  - Std: {y.std():.2f} LPA')
        print(f'  - Min: {y.min():.2f} LPA')
        print(f'  - Max: {y.max():.2f} LPA')
        
        return X, y
    
    def train_model(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> Tuple[Pipeline, Dict[str, float]]:
        """
        Train Ridge regression model with StandardScaler.
        
        Args:
            X_train: Training features
            y_train: Training salary labels
            X_test: Test features
            y_test: Test salary labels
            
        Returns:
            Tuple of (trained_pipeline, metrics_dict)
        """
        print(f'\n{"="*60}')
        print('Training Salary Model (Ridge Regression)')
        print(f'{"="*60}')
        
        # Create pipeline with StandardScaler and Ridge regression
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('model', Ridge(alpha=1.0, random_state=self.random_seed))
        ])
        
        # Train model
        print('Training model...')
        pipeline.fit(X_train, y_train)
        
        # Cross-validation on training set
        print(f'Running {self.cv_folds}-fold cross-validation...')
        cv_scores = cross_val_score(
            pipeline, X_train, y_train,
            cv=self.cv_folds,
            scoring='neg_mean_absolute_error',
            n_jobs=-1
        )
        cv_mae = -cv_scores.mean()
        cv_mae_std = cv_scores.std()
        
        print(f'CV MAE: {cv_mae:.2f} ± {cv_mae_std:.2f} LPA')
        
        # Evaluate on test set
        y_pred = pipeline.predict(X_test)
        
        # Calculate residual standard deviation for confidence intervals
        residuals = y_test - y_pred
        std_residuals = np.std(residuals)
        
        metrics = {
            'mae': mean_absolute_error(y_test, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'r2': r2_score(y_test, y_pred),
            'cv_mae_mean': cv_mae,
            'cv_mae_std': cv_mae_std,
            'std_residuals': std_residuals
        }
        
        print(f'\nTest Set Metrics:')
        print(f'  - MAE: {metrics["mae"]:.2f} LPA')
        print(f'  - RMSE: {metrics["rmse"]:.2f} LPA')
        print(f'  - R²: {metrics["r2"]:.4f}')
        print(f'  - Residual Std: {metrics["std_residuals"]:.2f} LPA')
        
        return pipeline, metrics
    
    def train(self) -> Dict[str, float]:
        """
        Train salary model.
        
        Returns:
            Dictionary of metrics
        """
        # Load and prepare data
        X, y = self.load_and_prepare_data()
        
        # 80/20 train-test split
        print('\nSplitting data (80/20 train-test)...')
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=0.2,
            random_state=self.random_seed
        )
        
        print(f'Train set: {len(X_train)} samples')
        print(f'Test set: {len(X_test)} samples')
        
        # Train model
        model, metrics = self.train_model(X_train, y_train, X_test, y_test)
        
        # Save model
        model_path = self.model_dir / 'salary_model.pkl'
        joblib.dump(model, model_path)
        print(f'\n✓ Model saved to {model_path}')
        
        # Store metrics
        self.metrics = metrics
        return metrics
    
    def save_metrics(self, output_path: str = None):
        """
        Save training metrics to JSON file.
        
        Args:
            output_path: Path to save metrics (default: model_dir/salary_metrics.json)
        """
        if output_path is None:
            output_path = self.model_dir / 'salary_metrics.json'
        
        # Convert numpy types to Python types for JSON serialization
        metrics_serializable = {
            key: float(value) for key, value in self.metrics.items()
        }
        
        with open(output_path, 'w') as f:
            json.dump(metrics_serializable, f, indent=2)
        
        print(f'✓ Metrics saved to {output_path}')


def main():
    """
    Main function to train salary model.
    """
    print('EduRisk AI - Salary Model Training')
    print('=' * 60)
    
    # Initialize trainer
    trainer = SalaryModelTrainer(
        data_path='ml/data/synthetic/students.csv',
        model_dir='ml/models',
        cv_folds=5,
        random_seed=42
    )
    
    # Train model
    metrics = trainer.train()
    
    # Save metrics
    trainer.save_metrics()
    
    print('\n' + '=' * 60)
    print('✓ Training complete!')
    print('=' * 60)
    print('\nSummary:')
    print(f'  - MAE: {metrics["mae"]:.2f} LPA')
    print(f'  - RMSE: {metrics["rmse"]:.2f} LPA')
    print(f'  - R²: {metrics["r2"]:.4f}')
    print(f'  - Residual Std: {metrics["std_residuals"]:.2f} LPA')


if __name__ == '__main__':
    main()
