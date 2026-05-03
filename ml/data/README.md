# Kaggle Data Integration Guide

## Overview

EduRisk AI supports training ML models with real-world Kaggle datasets alongside synthetic data. This document describes the expected dataset schemas, required columns, and integration process.

## Expected Dataset Schema

### Required Columns

The following columns are **required** in any Kaggle dataset used for training:

| Column Name | Data Type | Description | Valid Range/Values |
|------------|-----------|-------------|-------------------|
| `name` | string | Student name or identifier | Any non-empty string |
| `course_type` | string | Type of course | Engineering, MBA, MCA, MSc |
| `institute_tier` | integer | Institute tier ranking | 1 (top tier), 2 (mid tier), 3 (lower tier) |
| `cgpa` | float | Cumulative GPA | 0.0 to 10.0 |
| `year_of_grad` | integer | Year of graduation | 2020-2030 |
| `loan_amount` | float | Loan amount in lakhs (₹) | > 0 |
| `loan_emi` | float | Monthly EMI in thousands (₹) | > 0 |
| `placed_3m` | integer | Placed within 3 months | 0 (not placed) or 1 (placed) |
| `placed_6m` | integer | Placed within 6 months | 0 or 1 |
| `placed_12m` | integer | Placed within 12 months | 0 or 1 |

### Optional Columns

The following columns are **optional** and will be filled with defaults if missing:

| Column Name | Data Type | Description | Default Value |
|------------|-----------|-------------|---------------|
| `institute_name` | string | Name of institute | "Unknown" |
| `cgpa_scale` | float | CGPA scale (e.g., 10.0, 4.0) | 10.0 |
| `internship_count` | integer | Number of internships completed | 0 |
| `internship_months` | integer | Total months of internship experience | 0 |
| `internship_employer_type` | string | Type of internship employer | None |
| `certifications` | integer | Number of certifications | 0 |
| `region` | string | Geographic region | None |
| `salary_lpa` | float | Salary in lakhs per annum (LPA) | None |

## Data Validation

The integration pipeline validates:

1. **Required columns present**: All required columns must exist in the CSV
2. **Data types**: Numeric columns must contain valid numbers
3. **Value ranges**: 
   - CGPA must be between 0 and 10
   - Institute tier must be 1, 2, or 3
   - Placement labels must be 0 or 1
4. **Logical consistency**: 
   - `placed_6m >= placed_3m` (if placed at 3m, must be placed at 6m)
   - `placed_12m >= placed_6m` (if placed at 6m, must be placed at 12m)

## Example Kaggle Datasets

The following Kaggle datasets are compatible with EduRisk AI (after appropriate column mapping):

### 1. Campus Placement Data
- **Dataset**: [Campus Recruitment](https://www.kaggle.com/datasets/benroshan/factors-affecting-campus-placement)
- **Size**: ~200 records
- **Columns to map**:
  - `degree_t` → `course_type`
  - `ssc_p` + `hsc_p` → derive `cgpa`
  - `status` → `placed_3m`, `placed_6m`, `placed_12m`
  - `salary` → `salary_lpa`

### 2. Engineering Students Placement
- **Dataset**: [Engineering Students Placement](https://www.kaggle.com/datasets/tejashvi14/engineering-placements-prediction)
- **Size**: ~500 records
- **Columns to map**:
  - `Stream` → `course_type`
  - `CGPA` → `cgpa`
  - `PlacedOrNot` → `placed_3m`, `placed_6m`, `placed_12m`

### 3. Student Performance and Placement
- **Dataset**: [Student Performance](https://www.kaggle.com/datasets/ahsan81/student-performance-data-set)
- **Size**: ~1000 records
- **Columns to map**:
  - `Course` → `course_type`
  - `GPA` → `cgpa`
  - Add synthetic placement labels based on GPA thresholds

## Using Kaggle Data

### Step 1: Download Dataset

Use the provided download script:

```bash
# Install Kaggle API
pip install kaggle

# Configure Kaggle credentials (one-time setup)
# Download kaggle.json from https://www.kaggle.com/settings
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json

# Download a dataset
python ml/data/download_kaggle.py <dataset-name>

# Example:
python ml/data/download_kaggle.py benroshan/factors-affecting-campus-placement
```

### Step 2: Prepare CSV File

Ensure your CSV file has the required columns. You may need to:

1. **Rename columns** to match the expected schema
2. **Map categorical values** (e.g., "B.Tech" → "Engineering")
3. **Derive missing columns** (e.g., calculate CGPA from percentage)
4. **Add placement labels** if not present

Example preprocessing script:

```python
import pandas as pd

# Load Kaggle dataset
df = pd.read_csv('ml/data/kaggle/placement_data.csv')

# Rename columns
df = df.rename(columns={
    'degree_t': 'course_type',
    'status': 'placed_3m'
})

# Map course types
course_mapping = {
    'Sci&Tech': 'Engineering',
    'Comm&Mgmt': 'MBA'
}
df['course_type'] = df['course_type'].map(course_mapping)

# Derive CGPA from percentage (assuming 10-point scale)
df['cgpa'] = df['ssc_p'] / 10.0

# Add missing placement windows (assume same as 3m)
df['placed_6m'] = df['placed_3m']
df['placed_12m'] = df['placed_3m']

# Add required columns with defaults
df['institute_tier'] = 2  # Default to tier 2
df['year_of_grad'] = 2024
df['loan_amount'] = 15.0  # Default 15 lakhs
df['loan_emi'] = 15.0 * 0.012  # 1.2% monthly EMI

# Save preprocessed file
df.to_csv('ml/data/kaggle/preprocessed_placement.csv', index=False)
```

### Step 3: Train with Kaggle Data

Modify `ml/pipeline/train_all.py` to use Kaggle data:

```python
from ml.data.kaggle_integration import load_kaggle_dataset, merge_datasets

# Load synthetic data
synthetic_df = pd.read_csv('ml/data/synthetic/students.csv')

# Load Kaggle data (optional)
kaggle_df = load_kaggle_dataset('ml/data/kaggle/preprocessed_placement.csv')

# Merge datasets
training_data = merge_datasets(synthetic_df, kaggle_df)

# Train models with merged data
# ... (rest of training pipeline)
```

## Data Source Tracking

The training pipeline logs the data source in `training_metrics.json`:

```json
{
  "training_config": {
    "data_source": "mixed",  // "synthetic", "kaggle", or "mixed"
    "n_synthetic_records": 5000,
    "n_kaggle_records": 200,
    "n_total_records": 5200
  }
}
```

## Troubleshooting

### Issue: Missing Required Columns

**Error**: `Missing required columns: {'cgpa', 'institute_tier'}`

**Solution**: Add the missing columns to your CSV file or derive them from existing columns.

### Issue: Invalid Data Types

**Error**: `Column 'cgpa' must be numeric`

**Solution**: Convert the column to numeric type:
```python
df['cgpa'] = pd.to_numeric(df['cgpa'], errors='coerce')
df = df.dropna(subset=['cgpa'])  # Remove rows with invalid CGPA
```

### Issue: Value Out of Range

**Error**: `Column 'cgpa' must be between 0 and 10`

**Solution**: Normalize CGPA to 10-point scale:
```python
# If CGPA is on 4.0 scale
df['cgpa'] = (df['cgpa'] / 4.0) * 10.0

# If CGPA is percentage
df['cgpa'] = df['cgpa'] / 10.0
```

### Issue: Kaggle API Authentication Failed

**Error**: `Unauthorized: you must download an API key`

**Solution**: 
1. Go to https://www.kaggle.com/settings
2. Scroll to "API" section
3. Click "Create New API Token"
4. Move downloaded `kaggle.json` to `~/.kaggle/`
5. Set permissions: `chmod 600 ~/.kaggle/kaggle.json`

## Best Practices

1. **Always validate** Kaggle data before training to catch schema issues early
2. **Keep synthetic data** as a baseline - merge with Kaggle data rather than replacing
3. **Document preprocessing** steps for reproducibility
4. **Version control** preprocessed datasets separately from raw downloads
5. **Monitor metrics** - compare model performance with synthetic vs. mixed data
6. **Start small** - test with a small Kaggle dataset before scaling up

## Schema Version

- **Version**: 1.0.0
- **Last Updated**: 2024
- **Compatible with**: EduRisk AI v1.0.0+

## Support

For questions or issues with Kaggle data integration:
- Check validation errors in training logs
- Review example datasets above
- Ensure all required columns are present with correct data types
