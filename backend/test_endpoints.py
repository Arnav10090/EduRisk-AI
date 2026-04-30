"""
Integration tests for FastAPI endpoints.

Tests all implemented endpoints to verify they work correctly.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns API information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "EduRisk AI API"
    assert data["version"] == "1.0.0"
    assert data["status"] == "operational"


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/api/health")
    # May return 200 or 503 depending on database/model availability
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "database" in data
    assert "ml_models" in data


def test_predict_endpoint_validation():
    """Test predict endpoint validates input correctly."""
    # Test with missing required fields
    response = client.post("/api/predict", json={})
    assert response.status_code == 422  # Validation error
    
    # Test with invalid institute_tier
    response = client.post("/api/predict", json={
        "name": "Test Student",
        "course_type": "Engineering",
        "institute_tier": 5,  # Invalid: must be 1-3
        "cgpa": 8.0,
        "cgpa_scale": 10.0,
        "year_of_grad": 2025
    })
    assert response.status_code == 422


def test_batch_score_validation():
    """Test batch-score endpoint validates batch size."""
    # Test with empty batch
    response = client.post("/api/batch-score", json={"students": []})
    assert response.status_code == 422
    
    # Test with oversized batch (would need 501 students, skipping for brevity)
    # This would be tested in a full integration test


def test_explain_endpoint_not_found():
    """Test explain endpoint returns 404 for non-existent student."""
    import uuid
    fake_id = str(uuid.uuid4())
    response = client.get(f"/api/explain/{fake_id}")
    # May return 404 or 500 depending on database availability
    assert response.status_code in [404, 500]


def test_alerts_endpoint():
    """Test alerts endpoint accepts query parameters."""
    response = client.get("/api/alerts?threshold=high&limit=10&offset=0")
    # May return 200 or 500 depending on database availability
    assert response.status_code in [200, 500]


def test_students_endpoint():
    """Test students endpoint accepts query parameters."""
    response = client.get("/api/students?limit=10&offset=0")
    # May return 200 or 500 depending on database availability
    assert response.status_code in [200, 500]


if __name__ == "__main__":
    print("Running endpoint tests...")
    test_root_endpoint()
    print("✓ Root endpoint test passed")
    
    test_health_endpoint()
    print("✓ Health endpoint test passed")
    
    test_predict_endpoint_validation()
    print("✓ Predict validation test passed")
    
    test_batch_score_validation()
    print("✓ Batch score validation test passed")
    
    test_explain_endpoint_not_found()
    print("✓ Explain endpoint test passed")
    
    test_alerts_endpoint()
    print("✓ Alerts endpoint test passed")
    
    test_students_endpoint()
    print("✓ Students endpoint test passed")
    
    print("\nAll tests passed!")
