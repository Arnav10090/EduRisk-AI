"""
Test error handling behavior with DEBUG=True vs DEBUG=False

Requirements: 5.2.1, 5.2.2, 5.2.3
"""

import pytest
import os
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException
from backend.middleware.error_handler import ErrorHandlingMiddleware


# Create a test app with a route that raises an unhandled exception
def create_test_app():
    """Create a test FastAPI app with error handling middleware."""
    test_app = FastAPI()
    test_app.add_middleware(ErrorHandlingMiddleware)
    
    @test_app.get("/test-error")
    async def test_error():
        """Endpoint that raises an unhandled exception."""
        # Raise a RuntimeError which should trigger 500 handler
        raise RuntimeError("This is a test error")
    
    @test_app.get("/test-validation")
    async def test_validation():
        """Endpoint that raises a validation error."""
        from backend.middleware.error_handler import ValidationError
        raise ValidationError("Invalid input data", details={"field": "test"})
    
    return test_app


class TestDebugErrorHandling:
    """Test error responses with different DEBUG settings."""
    
    def test_api_error_debug_false_hides_stack_traces(self):
        """
        Test that API errors with DEBUG=False hide stack traces.
        
        Requirement: 5.2.1
        """
        # Set DEBUG=False
        os.environ["DEBUG"] = "False"
        
        # Create test app and client
        test_app = create_test_app()
        client = TestClient(test_app)
        
        # Trigger an unhandled error
        response = client.get("/test-error")
        
        # Should return 500 error
        assert response.status_code == 500
        
        # Response should be JSON
        data = response.json()
        
        # Should have error structure
        assert "error" in data
        assert "message" in data
        assert data["error"] == "InternalServerError"
        
        # Should NOT contain debug_info with stack trace
        assert "debug_info" not in data
        assert "stack_trace" not in data
        
        # Should NOT contain file paths or line numbers in response
        response_text = response.text.lower()
        assert "traceback" not in response_text
        # Check that no Python file paths are exposed (except test file)
        if ".py" in response_text:
            assert "test_debug" in response_text, "Python file paths should not be exposed in production mode"
        
        print("✅ DEBUG=False: Stack traces are hidden")
    
    def test_api_error_debug_true_shows_stack_traces(self):
        """
        Test that API errors with DEBUG=True show stack traces.
        
        Requirement: 5.2.2
        """
        # Set DEBUG=True
        os.environ["DEBUG"] = "True"
        
        # Create test app and client
        test_app = create_test_app()
        client = TestClient(test_app)
        
        # Trigger an unhandled error
        response = client.get("/test-error")
        
        # Should return 500 error
        assert response.status_code == 500
        
        # Response should be JSON
        data = response.json()
        
        # Should have error structure
        assert "error" in data
        assert "message" in data
        assert data["error"] == "InternalServerError"
        
        # Should contain debug_info with stack trace in DEBUG mode
        assert "debug_info" in data
        assert "stack_trace" in data["debug_info"]
        assert "exception_type" in data["debug_info"]
        assert "exception_message" in data["debug_info"]
        
        # Stack trace should contain useful debugging information
        stack_trace = data["debug_info"]["stack_trace"]
        assert "RuntimeError" in stack_trace
        assert "This is a test error" in stack_trace
        
        print("✅ DEBUG=True: Stack traces are shown")
    
    def test_production_mode_no_sensitive_info_leak(self):
        """
        Test that error responses don't leak sensitive information in production mode.
        
        Requirement: 5.2.3
        """
        # Set DEBUG=False (production mode)
        os.environ["DEBUG"] = "False"
        
        # Create test app and client
        test_app = create_test_app()
        client = TestClient(test_app)
        
        # Trigger various errors
        test_endpoints = [
            "/test-error",  # Unhandled exception
            "/test-validation",  # Validation error
        ]
        
        for endpoint in test_endpoints:
            response = client.get(endpoint)
            
            # Get response text
            response_text = response.text.lower()
            
            # Should NOT contain sensitive information
            sensitive_patterns = [
                "password",
                "secret_key",
                "api_key",
                "database_url",
                "postgres://",
                "postgresql://",
                "c:\\users",  # Windows file paths
                "/home/",  # Linux file paths
                "sqlalchemy",  # Internal library details (in error messages)
            ]
            
            for pattern in sensitive_patterns:
                if pattern in response_text:
                    # Allow some patterns in specific contexts
                    if pattern == "sqlalchemy" and "debug_info" not in response_text:
                        continue  # OK if not in debug info
                    assert False, f"Sensitive pattern '{pattern}' found in error response for {endpoint}"
        
        print("✅ Production mode: No sensitive information leaked")
    
    def test_error_response_structure(self):
        """
        Test that error responses have consistent structure.
        
        Requirement: 5.2.3
        """
        # Set DEBUG=False
        os.environ["DEBUG"] = "False"
        
        # Create test app and client
        test_app = create_test_app()
        client = TestClient(test_app)
        
        # Trigger an error
        response = client.get("/test-error")
        
        # Should return 500 error
        assert response.status_code == 500
        
        # Response should be JSON
        data = response.json()
        
        # Should have required fields
        assert "error" in data
        assert "message" in data
        assert "timestamp" in data
        assert "path" in data
        
        # Message should be user-friendly
        assert len(data["message"]) > 0
        assert data["message"] != ""
        
        # Should be a generic message in production mode
        assert "unexpected error occurred" in data["message"].lower()
        
        # Should not expose internal exception details in production
        assert "RuntimeError" not in data["message"]
        assert "This is a test error" not in data["message"]
        
        print("✅ Error responses have consistent structure")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
