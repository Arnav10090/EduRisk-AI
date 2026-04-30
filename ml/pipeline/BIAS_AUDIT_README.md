# Bias Audit Module

## Overview

The bias audit module provides post-hoc fairness testing for the EduRisk AI placement prediction models using Fairlearn. It computes demographic parity metrics to identify potential bias across demographic groups (gender and region).

## Requirements

- **Requirement 29.1**: Provides a bias audit script that runs Fairlearn demographic parity analysis
- **Requirement 29.2**: Computes accuracy and selection rate metrics grouped by gender and region
- **Requirement 29.3**: Computes demographic_parity_difference for gender groups
- **Requirement 29.4**: Generates a report showing metric disparities across groups
- **Requirement 29.5**: Flags models when demographic_parity_difference > 0.1
- **Requirement 29.6**: Saves reports as JSON files with timestamps in ml/reports/

## Installation

Install Fairlearn if not already installed:

```bash
pip install fairlearn
```

## Usage

### Running Bias Audit on All Models

```bash
python -m ml.pipeline.bias_audit
```

This will:
1. Load test data from `ml/data/synthetic/students.csv`
2. Generate synthetic demographic features (gender, region)
3. Load the trained placement model (3m by default)
4. Compute fairness metrics
5. Generate and save a bias audit report

### Running Comprehensive Tests

```bash
python -m ml.pipeline.test_bias_audit
```

This will:
1. Test bias threshold flagging logic
2. Run bias audits on all three placement models (3m, 6m, 12m)
3. Generate reports for each model
4. Display a summary of all audits

### Programmatic Usage

```python
from ml.pipeline.bias_audit import run_bias_audit, save_bias_report
import pandas as pd
import joblib

# Load model and data
model = joblib.load('ml/models/placement_model_3m.pkl')
X_test = ...  # Test features (WITHOUT demographic features)
y_test = ...  # True labels
sensitive_features = pd.DataFrame({
    'gender': [...],
    'region': [...]
})

# Run bias audit
report = run_bias_audit(
    model=model,
    X_test=X_test,
    y_test=y_test,
    sensitive_features=sensitive_features,
    model_name='placement_model_3m',
    bias_threshold=0.1
)

# Save report
save_bias_report(report, output_dir='ml/reports')

# Check if model is biased
if report.is_biased:
    print(f"⚠️  Model flagged as potentially biased!")
    print(f"Demographic Parity Difference: {report.demographic_parity_difference:.4f}")
```

## Metrics Computed

### Demographic Parity Difference (DPD)
- Measures the maximum difference in selection rates across demographic groups
- Formula: `max(selection_rate_group_i) - min(selection_rate_group_i)`
- Threshold: **0.1** (models with DPD > 0.1 are flagged as potentially biased)

### Equalized Odds Difference (EOD)
- Measures the maximum difference in error rates across demographic groups
- Considers both false positive and false negative rates

### Accuracy by Group
- Classification accuracy for each demographic group
- Helps identify if model performs differently across groups

### Selection Rate by Group
- Proportion of positive predictions for each demographic group
- Key metric for demographic parity

## Report Structure

Bias audit reports are saved as JSON files with the following structure:

```json
{
  "model_name": "placement_model_3m",
  "timestamp": "2026-05-01T02:47:10.775019",
  "demographic_parity_difference": 0.0131,
  "equalized_odds_difference": 0.0230,
  "metrics_by_gender": {
    "Female": {
      "accuracy": 0.7887,
      "selection_rate": 0.7680
    },
    "Male": {
      "accuracy": 0.7925,
      "selection_rate": 0.7549
    }
  },
  "metrics_by_region": {
    "Central": {
      "accuracy": 0.7750,
      "selection_rate": 0.7750
    },
    "East": {
      "accuracy": 0.8333,
      "selection_rate": 0.7533
    },
    ...
  },
  "bias_threshold": 0.1,
  "is_biased": false,
  "bias_flag": "PASSED"
}
```

## Interpreting Results

### ✓ PASSED
- Demographic parity difference ≤ 0.1
- Model shows acceptable fairness across demographic groups
- No immediate action required

### ⚠️ POTENTIALLY BIASED
- Demographic parity difference > 0.1
- Model may exhibit bias across demographic groups
- **Recommended Actions**:
  1. Review training data for representation imbalances
  2. Consider retraining with fairness constraints
  3. Adjust decision thresholds per group
  4. Consult with compliance team before deployment

## Important Notes

### Demographic Features Exclusion
- The EduRisk AI models **DO NOT** use demographic features (gender, religion, caste, state_of_origin) as model inputs
- Demographic features are only used for **post-hoc bias auditing**
- This ensures compliance with fair lending regulations (Requirement 16.1-16.5)

### Synthetic Demographic Data
- The current implementation uses synthetic demographic features for testing
- In production, actual demographic data should be collected separately and used only for auditing
- Demographic data should never be passed to the ML models during training or inference

### Bias Threshold
- The default threshold of 0.1 (10% difference) is based on industry standards
- Organizations may adjust this threshold based on their risk tolerance and regulatory requirements
- More stringent thresholds (e.g., 0.05) may be appropriate for high-stakes decisions

## Test Results

All three placement models (3m, 6m, 12m) have been tested and **PASSED** the bias audit:

| Model | DPD | EOD | Status |
|-------|-----|-----|--------|
| placement_model_3m | 0.0131 | 0.0230 | ✓ PASSED |
| placement_model_6m | 0.0179 | 0.1008 | ✓ PASSED |
| placement_model_12m | 0.0000 | 0.0000 | ✓ PASSED |

## References

- [Fairlearn Documentation](https://fairlearn.org/)
- [Demographic Parity](https://fairlearn.org/main/user_guide/fairness_in_machine_learning.html#demographic-parity)
- [Equalized Odds](https://fairlearn.org/main/user_guide/fairness_in_machine_learning.html#equalized-odds)
- [RBI Fair Lending Guidelines](https://www.rbi.org.in/)

## Support

For questions or issues with the bias audit module, please refer to:
- Design Document: `.kiro/specs/edurisk-ai-placement-intelligence/design.md`
- Requirements Document: `.kiro/specs/edurisk-ai-placement-intelligence/requirements.md`
- Task List: `.kiro/specs/edurisk-ai-placement-intelligence/tasks.md`
