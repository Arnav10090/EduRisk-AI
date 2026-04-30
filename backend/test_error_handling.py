"""
Tests for Error Handling and Logging Middleware

Feature: edurisk-ai-placement-intelligence
Requirements: 22.1, 22.2, 22.3, 22.4, 22.5, 22.6
"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from backend.middleware import (
    ErrorHandlingMiddleware,
    ValidationError,
    DatabaseError,
    ModelError,
    ExternalServiceError,
    NotFoundError,
    InternalServerError,
    configure_logging
)
import logging
import json


# Configure logging for tests
configure_logging(log_level="INFO", json_format=False)


@pytest.fixture
def app():
    """Create a test FastAPI app with error handling middleware"""
    app = FastAPI()
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Test endpoints
    @app.get("/test/success")
    async def success_endpoint():
        return {"status": "ok"}
    
    @app.get("/test/validation-error")
    async def validation_error_endpoint():
        raise ValidationError("Invalid input data", details={"field": "email"})
    
    @app.get("/test/database-error")
    async def database_error_endpoint():
        raise DatabaseError("Connection failed", details={"host": "localhost"})
    
    @app.get("/test/model-error")
    async def model_error_endpoint():
        raise ModelError("Model prediction failed")
    
    @app.get("/test/external-service-error")
    async def external_service_error_endpoint():
        raise ExternalServiceError("Claude API timeout")
    
    @app.get("/test/not-found-error")
    async def not_found_error_endpoint():
        raise NotFoundError("Student not found", details={"student_id": "123"})
    
    @app.get("/test/internal-server-error")
    async def internal_server_error_endpoint():
        raise InternalServerError("Unexpected error occurred")
    
    @app.get("/test/unhandled-exception")
    async def unhandled_exception_endpoint():
        raise RuntimeError("This is an unhandled exception")
    
    @app.get("/test/value-error")
    async def value_error_endpoint():
        raise ValueError("Invalid value provided")
    
    return app


@pytest.fixture
def client(app):
    """Create a test client"""
    return TestClient(app)


def test_success_endpoint(client):
    """Test that successful requests work normally"""
    response = client.get("/test/success")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_validation_error(client):
    """Test ValidationError returns HTTP 422 with proper format"""
    response = client.get("/test/validation-error")
    assert response.status_code == 422
    
    data = response.json()
    assert data["error"] == "ValidationError"
    assert data["message"] == "Invalid input data"
    assert data["details"]["field"] == "email"
    assert "timestamp" in data
    assert "path" in data


def test_database_error(client):
    """Test DatabaseError returns HTTP 503 with proper format"""
    response = client.get("/test/database-error")
    assert response.status_code == 503
    
    data = response.json()
    assert data["error"] == "DatabaseError"
    assert data["message"] == "Connection failed"
    assert data["details"]["host"] == "localhost"
    assert "timestamp" in data


def test_model_error(client):
    """Test ModelError returns HTTP 500 with proper format"""
    response = client.get("/test/model-error")
    assert response.status_code == 500
    
    data = response.json()
    assert data["error"] == "ModelError"
    assert data["message"] == "Model prediction failed"


def test_external_service_error(client):
    """Test ExternalServiceError returns HTTP 503 with proper format"""
    response = client.get("/test/external-service-error")
    assert response.status_code == 503
    
    data = response.json()
    assert data["error"] == "ExternalServiceError"
    assert data["message"] == "Claude API timeout"


def test_not_found_error(client):
    """Test NotFoundError returns HTTP 404 with proper format"""
    response = client.get("/test/not-found-error")
    assert response.status_code == 404
    
    data = response.json()
    assert data["error"] == "NotFoundError"
    assert data["message"] == "Student not found"
    assert data["details"]["student_id"] == "123"


def test_internal_server_error(client):
    """Test InternalServerError returns HTTP 500 with proper format"""
    response = client.get("/test/internal-server-error")
    assert response.status_code == 500
    
    data = response.json()
    assert data["error"] == "InternalServerError"
    assert data["message"] == "Unexpected error occurred"


def test_unhandled_exception(client):
    """Test unhandled exceptions return HTTP 500 with generic message"""
    response = client.get("/test/unhandled-exception")
    assert response.status_code == 500
    
    data = response.json()
    assert data["error"] == "InternalServerError"
    assert "unexpected error occurred" in data["message"].lower()
    # Should not expose internal error details
    assert "RuntimeError" not in data["message"]


def test_value_error(client):
    """Test ValueError returns HTTP 400 with proper format"""
    response = client.get("/test/value-error")
    assert response.status_code == 400
    
    data = response.json()
    assert data["error"] == "ValueError"
    assert data["message"] == "Invalid value provided"


def test_error_response_structure(client):
    """Test that all error responses have consistent structure"""
    response = client.get("/test/validation-error")
    data = response.json()
    
    # All error responses should have these fields
    required_fields = ["error", "message", "timestamp", "path"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"


def test_logging_configuration():
    """Test that logging is configured correctly"""
    # Get root logger
    root_logger = logging.getLogger()
    
    # Should have at least one handler
    assert len(root_logger.handlers) > 0
    
    # Should be set to INFO level or lower
    assert root_logger.level <= logging.INFO


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
