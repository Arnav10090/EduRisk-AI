# Error Handling and Logging Implementation

## Overview

This document describes the comprehensive error handling and structured logging implementation for the EduRisk AI backend system.

**Feature**: edurisk-ai-placement-intelligence  
**Requirements**: 22.1, 22.2, 22.3, 22.4, 22.5, 22.6

## Components

### 1. Error Handling Middleware (`backend/middleware/error_handler.py`)

#### Custom Exception Classes

The system provides a hierarchy of custom exception classes for different error scenarios:

- **`EduRiskException`**: Base exception class for all application errors
- **`ValidationError`**: HTTP 422 - Request validation failures
- **`DatabaseError`**: HTTP 503 - Database operation failures
- **`ModelError`**: HTTP 500 - ML model prediction failures
- **`ExternalServiceError`**: HTTP 503 - External API failures (e.g., Claude API)
- **`NotFoundError`**: HTTP 404 - Resource not found
- **`InternalServerError`**: HTTP 500 - Unexpected internal errors

#### Usage Example

```python
from backend.middleware import ValidationError, DatabaseError

# Raise validation error
if not student_id:
    raise ValidationError(
        "Student ID is required",
        details={"field": "student_id"}
    )

# Raise database error
try:
    result = await db.execute(query)
except Exception as e:
    raise DatabaseError(
        "Failed to query database",
        details={"operation": "select", "table": "students"}
    )
```

#### Error Response Format

All errors return a consistent JSON structure:

```json
{
  "error": "ValidationError",
  "message": "Student ID is required",
  "details": {
    "field": "student_id"
  },
  "path": "/api/predict",
  "timestamp": "2026-05-01T10:30:45.123456Z"
}
```

### 2. Structured Logging (`backend/middleware/logging_config.py`)

#### Configuration

The logging system uses JSON formatting for structured logs with the following fields:

- **timestamp**: ISO 8601 format with UTC timezone
- **level**: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **logger**: Logger name
- **message**: Log message
- **context**: Additional context fields

#### Setup

```python
from backend.middleware import configure_logging

# Configure with JSON format (production)
configure_logging(log_level="INFO", json_format=True)

# Configure with plain text (development)
configure_logging(log_level="DEBUG", json_format=False)
```

#### Environment Variables

- `LOG_LEVEL`: Logging level (default: "INFO")
- `LOG_JSON_FORMAT`: Use JSON format (default: "True")

### 3. Request Logger (`backend/middleware/logging_config.py`)

The `RequestLogger` class provides specialized logging methods for common scenarios:

#### API Request Logging

```python
from backend.middleware import request_logger

# Log request completion (Requirement 22.6)
request_logger.log_request_complete(
    method="POST",
    path="/api/predict",
    status_code=200,
    response_time=1.234,
    client_ip="192.168.1.1"
)
```

#### Prediction Request Logging

```python
# Log successful prediction
request_logger.log_prediction_request(
    student_id="123e4567-e89b-12d3-a456-426614174000",
    success=True
)

# Log failed prediction (Requirement 22.2)
request_logger.log_prediction_request(
    student_id="123e4567-e89b-12d3-a456-426614174000",
    success=False,
    error_type="ModelError",
    error_message="Model file not found"
)
```

#### Claude API Logging

```python
# Log Claude API call (Requirement 22.3)
request_logger.log_claude_api_call(
    success=False,
    status_code=503,
    error_message="Service temporarily unavailable"
)
```

#### Database Error Logging

```python
# Log database error (Requirement 22.4)
request_logger.log_database_error(
    operation="insert",
    error_type="IntegrityError",
    error_message="Duplicate key violation",
    sql_statement="INSERT INTO students ..."
)
```

### 4. Request Logging Middleware (`backend/middleware/request_logging.py`)

Automatically logs all API requests with:
- HTTP method
- Request path
- Status code
- Response time
- Client IP address

Adds `X-Process-Time` header to all responses.

## Requirements Mapping

### Requirement 22.1: Unhandled Exception Logging

**Implementation**: `ErrorHandlingMiddleware` catches all unhandled exceptions and logs them with full stack traces at ERROR level.

```python
logger.error(
    f"Unhandled exception: {str(e)}",
    extra={
        "error_type": type(e).__name__,
        "path": request.url.path,
        "method": request.method,
        "stack_trace": stack_trace,
        "timestamp": datetime.now(timezone.utc).isoformat()
    },
    exc_info=True
)
```

### Requirement 22.2: Prediction Request Failure Logging

**Implementation**: `RequestLogger.log_prediction_request()` logs student_id, error type, and error message.

```python
request_logger.log_prediction_request(
    student_id=student_id,
    success=False,
    error_type="ModelError",
    error_message="Model prediction failed"
)
```

### Requirement 22.3: Claude API Failure Logging

**Implementation**: `RequestLogger.log_claude_api_call()` logs API response status and error message.

```python
request_logger.log_claude_api_call(
    success=False,
    status_code=503,
    error_message="API timeout"
)
```

### Requirement 22.4: Database Query Failure Logging

**Implementation**: `RequestLogger.log_database_error()` logs SQL statement and error details.

```python
request_logger.log_database_error(
    operation="select",
    error_type="OperationalError",
    error_message="Connection timeout",
    sql_statement="SELECT * FROM students WHERE id = ?"
)
```

### Requirement 22.5: Structured JSON Logging

**Implementation**: `CustomJsonFormatter` formats all logs as JSON with timestamp, level, message, and context fields.

Example output:
```json
{
  "timestamp": "2026-05-01T10:30:45.123456Z",
  "level": "ERROR",
  "logger": "edurisk.api",
  "message": "Prediction failed for student 123",
  "context": {
    "event": "prediction_failure",
    "student_id": "123",
    "error_type": "ModelError",
    "error_message": "Model file not found"
  }
}
```

### Requirement 22.6: API Request Logging

**Implementation**: `RequestLoggingMiddleware` logs all API requests with INFO level including method, path, status code, and response time.

Example output:
```json
{
  "timestamp": "2026-05-01T10:30:45.123456Z",
  "level": "INFO",
  "logger": "edurisk.api.requests",
  "message": "Request completed: POST /api/predict - Status: 200 - Time: 1.234s",
  "context": {
    "event": "request_complete",
    "method": "POST",
    "path": "/api/predict",
    "status_code": 200,
    "response_time": 1.234,
    "client_ip": "192.168.1.1"
  }
}
```

## Integration

The error handling and logging middleware is automatically configured in `backend/api/router.py`:

```python
from backend.middleware import (
    ErrorHandlingMiddleware,
    RequestLoggingMiddleware,
    configure_logging
)

# Configure structured logging
configure_logging(log_level="INFO", json_format=True)

# Add middleware to app
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestLoggingMiddleware)
```

## Testing

Run the error handling tests:

```bash
python -m pytest backend/test_error_handling.py -v
```

All tests should pass with 100% coverage of error handling logic.

## Best Practices

1. **Use Custom Exceptions**: Always raise custom exception types instead of generic exceptions
2. **Include Context**: Add relevant details to exception `details` parameter
3. **Log Before Raising**: Log errors with context before raising exceptions
4. **Don't Expose Internals**: Never expose internal error details in production responses
5. **Use Request Logger**: Use the specialized `RequestLogger` methods for consistent logging

## Example: Complete Error Handling Flow

```python
from backend.middleware import (
    DatabaseError,
    request_logger
)

async def get_student(student_id: str, db: AsyncSession):
    try:
        result = await db.execute(
            select(Student).where(Student.id == student_id)
        )
        student = result.scalar_one_or_none()
        
        if not student:
            raise NotFoundError(
                f"Student not found",
                details={"student_id": student_id}
            )
        
        return student
        
    except SQLAlchemyError as e:
        # Log database error
        request_logger.log_database_error(
            operation="select",
            error_type=type(e).__name__,
            error_message=str(e),
            sql_statement=f"SELECT * FROM students WHERE id = {student_id}"
        )
        
        # Raise custom exception
        raise DatabaseError(
            "Failed to retrieve student",
            details={
                "student_id": student_id,
                "operation": "select"
            }
        )
```

## Monitoring and Observability

The structured JSON logs can be easily ingested by log aggregation systems like:

- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Splunk**
- **Datadog**
- **CloudWatch Logs**

All logs include consistent fields for filtering and analysis:
- `timestamp`: For time-series analysis
- `level`: For filtering by severity
- `logger`: For filtering by component
- `context.event`: For filtering by event type
- `context.error_type`: For error analysis
- `context.path`: For endpoint analysis
- `context.response_time`: For performance monitoring
