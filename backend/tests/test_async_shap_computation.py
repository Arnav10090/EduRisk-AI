"""
Test async SHAP computation for batch requests.

Tests that SHAP values are computed asynchronously in background tasks
to avoid timeouts with large batches.

Feature: edurisk-ai-placement-intelligence
Requirements: 27.1, 27.2, 27.3, 27.4, 27.5, 27.6, 27.7
"""

import pytest
import asyncio
import time
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from backend.main import app
from backend.db.session import get_db
from backend.models.prediction import Prediction
from sqlalchemy import select


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """
    Get authentication headers for test requests.
    
    In a real test, you would authenticate and get a JWT token.
    For this test, we'll use a mock API key.
    """
    return {
        "X-API-Key": "test_api_key_12345",
        "Content-Type": "application/json"
    }


def create_test_student_data(name: str = "Test Student"):
    """Create test student data."""
    return {
        "name": name,
        "course_type": "Engineering",
        "institute_name": "Test Institute",
        "institute_tier": 1,
        "cgpa": 8.5,
        "cgpa_scale": 10.0,
        "year_of_grad": 2024,
        "internship_count": 2,
        "internship_months": 6,
        "internship_employer_type": "startup",
        "certifications": ["AWS", "Python"],
        "region": "metro",
        "loan_amount": 500000,
        "loan_emi": 10000
    }


class TestAsyncShapComputation:
    """
    Test suite for async SHAP computation in batch requests.
    
    Requirements:
        - 27.1: Use FastAPI BackgroundTasks for SHAP computation
        - 27.2: Return prediction results immediately without SHAP values
        - 27.3: Set shap_values to null in initial response
        - 27.4: Compute SHAP values in background task
        - 27.5: Complete POST /api/batch-score in under 5 seconds for 100 students
    """
    
    def test_batch_returns_quickly_without_shap(self, client, auth_headers):
        """
        Test that batch scoring returns quickly without waiting for SHAP computation.
        
        Requirement 27.2, 27.5: Response should return in under 5 seconds for 100 students
        """
        # Create batch of 10 students (scaled down for test speed)
        students = [create_test_student_data(f"Student {i}") for i in range(10)]
        
        start_time = time.time()
        
        response = client.post(
            "/api/batch-score",
            json={"students": students},
            headers=auth_headers
        )
        
        elapsed_time = time.time() - start_time
        
        # Verify response is successful
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify response time is fast (should be under 5 seconds for 10 students)
        # For 100 students, this would scale to ~50 seconds without async SHAP,
        # but with async SHAP it should be under 5 seconds
        assert elapsed_time < 5.0, f"Batch scoring took {elapsed_time:.2f}s, expected < 5s"
        
        print(f"✅ Batch scoring completed in {elapsed_time:.2f} seconds")
    
    def test_batch_response_has_empty_shap_values(self, client, auth_headers):
        """
        Test that initial batch response has empty SHAP values.
        
        Requirement 27.3: Set shap_values to null in initial response
        """
        students = [create_test_student_data("Test Student")]
        
        response = client.post(
            "/api/batch-score",
            json={"students": students},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify results exist
        assert "results" in data
        assert len(data["results"]) > 0
        
        # Verify first result has empty top_risk_drivers (SHAP not computed yet)
        first_result = data["results"][0]
        assert "top_risk_drivers" in first_result
        
        # SHAP values should be empty in initial response (Requirement 27.3)
        assert len(first_result["top_risk_drivers"]) == 0, \
            "Expected empty top_risk_drivers in initial batch response"
        
        print("✅ Initial batch response has empty SHAP values")
    
    @pytest.mark.asyncio
    async def test_shap_retrieval_endpoint_returns_404_initially(self, client, auth_headers):
        """
        Test that SHAP retrieval endpoint returns 404 when SHAP values not yet computed.
        
        Requirement 27.4.3: Return 404 if SHAP values not yet available
        """
        # Create a prediction
        student = create_test_student_data("Test Student")
        
        response = client.post(
            "/api/batch-score",
            json={"students": [student]},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        prediction_id = data["results"][0]["prediction_id"]
        
        # Immediately try to retrieve SHAP values (should return 404)
        shap_response = client.get(
            f"/api/predictions/{prediction_id}/shap",
            headers=auth_headers
        )
        
        # Should return 404 because SHAP values are still being computed
        assert shap_response.status_code == 404, \
            f"Expected 404, got {shap_response.status_code}"
        
        assert "still being computed" in shap_response.json()["detail"].lower(), \
            "Expected message about SHAP values still being computed"
        
        print("✅ SHAP retrieval endpoint returns 404 when values not yet available")
    
    @pytest.mark.asyncio
    async def test_shap_values_computed_in_background(self, client, auth_headers):
        """
        Test that SHAP values are eventually computed in background.
        
        Requirement 27.1, 27.4: Compute SHAP values in background task
        """
        # Create a prediction
        student = create_test_student_data("Test Student")
        
        response = client.post(
            "/api/batch-score",
            json={"students": [student]},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        prediction_id = data["results"][0]["prediction_id"]
        
        # Wait for background task to complete (with timeout)
        max_wait = 30  # seconds
        wait_interval = 2  # seconds
        elapsed = 0
        shap_available = False
        
        while elapsed < max_wait:
            await asyncio.sleep(wait_interval)
            elapsed += wait_interval
            
            # Try to retrieve SHAP values
            shap_response = client.get(
                f"/api/predictions/{prediction_id}/shap",
                headers=auth_headers
            )
            
            if shap_response.status_code == 200:
                shap_available = True
                shap_data = shap_response.json()
                
                # Verify SHAP data structure (Requirement 27.4.2)
                assert "shap_values" in shap_data
                assert "base_value" in shap_data
                assert "prediction" in shap_data
                assert "waterfall_data" in shap_data
                
                # Verify SHAP values are not empty
                assert len(shap_data["shap_values"]) > 0, \
                    "Expected non-empty SHAP values"
                
                print(f"✅ SHAP values computed successfully after {elapsed} seconds")
                break
        
        assert shap_available, \
            f"SHAP values not available after {max_wait} seconds"
    
    def test_batch_summary_statistics(self, client, auth_headers):
        """
        Test that batch response includes summary statistics.
        
        Requirement 9.6: Include high_risk_count, medium_risk_count, low_risk_count
        """
        # Create batch with varied risk profiles
        students = [
            create_test_student_data(f"Student {i}")
            for i in range(5)
        ]
        
        response = client.post(
            "/api/batch-score",
            json={"students": students},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify summary exists
        assert "summary" in data
        summary = data["summary"]
        
        # Verify summary has required fields
        assert "high_risk_count" in summary
        assert "medium_risk_count" in summary
        assert "low_risk_count" in summary
        
        # Verify counts sum to total students
        total_count = (
            summary["high_risk_count"] +
            summary["medium_risk_count"] +
            summary["low_risk_count"]
        )
        assert total_count == len(students), \
            f"Expected total count {len(students)}, got {total_count}"
        
        print(f"✅ Batch summary: {summary}")


class TestShapComputationLogging:
    """
    Test suite for SHAP computation logging.
    
    Requirements:
        - 27.6: Log SHAP computation time separately from prediction time
        - 27.7: Handle SHAP computation failures gracefully
    """
    
    def test_shap_computation_logged(self, client, auth_headers, caplog):
        """
        Test that SHAP computation is logged with timing information.
        
        Requirement 27.6: Log SHAP computation time separately
        """
        import logging
        caplog.set_level(logging.INFO)
        
        student = create_test_student_data("Test Student")
        
        response = client.post(
            "/api/batch-score",
            json={"students": [student]},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Wait a bit for background task to start
        time.sleep(2)
        
        # Check logs for SHAP computation messages
        log_messages = [record.message for record in caplog.records]
        
        # Should see "Starting background SHAP computation" message
        shap_start_logs = [msg for msg in log_messages if "Starting background SHAP computation" in msg]
        assert len(shap_start_logs) > 0, \
            "Expected log message about starting SHAP computation"
        
        print("✅ SHAP computation logging verified")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
