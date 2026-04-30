"""
Complete Model Training Pipeline for EduRisk AI

This script orchestrates training of all models (placement and salary)
and generates model version tracking metadata.

Feature: edurisk-ai-placement-intelligence
Requirements: 15.1, 15.2, 15.3
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict

from ml.pipeline.train import PlacementModelTrainer
from ml.pipeline.train_salary import SalaryModelTrainer


class ModelVersionTracker:
    """
    Tracks model versions and training metadata.
    
    Generates version.json with:
    - Semantic version
    - Training date
    - Model metrics
    """
    
    def __init__(self, model_dir: str = 'ml/models'):
        """
        Initialize version tracker.
        
        Args:
            model_dir: Directory containing models
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_version_metadata(
        self,
        placement_metrics: Dict[str, Dict],
        salary_metrics: Dict[str, float],
        version: str = '1.0.0'
    ) -> Dict:
        """
        Generate version metadata.
        
        Args:
            placement_metrics: Metrics from placement model training
            salary_metrics: Metrics from salary model training
            version: Semantic version string (default: '1.0.0')
            
        Returns:
            Dictionary with version metadata
        """
        metadata = {
            'version': version,
            'training_date': datetime.now().isoformat(),
            'models': {
                'placement_3m': {
                    'type': 'XGBoostClassifier',
                    'file': 'placement_model_3m.pkl',
                    'metrics': {
                        'auc_roc': placement_metrics['3m']['auc_roc'],
                        'f1': placement_metrics['3m']['f1'],
                        'precision': placement_metrics['3m']['precision'],
                        'recall': placement_metrics['3m']['recall']
                    }
                },
                'placement_6m': {
                    'type': 'XGBoostClassifier',
                    'file': 'placement_model_6m.pkl',
                    'metrics': {
                        'auc_roc': placement_metrics['6m']['auc_roc'],
                        'f1': placement_metrics['6m']['f1'],
                        'precision': placement_metrics['6m']['precision'],
                        'recall': placement_metrics['6m']['recall']
                    }
                },
                'placement_12m': {
                    'type': 'XGBoostClassifier',
                    'file': 'placement_model_12m.pkl',
                    'metrics': {
                        'auc_roc': placement_metrics['12m']['auc_roc'],
                        'f1': placement_metrics['12m']['f1'],
                        'precision': placement_metrics['12m']['precision'],
                        'recall': placement_metrics['12m']['recall']
                    }
                },
                'salary': {
                    'type': 'Ridge',
                    'file': 'salary_model.pkl',
                    'metrics': {
                        'mae': salary_metrics['mae'],
                        'rmse': salary_metrics['rmse'],
                        'r2': salary_metrics['r2']
                    }
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
                'cv_folds': 5,
                'random_seed': 42
            }
        }
        
        return metadata
    
    def save_version(self, metadata: Dict):
        """
        Save version metadata to version.json.
        
        Args:
            metadata: Version metadata dictionary
        """
        version_path = self.model_dir / 'version.json'
        
        with open(version_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f'\n✓ Version metadata saved to {version_path}')
        print(f'  - Version: {metadata["version"]}')
        print(f'  - Training Date: {metadata["training_date"]}')


def main():
    """
    Main function to train all models and generate version metadata.
    """
    print('=' * 70)
    print('EduRisk AI - Complete Model Training Pipeline')
    print('=' * 70)
    print()
    
    # Step 1: Train placement models
    print('STEP 1: Training Placement Models')
    print('-' * 70)
    placement_trainer = PlacementModelTrainer(
        data_path='ml/data/synthetic/students.csv',
        model_dir='ml/models',
        n_trials=20,  # Reduced from 50 for faster training
        cv_folds=3,   # Reduced from 5 for faster training
        random_seed=42
    )
    placement_metrics = placement_trainer.train_all_models()
    placement_trainer.save_metrics()
    
    print('\n' + '=' * 70)
    
    # Step 2: Train salary model
    print('\nSTEP 2: Training Salary Model')
    print('-' * 70)
    salary_trainer = SalaryModelTrainer(
        data_path='ml/data/synthetic/students.csv',
        model_dir='ml/models',
        cv_folds=3,  # Reduced from 5 for faster training
        random_seed=42
    )
    salary_metrics = salary_trainer.train()
    salary_trainer.save_metrics()
    
    print('\n' + '=' * 70)
    
    # Step 3: Generate version metadata
    print('\nSTEP 3: Generating Model Version Metadata')
    print('-' * 70)
    version_tracker = ModelVersionTracker(model_dir='ml/models')
    metadata = version_tracker.generate_version_metadata(
        placement_metrics=placement_metrics,
        salary_metrics=salary_metrics,
        version='1.0.0'
    )
    version_tracker.save_version(metadata)
    
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
    print('  - ml/models/salary_metrics.json')
    print('\n' + '=' * 70)


if __name__ == '__main__':
    main()
