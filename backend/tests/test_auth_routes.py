"""
Test Authentication Routes

This test file verifies the JWT OAuth2 authentication endpoints.

Requirements: 20.1, 20.2, 20.3, 20.6, 20.8
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


class TestAuthLogin:
    """Test POST /api/auth/login endpoint"""
    
    def test_login_with_valid_credentials(self):
        """Test login with valid username and password (Requirement 20.2, 20.3)"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "admin123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure (Requirement 20.3)
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
    
    def test_login_with_invalid_username(self):
        """Test login with non-existent username (Requirement 20.8)"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "nonexistent",
                "password": "password123"
            }
        )
        
        # Should return 401 (Requirement 20.8)
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Invalid or expired token"
    
    def test_login_with_invalid_password(self):
        """Test login with wrong password (Requirement 20.8)"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "wrongpassword"
            }
        )
        
        # Should return 401 (Requirement 20.8)
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Invalid or expired token"
    
    def test_login_with_demo_user(self):
        """Test login with demo user credentials"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "demo",
                "password": "demo123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


class TestAuthRefresh:
    """Test POST /api/auth/refresh endpoint"""
    
    def test_refresh_with_valid_token(self):
        """Test token refresh with valid JWT (Requirement 20.6)"""
        # First, login to get a valid token
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "admin123"
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Now refresh the token
        refresh_response = client.post(
            "/api/auth/refresh",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert refresh_response.status_code == 200
        data = refresh_response.json()
        
        # Verify new token returned (Requirement 20.6)
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
        
        # New token should be different from old token
        assert data["access_token"] != token
    
    def test_refresh_with_invalid_token(self):
        """Test token refresh with invalid JWT (Requirement 20.8)"""
        response = client.post(
            "/api/auth/refresh",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        
        # Should return 401 (Requirement 20.8)
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Invalid or expired token"
    
    def test_refresh_without_token(self):
        """Test token refresh without Authorization header"""
        response = client.post("/api/auth/refresh")
        
        # Should return 401 or 403
        assert response.status_code in [401, 403]


class TestAuthPublicAccess:
    """Test that auth endpoints are publicly accessible (no API key required)"""
    
    def test_login_without_api_key(self):
        """Test that login endpoint doesn't require API key"""
        # This should work even without X-API-Key header
        response = client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "admin123"
            }
        )
        
        # Should succeed (not 401 for missing API key)
        assert response.status_code == 200
    
    def test_refresh_without_api_key(self):
        """Test that refresh endpoint doesn't require API key"""
        # First get a token
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "admin123"
            }
        )
        token = login_response.json()["access_token"]
        
        # Refresh should work without API key
        response = client.post(
            "/api/auth/refresh",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200


class TestGetCurrentUser:
    """Test the get_current_user dependency function"""
    
    def test_extract_user_from_valid_token(self):
        """Test that user info can be extracted from valid JWT"""
        # Login to get a token
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "admin123"
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # The token should contain user information
        # We can verify this by refreshing (which internally validates the token)
        refresh_response = client.post(
            "/api/auth/refresh",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert refresh_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
