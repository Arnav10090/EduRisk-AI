"""
Demonstration script for configuration management.

This script demonstrates:
1. Creating a Configuration object
2. Parsing configuration from JSON file
3. Printing configuration back to JSON
4. Round-trip property verification
"""

from backend.config import Configuration, parse_config, print_config


def demo_basic_usage():
    """Demonstrate basic configuration usage."""
    print("=" * 60)
    print("Demo 1: Creating Configuration from code")
    print("=" * 60)
    
    config = Configuration(
        database_url="postgresql://localhost/test",
        ml_model_path="/path/to/models",
        redis_url="redis://localhost:6379",
        anthropic_api_key="sk-ant-test123",
        secret_key="supersecret",
        cors_origins=["http://localhost:3000", "http://localhost:3001"]
    )
    
    print(f"Database URL: {config.database_url}")
    print(f"ML Model Path: {config.ml_model_path}")
    print(f"Redis URL: {config.redis_url}")
    print(f"CORS Origins: {config.cors_origins}")
    print()


def demo_parse_and_print():
    """Demonstrate parsing and printing configuration."""
    print("=" * 60)
    print("Demo 2: Parsing configuration from JSON file")
    print("=" * 60)
    
    # Parse configuration from example file
    config = parse_config("backend/config.example.json")
    
    print(f"Loaded configuration:")
    print(f"  Database URL: {config.database_url}")
    print(f"  ML Model Path: {config.ml_model_path}")
    print(f"  Redis URL: {config.redis_url}")
    print(f"  CORS Origins: {config.cors_origins}")
    print()
    
    print("=" * 60)
    print("Demo 3: Printing configuration as JSON")
    print("=" * 60)
    
    json_output = print_config(config)
    print(json_output)
    print()


def demo_round_trip():
    """Demonstrate round-trip property."""
    print("=" * 60)
    print("Demo 4: Round-trip property verification")
    print("=" * 60)
    
    # Parse original
    config1 = parse_config("backend/config.example.json")
    print("Step 1: Parsed configuration from file")
    
    # Print to JSON
    json_str = print_config(config1)
    print("Step 2: Converted to JSON string")
    
    # Write to temporary file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(json_str)
        temp_path = f.name
    print(f"Step 3: Wrote to temporary file: {temp_path}")
    
    # Parse again
    config2 = parse_config(temp_path)
    print("Step 4: Parsed configuration from temporary file")
    
    # Verify equivalence
    print("\nVerifying equivalence:")
    print(f"  database_url matches: {config1.database_url == config2.database_url}")
    print(f"  ml_model_path matches: {config1.ml_model_path == config2.ml_model_path}")
    print(f"  redis_url matches: {config1.redis_url == config2.redis_url}")
    print(f"  anthropic_api_key matches: {config1.anthropic_api_key == config2.anthropic_api_key}")
    print(f"  secret_key matches: {config1.secret_key == config2.secret_key}")
    print(f"  cors_origins matches: {config1.cors_origins == config2.cors_origins}")
    
    # Clean up
    import os
    os.unlink(temp_path)
    print(f"\nCleaned up temporary file")
    print()


def demo_validation():
    """Demonstrate validation errors."""
    print("=" * 60)
    print("Demo 5: Validation error handling")
    print("=" * 60)
    
    try:
        # Missing required field
        config = Configuration(
            database_url="postgresql://localhost/test"
            # Missing ml_model_path
        )
    except Exception as e:
        print(f"Error when missing ml_model_path: {e}")
    
    try:
        # Empty required field
        config = Configuration(
            database_url="",
            ml_model_path="/path/to/models"
        )
    except Exception as e:
        print(f"Error when database_url is empty: {e}")
    
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Configuration Management Demonstration")
    print("=" * 60 + "\n")
    
    demo_basic_usage()
    demo_parse_and_print()
    demo_round_trip()
    demo_validation()
    
    print("=" * 60)
    print("All demonstrations completed successfully!")
    print("=" * 60)
