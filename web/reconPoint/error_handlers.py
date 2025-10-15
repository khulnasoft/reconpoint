"""
Enhanced error handling utilities for reconPoint.
"""
import logging
import traceback
from typing import Optional, Dict, Any, Callable
from functools import wraps

from django.http import JsonResponse
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


logger = logging.getLogger(__name__)


class ReconPointException(Exception):
    """Base exception for reconPoint."""
    
    def __init__(self, message: str, code: str = 'RECONPOINT_ERROR', details: Optional[Dict] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(ReconPointException):
    """Exception for validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict] = None):
        super().__init__(message, 'VALIDATION_ERROR', details)
        self.field = field


class AuthenticationException(ReconPointException):
    """Exception for authentication errors."""
    
    def __init__(self, message: str = 'Authentication failed', details: Optional[Dict] = None):
        super().__init__(message, 'AUTHENTICATION_ERROR', details)


class AuthorizationException(ReconPointException):
    """Exception for authorization errors."""
    
    def __init__(self, message: str = 'Permission denied', details: Optional[Dict] = None):
        super().__init__(message, 'AUTHORIZATION_ERROR', details)


class ResourceNotFoundException(ReconPointException):
    """Exception for resource not found errors."""
    
    def __init__(self, resource: str, identifier: Any, details: Optional[Dict] = None):
        message = f'{resource} with identifier {identifier} not found'
        super().__init__(message, 'RESOURCE_NOT_FOUND', details)
        self.resource = resource
        self.identifier = identifier


class RateLimitException(ReconPointException):
    """Exception for rate limit errors."""
    
    def __init__(self, message: str = 'Rate limit exceeded', retry_after: Optional[int] = None):
        details = {'retry_after': retry_after} if retry_after else {}
        super().__init__(message, 'RATE_LIMIT_EXCEEDED', details)


class ExternalServiceException(ReconPointException):
    """Exception for external service errors."""
    
    def __init__(self, service: str, message: str, details: Optional[Dict] = None):
        super().__init__(f'{service} error: {message}', 'EXTERNAL_SERVICE_ERROR', details)
        self.service = service


class DatabaseException(ReconPointException):
    """Exception for database errors."""
    
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, 'DATABASE_ERROR', details)


class TaskException(ReconPointException):
    """Exception for Celery task errors."""
    
    def __init__(self, task_name: str, message: str, details: Optional[Dict] = None):
        super().__init__(f'Task {task_name} failed: {message}', 'TASK_ERROR', details)
        self.task_name = task_name


def custom_exception_handler(exc, context):
    """
    Custom exception handler for Django REST Framework.
    
    Args:
        exc: The exception instance
        context: Context dictionary with view and request
        
    Returns:
        Response object with error details
    """
    # Call DRF's default exception handler first
    response = drf_exception_handler(exc, context)
    
    # If DRF handled it, return the response
    if response is not None:
        return response
    
    # Handle custom exceptions
    if isinstance(exc, ReconPointException):
        error_response = {
            'error': exc.code,
            'message': exc.message,
            'details': exc.details
        }
        
        # Determine status code based on exception type
        if isinstance(exc, ValidationException):
            status_code = status.HTTP_400_BAD_REQUEST
        elif isinstance(exc, AuthenticationException):
            status_code = status.HTTP_401_UNAUTHORIZED
        elif isinstance(exc, AuthorizationException):
            status_code = status.HTTP_403_FORBIDDEN
        elif isinstance(exc, ResourceNotFoundException):
            status_code = status.HTTP_404_NOT_FOUND
        elif isinstance(exc, RateLimitException):
            status_code = status.HTTP_429_TOO_MANY_REQUESTS
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        # Log the error
        logger.error(
            f"Exception: {exc.code}",
            extra={
                'exception_type': type(exc).__name__,
                'message': exc.message,
                'details': exc.details,
                'view': context.get('view'),
                'request': context.get('request')
            }
        )
        
        return Response(error_response, status=status_code)
    
    # Handle unexpected exceptions
    logger.exception(
        "Unhandled exception",
        extra={
            'exception_type': type(exc).__name__,
            'view': context.get('view'),
            'request': context.get('request')
        }
    )
    
    # In production, don't expose internal error details
    if settings.DEBUG:
        error_response = {
            'error': 'INTERNAL_ERROR',
            'message': str(exc),
            'traceback': traceback.format_exc()
        }
    else:
        error_response = {
            'error': 'INTERNAL_ERROR',
            'message': 'An internal error occurred. Please contact support.'
        }
    
    return Response(error_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def handle_exceptions(default_return=None, log_traceback=True):
    """
    Decorator to handle exceptions in functions.
    
    Args:
        default_return: Value to return if exception occurs
        log_traceback: Whether to log full traceback
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ReconPointException:
                # Re-raise custom exceptions
                raise
            except Exception as e:
                # Log unexpected exceptions
                if log_traceback:
                    logger.exception(f"Exception in {func.__name__}: {e}")
                else:
                    logger.error(f"Exception in {func.__name__}: {e}")
                
                # Return default value or re-raise
                if default_return is not None:
                    return default_return
                raise
        
        return wrapper
    return decorator


def safe_execute(func: Callable, *args, default=None, log_errors=True, **kwargs) -> Any:
    """
    Safely execute a function and return default value on error.
    
    Args:
        func: Function to execute
        *args: Positional arguments for function
        default: Default value to return on error
        log_errors: Whether to log errors
        **kwargs: Keyword arguments for function
        
    Returns:
        Function result or default value
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            logger.error(f"Error executing {func.__name__}: {e}")
        return default


class ErrorContext:
    """Context manager for error handling with cleanup."""
    
    def __init__(self, operation: str, cleanup_func: Optional[Callable] = None):
        self.operation = operation
        self.cleanup_func = cleanup_func
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(f"Error during {self.operation}: {exc_val}")
            
            # Run cleanup function if provided
            if self.cleanup_func:
                try:
                    self.cleanup_func()
                except Exception as cleanup_error:
                    logger.error(f"Error during cleanup: {cleanup_error}")
            
            # Don't suppress the exception
            return False
        
        return True


def format_error_response(
    error_code: str,
    message: str,
    details: Optional[Dict] = None,
    status_code: int = 400
) -> JsonResponse:
    """
    Format error response in consistent format.
    
    Args:
        error_code: Error code identifier
        message: Human-readable error message
        details: Additional error details
        status_code: HTTP status code
        
    Returns:
        JsonResponse with error details
    """
    response_data = {
        'error': error_code,
        'message': message
    }
    
    if details:
        response_data['details'] = details
    
    return JsonResponse(response_data, status=status_code)


def validate_or_error(condition: bool, message: str, field: Optional[str] = None):
    """
    Validate condition or raise ValidationException.
    
    Args:
        condition: Condition to validate
        message: Error message if condition is False
        field: Field name for validation error
        
    Raises:
        ValidationException: If condition is False
    """
    if not condition:
        raise ValidationException(message, field=field)


def require_fields(data: Dict, required_fields: list, field_types: Optional[Dict] = None):
    """
    Validate required fields in data dictionary.
    
    Args:
        data: Data dictionary to validate
        required_fields: List of required field names
        field_types: Optional dict mapping field names to expected types
        
    Raises:
        ValidationException: If validation fails
    """
    # Check for missing fields
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValidationException(
            f"Missing required fields: {', '.join(missing_fields)}",
            details={'missing_fields': missing_fields}
        )
    
    # Check field types if specified
    if field_types:
        for field, expected_type in field_types.items():
            if field in data and not isinstance(data[field], expected_type):
                raise ValidationException(
                    f"Field '{field}' must be of type {expected_type.__name__}",
                    field=field,
                    details={
                        'expected_type': expected_type.__name__,
                        'actual_type': type(data[field]).__name__
                    }
                )


class RetryableError(Exception):
    """Exception that indicates an operation should be retried."""
    pass


def retry_on_error(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator to retry function on error.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for delay
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except RetryableError as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
                except Exception as e:
                    # Don't retry on non-retryable errors
                    logger.error(f"Non-retryable error in {func.__name__}: {e}")
                    raise
            
            # If we get here, all retries failed
            raise last_exception
        
        return wrapper
    return decorator
