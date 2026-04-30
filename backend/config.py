"""
EduRisk AI Backend - Configuration Management

This module provides configuration management using Pydantic Settings.
It supports loading configuration from environment variables and JSON files.

Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.7
"""

import json
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuration(BaseSettings):
    """
    Application configuration using Pydantic Settings.
    
    Supports loading from environment variables and JSON files.
    Required fields: database_url, ml_model_path
    Optional fields: redis_url, anthropic_api_key, secret_key, cors_origins
    
    Requirements: 19.1, 19.2, 19.3, 19.4
    """
    
    # Required fields
    database_url: str = Field(
        ...,
        description="PostgreSQL database connection URL"
    )
    ml_model_path: str = Field(
        ...,
        description="Path to ML model files directory"
    )
    
    # Optional fields
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis connection URL for caching"
    )
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key for LLM integration"
    )
    secret_key: Optional[str] = Field(
        default=None,
        description="Secret key for JWT token signing"
    )
    cors_origins: str | List[str] = Field(
        default="http://localhost:3000",
        description="Allowed CORS origins (comma-separated string or list)"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate that database_url is not empty."""
        if not v or not v.strip():
            raise ValueError("database_url is required and cannot be empty")
        return v
    
    @field_validator("ml_model_path")
    @classmethod
    def validate_ml_model_path(cls, v: str) -> str:
        """Validate that ml_model_path is not empty."""
        if not v or not v.strip():
            raise ValueError("ml_model_path is required and cannot be empty")
        return v
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v) -> List[str]:
        """Parse cors_origins from string or list."""
        if v is None or v == "":
            return ["http://localhost:3000"]
        if isinstance(v, str):
            # Split comma-separated string into list
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return v
        # If it's some other type, try to convert to list
        return list(v)
    
    def model_post_init(self, __context) -> None:
        """Ensure cors_origins is always a list after initialization."""
        if isinstance(self.cors_origins, str):
            self.cors_origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


def parse_config(file_path: str) -> Configuration:
    """
    Parse a JSON configuration file into a Configuration object.
    
    Args:
        file_path: Path to the JSON configuration file
        
    Returns:
        Configuration object with validated settings
        
    Raises:
        FileNotFoundError: If the configuration file does not exist
        json.JSONDecodeError: If the file contains invalid JSON
        ValueError: If required fields are missing or validation fails
        
    Requirements: 19.1, 19.2, 19.3, 19.4, 19.5
    
    Example:
        >>> config = parse_config("config.json")
        >>> print(config.database_url)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in configuration file at line {e.lineno}, column {e.colno}: {e.msg}",
            e.doc,
            e.pos
        )
    
    try:
        return Configuration(**config_data)
    except Exception as e:
        raise ValueError(f"Configuration validation failed: {str(e)}")


def print_config(config: Configuration) -> str:
    """
    Format a Configuration object as a JSON string.
    
    The output is formatted with 2-space indentation and sorted keys,
    suitable for writing back to a configuration file.
    
    Args:
        config: Configuration object to format
        
    Returns:
        JSON string with 2-space indentation and sorted keys
        
    Requirements: 19.5, 19.7
    
    Example:
        >>> config = Configuration(database_url="postgresql://...", ml_model_path="/path")
        >>> json_str = print_config(config)
        >>> print(json_str)
    """
    # Convert Configuration to dict
    config_dict = config.model_dump(mode='json')
    
    # Format as JSON with 2-space indentation and sorted keys
    return json.dumps(config_dict, indent=2, sort_keys=True, ensure_ascii=False)


# Singleton instance for application-wide configuration
_config_instance: Optional[Configuration] = None


def get_config() -> Configuration:
    """
    Get the application configuration singleton.
    
    Loads configuration from environment variables on first call.
    Subsequent calls return the cached instance.
    
    Returns:
        Configuration object
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Configuration()
    return _config_instance


def set_config(config: Configuration) -> None:
    """
    Set the application configuration singleton.
    
    Useful for testing or loading configuration from files.
    
    Args:
        config: Configuration object to use
    """
    global _config_instance
    _config_instance = config
