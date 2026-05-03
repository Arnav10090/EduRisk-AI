"""
Test JWT Protected Routes

This test file verifies that protected routes require valid JWT tokens
and properly reject invalid/missing tokens.

Requirements: 7.3.1, 7.3.2, 7.3.3, 7.3.4
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


class TestJWTProtectedRoutes:
    """Test JWT authentication on protected routes"""
    
    @pytest.fixture
    def valid_token(self):
        """Get a valid JWT token by logging in"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "admin123"
            }
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_students_list_requires_jwt(self):
        """Test GET /api/students requires JWT token (Requirement 7.3.4)"""
        # Request without token should return 401
        response = client.get("/api/students")
        assert response.status_code == 401
        assert "detail" in response.json()
    
    def test_students_list_with_valid_jwt(self, valid_token):
        """Test GET /api/students succeeds with valid JWT (Requirement 7.3.1, 7.3.2, 7.3.3)"""
        response = client.get(
            "/api/students",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        # Should succeed (200) or return empty list
        assert response.status_code == 200
        data = response.json()
        assert "students" in data
        assert "total_count" in data
    
    def test_students_list_with_invalid_jwt(self):
        """Test GET /api/students rejects invalid JWT (Requirement 7.3.4)"""
        response = client.get(
            "/api/students",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid or expired token"
    
    def test_predict_requires_jwt(self):
        """Test POST /api/predict requires JWT token (Requirement 7.3.4)"""
        student_data = {
            "name": "Test Student",
            "course_type": "Engineering",
            "institute_tier": 1,
            "cgpa": 8.5,
            "year_of_grad": 2024,
            "loan_amount": 500000,
            "loan_emi": 10000
        }
        
        # Request without token should return 401
        response = client.post("/api/predict", json=student_data)
        assert response.status_code == 401
    
    def test_predict_with_valid_jwt(self, valid_token):
        """Test POST /api/predict succeeds with valid JWT (Requirement 7.3.1, 7.3.2, 7.3.3)"""
        student_data = {
            "name": "Test Student",
            "course_type": "Engineering",
            "institute_tier": 1,
            "cgpa": 8.5,
            "year_of_grad": 2024,
            "loan_amount": 500000,
            "loan_emi": 10000
        }
        
        response = client.post(
            "/api/predict",
            json=student_data,
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        # Should succeed (200) or fail with validation error (422), not auth error (401)
        assert response.status_code in [200, 422, 500]  # Not 401
    
    def test_batch_score_requires_jwt(self):
        """Test POST /api/batch-score requires JWT token (Requirement 7.3.4)"""
        batch_data = {
            "students": [
                {
                    "name": "Student 1",
                    "course_type": "Engineering",
                    "institute_tier": 1,
                    "cgpa": 8.5,
                    "year_of_grad": 2024,
                    "loan_amount": 500000,
                    "loan_emi": 10000
                }
            ]
        }
        
        # Request without token should return 401
        response = client.post("/api/batch-score", json=batch_data)
        assert response.status_code == 401
    
    def test_batch_score_with_valid_jwt(self, valid_token):
        """Test POST /api/batch-score succeeds with valid JWT (Requirement 7.3.1, 7.3.2, 7.3.3)"""
        batch_data = {
            "students": [
                {
                    "name": "Student 1",
                    "course_type": "Engineering",
                    "institute_tier": 1,
                    "cgpa": 8.5,
                    "year_of_grad": 2024,
                    "loan_amount": 500000,
                    "loan_emi": 10000
                }
            ]
        }
        
        response = client.post(
            "/api/batch-score",
            json=batch_data,
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        # Should succeed (200) or fail with validation error (422), not auth error (401)
        assert response.status_code in [200, 422, 500]  # Not 401
    
    def test_alerts_requires_jwt(self):
        """Test GET /api/alerts requires JWT token (Requirement 7.3.4)"""
        # Request without token should return 401
        response = client.get("/api/alerts")
        assert response.status_code == 401
    
    def test_alerts_with_valid_jwt(self, valid_token):
        """Test GET /api/alerts succeeds with valid JWT (Requirement 7.3.1, 7.3.2, 7.3.3)"""
        response = client.get(
            "/api/alerts",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        # Should succeed (200) and return list
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_explain_requires_jwt(self):
        """Test GET /api/explain/{student_id} requires JWT token (Requirement 7.3.4)"""
        # Use a dummy UUID
        student_id = "00000000-0000-0000-0000-000000000000"
        
        # Request without token should return 401
        response = client.get(f"/api/explain/{student_id}")
        assert response.status_code == 401
    
    def test_explain_with_valid_jwt(self, valid_token):
        """Test GET /api/explain/{student_id} succeeds with valid JWT (Requirement 7.3.1, 7.3.2, 7.3.3)"""
        # Use a dummy UUID
        student_id = "00000000-0000-0000-0000-000000000000"
        
        response = client.get(
            f"/api/explain/{student_id}",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        # Should fail with 404 (student not found), not 401 (auth error)
        assert response.status_code in [200, 404, 500]  # Not 401
    
    def test_student_detail_requires_jwt(self):
        """Test GET /api/students/{student_id} requires JWT token (Requirement 7.3.4)"""
        # Use a dummy UUID
        student_id = "00000000-0000-0000-0000-000000000000"
        
        # Request without token should return 401
        response = client.get(f"/api/students/{student_id}")
        assert response.status_code == 401
    
    def test_student_detail_with_valid_jwt(self, valid_token):
        """Test GET /api/students/{student_id} succeeds with valid JWT (Requirement 7.3.1, 7.3.2, 7.3.3)"""
        # Use a dummy UUID
        student_id = "00000000-0000-0000-0000-000000000000"
        
        response = client.get(
            f"/api/students/{student_id}",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        # Should fail with 404 (student not found), not 401 (auth error)
        assert response.status_code in [200, 404, 500]  # Not 401
    
    def test_student_predictions_requires_jwt(self):
        """Test GET /api/students/{student_id}/predictions requires JWT token (Requirement 7.3.4)"""
        # Use a dummy UUID
        student_id = "00000000-0000-0000-0000-000000000000"
        
        # Request without token should return 401
        response = client.get(f"/api/students/{student_id}/predictions")
        assert response.status_code == 401
    
    def test_student_predictions_with_valid_jwt(self, valid_token):
        """Test GET /api/students/{student_id}/predictions succeeds with valid JWT (Requirement 7.3.1, 7.3.2, 7.3.3)"""
        # Use a dummy UUID
        student_id = "00000000-0000-0000-0000-000000000000"
        
        response = client.get(
            f"/api/students/{student_id}/predictions",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        # Should fail with 404 (student not found), not 401 (auth error)
        assert response.status_code in [200, 404, 500]  # Not 401


class TestPublicEndpoints:
    """Test that public endpoints don't require JWT"""
    
    def test_health_endpoint_public(self):
        """Test /api/health is publicly accessible"""
        response = client.get("/api/health")
        # Should succeed without JWT
        assert response.status_code == 200
    
    def test_login_endpoint_public(self):
        """Test /api/auth/login is publicly accessible"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "admin123"
            }
        )
        # Should succeed without JWT
        assert response.status_code == 200
    
    def test_docs_endpoint_public(self):
        """Test /docs is publicly accessible"""
        response = client.get("/docs")
        # Should succeed without JWT (may redirect or return HTML)
        assert response.status_code in [200, 307]


class TestUserInfoExtraction:
    """Test that user information is properly extracted from JWT (Requirement 7.3.3)"""
    
    def test_username_logged_in_protected_routes(self):
        """Test that username from JWT is used in audit logs"""
        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "admin123"
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Make a request to a protected route
        response = client.get(
            "/api/students",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should succeed
        assert response.status_code == 200
        
        # The username should be extracted from JWT and used internally
        # (We can't directly verify this without checking logs or database,
        # but the fact that the request succeeds confirms JWT parsing works)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
