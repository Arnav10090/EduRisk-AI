# EduRisk AI Test Suite

This directory contains integration and unit tests for the EduRisk AI backend.

## Test Structure

```
backend/tests/
├── __init__.py
├── README.md (this file)
└── test_startup_behavior.py  # Task 1.3: ML model auto-training tests
```

## Running Tests

### Prerequisites

Ensure you have pytest installed:
```bash
pip install pytest pytest-asyncio pytest-cov
```

### Run All Tests

```bash
# From project root
python -m pytest backend/tests/ -v

# With coverage report
python -m pytest backend/tests/ --cov=backend --cov=ml --cov-report=html
```

### Run Specific Test File

```bash
python -m pytest backend/tests/test_startup_behavior.py -v
```

### Run Specific Test

```bash
python -m pytest backend/tests/test_startup_behavior.py::TestStartupBehavior::test_subsequent_boot_with_models -v
```

## Test Categories

### Integration Tests

#### test_startup_behavior.py

Tests for ML model auto-training on startup (Task 1.3):

- **test_subsequent_boot_with_models** (Sub-task 1.3.2)
  - Verifies that when models exist, training is skipped
  - Checks for correct log messages
  - Ensures quick completion (< 5 seconds)

- **test_first_boot_without_models** (Sub-task 1.3.1)
  - Simulates first boot by removing models
  - Verifies automatic training is triggered
  - Confirms all 4 model files are created
  - Validates completion within 120 seconds

- **test_training_timeout_enforcement** (Sub-task 1.3.3)
  - Verifies training completes within 120-second timeout
  - Ensures timeout mechanism is properly enforced

- **test_server_fails_if_training_fails** (Sub-task 1.3.4)
  - Simulates training failure
  - Verifies script exits with error code 1
  - Confirms FastAPI server would not start

- **test_health_endpoint_reports_ml_available**
  - Requires running backend server
  - Verifies health endpoint reports ml_models: available
  - Skipped if backend is not running

## Test Fixtures

### backup_models

Backs up existing ML models before tests and restores them after. This allows testing the "no models" scenario without permanently deleting models.

Usage:
```python
def test_something(backup_models):
    # Models are backed up
    remove_models()  # Safe to remove
    # ... test logic ...
    # Models are automatically restored after test
```

## Test Output

Tests use descriptive output with status indicators:

```
✓ Test passed: Models detected, training skipped in 0.07s
✓ Test passed: Models trained successfully in 22.26s
✓ Test passed: Training completed within timeout (21.81s < 120s)
✓ Test passed: Script exits with error when training fails
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    python -m pytest backend/tests/ -v --tb=short
```

## Troubleshooting

### Models Not Found

If tests fail with "Models not found", ensure you're running from the project root directory where `ml/models/` exists.

### Timeout Issues

If training timeout tests fail, the ML training pipeline may need optimization. The current implementation completes in ~20-25 seconds.

### Windows Encoding Issues

Tests use plain text log messages (e.g., `[OK]`, `[WARN]`, `[ERROR]`) instead of emoji characters to ensure Windows compatibility.

## Adding New Tests

When adding new tests:

1. Follow the existing naming convention: `test_<feature>_<scenario>`
2. Add docstrings explaining what the test verifies
3. Use descriptive assertion messages
4. Clean up any test artifacts (temporary files, etc.)
5. Update this README with test descriptions

## Related Documentation

- [Requirements Document](../../.kiro/specs/edurisk-submission-improvements/requirements.md)
- [Design Document](../../.kiro/specs/edurisk-submission-improvements/design.md)
- [Tasks Document](../../.kiro/specs/edurisk-submission-improvements/tasks.md)
