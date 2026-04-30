"""
Integration test for configuration management with environment variables.

This test verifies that the configuration system works correctly when
environment variables are set.
"""

import os
import sys

# Set required environment variables for testing
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test_db"
os.environ["ML_MODEL_PATH"] = "../ml/models"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test-key"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://localhost:3001"

# Now import and test configuration
from backend.config import get_config, Configuration

def test_environment_variable_loading():
    """Test that configuration loads from environment variables."""
    print("Testing configuration loading from environment variables...")
    
    config = get_config()
    
    assert config.database_url == "postgresql+asyncpg://test:test@localhost:5432/test_db"
    assert config.ml_model_path == "../ml/models"
    assert config.redis_url == "redis://localhost:6379/0"
    assert config.anthropic_api_key == "sk-ant-test-key"
    assert config.secret_key == "test-secret-key"
    assert len(config.cors_origins) == 2
    assert "http://localhost:3000" in config.cors_origins
    assert "http://localhost:3001" in config.cors_origins
    
    print("✓ Configuration loaded successfully from environment variables")
    print(f"  Database URL: {config.database_url}")
    print(f"  ML Model Path: {config.ml_model_path}")
    print(f"  Redis URL: {config.redis_url}")
    print(f"  CORS Origins: {config.cors_origins}")
    print()


def test_configuration_singleton():
    """Test that get_config returns the same instance."""
    print("Testing configuration singleton pattern...")
    
    config1 = get_config()
    config2 = get_config()
    
    assert config1 is config2, "get_config should return the same instance"
    
    print("✓ Configuration singleton pattern works correctly")
    print()


def test_direct_instantiation():
    """Test creating Configuration directly."""
    print("Testing direct Configuration instantiation...")
    
    config = Configuration(
        database_url="postgresql://localhost/direct_test",
        ml_model_path="/direct/path/to/models"
    )
    
    assert config.database_url == "postgresql://localhost/direct_test"
    assert config.ml_model_path == "/direct/path/to/models"
    
    print("✓ Direct Configuration instantiation works correctly")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("Configuration Integration Tests")
    print("=" * 60)
    print()
    
    try:
        test_environment_variable_loading()
        test_configuration_singleton()
        test_direct_instantiation()
        
        print("=" * 60)
        print("All integration tests passed!")
        print("=" * 60)
        sys.exit(0)
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        sys.exit(1)
