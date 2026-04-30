"""
Tests for Configuration Management

Tests cover:
- Configuration object creation and validation
- JSON file parsing (parse_config)
- JSON formatting (print_config)
- Round-trip property: parse(print(parse(json))) == parse(json)
- Error handling for invalid configurations

Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7
"""

import json
import os
import tempfile
import pytest
from backend.config import Configuration, parse_config, print_config


class TestConfigurationValidation:
    """Test Configuration object validation."""
    
    def test_valid_minimal_config(self):
        """Test creating a Configuration with only required fields."""
        config = Configuration(
            database_url="postgresql://localhost/test",
            ml_model_path="/path/to/models"
        )
        assert config.database_url == "postgresql://localhost/test"
        assert config.ml_model_path == "/path/to/models"
        assert config.redis_url is None
        assert config.anthropic_api_key is None
        assert config.secret_key is None
        assert config.cors_origins == ["http://localhost:3000"]
    
    def test_valid_full_config(self):
        """Test creating a Configuration with all fields."""
        config = Configuration(
            database_url="postgresql://localhost/test",
            ml_model_path="/path/to/models",
            redis_url="redis://localhost:6379",
            anthropic_api_key="sk-ant-test123",
            secret_key="supersecret",
            cors_origins=["http://localhost:3000", "http://localhost:3001"]
        )
        assert config.database_url == "postgresql://localhost/test"
        assert config.ml_model_path == "/path/to/models"
        assert config.redis_url == "redis://localhost:6379"
        assert config.anthropic_api_key == "sk-ant-test123"
        assert config.secret_key == "supersecret"
        assert len(config.cors_origins) == 2
    
    def test_missing_database_url(self):
        """Test that missing database_url raises validation error."""
        with pytest.raises(Exception) as exc_info:
            Configuration(ml_model_path="/path/to/models")
        assert "database_url" in str(exc_info.value).lower()
    
    def test_missing_ml_model_path(self):
        """Test that missing ml_model_path raises validation error."""
        with pytest.raises(Exception) as exc_info:
            Configuration(database_url="postgresql://localhost/test")
        assert "ml_model_path" in str(exc_info.value).lower()
    
    def test_empty_database_url(self):
        """Test that empty database_url raises validation error."""
        with pytest.raises(ValueError) as exc_info:
            Configuration(
                database_url="",
                ml_model_path="/path/to/models"
            )
        assert "database_url" in str(exc_info.value).lower()
    
    def test_empty_ml_model_path(self):
        """Test that empty ml_model_path raises validation error."""
        with pytest.raises(ValueError) as exc_info:
            Configuration(
                database_url="postgresql://localhost/test",
                ml_model_path=""
            )
        assert "ml_model_path" in str(exc_info.value).lower()
    
    def test_cors_origins_from_string(self):
        """Test parsing cors_origins from comma-separated string."""
        config = Configuration(
            database_url="postgresql://localhost/test",
            ml_model_path="/path/to/models",
            cors_origins="http://localhost:3000,http://localhost:3001,http://example.com"
        )
        assert len(config.cors_origins) == 3
        assert "http://localhost:3000" in config.cors_origins
        assert "http://localhost:3001" in config.cors_origins
        assert "http://example.com" in config.cors_origins


class TestParseConfig:
    """Test parse_config function."""
    
    def test_parse_valid_minimal_config(self):
        """Test parsing a valid minimal JSON configuration file."""
        config_data = {
            "database_url": "postgresql://localhost/test",
            "ml_model_path": "/path/to/models"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = parse_config(temp_path)
            assert config.database_url == "postgresql://localhost/test"
            assert config.ml_model_path == "/path/to/models"
        finally:
            os.unlink(temp_path)
    
    def test_parse_valid_full_config(self):
        """Test parsing a valid full JSON configuration file."""
        config_data = {
            "database_url": "postgresql://localhost/test",
            "ml_model_path": "/path/to/models",
            "redis_url": "redis://localhost:6379",
            "anthropic_api_key": "sk-ant-test123",
            "secret_key": "supersecret",
            "cors_origins": ["http://localhost:3000", "http://localhost:3001"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = parse_config(temp_path)
            assert config.database_url == "postgresql://localhost/test"
            assert config.redis_url == "redis://localhost:6379"
            assert config.anthropic_api_key == "sk-ant-test123"
            assert len(config.cors_origins) == 2
        finally:
            os.unlink(temp_path)
    
    def test_parse_missing_file(self):
        """Test that parsing a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError) as exc_info:
            parse_config("/nonexistent/config.json")
        assert "not found" in str(exc_info.value).lower()
    
    def test_parse_invalid_json(self):
        """Test that parsing invalid JSON raises JSONDecodeError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name
        
        try:
            with pytest.raises(json.JSONDecodeError):
                parse_config(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_parse_missing_required_field(self):
        """Test that parsing config without required fields raises ValueError."""
        config_data = {
            "database_url": "postgresql://localhost/test"
            # Missing ml_model_path
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError) as exc_info:
                parse_config(temp_path)
            assert "validation failed" in str(exc_info.value).lower()
        finally:
            os.unlink(temp_path)


class TestPrintConfig:
    """Test print_config function."""
    
    def test_print_minimal_config(self):
        """Test formatting a minimal Configuration as JSON."""
        config = Configuration(
            database_url="postgresql://localhost/test",
            ml_model_path="/path/to/models"
        )
        
        json_str = print_config(config)
        parsed = json.loads(json_str)
        
        assert parsed["database_url"] == "postgresql://localhost/test"
        assert parsed["ml_model_path"] == "/path/to/models"
    
    def test_print_full_config(self):
        """Test formatting a full Configuration as JSON."""
        config = Configuration(
            database_url="postgresql://localhost/test",
            ml_model_path="/path/to/models",
            redis_url="redis://localhost:6379",
            anthropic_api_key="sk-ant-test123",
            secret_key="supersecret",
            cors_origins=["http://localhost:3000", "http://localhost:3001"]
        )
        
        json_str = print_config(config)
        parsed = json.loads(json_str)
        
        assert parsed["database_url"] == "postgresql://localhost/test"
        assert parsed["redis_url"] == "redis://localhost:6379"
        assert parsed["anthropic_api_key"] == "sk-ant-test123"
        assert len(parsed["cors_origins"]) == 2
    
    def test_print_config_formatting(self):
        """Test that print_config uses 2-space indentation and sorted keys."""
        config = Configuration(
            database_url="postgresql://localhost/test",
            ml_model_path="/path/to/models",
            redis_url="redis://localhost:6379"
        )
        
        json_str = print_config(config)
        
        # Check 2-space indentation at root level
        assert '  "' in json_str
        
        # Verify it's valid JSON with proper formatting
        parsed = json.loads(json_str)
        reformatted = json.dumps(parsed, indent=2, sort_keys=True)
        assert json_str == reformatted, "Should use 2-space indentation and sorted keys"
    
    def test_print_config_valid_json(self):
        """Test that print_config produces valid JSON."""
        config = Configuration(
            database_url="postgresql://localhost/test",
            ml_model_path="/path/to/models"
        )
        
        json_str = print_config(config)
        
        # Should be parseable as JSON
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)


class TestRoundTripProperty:
    """
    Test the round-trip property: parse(print(parse(json))) == parse(json)
    
    Requirement 19.6: FOR ALL valid Configuration objects, parsing then printing
    then parsing SHALL produce an equivalent Configuration object.
    """
    
    def test_round_trip_minimal_config(self):
        """Test round-trip property with minimal configuration."""
        config_data = {
            "database_url": "postgresql://localhost/test",
            "ml_model_path": "/path/to/models"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            # First parse
            config1 = parse_config(temp_path)
            
            # Print to JSON
            json_str = print_config(config1)
            
            # Write to new file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f2:
                f2.write(json_str)
                temp_path2 = f2.name
            
            try:
                # Second parse
                config2 = parse_config(temp_path2)
                
                # Verify equivalence
                assert config1.database_url == config2.database_url
                assert config1.ml_model_path == config2.ml_model_path
                assert config1.redis_url == config2.redis_url
                assert config1.anthropic_api_key == config2.anthropic_api_key
                assert config1.secret_key == config2.secret_key
                assert config1.cors_origins == config2.cors_origins
            finally:
                os.unlink(temp_path2)
        finally:
            os.unlink(temp_path)
    
    def test_round_trip_full_config(self):
        """Test round-trip property with full configuration."""
        config_data = {
            "database_url": "postgresql://user:pass@localhost:5432/db",
            "ml_model_path": "/path/to/models",
            "redis_url": "redis://localhost:6379/0",
            "anthropic_api_key": "sk-ant-test123",
            "secret_key": "supersecret",
            "cors_origins": ["http://localhost:3000", "http://localhost:3001", "http://example.com"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            # First parse
            config1 = parse_config(temp_path)
            
            # Print to JSON
            json_str = print_config(config1)
            
            # Write to new file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f2:
                f2.write(json_str)
                temp_path2 = f2.name
            
            try:
                # Second parse
                config2 = parse_config(temp_path2)
                
                # Verify equivalence
                assert config1.database_url == config2.database_url
                assert config1.ml_model_path == config2.ml_model_path
                assert config1.redis_url == config2.redis_url
                assert config1.anthropic_api_key == config2.anthropic_api_key
                assert config1.secret_key == config2.secret_key
                assert config1.cors_origins == config2.cors_origins
            finally:
                os.unlink(temp_path2)
        finally:
            os.unlink(temp_path)
    
    def test_round_trip_with_none_values(self):
        """Test round-trip property preserves None values for optional fields."""
        config_data = {
            "database_url": "postgresql://localhost/test",
            "ml_model_path": "/path/to/models",
            "redis_url": None,
            "anthropic_api_key": None,
            "secret_key": None
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            # First parse
            config1 = parse_config(temp_path)
            
            # Print to JSON
            json_str = print_config(config1)
            
            # Write to new file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f2:
                f2.write(json_str)
                temp_path2 = f2.name
            
            try:
                # Second parse
                config2 = parse_config(temp_path2)
                
                # Verify equivalence (None values should be preserved)
                assert config1.redis_url == config2.redis_url
                assert config1.anthropic_api_key == config2.anthropic_api_key
                assert config1.secret_key == config2.secret_key
            finally:
                os.unlink(temp_path2)
        finally:
            os.unlink(temp_path)


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_config_with_special_characters(self):
        """Test configuration with special characters in values."""
        config = Configuration(
            database_url="postgresql://user:p@ss!w0rd@localhost:5432/db",
            ml_model_path="/path/to/models with spaces",
            secret_key="key_with_special_chars!@#$%^&*()"
        )
        
        json_str = print_config(config)
        parsed = json.loads(json_str)
        
        assert parsed["database_url"] == "postgresql://user:p@ss!w0rd@localhost:5432/db"
        assert parsed["ml_model_path"] == "/path/to/models with spaces"
        assert parsed["secret_key"] == "key_with_special_chars!@#$%^&*()"
    
    def test_config_with_unicode(self):
        """Test configuration with unicode characters."""
        config = Configuration(
            database_url="postgresql://localhost/test",
            ml_model_path="/path/to/模型",  # Chinese characters
            secret_key="clé_secrète"  # French characters
        )
        
        json_str = print_config(config)
        parsed = json.loads(json_str)
        
        assert parsed["ml_model_path"] == "/path/to/模型"
        assert parsed["secret_key"] == "clé_secrète"
    
    def test_empty_cors_origins_list(self):
        """Test configuration with empty cors_origins list."""
        config = Configuration(
            database_url="postgresql://localhost/test",
            ml_model_path="/path/to/models",
            cors_origins=[]
        )
        
        assert config.cors_origins == []
        
        json_str = print_config(config)
        parsed = json.loads(json_str)
        assert parsed["cors_origins"] == []
