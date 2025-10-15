"""
API versioning utilities for reconPoint.
"""
from typing import Optional
from rest_framework.versioning import URLPathVersioning, AcceptHeaderVersioning
from rest_framework.exceptions import NotAcceptable


class ReconPointURLPathVersioning(URLPathVersioning):
    """
    URL path versioning for reconPoint API.
    Example: /api/v1/scans/, /api/v2/scans/
    """
    
    default_version = 'v1'
    allowed_versions = ['v1', 'v2']
    version_param = 'version'


class ReconPointAcceptHeaderVersioning(AcceptHeaderVersioning):
    """
    Accept header versioning for reconPoint API.
    Example: Accept: application/json; version=v1
    """
    
    default_version = 'v1'
    allowed_versions = ['v1', 'v2']
    version_param = 'version'


class HybridVersioning:
    """
    Hybrid versioning that supports both URL path and Accept header.
    Prioritizes URL path over Accept header.
    """
    
    default_version = 'v1'
    allowed_versions = ['v1', 'v2']
    
    def determine_version(self, request, *args, **kwargs):
        """
        Determine API version from request.
        
        Args:
            request: HTTP request object
            *args: Additional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            Version string
            
        Raises:
            NotAcceptable: If version is not supported
        """
        # Try URL path first
        version = kwargs.get('version')
        
        # Try Accept header if not in URL
        if not version:
            media_type = request.accepted_media_type
            if media_type:
                version = request.accepted_renderer.media_type.get('version')
        
        # Try custom header
        if not version:
            version = request.META.get('HTTP_API_VERSION')
        
        # Use default if not specified
        if not version:
            version = self.default_version
        
        # Validate version
        if version not in self.allowed_versions:
            raise NotAcceptable(
                f"Invalid API version '{version}'. "
                f"Supported versions: {', '.join(self.allowed_versions)}"
            )
        
        return version


def get_api_version(request) -> str:
    """
    Get API version from request.
    
    Args:
        request: HTTP request object
        
    Returns:
        API version string
    """
    return getattr(request, 'version', 'v1')


def is_version_deprecated(version: str) -> bool:
    """
    Check if API version is deprecated.
    
    Args:
        version: API version string
        
    Returns:
        True if deprecated, False otherwise
    """
    deprecated_versions = []  # Add deprecated versions here
    return version in deprecated_versions


def get_deprecation_info(version: str) -> Optional[dict]:
    """
    Get deprecation information for API version.
    
    Args:
        version: API version string
        
    Returns:
        Dictionary with deprecation info or None
    """
    deprecation_info = {
        # Example:
        # 'v1': {
        #     'deprecated_date': '2025-01-01',
        #     'sunset_date': '2025-06-01',
        #     'migration_guide': 'https://docs.reconpoint.com/api/v1-to-v2'
        # }
    }
    
    return deprecation_info.get(version)


class VersionedSerializer:
    """
    Base class for versioned serializers.
    Allows different serializer behavior based on API version.
    """
    
    def __init__(self, *args, **kwargs):
        self.version = kwargs.pop('version', 'v1')
        super().__init__(*args, **kwargs)
    
    def get_fields(self):
        """
        Get fields based on API version.
        Override this method to customize fields per version.
        """
        fields = super().get_fields()
        
        # Example: Remove certain fields in older versions
        if self.version == 'v1':
            # Remove fields not available in v1
            fields.pop('new_field', None)
        
        return fields


class VersionedViewMixin:
    """
    Mixin for versioned API views.
    """
    
    def get_serializer_class(self):
        """
        Get serializer class based on API version.
        """
        version = self.request.version
        
        # Look for version-specific serializer
        serializer_class_name = f"{self.serializer_class.__name__}_{version.upper()}"
        serializer_class = getattr(self, serializer_class_name, None)
        
        if serializer_class:
            return serializer_class
        
        # Fall back to default serializer
        return self.serializer_class
    
    def get_queryset(self):
        """
        Get queryset based on API version.
        Override to customize queryset per version.
        """
        queryset = super().get_queryset()
        version = self.request.version
        
        # Example: Apply version-specific filters
        if version == 'v1':
            # v1 might have different default filters
            pass
        
        return queryset


def version_specific_behavior(v1_func=None, v2_func=None):
    """
    Decorator to execute different functions based on API version.
    
    Args:
        v1_func: Function to execute for v1
        v2_func: Function to execute for v2
        
    Returns:
        Decorated function
    """
    def decorator(func):
        def wrapper(self, request, *args, **kwargs):
            version = get_api_version(request)
            
            if version == 'v1' and v1_func:
                return v1_func(self, request, *args, **kwargs)
            elif version == 'v2' and v2_func:
                return v2_func(self, request, *args, **kwargs)
            else:
                return func(self, request, *args, **kwargs)
        
        return wrapper
    return decorator
