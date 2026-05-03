"""
Kaggle Dataset Integration for EduRisk AI

This module provides functions to load, validate, and merge Kaggle datasets
with synthetic training data.

Requirements: 25.1, 25.2, 25.3, 25.4, 25.5, 25.6
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Optional, Tuple, List

logger = logging.getLogger(__name__)


# Expected schema for Kaggle datasets (Requirement 25.2)
REQUIRED_COLUMNS = [
    'name', 'course_type', 'institute_tier', 'cgpa', 'year_of_grad',
    'loan_amount', 'loan_emi', 'placed_3m', 'placed_6m', 'placed_12m'
]

OPTIONAL_COLUMNS = [
    'institute_name', 'cgpa_scale', 'internship_count', 'internship_months',
    'internship_employer_type', 'certifications', 'region', 'salary_lpa'
]


def validate_kaggle_dataset(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate Kaggle dataset schema.
    
    Requirements: 25.3
    
    Args:
        df: DataFrame to validate
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    
    Examples:
        >>> df = pd.DataFrame({'name': ['Student1'], 'cgpa': [8.5], ...})
        >>> is_valid, errors = validate_kaggle_dataset(df)
        >>> assert is_valid == True
    """
    errors = []
    
    # Check required columns
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
    
    # Check data types for numeric columns
    numeric_cols = {
        'cgpa': 'float',
        'institute_tier': 'integer',
        'year_of_grad': 'integer',
        'loan_amount': 'float',
        'loan_emi': 'float',
        'placed_3m': 'integer',
        'placed_6m': 'integer',
        'placed_12m': 'integer'
    }
    
    for col, expected_type in numeric_cols.items():
        if col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                errors.append(f"Column '{col}' must be numeric ({expected_type})")
    
    # Check value ranges
    if 'cgpa' in df.columns:
        invalid_cgpa = df[(df['cgpa'] < 0) | (df['cgpa'] > 10)]
        if len(invalid_cgpa) > 0:
            errors.append(
                f"Column 'cgpa' must be between 0 and 10 "
                f"(found {len(invalid_cgpa)} invalid rows)"
            )
    
    if 'institute_tier' in df.columns:
        invalid_tier = df[~df['institute_tier'].isin([1, 2, 3])]
        if len(invalid_tier) > 0:
            errors.append(
                f"Column 'institute_tier' must be 1, 2, or 3 "
                f"(found {len(invalid_tier)} invalid rows)"
            )
    
    # Check placement labels are binary
    for col in ['placed_3m', 'placed_6m', 'placed_12m']:
        if col in df.columns:
            invalid_placement = df[~df[col].isin([0, 1])]
            if len(invalid_placement) > 0:
                errors.append(
                    f"Column '{col}' must be 0 or 1 "
                    f"(found {len(invalid_placement)} invalid rows)"
                )
    
    # Check logical consistency
    if all(col in df.columns for col in ['placed_3m', 'placed_6m', 'placed_12m']):
        # placed_6m should be >= placed_3m
        inconsistent_6m = df[df['placed_6m'] < df['placed_3m']]
        if len(inconsistent_6m) > 0:
            errors.append(
                f"Logical inconsistency: placed_6m < placed_3m "
                f"(found {len(inconsistent_6m)} rows)"
            )
        
        # placed_12m should be >= placed_6m
        inconsistent_12m = df[df['placed_12m'] < df['placed_6m']]
        if len(inconsistent_12m) > 0:
            errors.append(
                f"Logical inconsistency: placed_12m < placed_6m "
                f"(found {len(inconsistent_12m)} rows)"
            )
    
    is_valid = len(errors) == 0
    return is_valid, errors


def handle_missing_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add default values for missing optional columns.
    
    Requirements: 25.6
    
    Args:
        df: DataFrame with potentially missing columns
    
    Returns:
        DataFrame with all columns filled
    
    Examples:
        >>> df = pd.DataFrame({'name': ['Student1'], 'cgpa': [8.5]})
        >>> df = handle_missing_columns(df)
        >>> assert 'institute_name' in df.columns
        >>> assert df['institute_name'].iloc[0] == 'Unknown'
    """
    defaults = {
        'institute_name': 'Unknown',
        'cgpa_scale': 10.0,
        'internship_count': 0,
        'internship_months': 0,
        'internship_employer_type': None,
        'certifications': 0,
        'region': None,
        'salary_lpa': None
    }
    
    for col, default_value in defaults.items():
        if col not in df.columns:
            df[col] = default_value
            logger.info(f"Added missing column '{col}' with default value: {default_value}")
    
    return df


def load_kaggle_dataset(dataset_path: str) -> Optional[pd.DataFrame]:
    """
    Load Kaggle dataset from CSV file.
    
    Requirements: 25.1, 25.2
    
    Args:
        dataset_path: Path to Kaggle CSV file
    
    Returns:
        DataFrame if successful, None otherwise
    
    Examples:
        >>> df = load_kaggle_dataset('ml/data/kaggle/placement.csv')
        >>> if df is not None:
        ...     assert len(df) > 0
    """
    path = Path(dataset_path)
    
    if not path.exists():
        logger.warning(f"Kaggle dataset not found: {dataset_path}")
        return None
    
    try:
        df = pd.read_csv(path)
        logger.info(f"Loaded Kaggle dataset: {len(df)} rows from {dataset_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load Kaggle dataset: {e}")
        return None


def merge_datasets(
    synthetic_df: pd.DataFrame,
    kaggle_df: Optional[pd.DataFrame] = None
) -> Tuple[pd.DataFrame, str]:
    """
    Merge synthetic and Kaggle datasets.
    
    Requirements: 25.4, 25.5
    
    Args:
        synthetic_df: Synthetic training data
        kaggle_df: Optional Kaggle dataset
    
    Returns:
        Tuple of (merged_df, data_source)
        data_source is one of: "synthetic", "kaggle", "mixed"
    
    Examples:
        >>> synthetic = pd.DataFrame({'name': ['S1'], 'cgpa': [7.5], ...})
        >>> kaggle = pd.DataFrame({'name': ['K1'], 'cgpa': [8.5], ...})
        >>> merged, source = merge_datasets(synthetic, kaggle)
        >>> assert source == "mixed"
        >>> assert len(merged) == len(synthetic) + len(kaggle)
    """
    if kaggle_df is None or len(kaggle_df) == 0:
        logger.info("No Kaggle data provided, using synthetic data only")
        return synthetic_df, "synthetic"
    
    # Validate Kaggle dataset
    is_valid, errors = validate_kaggle_dataset(kaggle_df)
    if not is_valid:
        logger.error(f"Kaggle dataset validation failed: {errors}")
        logger.warning("Falling back to synthetic data only")
        return synthetic_df, "synthetic"
    
    # Handle missing columns
    kaggle_df = handle_missing_columns(kaggle_df)
    
    # Ensure column order matches
    # Get all columns from both dataframes
    all_columns = list(synthetic_df.columns)
    for col in kaggle_df.columns:
        if col not in all_columns:
            all_columns.append(col)
    
    # Reindex both dataframes to have same columns
    synthetic_df = synthetic_df.reindex(columns=all_columns)
    kaggle_df = kaggle_df.reindex(columns=all_columns)
    
    # Merge datasets
    merged_df = pd.concat([synthetic_df, kaggle_df], ignore_index=True)
    
    logger.info(
        f"Merged datasets: {len(synthetic_df)} synthetic + "
        f"{len(kaggle_df)} Kaggle = {len(merged_df)} total"
    )
    
    return merged_df, "mixed"


def get_data_source_info(
    synthetic_df: pd.DataFrame,
    kaggle_df: Optional[pd.DataFrame],
    merged_df: pd.DataFrame,
    data_source: str
) -> dict:
    """
    Generate data source information for training metrics.
    
    Requirements: 25.5
    
    Args:
        synthetic_df: Synthetic training data
        kaggle_df: Kaggle dataset (if used)
        merged_df: Merged dataset
        data_source: Data source type ("synthetic", "kaggle", "mixed")
    
    Returns:
        Dictionary with data source information
    
    Examples:
        >>> info = get_data_source_info(synthetic, kaggle, merged, "mixed")
        >>> assert info['data_source'] == "mixed"
        >>> assert info['n_total_records'] == len(merged)
    """
    info = {
        'data_source': data_source,
        'n_total_records': len(merged_df)
    }
    
    if data_source == "synthetic":
        info['n_synthetic_records'] = len(synthetic_df)
        info['n_kaggle_records'] = 0
    elif data_source == "kaggle":
        info['n_synthetic_records'] = 0
        info['n_kaggle_records'] = len(kaggle_df) if kaggle_df is not None else 0
    else:  # mixed
        info['n_synthetic_records'] = len(synthetic_df)
        info['n_kaggle_records'] = len(kaggle_df) if kaggle_df is not None else 0
    
    return info
