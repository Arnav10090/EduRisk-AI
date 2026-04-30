# Configuration Management

This document describes the configuration management system for the EduRisk AI backend.

## Overview

The configuration management system uses Pydantic Settings to provide:
- Type-safe configuration with validation
- Support for environment variables
- JSON configuration file parsing
- Configuration serialization with proper formatting
- Round-trip property guarantees

## Requirements Implemented

- **19.1**: Parse configuration files into Configuration objects
- **19.2**: Return descriptive errors for invalid configuration files
- **19.3**: Support JSON format with required fields
- **19.4**: Validate required fields (database_url, ml_model_path)
- **19.5**: Provide Pretty_Printer (print_config) for formatting
- **19.6**: Round-trip property: parse(print(parse(json))) == parse(json)
- **19.7**: Format JSON with 2-space indentation and sorted keys

## Configuration Fields

### Required Fields
- `database_url` (str): PostgreSQL database connection URL
- `ml_model_path` (str): Path to ML model files directory

### Optional Fields
- `redis_url` (str): Redis connection URL for caching
- `anthropic_api_key` (str): Anthropic API key for LLM integration
- `secret_key` (str): Secret key for JWT token signing
- `cors_origins` (List[str]): Allowed CORS origins (default: ["http://localhost:3000"])

## Usage

### 1. Loading Configuration from Environment Variables

The simplest way to use configuration is through environment variables:

```python
from backend.config import get_config

# Load configuration from environment variables
config = get_config()

print(config.database_url)
print(config.ml_model_path)
```

Environment variables are automatically loaded from `.env` file if present.

### 2. Creating Configuration Programmatically

```python
from backend.config import Configuration

config = Configuration(
    database_url="postgresql://localhost/test",
    ml_model_path="/path/to/models",
    redis_url="redis://localhost:6379",
    anthropic_api_key="sk-ant-test123",
    secret_key="supersecret",
    cors_origins=["http://localhost:3000", "http://localhost:3001"]
)
```

### 3. Parsing Configuration from JSON File

```python
from backend.config import parse_config

# Parse configuration from JSON file
config = parse_config("config.json")

print(config.database_url)
print(config.ml_model_path)
```

Example JSON file (`config.json`):
```json
{
  "database_url": "postgresql://localhost/test",
  "ml_model_path": "/path/to/models",
  "redis_url": "redis://localhost:6379",
  "anthropic_api_key": "sk-ant-test123",
  "secret_key": "supersecret",
  "cors_origins": [
    "http://localhost:3000",
    "http://localhost:3001"
  ]
}
```

### 4. Printing Configuration as JSON

```python
from backend.config import print_config

# Format configuration as JSON string
json_str = print_config(config)
print(json_str)

# Write to file
with open("output.json", "w") as f:
    f.write(json_str)
```

Output format:
- 2-space indentation
- Sorted keys alphabetically
- Valid JSON that can be parsed back

### 5. Round-Trip Property

The configuration system guarantees that parsing, printing, and parsing again produces an equivalent configuration:

```python
from backend.config import parse_config, print_config

# Parse original
config1 = parse_config("config.json")

# Print to JSON
json_str = print_config(config1)

# Write and parse again
with open("temp.json", "w") as f:
    f.write(json_str)
config2 = parse_config("temp.json")

# config1 and config2 are equivalent
assert config1.database_url == config2.database_url
assert config1.ml_model_path == config2.ml_model_path
# ... all fields match
```

## Validation

The configuration system validates:

1. **Required fields**: `database_url` and `ml_model_path` must be present
2. **Non-empty values**: Required fields cannot be empty strings
3. **Type checking**: All fields must match their declared types

### Validation Examples

```python
from backend.config import Configuration

# Missing required field - raises ValidationError
try:
    config = Configuration(database_url="postgresql://localhost/test")
except Exception as e:
    print(f"Error: {e}")  # ml_model_path is required

# Empty required field - raises ValueError
try:
    config = Configuration(
        database_url="",
        ml_model_path="/path/to/models"
    )
except ValueError as e:
    print(f"Error: {e}")  # database_url cannot be empty
```

## Error Handling

### File Not Found
```python
from backend.config import parse_config

try:
    config = parse_config("/nonexistent/config.json")
except FileNotFoundError as e:
    print(f"Error: {e}")  # Configuration file not found
```

### Invalid JSON
```python
try:
    config = parse_config("invalid.json")
except json.JSONDecodeError as e:
    print(f"Error at line {e.lineno}, column {e.colno}: {e.msg}")
```

### Validation Errors
```python
try:
    config = parse_config("config.json")
except ValueError as e:
    print(f"Configuration validation failed: {e}")
```

## Integration with FastAPI

The configuration system integrates seamlessly with FastAPI:

```python
from fastapi import FastAPI
from backend.config import get_config

# Get configuration
config = get_config()

# Create FastAPI app
app = FastAPI()

# Use configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Environment Variable Mapping

Pydantic Settings automatically maps environment variables to configuration fields:

- `DATABASE_URL` → `database_url`
- `ML_MODEL_PATH` → `ml_model_path`
- `REDIS_URL` → `redis_url`
- `ANTHROPIC_API_KEY` → `anthropic_api_key`
- `SECRET_KEY` → `secret_key`
- `CORS_ORIGINS` → `cors_origins` (comma-separated string)

Example `.env` file:
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db
ML_MODEL_PATH=../ml/models
REDIS_URL=redis://localhost:6379/0
ANTHROPIC_API_KEY=sk-ant-your-key-here
SECRET_KEY=your-secret-key
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

## Testing

Run the test suite:
```bash
pytest backend/test_config.py -v
```

Run the demonstration script:
```bash
python -m backend.demo_config
```

## Files

- `backend/config.py` - Main configuration module
- `backend/test_config.py` - Comprehensive test suite
- `backend/demo_config.py` - Demonstration script
- `backend/config.example.json` - Example JSON configuration file
- `backend/.env.example` - Example environment variables file

## Best Practices

1. **Use environment variables for secrets**: Never commit API keys or passwords to version control
2. **Use JSON files for deployment configs**: Store non-sensitive configuration in JSON files
3. **Validate early**: Load and validate configuration at application startup
4. **Use the singleton pattern**: Call `get_config()` to get the shared configuration instance
5. **Test configuration changes**: Use the test suite to verify configuration changes

## Troubleshooting

### Configuration not loading from .env file
- Ensure `.env` file is in the correct directory (backend/)
- Check that `python-dotenv` is installed
- Verify environment variable names match the field names (case-insensitive)

### Validation errors
- Check that all required fields are present
- Verify field values are not empty strings
- Ensure types match (e.g., cors_origins should be a list or comma-separated string)

### Round-trip property fails
- This should never happen - if it does, it's a bug
- Check that JSON serialization preserves all field values
- Verify that parsing handles all field types correctly
