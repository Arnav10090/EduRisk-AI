"""
Kaggle Dataset Download Script for EduRisk AI

This script automates downloading Kaggle datasets using the Kaggle API,
with schema validation and preprocessing support.

Requirements: 25.1, 25.2, 25.3, 25.6, 25.7
"""

import os
import sys
from pathlib import Path
from typing import Optional
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
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


def validate_kaggle_dataset(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """
    Validate Kaggle dataset schema.
    
    Requirements: 25.3
    
    Args:
        df: DataFrame to validate
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required columns
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
    
    # Check data types for numeric columns
    numeric_cols = ['cgpa', 'institute_tier', 'year_of_grad', 'loan_amount', 
                    'loan_emi', 'placed_3m', 'placed_6m', 'placed_12m']
    
    for col in numeric_cols:
        if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
            errors.append(f"Column '{col}' must be numeric")
    
    # Check value ranges
    if 'cgpa' in df.columns:
        invalid_cgpa = df[(df['cgpa'] < 0) | (df['cgpa'] > 10)]
        if len(invalid_cgpa) > 0:
            errors.append(f"Column 'cgpa' must be between 0 and 10 (found {len(invalid_cgpa)} invalid rows)")
    
    if 'institute_tier' in df.columns:
        invalid_tier = df[~df['institute_tier'].isin([1, 2, 3])]
        if len(invalid_tier) > 0:
            errors.append(f"Column 'institute_tier' must be 1, 2, or 3 (found {len(invalid_tier)} invalid rows)")
    
    # Check placement labels are binary
    for col in ['placed_3m', 'placed_6m', 'placed_12m']:
        if col in df.columns:
            invalid_placement = df[~df[col].isin([0, 1])]
            if len(invalid_placement) > 0:
                errors.append(f"Column '{col}' must be 0 or 1 (found {len(invalid_placement)} invalid rows)")
    
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


def download_kaggle_dataset(
    dataset_name: str,
    output_dir: str = "ml/data/kaggle"
) -> Optional[str]:
    """
    Download dataset from Kaggle using Kaggle API.
    
    Requirements: 25.7
    
    Prerequisites:
    - Install kaggle package: pip install kaggle
    - Configure Kaggle API credentials: ~/.kaggle/kaggle.json
    
    Args:
        dataset_name: Kaggle dataset identifier (e.g., "username/dataset-name")
        output_dir: Directory to save downloaded files
    
    Returns:
        Path to downloaded directory, or None if failed
    """
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError:
        logger.error("❌ Kaggle package not installed. Run: pip install kaggle")
        return None
    
    try:
        # Initialize Kaggle API
        api = KaggleApi()
        api.authenticate()
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Download dataset
        logger.info(f"Downloading {dataset_name} to {output_dir}...")
        api.dataset_download_files(dataset_name, path=output_dir, unzip=True)
        
        logger.info(f"✅ Dataset downloaded to {output_dir}")
        return output_dir
        
    except Exception as e:
        logger.error(f"❌ Failed to download dataset: {e}")
        return None


def validate_csv_file(csv_path: str) -> bool:
    """
    Validate a CSV file against the expected schema.
    
    Requirements: 25.3
    
    Args:
        csv_path: Path to CSV file
    
    Returns:
        True if valid, False otherwise
    """
    try:
        logger.info(f"Validating {csv_path}...")
        df = pd.read_csv(csv_path)
        
        logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        logger.info(f"Columns: {list(df.columns)}")
        
        # Validate schema
        is_valid, errors = validate_kaggle_dataset(df)
        
        if is_valid:
            logger.info("✅ Schema validation passed")
            
            # Handle missing optional columns
            df = handle_missing_columns(df)
            
            # Save validated file
            validated_path = csv_path.replace('.csv', '_validated.csv')
            df.to_csv(validated_path, index=False)
            logger.info(f"✅ Saved validated file to {validated_path}")
            
            return True
        else:
            logger.error("❌ Schema validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to validate CSV: {e}")
        return False


def main():
    """
    Main function to download and validate Kaggle datasets.
    """
    if len(sys.argv) < 2:
        print("=" * 70)
        print("Kaggle Dataset Download Script for EduRisk AI")
        print("=" * 70)
        print()
        print("Usage:")
        print("  python ml/data/download_kaggle.py <dataset-name> [csv-file]")
        print()
        print("Examples:")
        print("  # Download dataset")
        print("  python ml/data/download_kaggle.py benroshan/factors-affecting-campus-placement")
        print()
        print("  # Validate existing CSV")
        print("  python ml/data/download_kaggle.py validate ml/data/kaggle/placement.csv")
        print()
        print("Prerequisites:")
        print("  1. Install Kaggle API: pip install kaggle")
        print("  2. Download API key from https://www.kaggle.com/settings")
        print("  3. Place kaggle.json in ~/.kaggle/")
        print("  4. Set permissions: chmod 600 ~/.kaggle/kaggle.json")
        print()
        print("=" * 70)
        sys.exit(1)
    
    command = sys.argv[1]
    
    # Validate existing CSV file
    if command == "validate":
        if len(sys.argv) < 3:
            logger.error("Please provide CSV file path")
            sys.exit(1)
        
        csv_path = sys.argv[2]
        if not Path(csv_path).exists():
            logger.error(f"File not found: {csv_path}")
            sys.exit(1)
        
        success = validate_csv_file(csv_path)
        sys.exit(0 if success else 1)
    
    # Download dataset
    dataset_name = command
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "ml/data/kaggle"
    
    # Download
    result = download_kaggle_dataset(dataset_name, output_dir)
    
    if result is None:
        sys.exit(1)
    
    # Find CSV files in downloaded directory
    csv_files = list(Path(output_dir).glob("*.csv"))
    
    if not csv_files:
        logger.warning("⚠️ No CSV files found in downloaded dataset")
        sys.exit(0)
    
    logger.info(f"Found {len(csv_files)} CSV file(s)")
    
    # Validate each CSV file
    all_valid = True
    for csv_file in csv_files:
        logger.info(f"\nValidating {csv_file.name}...")
        if not validate_csv_file(str(csv_file)):
            all_valid = False
    
    if all_valid:
        logger.info("\n✅ All CSV files validated successfully")
        logger.info("\nNext steps:")
        logger.info("  1. Review validated CSV files (*_validated.csv)")
        logger.info("  2. Preprocess if needed (see ml/data/README.md)")
        logger.info("  3. Update ml/pipeline/train_all.py to use Kaggle data")
    else:
        logger.warning("\n⚠️ Some CSV files failed validation")
        logger.info("See ml/data/README.md for preprocessing guidance")
    
    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()
