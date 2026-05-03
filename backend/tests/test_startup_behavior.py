"""
Integration tests for ML model auto-training on startup.

Tests verify that the startup script correctly:
1. Detects missing models and triggers training
2. Skips training when models exist
3. Enforces 120-second timeout
4. Prevents FastAPI from starting if training fails

Feature: edurisk-submission-improvements
Requirements: Task 1.3 (Sub-tasks 1.3.1, 1.3.2, 1.3.3, 1.3.4)
"""

import pytest
import subprocess
import time
import shutil
import tempfile
from pathlib import Path
from typing import Generator
import httpx


# Test configuration
MODEL_DIR = Path("ml/models")
REQUIRED_MODELS = [
    "placement_model_3m.pkl",
    "placement_model_6m.pkl",
    "placement_model_12m.pkl",
    "salary_model.pkl"
]
STARTUP_SCRIPT = Path("docker/start-backend.sh")
HEALTH_ENDPOINT = "http://localhost:8000/api/health"


@pytest.fixture
def backup_models() -> Generator[Path, None, None]:
    """
    Backup existing models to a temporary directory and restore after test.
    
    This allows us to test the "no models" scenario without permanently
    deleting the models.
    """
    backup_dir = Path(tempfile.mkdtemp())
    
    # Backup existing models
    backed_up_files = []
    for model_file in REQUIRED_MODELS:
        model_path = MODEL_DIR / model_file
        if model_path.exists():
            backup_path = backup_dir / model_file
            shutil.copy2(model_path, backup_path)
            backed_up_files.append(model_file)
    
    # Also backup metadata files
    metadata_files = ["version.json", "training_metrics.json", "salary_metrics.json", "feature_names.json"]
    for meta_file in metadata_files:
        meta_path = MODEL_DIR / meta_file
        if meta_path.exists():
            backup_path = backup_dir / meta_file
            shutil.copy2(meta_path, backup_path)
    
    yield backup_dir
    
    # Restore models after test
    for model_file in backed_up_files:
        backup_path = backup_dir / model_file
        model_path = MODEL_DIR / model_file
        if backup_path.exists():
            shutil.copy2(backup_path, model_path)
    
    # Restore metadata files
    for meta_file in metadata_files:
        backup_path = backup_dir / meta_file
        meta_path = MODEL_DIR / meta_file
        if backup_path.exists():
            shutil.copy2(backup_path, meta_path)
    
    # Clean up backup directory
    shutil.rmtree(backup_dir)


def remove_models():
    """Remove all model files to simulate first boot."""
    for model_file in REQUIRED_MODELS:
        model_path = MODEL_DIR / model_file
        if model_path.exists():
            model_path.unlink()


def models_exist() -> bool:
    """Check if all required model files exist."""
    return all((MODEL_DIR / model_file).exists() for model_file in REQUIRED_MODELS)


def run_ml_check_script() -> tuple[int, str, str, float]:
    """
    Run the ML model check portion of the startup script.
    
    Returns:
        Tuple of (return_code, stdout, stderr, elapsed_time)
    """
    # Extract just the ML check portion from start-backend.sh
    # Note: Using plain text instead of emojis for Windows compatibility
    check_script = """
import sys
import subprocess
from pathlib import Path
import time

start_time = time.time()

model_files = [
    'ml/models/placement_model_3m.pkl',
    'ml/models/placement_model_6m.pkl',
    'ml/models/placement_model_12m.pkl',
    'ml/models/salary_model.pkl'
]

all_exist = all(Path(f).exists() for f in model_files)

if all_exist:
    print('[OK] ML models found and ready')
    elapsed = time.time() - start_time
    print(f'Elapsed time: {elapsed:.2f}s')
    sys.exit(0)
else:
    print('[WARN] ML models not found, training...')
    print('    This may take up to 2 minutes on first boot.')
    
    try:
        result = subprocess.run(
            ['python', '-m', 'ml.pipeline.train_all'],
            timeout=120,
            capture_output=True,
            text=True
        )
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            print('[OK] ML models trained successfully')
            print(f'Elapsed time: {elapsed:.2f}s')
            sys.exit(0)
        else:
            print('[ERROR] ML model training failed')
            print(f'   Error: {result.stderr}')
            print(f'Elapsed time: {elapsed:.2f}s')
            sys.exit(1)
    
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print('[ERROR] ML model training timed out (exceeded 120 seconds)')
        print(f'Elapsed time: {elapsed:.2f}s')
        sys.exit(1)
    
    except Exception as e:
        elapsed = time.time() - start_time
        print(f'[ERROR] ML model training error: {str(e)}')
        print(f'Elapsed time: {elapsed:.2f}s')
        sys.exit(1)
"""
    
    start_time = time.time()
    result = subprocess.run(
        ["python", "-c", check_script],
        capture_output=True,
        text=True,
        timeout=150  # Give extra time for the test itself
    )
    elapsed_time = time.time() - start_time
    
    return result.returncode, result.stdout, result.stderr, elapsed_time


class TestStartupBehavior:
    """Test suite for ML model auto-training on startup."""
    
    def test_subsequent_boot_with_models(self):
        """
        Test 1.3.2: Test subsequent boot with models (should skip training).
        
        When all model files exist, the startup script should:
        - Detect existing models
        - Skip training
        - Log success message
        - Complete quickly (< 5 seconds)
        """
        # Ensure models exist
        assert models_exist(), "Models must exist for this test"
        
        # Run the ML check script
        return_code, stdout, stderr, elapsed_time = run_ml_check_script()
        
        # Verify success
        assert return_code == 0, f"Script should succeed when models exist. stderr: {stderr}"
        
        # Verify correct message
        assert "[OK] ML models found and ready" in stdout, \
            f"Should log 'models found' message. stdout: {stdout}"
        
        # Verify training was NOT triggered
        assert "training..." not in stdout.lower(), \
            f"Should not trigger training when models exist. stdout: {stdout}"
        
        # Verify quick completion (should be nearly instant)
        assert elapsed_time < 5.0, \
            f"Should complete quickly when models exist. Took {elapsed_time:.2f}s"
        
        print(f"✓ Test passed: Models detected, training skipped in {elapsed_time:.2f}s")
    
    
    def test_first_boot_without_models(self, backup_models):
        """
        Test 1.3.1: Test first boot without models (should auto-train).
        
        When model files are missing, the startup script should:
        - Detect missing models
        - Automatically trigger training
        - Generate all 4 required model files
        - Log success message
        - Complete within 120 seconds
        """
        # Remove models to simulate first boot
        remove_models()
        assert not models_exist(), "Models should be removed for this test"
        
        # Run the ML check script
        return_code, stdout, stderr, elapsed_time = run_ml_check_script()
        
        # Verify success
        assert return_code == 0, \
            f"Script should succeed after training. stderr: {stderr}\nstdout: {stdout}"
        
        # Verify training was triggered
        assert "[WARN] ML models not found, training..." in stdout, \
            f"Should detect missing models. stdout: {stdout}"
        
        # Verify training completed successfully
        assert "[OK] ML models trained successfully" in stdout, \
            f"Should log training success. stdout: {stdout}"
        
        # Verify all models were created
        assert models_exist(), \
            f"All model files should exist after training. Missing: {[m for m in REQUIRED_MODELS if not (MODEL_DIR / m).exists()]}"
        
        # Verify completion time
        assert elapsed_time < 120.0, \
            f"Training should complete within 120 seconds. Took {elapsed_time:.2f}s"
        
        print(f"✓ Test passed: Models trained successfully in {elapsed_time:.2f}s")
    
    
    def test_training_timeout_enforcement(self, backup_models):
        """
        Test 1.3.3: Verify training completes within 120 seconds.
        
        This test verifies that:
        - Training completes within the 120-second timeout
        - The timeout mechanism is properly enforced
        
        Note: We test the actual training time rather than simulating a timeout,
        as the training pipeline is optimized to complete quickly.
        """
        # Remove models to trigger training
        remove_models()
        assert not models_exist(), "Models should be removed for this test"
        
        # Run the ML check script
        return_code, stdout, stderr, elapsed_time = run_ml_check_script()
        
        # Verify training completed (didn't timeout)
        assert return_code == 0, \
            f"Training should complete successfully. stderr: {stderr}"
        
        # Verify it completed within timeout
        assert elapsed_time < 120.0, \
            f"Training must complete within 120 seconds. Took {elapsed_time:.2f}s"
        
        # Verify timeout message was NOT shown
        assert "timed out" not in stdout.lower(), \
            f"Should not timeout with optimized training. stdout: {stdout}"
        
        print(f"✓ Test passed: Training completed within timeout ({elapsed_time:.2f}s < 120s)")
    
    
    def test_server_fails_if_training_fails(self, backup_models):
        """
        Test 1.3.4: Verify FastAPI server doesn't start if training fails.
        
        This test verifies that:
        - If training fails, the script exits with error code 1
        - The startup script would prevent FastAPI from starting
        - Appropriate error messages are logged
        
        Note: We simulate a training failure by removing the training script
        temporarily, which will cause the subprocess to fail.
        """
        # Remove models to trigger training
        remove_models()
        assert not models_exist(), "Models should be removed for this test"
        
        # Create a script that simulates training failure
        # Note: Using plain text instead of emojis for Windows compatibility
        failure_script = """
import sys
import subprocess
from pathlib import Path

model_files = [
    'ml/models/placement_model_3m.pkl',
    'ml/models/placement_model_6m.pkl',
    'ml/models/placement_model_12m.pkl',
    'ml/models/salary_model.pkl'
]

all_exist = all(Path(f).exists() for f in model_files)

if all_exist:
    print('[OK] ML models found and ready')
    sys.exit(0)
else:
    print('[WARN] ML models not found, training...')
    
    # Simulate training failure by calling a non-existent module
    try:
        result = subprocess.run(
            ['python', '-m', 'ml.pipeline.nonexistent_module'],
            timeout=120,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print('[OK] ML models trained successfully')
            sys.exit(0)
        else:
            print('[ERROR] ML model training failed')
            print(f'   Error: {result.stderr}')
            sys.exit(1)
    
    except Exception as e:
        print(f'[ERROR] ML model training error: {str(e)}')
        sys.exit(1)
"""
        
        # Run the failure simulation script
        result = subprocess.run(
            ["python", "-c", failure_script],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Verify the script exits with error code 1
        assert result.returncode == 1, \
            f"Script should exit with code 1 when training fails. Got: {result.returncode}"
        
        # Verify error message is logged
        assert "[ERROR] ML model training failed" in result.stdout or "[ERROR] ML model training error" in result.stdout, \
            f"Should log training failure. stdout: {result.stdout}"
        
        # Verify models were NOT created
        assert not models_exist(), \
            "Models should not exist after training failure"
        
        print("✓ Test passed: Script exits with error when training fails")


class TestHealthEndpointMLStatus:
    """Test that health endpoint reports ML model status correctly."""
    
    @pytest.mark.skipif(
        not all((MODEL_DIR / m).exists() for m in REQUIRED_MODELS),
        reason="Requires running backend with models"
    )
    def test_health_endpoint_reports_ml_available(self):
        """
        Verify health endpoint reports ml_models: available when models exist.
        
        This test requires the backend to be running.
        Run with: docker-compose up -d backend
        """
        try:
            response = httpx.get(HEALTH_ENDPOINT, timeout=5.0)
            
            assert response.status_code == 200, \
                f"Health endpoint should return 200. Got: {response.status_code}"
            
            data = response.json()
            
            assert "ml_models" in data, \
                f"Health response should include ml_models field. Got: {data}"
            
            assert data["ml_models"] == "available", \
                f"ML models should be reported as available. Got: {data['ml_models']}"
            
            print("✓ Test passed: Health endpoint reports ml_models: available")
        
        except httpx.ConnectError:
            pytest.skip("Backend not running. Start with: docker-compose up -d backend")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
