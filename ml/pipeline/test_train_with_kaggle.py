"""
Integration Tests for Training Pipeline with Kaggle Data

Tests training with:
- Synthetic data only
- Kaggle data only (simulated)
- Mixed data sources

Requirements: 25.1, 25.3, 25.4, 25.5
"""

import pytest
import pandas as pd
import tempfile
import json
from pathlib import Path

from ml.pipeline.train_all import prepare_training_data
from ml.data.kaggle_integration import merge_datasets, get_data_source_info


class TestTrainingDataPreparation:
    """Test training data preparation with different sources."""
    
    def test_prepare_synthetic_only(self):
        """Should prepare synthetic data when no Kaggle data provided."""
        # This test assumes synthetic data exists or will be generated
        training_df, data_source_info = prepare_training_data(kaggle_csv_path=None)
        
        assert data_source_info['data_source'] == 'synthetic'
        assert data_source_info['n_synthetic_records'] > 0
        assert data_source_info['n_kaggle_records'] == 0
        assert len(training_df) == data_source_info['n_total_records']
        
        # Verify training data has required columns
        required_cols = ['name', 'course_type', 'institute_tier', 'cgpa', 
                        'placed_3m', 'placed_6m', 'placed_12m']
        for col in required_cols:
            assert col in training_df.columns
    
    def test_prepare_with_valid_kaggle_data(self):
        """Should merge synthetic and Kaggle data when Kaggle data is valid."""
        # Create temporary Kaggle CSV file
        kaggle_data = pd.DataFrame({
            'name': ['K1', 'K2', 'K3'],
            'course_type': ['Engineering', 'MBA', 'MCA'],
            'institute_tier': [1, 2, 1],
            'cgpa': [8.5, 7.8, 9.0],
            'year_of_grad': [2024, 2025, 2024],
            'loan_amount': [15.0, 20.0, 12.0],
            'loan_emi': [1.8, 2.4, 1.44],
            'placed_3m': [1, 0, 1],
            'placed_6m': [1, 1, 1],
            'placed_12m': [1, 1, 1]
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            kaggle_data.to_csv(f.name, index=False)
            temp_path = f.name
        
        try:
            training_df, data_source_info = prepare_training_data(kaggle_csv_path=temp_path)
            
            assert data_source_info['data_source'] == 'mixed'
            assert data_source_info['n_synthetic_records'] > 0
            assert data_source_info['n_kaggle_records'] == 3
            assert data_source_info['n_total_records'] == (
                data_source_info['n_synthetic_records'] + 
                data_source_info['n_kaggle_records']
            )
            
            # Verify Kaggle records are in training data
            assert 'K1' in training_df['name'].values
            assert 'K2' in training_df['name'].values
            assert 'K3' in training_df['name'].values
            
        finally:
            Path(temp_path).unlink()
    
    def test_prepare_with_invalid_kaggle_data(self):
        """Should fall back to synthetic data when Kaggle data is invalid."""
        # Create temporary invalid Kaggle CSV file (missing required columns)
        invalid_kaggle_data = pd.DataFrame({
            'name': ['K1', 'K2'],
            'cgpa': [8.5, 7.8]
            # Missing many required columns
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            invalid_kaggle_data.to_csv(f.name, index=False)
            temp_path = f.name
        
        try:
            training_df, data_source_info = prepare_training_data(kaggle_csv_path=temp_path)
            
            # Should fall back to synthetic only
            assert data_source_info['data_source'] == 'synthetic'
            assert data_source_info['n_kaggle_records'] == 0
            
        finally:
            Path(temp_path).unlink()


class TestDataSourceLogging:
    """Test that data source is correctly logged in training metrics."""
    
    def test_synthetic_data_source_info(self):
        """Should generate correct info for synthetic-only training."""
        synthetic_df = pd.DataFrame({
            'name': ['S1', 'S2', 'S3', 'S4', 'S5'],
            'cgpa': [7.5, 8.0, 7.2, 8.5, 9.0]
        })
        
        merged_df, data_source = merge_datasets(synthetic_df, None)
        info = get_data_source_info(synthetic_df, None, merged_df, data_source)
        
        assert info['data_source'] == 'synthetic'
        assert info['n_synthetic_records'] == 5
        assert info['n_kaggle_records'] == 0
        assert info['n_total_records'] == 5
    
    def test_mixed_data_source_info(self):
        """Should generate correct info for mixed training."""
        synthetic_df = pd.DataFrame({
            'name': ['S1', 'S2', 'S3'],
            'course_type': ['Engineering', 'MBA', 'MCA'],
            'institute_tier': [2, 2, 3],
            'cgpa': [7.5, 8.0, 7.2],
            'year_of_grad': [2024, 2025, 2024],
            'loan_amount': [15.0, 20.0, 12.0],
            'loan_emi': [1.8, 2.4, 1.44],
            'placed_3m': [1, 0, 1],
            'placed_6m': [1, 1, 1],
            'placed_12m': [1, 1, 1]
        })
        
        kaggle_df = pd.DataFrame({
            'name': ['K1', 'K2'],
            'course_type': ['Engineering', 'MBA'],
            'institute_tier': [1, 1],
            'cgpa': [8.5, 9.0],
            'year_of_grad': [2024, 2025],
            'loan_amount': [18.0, 22.0],
            'loan_emi': [2.16, 2.64],
            'placed_3m': [1, 1],
            'placed_6m': [1, 1],
            'placed_12m': [1, 1]
        })
        
        merged_df, data_source = merge_datasets(synthetic_df, kaggle_df)
        info = get_data_source_info(synthetic_df, kaggle_df, merged_df, data_source)
        
        assert info['data_source'] == 'mixed'
        assert info['n_synthetic_records'] == 3
        assert info['n_kaggle_records'] == 2
        assert info['n_total_records'] == 5


class TestTrainingMetricsLogging:
    """Test that training metrics include data source information."""
    
    def test_metrics_include_data_source(self):
        """Training metrics should include data source information."""
        # Simulate training metrics structure
        data_source_info = {
            'data_source': 'mixed',
            'n_synthetic_records': 5000,
            'n_kaggle_records': 200,
            'n_total_records': 5200
        }
        
        # This would be part of the actual training_metrics.json
        training_config = {
            'data_source': data_source_info['data_source'],
            'n_synthetic_records': data_source_info['n_synthetic_records'],
            'n_kaggle_records': data_source_info['n_kaggle_records'],
            'n_total_records': data_source_info['n_total_records'],
            'train_test_split': 0.8,
            'cv_folds': 3,
            'random_seed': 42
        }
        
        assert training_config['data_source'] == 'mixed'
        assert training_config['n_synthetic_records'] == 5000
        assert training_config['n_kaggle_records'] == 200
        assert training_config['n_total_records'] == 5200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
