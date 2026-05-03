"""
Tests for Kaggle Data Integration

Requirements: 25.1, 25.2, 25.3, 25.4, 25.5, 25.6
"""

import pytest
import pandas as pd
import tempfile
from pathlib import Path

from ml.data.kaggle_integration import (
    validate_kaggle_dataset,
    handle_missing_columns,
    load_kaggle_dataset,
    merge_datasets,
    get_data_source_info,
    REQUIRED_COLUMNS,
    OPTIONAL_COLUMNS
)


class TestValidateKaggleDataset:
    """Test schema validation for Kaggle datasets."""
    
    def test_valid_dataset(self):
        """Valid dataset should pass validation."""
        df = pd.DataFrame({
            'name': ['Student1', 'Student2'],
            'course_type': ['Engineering', 'MBA'],
            'institute_tier': [1, 2],
            'cgpa': [8.5, 7.2],
            'year_of_grad': [2024, 2025],
            'loan_amount': [15.0, 20.0],
            'loan_emi': [1.8, 2.4],
            'placed_3m': [1, 0],
            'placed_6m': [1, 0],
            'placed_12m': [1, 1]
        })
        
        is_valid, errors = validate_kaggle_dataset(df)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_missing_required_columns(self):
        """Dataset missing required columns should fail validation."""
        df = pd.DataFrame({
            'name': ['Student1'],
            'cgpa': [8.5]
            # Missing many required columns
        })
        
        is_valid, errors = validate_kaggle_dataset(df)
        assert is_valid is False
        assert any('Missing required columns' in err for err in errors)
    
    def test_invalid_cgpa_range(self):
        """CGPA outside 0-10 range should fail validation."""
        df = pd.DataFrame({
            'name': ['Student1', 'Student2'],
            'course_type': ['Engineering', 'MBA'],
            'institute_tier': [1, 2],
            'cgpa': [12.0, -1.0],  # Invalid values
            'year_of_grad': [2024, 2025],
            'loan_amount': [15.0, 20.0],
            'loan_emi': [1.8, 2.4],
            'placed_3m': [1, 0],
            'placed_6m': [1, 0],
            'placed_12m': [1, 1]
        })
        
        is_valid, errors = validate_kaggle_dataset(df)
        assert is_valid is False
        assert any('cgpa' in err and 'between 0 and 10' in err for err in errors)
    
    def test_invalid_institute_tier(self):
        """Institute tier not in [1, 2, 3] should fail validation."""
        df = pd.DataFrame({
            'name': ['Student1'],
            'course_type': ['Engineering'],
            'institute_tier': [5],  # Invalid tier
            'cgpa': [8.5],
            'year_of_grad': [2024],
            'loan_amount': [15.0],
            'loan_emi': [1.8],
            'placed_3m': [1],
            'placed_6m': [1],
            'placed_12m': [1]
        })
        
        is_valid, errors = validate_kaggle_dataset(df)
        assert is_valid is False
        assert any('institute_tier' in err and 'must be 1, 2, or 3' in err for err in errors)
    
    def test_invalid_placement_labels(self):
        """Placement labels not in [0, 1] should fail validation."""
        df = pd.DataFrame({
            'name': ['Student1'],
            'course_type': ['Engineering'],
            'institute_tier': [1],
            'cgpa': [8.5],
            'year_of_grad': [2024],
            'loan_amount': [15.0],
            'loan_emi': [1.8],
            'placed_3m': [2],  # Invalid value
            'placed_6m': [1],
            'placed_12m': [1]
        })
        
        is_valid, errors = validate_kaggle_dataset(df)
        assert is_valid is False
        assert any('placed_3m' in err and 'must be 0 or 1' in err for err in errors)
    
    def test_logical_inconsistency_placement(self):
        """Placement labels with logical inconsistency should fail validation."""
        df = pd.DataFrame({
            'name': ['Student1', 'Student2'],
            'course_type': ['Engineering', 'MBA'],
            'institute_tier': [1, 2],
            'cgpa': [8.5, 7.2],
            'year_of_grad': [2024, 2025],
            'loan_amount': [15.0, 20.0],
            'loan_emi': [1.8, 2.4],
            'placed_3m': [1, 0],
            'placed_6m': [0, 1],  # Student1: placed at 3m but not at 6m (inconsistent)
            'placed_12m': [1, 0]  # Student2: placed at 6m but not at 12m (inconsistent)
        })
        
        is_valid, errors = validate_kaggle_dataset(df)
        assert is_valid is False
        assert any('placed_6m < placed_3m' in err for err in errors)
        assert any('placed_12m < placed_6m' in err for err in errors)


class TestHandleMissingColumns:
    """Test handling of missing optional columns."""
    
    def test_add_missing_optional_columns(self):
        """Missing optional columns should be added with defaults."""
        df = pd.DataFrame({
            'name': ['Student1'],
            'cgpa': [8.5]
        })
        
        df = handle_missing_columns(df)
        
        # Check all optional columns are added
        assert 'institute_name' in df.columns
        assert 'cgpa_scale' in df.columns
        assert 'internship_count' in df.columns
        assert 'internship_months' in df.columns
        assert 'certifications' in df.columns
        
        # Check default values
        assert df['institute_name'].iloc[0] == 'Unknown'
        assert df['cgpa_scale'].iloc[0] == 10.0
        assert df['internship_count'].iloc[0] == 0
        assert df['internship_months'].iloc[0] == 0
        assert df['certifications'].iloc[0] == 0
    
    def test_preserve_existing_columns(self):
        """Existing columns should not be overwritten."""
        df = pd.DataFrame({
            'name': ['Student1'],
            'cgpa': [8.5],
            'institute_name': ['IIT Delhi'],
            'internship_count': [3]
        })
        
        df = handle_missing_columns(df)
        
        # Existing values should be preserved
        assert df['institute_name'].iloc[0] == 'IIT Delhi'
        assert df['internship_count'].iloc[0] == 3
        
        # Missing columns should be added
        assert 'cgpa_scale' in df.columns
        assert df['cgpa_scale'].iloc[0] == 10.0


class TestLoadKaggleDataset:
    """Test loading Kaggle datasets from CSV files."""
    
    def test_load_existing_csv(self):
        """Should successfully load existing CSV file."""
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('name,cgpa\n')
            f.write('Student1,8.5\n')
            f.write('Student2,7.2\n')
            temp_path = f.name
        
        try:
            df = load_kaggle_dataset(temp_path)
            assert df is not None
            assert len(df) == 2
            assert 'name' in df.columns
            assert 'cgpa' in df.columns
        finally:
            Path(temp_path).unlink()
    
    def test_load_nonexistent_csv(self):
        """Should return None for nonexistent file."""
        df = load_kaggle_dataset('nonexistent_file.csv')
        assert df is None


class TestMergeDatasets:
    """Test merging synthetic and Kaggle datasets."""
    
    def test_merge_with_no_kaggle_data(self):
        """Should return synthetic data only when no Kaggle data provided."""
        synthetic_df = pd.DataFrame({
            'name': ['S1', 'S2'],
            'cgpa': [7.5, 8.0]
        })
        
        merged_df, data_source = merge_datasets(synthetic_df, None)
        
        assert data_source == "synthetic"
        assert len(merged_df) == 2
        assert merged_df.equals(synthetic_df)
    
    def test_merge_with_valid_kaggle_data(self):
        """Should merge synthetic and Kaggle data when both valid."""
        synthetic_df = pd.DataFrame({
            'name': ['S1'],
            'course_type': ['Engineering'],
            'institute_tier': [2],
            'cgpa': [7.5],
            'year_of_grad': [2024],
            'loan_amount': [15.0],
            'loan_emi': [1.8],
            'placed_3m': [1],
            'placed_6m': [1],
            'placed_12m': [1]
        })
        
        kaggle_df = pd.DataFrame({
            'name': ['K1'],
            'course_type': ['MBA'],
            'institute_tier': [1],
            'cgpa': [8.5],
            'year_of_grad': [2025],
            'loan_amount': [20.0],
            'loan_emi': [2.4],
            'placed_3m': [1],
            'placed_6m': [1],
            'placed_12m': [1]
        })
        
        merged_df, data_source = merge_datasets(synthetic_df, kaggle_df)
        
        assert data_source == "mixed"
        assert len(merged_df) == 2
        assert 'S1' in merged_df['name'].values
        assert 'K1' in merged_df['name'].values
    
    def test_merge_with_invalid_kaggle_data(self):
        """Should fall back to synthetic data when Kaggle data is invalid."""
        synthetic_df = pd.DataFrame({
            'name': ['S1'],
            'course_type': ['Engineering'],
            'institute_tier': [2],
            'cgpa': [7.5],
            'year_of_grad': [2024],
            'loan_amount': [15.0],
            'loan_emi': [1.8],
            'placed_3m': [1],
            'placed_6m': [1],
            'placed_12m': [1]
        })
        
        # Invalid Kaggle data (missing required columns)
        kaggle_df = pd.DataFrame({
            'name': ['K1'],
            'cgpa': [8.5]
        })
        
        merged_df, data_source = merge_datasets(synthetic_df, kaggle_df)
        
        assert data_source == "synthetic"
        assert len(merged_df) == 1
        assert merged_df.equals(synthetic_df)


class TestGetDataSourceInfo:
    """Test data source information generation."""
    
    def test_synthetic_only(self):
        """Should generate correct info for synthetic-only data."""
        synthetic_df = pd.DataFrame({'name': ['S1', 'S2']})
        merged_df = synthetic_df.copy()
        
        info = get_data_source_info(synthetic_df, None, merged_df, "synthetic")
        
        assert info['data_source'] == "synthetic"
        assert info['n_synthetic_records'] == 2
        assert info['n_kaggle_records'] == 0
        assert info['n_total_records'] == 2
    
    def test_mixed_data(self):
        """Should generate correct info for mixed data."""
        synthetic_df = pd.DataFrame({'name': ['S1', 'S2', 'S3']})
        kaggle_df = pd.DataFrame({'name': ['K1', 'K2']})
        merged_df = pd.concat([synthetic_df, kaggle_df], ignore_index=True)
        
        info = get_data_source_info(synthetic_df, kaggle_df, merged_df, "mixed")
        
        assert info['data_source'] == "mixed"
        assert info['n_synthetic_records'] == 3
        assert info['n_kaggle_records'] == 2
        assert info['n_total_records'] == 5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
