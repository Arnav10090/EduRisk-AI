"""
Test CORS Configuration

Tests for Requirement 22: Strict CORS Configuration
- CORS_ORIGINS read from environment variables
- Parse comma-separated list of URLs
- Reject wildcard (*) in production
- Log warning if wildcard detected
"""

import pytest
import os
from backend.config import Configuration
from pydantic import ValidationError


class TestCORSConfiguration:
    """Test CORS configuration parsing and validation."""
    
    def test_parse_single_origin(self, monkeypatch):
        """Test parsing a single CORS origin."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://test")
        monkeypatch.setenv("ML_MODEL_PATH", "/test/path")
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")
        
        config = Configuration()
        assert config.cors_origins == ["http://localhost:3000"]
    
    def test_parse_multiple_origins(self, monkeypatch):
        """Test parsing comma-separated CORS origins."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://test")
        monkeypatch.setenv("ML_MODEL_PATH", "/test/path")
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001,https://app.example.com")
        
        config = Configuration()
        assert config.cors_origins == [
            "http://localhost:3000",
            "http://localhost:3001",
            "https://app.example.com"
        ]
    
    def test_parse_origins_with_spaces(self, monkeypatch):
        """Test parsing CORS origins with extra spaces."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://test")
        monkeypatch.setenv("ML_MODEL_PATH", "/test/path")
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000 , http://localhost:3001 , https://app.example.com")
        
        config = Configuration()
        assert config.cors_origins == [
            "http://localhost:3000",
            "http://localhost:3001",
            "https://app.example.com"
        ]
    
    def test_default_origin_when_empty(self, monkeypatch):
        """Test default CORS origin when not specified."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://test")
        monkeypatch.setenv("ML_MODEL_PATH", "/test/path")
        monkeypatch.setenv("CORS_ORIGINS", "")  # Explicitly set to empty string
        
        config = Configuration()
        assert config.cors_origins == [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    
    def test_reject_wildcard_in_production(self, monkeypatch):
        """Test that wildcard (*) is rejected when DEBUG=False."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://test")
        monkeypatch.setenv("ML_MODEL_PATH", "/test/path")
        monkeypatch.setenv("CORS_ORIGINS", "*")
        monkeypatch.setenv("DEBUG", "False")
        
        with pytest.raises(ValidationError) as exc_info:
            Configuration()
        
        assert "Wildcard (*) CORS origins are not allowed in production" in str(exc_info.value)
    
    def test_allow_wildcard_in_debug_mode(self, monkeypatch):
        """Test that wildcard (*) is allowed when DEBUG=True."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://test")
        monkeypatch.setenv("ML_MODEL_PATH", "/test/path")
        monkeypatch.setenv("CORS_ORIGINS", "*")
        monkeypatch.setenv("DEBUG", "True")
        
        config = Configuration()
        assert config.cors_origins == ["*"]
    
    def test_reject_invalid_origin_format(self, monkeypatch):
        """Test that origins without http:// or https:// are rejected."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://test")
        monkeypatch.setenv("ML_MODEL_PATH", "/test/path")
        monkeypatch.setenv("CORS_ORIGINS", "localhost:3000")
        
        with pytest.raises(ValidationError) as exc_info:
            Configuration()
        
        assert "Origins must be full URLs starting with http:// or https://" in str(exc_info.value)
    
    def test_reject_domain_without_protocol(self, monkeypatch):
        """Test that domain names without protocol are rejected."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://test")
        monkeypatch.setenv("ML_MODEL_PATH", "/test/path")
        monkeypatch.setenv("CORS_ORIGINS", "example.com")
        
        with pytest.raises(ValidationError) as exc_info:
            Configuration()
        
        assert "Origins must be full URLs starting with http:// or https://" in str(exc_info.value)
    
    def test_mixed_valid_and_wildcard(self, monkeypatch):
        """Test that wildcard is detected even when mixed with valid origins."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://test")
        monkeypatch.setenv("ML_MODEL_PATH", "/test/path")
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000,*")
        monkeypatch.setenv("DEBUG", "False")
        
        with pytest.raises(ValidationError) as exc_info:
            Configuration()
        
        assert "Wildcard (*) CORS origins are not allowed in production" in str(exc_info.value)
    
    def test_https_origins_accepted(self, monkeypatch):
        """Test that HTTPS origins are accepted."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://test")
        monkeypatch.setenv("ML_MODEL_PATH", "/test/path")
        monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com,https://api.example.com")
        
        config = Configuration()
        assert config.cors_origins == [
            "https://app.example.com",
            "https://api.example.com"
        ]
    
    def test_cors_origins_as_list(self, monkeypatch):
        """Test that CORS_ORIGINS can be provided as a list."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://test")
        monkeypatch.setenv("ML_MODEL_PATH", "/test/path")
        
        # This test simulates programmatic configuration
        config = Configuration(
            database_url="postgresql://test",
            ml_model_path="/test/path",
            cors_origins=["http://localhost:3000", "http://localhost:3001"]
        )
        
        assert config.cors_origins == ["http://localhost:3000", "http://localhost:3001"]


class TestCORSMiddlewareIntegration:
    """Test CORS middleware integration with FastAPI."""
    
    def test_cors_middleware_configured(self):
        """Test that CORS middleware is properly configured."""
        from fastapi import FastAPI
        from backend.api.router import configure_cors
        
        app = FastAPI()
        origins = ["http://localhost:3000", "http://localhost:3001"]
        
        configure_cors(app, origins)
        
        # Check that CORS middleware was added
        cors_middleware = None
        for middleware in app.user_middleware:
            if "CORSMiddleware" in str(middleware.cls):
                cors_middleware = middleware
                break
        
        assert cors_middleware is not None, "CORS middleware not found"
    
    def test_cors_allows_configured_origin(self):
        """Test that requests from configured origins are allowed."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from backend.api.router import configure_cors
        
        app = FastAPI()
        origins = ["http://localhost:3000"]
        configure_cors(app, origins)
        
        @app.get("/test")
        def test_endpoint():
            return {"message": "test"}
        
        client = TestClient(app)
        response = client.get(
            "/test",
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
    
    def test_cors_rejects_unauthorized_origin(self):
        """Test that requests from unauthorized origins are rejected."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from backend.api.router import configure_cors
        
        app = FastAPI()
        origins = ["http://localhost:3000"]
        configure_cors(app, origins)
        
        @app.get("/test")
        def test_endpoint():
            return {"message": "test"}
        
        client = TestClient(app)
        response = client.options(
            "/test",
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "GET"
            }
        )
        
        # CORS should not include the unauthorized origin in the response
        if "access-control-allow-origin" in response.headers:
            assert response.headers["access-control-allow-origin"] != "http://evil.com"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
