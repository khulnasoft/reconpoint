"""
Base service class with common functionality.
"""
from typing import Dict, List, Optional, Any
from django.db import transaction
from reconPoint.error_handlers import ValidationException
import logging

logger = logging.getLogger(__name__)


class BaseService:
    """Base service class with common utilities."""
    
    @staticmethod
    def validate_required_fields(data: Dict, required_fields: List[str]) -> None:
        """
        Validate that all required fields are present in data.
        
        Args:
            data: Dictionary to validate
            required_fields: List of required field names
            
        Raises:
            ValidationException: If any required fields are missing
        """
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        if missing_fields:
            raise ValidationException(
                f"Missing required fields: {', '.join(missing_fields)}",
                details={'missing_fields': missing_fields}
            )
    
    @staticmethod
    def validate_field_types(data: Dict, field_types: Dict[str, type]) -> None:
        """
        Validate field types in data dictionary.
        
        Args:
            data: Dictionary to validate
            field_types: Dictionary mapping field names to expected types
            
        Raises:
            ValidationException: If any field has incorrect type
        """
        for field, expected_type in field_types.items():
            if field in data and data[field] is not None:
                if not isinstance(data[field], expected_type):
                    raise ValidationException(
                        f"Field '{field}' must be of type {expected_type.__name__}",
                        field=field,
                        details={
                            'expected_type': expected_type.__name__,
                            'actual_type': type(data[field]).__name__
                        }
                    )
    
    @staticmethod
    def log_operation(operation: str, details: Optional[Dict] = None) -> None:
        """
        Log a service operation.
        
        Args:
            operation: Operation description
            details: Optional operation details
        """
        log_message = f"Service operation: {operation}"
        if details:
            log_message += f" | Details: {details}"
        logger.info(log_message)
    
    @staticmethod
    @transaction.atomic
    def execute_in_transaction(func, *args, **kwargs) -> Any:
        """
        Execute a function within a database transaction.
        
        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            Function result
        """
        return func(*args, **kwargs)
