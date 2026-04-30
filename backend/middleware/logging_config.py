"""
Structured Logging Configuration

This module configures structured JSON logging for the application
with consistent formatting and context fields.

Feature: edurisk-ai-placement-intelligence
Requirements: 22.1, 22.2, 22.3, 22.4, 22.5, 22.6
"""

import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter that adds standard fields to all log records.
    
    Requirement 22.5: JSON format with timestamp, level, message, context
    """
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        """Add custom fields to log record"""
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO format
        log_record['timestamp'] = datetime.now(timezone.utc).isoformat() + 'Z'
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add logger name
        log_record['logger'] = record.name
        
        # Add message
        log_record['message'] = record.getMessage()
        
        # Add context from extra fields
        context = {}
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'levelno', 'lineno', 'module', 'msecs',
                          'message', 'pathname', 'process', 'processName',
                          'relativeCreated', 'thread', 'threadName', 'exc_info',
                          'exc_text', 'stack_info', 'timestamp', 'level', 'logger']:
                context[key] = value
        
        if context:
            log_record['context'] = context
        
        # Add exception info if present
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)


def configure_logging(log_level: str = "INFO", json_format: bool = True):
    """
    Configure structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Whether to use JSON formatting (True) or plain text (False)
        
    Requirements: 22.5, 22.6
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    if json_format:
        # Use JSON formatter for structured logging
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(logger)s %(message)s'
        )
    else:
        # Use plain text formatter for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    
    root_logger.info(
        "Logging configured",
        extra={
            "log_level": log_level,
            "json_format": json_format
        }
    )


class RequestLogger:
    """
    Helper class for logging API requests with consistent context.
    
    Requirement 22.6: Log all API requests with method, path, status, response time
    """
    
    def __init__(self, logger_name: str = __name__):
        self.logger = logging.getLogger(logger_name)
    
    def log_request_start(self, method: str, path: str, client_ip: str = None):
        """Log the start of an API request"""
        self.logger.info(
            f"Request started: {method} {path}",
            extra={
                "event": "request_start",
                "method": method,
                "path": path,
                "client_ip": client_ip
            }
        )
    
    def log_request_complete(
        self,
        method: str,
        path: str,
        status_code: int,
        response_time: float,
        client_ip: str = None
    ):
        """
        Log the completion of an API request.
        
        Requirement 22.6: Include method, path, status code, response time
        """
        self.logger.info(
            f"Request completed: {method} {path} - Status: {status_code} - Time: {response_time:.3f}s",
            extra={
                "event": "request_complete",
                "method": method,
                "path": path,
                "status_code": status_code,
                "response_time": response_time,
                "client_ip": client_ip
            }
        )
    
    def log_prediction_request(
        self,
        student_id: str = None,
        success: bool = True,
        error_type: str = None,
        error_message: str = None
    ):
        """
        Log prediction request outcomes.
        
        Requirement 22.2: Log student_id, error type, error message on failure
        """
        if success:
            self.logger.info(
                f"Prediction successful for student {student_id}",
                extra={
                    "event": "prediction_success",
                    "student_id": student_id
                }
            )
        else:
            self.logger.error(
                f"Prediction failed for student {student_id}: {error_message}",
                extra={
                    "event": "prediction_failure",
                    "student_id": student_id,
                    "error_type": error_type,
                    "error_message": error_message
                }
            )
    
    def log_claude_api_call(
        self,
        success: bool,
        status_code: int = None,
        error_message: str = None,
        response_time: float = None
    ):
        """
        Log Claude API call outcomes.
        
        Requirement 22.3: Log API response status and error message
        """
        if success:
            self.logger.info(
                f"Claude API call successful - Time: {response_time:.3f}s",
                extra={
                    "event": "claude_api_success",
                    "status_code": status_code,
                    "response_time": response_time
                }
            )
        else:
            self.logger.error(
                f"Claude API call failed: {error_message}",
                extra={
                    "event": "claude_api_failure",
                    "status_code": status_code,
                    "error_message": error_message
                }
            )
    
    def log_database_error(
        self,
        operation: str,
        error_type: str,
        error_message: str,
        sql_statement: str = None
    ):
        """
        Log database operation errors.
        
        Requirement 22.4: Log SQL statement and error details
        """
        self.logger.error(
            f"Database error during {operation}: {error_message}",
            extra={
                "event": "database_error",
                "operation": operation,
                "error_type": error_type,
                "error_message": error_message,
                "sql_statement": sql_statement
            }
        )


# Create a global request logger instance
request_logger = RequestLogger("edurisk.api")
