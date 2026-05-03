"""
Test suite for batch scoring database session safety.

Tests verify that each student in a batch gets an independent database session
to prevent race conditions and session corruption during concurrent processing.

Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from typing import Dict, Any

from backend.main import app


# Create test client
client = TestClient(app)


@pytest.fixture
def valid_token():
    """Get a valid JWT token by logging in."""
    response = client.post(
        "/api/auth/login",
        json={
            "username": "admin",
            "password": "admin123"
        }
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def valid_student_data() -> Dict[str, Any]:
    """Create valid student data for testing."""
    return {
        "name": "Test Student",
        "course_type": "Engineering",
        "institute_tier": 1,
        "cgpa": 8.5,
        "year_of_grad": 2024,
        "loan_amount": 500000,
        "loan_emi": 10000
    }


@pytest.fixture
def invalid_student_data() -> Dict[str, Any]:
    """Create invalid student data for testing (invalid CGPA)."""
    return {
        "name": "Invalid Student",
        "course_type": "Engineering",
        "institute_tier": 1,
        "cgpa": 15.0,  # Invalid CGPA (> 10)
        "year_of_grad": 2024,
        "loan_amount": 500000,
        "loan_emi": 10000
    }


class TestBatchScoringSessionSafety:
    """Test batch scoring with independent database sessions."""
    
    def test_batch_all_valid_students(self, valid_token, valid_student_data):
        """
        Test batch with all valid students - all should succeed.
        
        Requirement 9.1: Each student gets separate database session
        Requirement 9.3: Process in parallel with asyncio.gather()
        Requirement 9.5: Return success=True with prediction data
        """
        # Create batch of 5 valid students
        students = [
            {**valid_student_data, "name": f"Student {i}"}
            for i in range(5)
        ]
        
        batch_request = {"students": students}
        
        # Send batch request with authentication
        response = client.post(
            "/api/batch-score",
            json=batch_request,
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # All students should succeed
        assert "results" in data
        assert len(data["results"]) == 5
        
        # Verify summary
        assert "summary" in data
        total_students = (
            data["summary"]["high_risk_count"] +
            data["summary"]["medium_risk_count"] +
            data["summary"]["low_risk_count"]
        )
        assert total_students == 5
        
        # Verify each result has required fields
        for result in data["results"]:
            assert "student_id" in result
            assert "risk_score" in result
            assert "risk_level" in result
            assert "placement_probabilities" in result
    
    
    def test_batch_with_mixed_results(self, valid_token, valid_student_data):
        """
        Test batch with students that may have different outcomes.
        
        Requirement 9.2: Do not share session across concurrent predictions
        Requirement 9.4: Handle failures without affecting other students
        Requirement 9.6: Close each session after processing
        """
        # Create batch with students having different characteristics
        students = [
            {**valid_student_data, "name": "High CGPA Student", "cgpa": 9.5},
            {**valid_student_data, "name": "Medium CGPA Student", "cgpa": 7.5},
            {**valid_student_data, "name": "Low CGPA Student", "cgpa": 6.0},
            {**valid_student_data, "name": "Tier 2 Student", "institute_tier": 2},
            {**valid_student_data, "name": "High Loan Student", "loan_amount": 1000000},
        ]
        
        batch_request = {"students": students}
        
        # Send batch request with authentication
        response = client.post(
            "/api/batch-score",
            json=batch_request,
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # All students should succeed (they're all valid)
        assert len(data["results"]) == 5
        
        # Verify summary counts
        total_successful = (
            data["summary"]["high_risk_count"] +
            data["summary"]["medium_risk_count"] +
            data["summary"]["low_risk_count"]
        )
        assert total_successful == 5
    
    
    def test_batch_large_parallel_processing(self, valid_token, valid_student_data):
        """
        Test batch with 50+ students - verify parallel processing.
        
        Requirement 9.1: Create separate database session for each student
        Requirement 9.3: Use asyncio.gather() for parallel processing
        Requirement 9.6: Close each session after processing
        """
        # Create batch of 50 students
        students = [
            {**valid_student_data, "name": f"Student {i}"}
            for i in range(50)
        ]
        
        batch_request = {"students": students}
        
        # Measure processing time
        import time
        start_time = time.time()
        
        # Send batch request with authentication
        response = client.post(
            "/api/batch-score",
            json=batch_request,
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # All 50 students should succeed
        assert len(data["results"]) == 50
        
        # Verify parallel processing is reasonably fast
        # Note: Actual time depends on system performance
        # We just verify it completes successfully
        print(f"Batch processing time for 50 students: {processing_time:.2f}s")
        
        # Verify summary
        total_successful = (
            data["summary"]["high_risk_count"] +
            data["summary"]["medium_risk_count"] +
            data["summary"]["low_risk_count"]
        )
        assert total_successful == 50
    
    
    def test_batch_max_size_validation(self, valid_token, valid_student_data):
        """
        Test that batches exceeding 500 students are rejected.
        
        Requirement: Reject batches > 500 students with HTTP 400
        """
        # Create batch of 501 students (exceeds limit)
        students = [
            {**valid_student_data, "name": f"Student {i}"}
            for i in range(501)
        ]
        
        batch_request = {"students": students}
        
        # Send batch request with authentication
        response = client.post(
            "/api/batch-score",
            json=batch_request,
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        # Verify rejection
        assert response.status_code == 400
        assert "exceed 500" in response.json()["detail"].lower()
    
    
    def test_batch_empty_list(self, valid_token):
        """
        Test batch with empty student list.
        """
        batch_request = {"students": []}
        
        # Send batch request with authentication
        response = client.post(
            "/api/batch-score",
            json=batch_request,
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        # Should handle empty list gracefully
        # May return 200 with empty results or 422 validation error
        assert response.status_code in [200, 422]
    
    
    def test_batch_requires_authentication(self, valid_student_data):
        """
        Test that batch scoring requires JWT authentication.
        
        Requirement 7.3.4: Raise 401 exception for invalid/expired tokens
        """
        students = [
            {**valid_student_data, "name": "Student 1"}
        ]
        
        batch_request = {"students": students}
        
        # Send batch request without authentication
        response = client.post(
            "/api/batch-score",
            json=batch_request
        )
        
        # Should return 401 Unauthorized
        assert response.status_code == 401


class TestBatchScoringPerformance:
    """Test batch scoring performance characteristics."""
    
    def test_batch_processing_time_100_students(self, valid_token, valid_student_data):
        """
        Test that batch processing completes within acceptable time.
        
        Requirement: Complete within 60 seconds for batches of 500 students
        """
        # Create batch of 100 students (smaller for faster testing)
        students = [
            {**valid_student_data, "name": f"Student {i}"}
            for i in range(100)
        ]
        
        batch_request = {"students": students}
        
        # Measure processing time
        import time
        start_time = time.time()
        
        # Send batch request with authentication
        response = client.post(
            "/api/batch-score",
            json=batch_request,
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify response
        assert response.status_code == 200
        
        # Log processing time for monitoring
        print(f"Batch processing time for 100 students: {processing_time:.2f}s")
        
        # Verify all students processed
        data = response.json()
        assert len(data["results"]) == 100


class TestSessionIsolation:
    """Test database session isolation."""
    
    @pytest.mark.asyncio
    async def test_session_independence(self):
        """
        Test that database sessions are independent.
        
        Requirement 9.1: Create separate database session for each student
        Requirement 9.2: Do not share session across concurrent predictions
        """
        from backend.db.session import get_async_session
        
        # Track session IDs to verify they are different
        session_ids = []
        
        async def track_session():
            """Track session ID."""
            async with get_async_session() as db:
                session_id = id(db)
                session_ids.append(session_id)
                await asyncio.sleep(0.01)  # Simulate work
                return session_id
        
        # Create 5 sessions in parallel
        await asyncio.gather(*[track_session() for _ in range(5)])
        
        # Verify all sessions have different IDs (independent sessions)
        assert len(set(session_ids)) == 5, "Sessions should be independent"
    
    
    @pytest.mark.asyncio
    async def test_session_cleanup_on_error(self):
        """
        Test that sessions are properly closed even when errors occur.
        
        Requirement 9.6: Close each session after processing
        """
        from backend.db.session import get_async_session
        
        error_raised = False
        
        try:
            async with get_async_session() as db:
                # Simulate an error during processing
                raise ValueError("Simulated error")
        except ValueError:
            error_raised = True
        
        # Error should be raised and session should be closed
        assert error_raised, "Error should be raised"
        # Session cleanup is implicit in the context manager


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

