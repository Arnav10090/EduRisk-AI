"""
Integration tests for API Key Authentication Middleware.

Tests verify that the ApiKeyMiddleware correctly:
1. Allows requests with valid API keys
2. Rejects requests without API keys (401)
3. Rejects requests with invalid API keys (401)
4. Allows public endpoints without API keys
5. Logs warnings when API_KEY is not configured

Feature: edurisk-submission-improvements
Requirements: Task 2.4 (Sub-tasks 2.4.1, 2.4.2, 2.4.3, 2.4.4, 2.4.5)
"""

import pytest
import os
import logging
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch
from backend.middleware.api_key_auth import ApiKeyMiddleware


# Test API key values
VALID_API_KEY = "test_api_key_12345"
INVALID_API_KEY = "wrong_api_key"


@pytest.fixture
def app_with_auth():
    """
    Create a FastAPI app with API key authentication middleware.
    
    This fixture creates a minimal FastAPI app with the ApiKeyMiddleware
    and test endpoints to verify authentication behavior.
    """
    app = FastAPI()
    
    # Add the API key middleware
    app.add_middleware(ApiKeyMiddleware)
    
    # Create test endpoints
    @app.get("/")
    async def root():
        """Public root endpoint."""
        return {"message": "Root endpoint"}
    
    @app.get("/api/health")
    async def health():
        """Public health check endpoint."""
        return {"status": "healthy", "ml_models": "available"}
    
    @app.get("/docs")
    async def docs():
        """Public documentation endpoint."""
        return {"message": "API Documentation"}
    
    @app.get("/redoc")
    async def redoc():
        """Public ReDoc endpoint."""
        return {"message": "ReDoc Documentation"}
    
    @app.get("/openapi.json")
    async def openapi():
        """Public OpenAPI schema endpoint."""
        return {"openapi": "3.0.0"}
    
    @app.get("/api/predict")
    async def predict():
        """Protected prediction endpoint."""
        return {"prediction": "success"}
    
    @app.post("/api/batch-score")
    async def batch_score():
        """Protected batch scoring endpoint."""
        return {"batch": "success"}
    
    @app.get("/api/students")
    async def get_students():
        """Protected students endpoint."""
        return {"students": []}
    
    @app.get("/api/explain/{student_id}")
    async def explain(student_id: str):
        """Protected explanation endpoint."""
        return {"explanation": "success", "student_id": student_id}
    
    return app


@pytest.fixture
def client_with_api_key(app_with_auth):
    """
    Create a test client with API_KEY environment variable set.
    
    This simulates the production scenario where API_KEY is configured.
    """
    with patch.dict(os.environ, {"API_KEY": VALID_API_KEY}):
        # Recreate the app to pick up the new environment variable
        app = FastAPI()
        app.add_middleware(ApiKeyMiddleware)
        
        # Recreate test endpoints
        @app.get("/")
        async def root():
            return {"message": "Root endpoint"}
        
        @app.get("/api/health")
        async def health():
            return {"status": "healthy", "ml_models": "available"}
        
        @app.get("/docs")
        async def docs():
            return {"message": "API Documentation"}
        
        @app.get("/redoc")
        async def redoc():
            return {"message": "ReDoc Documentation"}
        
        @app.get("/openapi.json")
        async def openapi():
            return {"openapi": "3.0.0"}
        
        @app.get("/api/predict")
        async def predict():
            return {"prediction": "success"}
        
        @app.post("/api/batch-score")
        async def batch_score():
            return {"batch": "success"}
        
        @app.get("/api/students")
        async def get_students():
            return {"students": []}
        
        @app.get("/api/explain/{student_id}")
        async def explain(student_id: str):
            return {"explanation": "success", "student_id": student_id}
        
        # Configure client to not raise exceptions on 4xx/5xx responses
        client = TestClient(app, raise_server_exceptions=False)
        yield client


@pytest.fixture
def client_without_api_key(app_with_auth):
    """
    Create a test client without API_KEY environment variable.
    
    This simulates the scenario where API_KEY is not configured,
    which should disable authentication and log a warning.
    """
    with patch.dict(os.environ, {}, clear=True):
        # Remove API_KEY if it exists
        os.environ.pop("API_KEY", None)
        
        # Recreate the app to pick up the cleared environment
        app = FastAPI()
        app.add_middleware(ApiKeyMiddleware)
        
        # Recreate test endpoints
        @app.get("/")
        async def root():
            return {"message": "Root endpoint"}
        
        @app.get("/api/health")
        async def health():
            return {"status": "healthy", "ml_models": "available"}
        
        @app.get("/docs")
        async def docs():
            return {"message": "API Documentation"}
        
        @app.get("/api/predict")
        async def predict():
            return {"prediction": "success"}
        
        # Configure client to not raise exceptions on 4xx/5xx responses
        client = TestClient(app, raise_server_exceptions=False)
        yield client


class TestProtectedEndpointsWithValidKey:
    """Test 2.4.1: Test protected endpoint with valid API key (should succeed)."""
    
    def test_predict_endpoint_with_valid_key(self, client_with_api_key):
        """Test GET /api/predict with valid API key."""
        response = client_with_api_key.get(
            "/api/predict",
            headers={"X-API-Key": VALID_API_KEY}
        )
        
        assert response.status_code == 200, \
            f"Should return 200 with valid API key. Got: {response.status_code}"
        
        assert response.json() == {"prediction": "success"}, \
            f"Should return prediction response. Got: {response.json()}"
        
        print("✓ Test passed: GET /api/predict with valid API key succeeded")
    
    def test_batch_score_endpoint_with_valid_key(self, client_with_api_key):
        """Test POST /api/batch-score with valid API key."""
        response = client_with_api_key.post(
            "/api/batch-score",
            headers={"X-API-Key": VALID_API_KEY}
        )
        
        assert response.status_code == 200, \
            f"Should return 200 with valid API key. Got: {response.status_code}"
        
        assert response.json() == {"batch": "success"}, \
            f"Should return batch response. Got: {response.json()}"
        
        print("✓ Test passed: POST /api/batch-score with valid API key succeeded")
    
    def test_students_endpoint_with_valid_key(self, client_with_api_key):
        """Test GET /api/students with valid API key."""
        response = client_with_api_key.get(
            "/api/students",
            headers={"X-API-Key": VALID_API_KEY}
        )
        
        assert response.status_code == 200, \
            f"Should return 200 with valid API key. Got: {response.status_code}"
        
        assert response.json() == {"students": []}, \
            f"Should return students response. Got: {response.json()}"
        
        print("✓ Test passed: GET /api/students with valid API key succeeded")
    
    def test_explain_endpoint_with_valid_key(self, client_with_api_key):
        """Test GET /api/explain/{student_id} with valid API key."""
        response = client_with_api_key.get(
            "/api/explain/test-student-123",
            headers={"X-API-Key": VALID_API_KEY}
        )
        
        assert response.status_code == 200, \
            f"Should return 200 with valid API key. Got: {response.status_code}"
        
        data = response.json()
        assert data["explanation"] == "success", \
            f"Should return explanation response. Got: {data}"
        assert data["student_id"] == "test-student-123", \
            f"Should include student_id. Got: {data}"
        
        print("✓ Test passed: GET /api/explain with valid API key succeeded")


class TestProtectedEndpointsWithoutKey:
    """Test 2.4.2: Test protected endpoint without API key (should return 401)."""
    
    def test_predict_endpoint_without_key(self, client_with_api_key):
        """Test GET /api/predict without API key header."""
        response = client_with_api_key.get("/api/predict")
        
        assert response.status_code == 401, \
            f"Should return 401 without API key. Got: {response.status_code}"
        
        data = response.json()
        assert "Missing API key" in data["detail"], \
            f"Should return missing API key message. Got: {data}"
        
        assert "Include X-API-Key header" in data["detail"], \
            f"Should provide guidance on how to fix. Got: {data}"
        
        print("✓ Test passed: GET /api/predict without API key returned 401")
    
    def test_batch_score_endpoint_without_key(self, client_with_api_key):
        """Test POST /api/batch-score without API key header."""
        response = client_with_api_key.post("/api/batch-score")
        
        assert response.status_code == 401, \
            f"Should return 401 without API key. Got: {response.status_code}"
        
        data = response.json()
        assert "Missing API key" in data["detail"], \
            f"Should return missing API key message. Got: {data}"
        
        print("✓ Test passed: POST /api/batch-score without API key returned 401")
    
    def test_students_endpoint_without_key(self, client_with_api_key):
        """Test GET /api/students without API key header."""
        response = client_with_api_key.get("/api/students")
        
        assert response.status_code == 401, \
            f"Should return 401 without API key. Got: {response.status_code}"
        
        data = response.json()
        assert "Missing API key" in data["detail"], \
            f"Should return missing API key message. Got: {data}"
        
        print("✓ Test passed: GET /api/students without API key returned 401")
    
    def test_explain_endpoint_without_key(self, client_with_api_key):
        """Test GET /api/explain/{student_id} without API key header."""
        response = client_with_api_key.get("/api/explain/test-student-123")
        
        assert response.status_code == 401, \
            f"Should return 401 without API key. Got: {response.status_code}"
        
        data = response.json()
        assert "Missing API key" in data["detail"], \
            f"Should return missing API key message. Got: {data}"
        
        print("✓ Test passed: GET /api/explain without API key returned 401")


class TestProtectedEndpointsWithInvalidKey:
    """Test 2.4.3: Test protected endpoint with invalid API key (should return 401)."""
    
    def test_predict_endpoint_with_invalid_key(self, client_with_api_key):
        """Test GET /api/predict with invalid API key."""
        response = client_with_api_key.get(
            "/api/predict",
            headers={"X-API-Key": INVALID_API_KEY}
        )
        
        assert response.status_code == 401, \
            f"Should return 401 with invalid API key. Got: {response.status_code}"
        
        data = response.json()
        assert data["detail"] == "Invalid API key", \
            f"Should return invalid API key message. Got: {data}"
        
        print("✓ Test passed: GET /api/predict with invalid API key returned 401")
    
    def test_batch_score_endpoint_with_invalid_key(self, client_with_api_key):
        """Test POST /api/batch-score with invalid API key."""
        response = client_with_api_key.post(
            "/api/batch-score",
            headers={"X-API-Key": INVALID_API_KEY}
        )
        
        assert response.status_code == 401, \
            f"Should return 401 with invalid API key. Got: {response.status_code}"
        
        data = response.json()
        assert data["detail"] == "Invalid API key", \
            f"Should return invalid API key message. Got: {data}"
        
        print("✓ Test passed: POST /api/batch-score with invalid API key returned 401")
    
    def test_students_endpoint_with_invalid_key(self, client_with_api_key):
        """Test GET /api/students with invalid API key."""
        response = client_with_api_key.get(
            "/api/students",
            headers={"X-API-Key": INVALID_API_KEY}
        )
        
        assert response.status_code == 401, \
            f"Should return 401 with invalid API key. Got: {response.status_code}"
        
        data = response.json()
        assert data["detail"] == "Invalid API key", \
            f"Should return invalid API key message. Got: {data}"
        
        print("✓ Test passed: GET /api/students with invalid API key returned 401")
    
    def test_explain_endpoint_with_invalid_key(self, client_with_api_key):
        """Test GET /api/explain/{student_id} with invalid API key."""
        response = client_with_api_key.get(
            "/api/explain/test-student-123",
            headers={"X-API-Key": INVALID_API_KEY}
        )
        
        assert response.status_code == 401, \
            f"Should return 401 with invalid API key. Got: {response.status_code}"
        
        data = response.json()
        assert data["detail"] == "Invalid API key", \
            f"Should return invalid API key message. Got: {data}"
        
        print("✓ Test passed: GET /api/explain with invalid API key returned 401")


class TestPublicEndpoints:
    """Test 2.4.4: Test public endpoints without API key (should succeed)."""
    
    def test_root_endpoint_without_key(self, client_with_api_key):
        """Test GET / without API key (public endpoint)."""
        response = client_with_api_key.get("/")
        
        assert response.status_code == 200, \
            f"Root endpoint should be public. Got: {response.status_code}"
        
        assert response.json() == {"message": "Root endpoint"}, \
            f"Should return root response. Got: {response.json()}"
        
        print("✓ Test passed: GET / without API key succeeded (public endpoint)")
    
    def test_health_endpoint_without_key(self, client_with_api_key):
        """Test GET /api/health without API key (public endpoint)."""
        response = client_with_api_key.get("/api/health")
        
        assert response.status_code == 200, \
            f"Health endpoint should be public. Got: {response.status_code}"
        
        data = response.json()
        assert data["status"] == "healthy", \
            f"Should return health status. Got: {data}"
        
        print("✓ Test passed: GET /api/health without API key succeeded (public endpoint)")
    
    def test_docs_endpoint_without_key(self, client_with_api_key):
        """Test GET /docs without API key (public endpoint)."""
        response = client_with_api_key.get("/docs")
        
        assert response.status_code == 200, \
            f"Docs endpoint should be public. Got: {response.status_code}"
        
        # /docs returns HTML, not JSON, so just check status code
        print("✓ Test passed: GET /docs without API key succeeded (public endpoint)")
    
    def test_redoc_endpoint_without_key(self, client_with_api_key):
        """Test GET /redoc without API key (public endpoint)."""
        response = client_with_api_key.get("/redoc")
        
        assert response.status_code == 200, \
            f"ReDoc endpoint should be public. Got: {response.status_code}"
        
        # /redoc returns HTML, not JSON, so just check status code
        print("✓ Test passed: GET /redoc without API key succeeded (public endpoint)")
    
    def test_openapi_endpoint_without_key(self, client_with_api_key):
        """Test GET /openapi.json without API key (public endpoint)."""
        response = client_with_api_key.get("/openapi.json")
        
        assert response.status_code == 200, \
            f"OpenAPI endpoint should be public. Got: {response.status_code}"
        
        data = response.json()
        # OpenAPI schema should have 'openapi' field (version may vary)
        assert "openapi" in data, \
            f"Should return OpenAPI schema. Got: {data}"
        
        print("✓ Test passed: GET /openapi.json without API key succeeded (public endpoint)")


class TestAuthenticationDisabled:
    """Test 2.4.5: Verify warning logged when API_KEY not configured."""
    
    def test_warning_logged_when_api_key_not_configured(self, client_without_api_key, caplog):
        """
        Test that a warning is logged when API_KEY is not configured.
        
        When API_KEY is not set, the middleware should:
        - Log a warning message
        - Allow all requests (authentication disabled)
        """
        with caplog.at_level(logging.WARNING):
            # Make a request to a protected endpoint without API key
            response = client_without_api_key.get("/api/predict")
            
            # Should succeed because authentication is disabled
            assert response.status_code == 200, \
                f"Should allow request when API_KEY not configured. Got: {response.status_code}"
            
            # Check that warning was logged
            warning_messages = [record.message for record in caplog.records if record.levelname == "WARNING"]
            
            assert any("API_KEY not configured" in msg for msg in warning_messages), \
                f"Should log warning about missing API_KEY. Got warnings: {warning_messages}"
            
            assert any("authentication disabled" in msg for msg in warning_messages), \
                f"Should indicate authentication is disabled. Got warnings: {warning_messages}"
            
            print("✓ Test passed: Warning logged when API_KEY not configured")
    
    def test_all_endpoints_accessible_without_api_key_when_disabled(self, client_without_api_key):
        """
        Test that all endpoints are accessible when API_KEY is not configured.
        
        This verifies graceful degradation - the system works without authentication
        when API_KEY is not set.
        """
        # Test protected endpoints without API key
        endpoints = [
            ("/api/predict", "GET"),
            ("/api/health", "GET"),
            ("/", "GET"),
        ]
        
        for endpoint, method in endpoints:
            if method == "GET":
                response = client_without_api_key.get(endpoint)
            else:
                response = client_without_api_key.post(endpoint)
            
            assert response.status_code == 200, \
                f"{method} {endpoint} should succeed when auth disabled. Got: {response.status_code}"
        
        print("✓ Test passed: All endpoints accessible when authentication disabled")


class TestClientIPLogging:
    """Test that client IP is logged for authentication failures."""
    
    def test_client_ip_logged_for_missing_key(self, client_with_api_key, caplog):
        """Test that client IP is logged when API key is missing."""
        with caplog.at_level(logging.WARNING):
            response = client_with_api_key.get("/api/predict")
            
            assert response.status_code == 401
            
            # Check that client IP was logged
            warning_messages = [record.message for record in caplog.records if record.levelname == "WARNING"]
            
            assert any("Missing API key from" in msg for msg in warning_messages), \
                f"Should log client IP for missing key. Got warnings: {warning_messages}"
            
            print("✓ Test passed: Client IP logged for missing API key")
    
    def test_client_ip_logged_for_invalid_key(self, client_with_api_key, caplog):
        """Test that client IP is logged when API key is invalid."""
        with caplog.at_level(logging.WARNING):
            response = client_with_api_key.get(
                "/api/predict",
                headers={"X-API-Key": INVALID_API_KEY}
            )
            
            assert response.status_code == 401
            
            # Check that client IP was logged
            warning_messages = [record.message for record in caplog.records if record.levelname == "WARNING"]
            
            assert any("Invalid API key from" in msg for msg in warning_messages), \
                f"Should log client IP for invalid key. Got warnings: {warning_messages}"
            
            print("✓ Test passed: Client IP logged for invalid API key")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
