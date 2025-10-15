"""
Security middleware for reconPoint.
Implements rate limiting, security headers, and request validation.
"""
import logging
import time
from typing import Callable, Optional
from collections import defaultdict
from datetime import datetime, timedelta

from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


logger = logging.getLogger(__name__)


class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting middleware to prevent abuse.
    Uses Redis cache for distributed rate limiting.
    """
    
    # Default rate limits (requests per minute)
    DEFAULT_RATE_LIMIT = 60
    API_RATE_LIMIT = 100
    AUTH_RATE_LIMIT = 10
    
    # Paths that should have stricter rate limits
    STRICT_PATHS = [
        '/api/auth/',
        '/api/login/',
        '/api/register/',
    ]
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """
        Check rate limit before processing request.
        
        Args:
            request: HTTP request object
            
        Returns:
            None if allowed, HttpResponse with 429 if rate limited
        """
        # Skip rate limiting for superusers in debug mode
        if settings.DEBUG and request.user.is_authenticated and request.user.is_superuser:
            return None
        
        # Get client identifier (user ID or IP)
        client_id = self._get_client_identifier(request)
        
        # Determine rate limit based on path
        rate_limit = self._get_rate_limit(request.path)
        
        # Check rate limit
        if not self._check_rate_limit(client_id, rate_limit):
            logger.warning(
                f"Rate limit exceeded for client {client_id} on path {request.path}"
            )
            return JsonResponse(
                {
                    'error': 'Rate limit exceeded',
                    'detail': f'Maximum {rate_limit} requests per minute allowed'
                },
                status=429
            )
        
        return None
    
    def _get_client_identifier(self, request: HttpRequest) -> str:
        """
        Get unique identifier for the client.
        
        Args:
            request: HTTP request object
            
        Returns:
            Client identifier string
        """
        if request.user.is_authenticated:
            return f"user_{request.user.id}"
        
        # Get IP from X-Forwarded-For or REMOTE_ADDR
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        return f"ip_{ip}"
    
    def _get_rate_limit(self, path: str) -> int:
        """
        Get rate limit for a specific path.
        
        Args:
            path: Request path
            
        Returns:
            Rate limit (requests per minute)
        """
        # Check if path requires strict rate limiting
        for strict_path in self.STRICT_PATHS:
            if path.startswith(strict_path):
                return self.AUTH_RATE_LIMIT
        
        # API paths get higher rate limit
        if path.startswith('/api/'):
            return self.API_RATE_LIMIT
        
        return self.DEFAULT_RATE_LIMIT
    
    def _check_rate_limit(self, client_id: str, rate_limit: int) -> bool:
        """
        Check if client is within rate limit.
        
        Args:
            client_id: Client identifier
            rate_limit: Maximum requests per minute
            
        Returns:
            True if within limit, False otherwise
        """
        cache_key = f"rate_limit_{client_id}"
        
        # Get current request count
        request_count = cache.get(cache_key, 0)
        
        if request_count >= rate_limit:
            return False
        
        # Increment counter
        cache.set(cache_key, request_count + 1, 60)  # 60 seconds TTL
        
        return True


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers to all responses.
    """
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """
        Add security headers to response.
        
        Args:
            request: HTTP request object
            response: HTTP response object
            
        Returns:
            Modified response with security headers
        """
        # X-Content-Type-Options
        response['X-Content-Type-Options'] = 'nosniff'
        
        # X-Frame-Options (prevent clickjacking)
        response['X-Frame-Options'] = 'DENY'
        
        # X-XSS-Protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer-Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content-Security-Policy (adjust based on your needs)
        if not settings.DEBUG:
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
                "style-src 'self' 'unsafe-inline'",
                "img-src 'self' data: https:",
                "font-src 'self' data:",
                "connect-src 'self'",
                "frame-ancestors 'none'",
            ]
            response['Content-Security-Policy'] = '; '.join(csp_directives)
        
        # Strict-Transport-Security (HSTS) - only in production
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Permissions-Policy (formerly Feature-Policy)
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response


class RequestValidationMiddleware(MiddlewareMixin):
    """
    Validate incoming requests for common security issues.
    """
    
    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10 MB
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """
        Validate request before processing.
        
        Args:
            request: HTTP request object
            
        Returns:
            None if valid, HttpResponse with error if invalid
        """
        # Check request size
        content_length = request.META.get('CONTENT_LENGTH')
        if content_length:
            try:
                content_length = int(content_length)
                if content_length > self.MAX_REQUEST_SIZE:
                    logger.warning(
                        f"Request too large: {content_length} bytes from {request.META.get('REMOTE_ADDR')}"
                    )
                    return JsonResponse(
                        {
                            'error': 'Request too large',
                            'detail': f'Maximum request size is {self.MAX_REQUEST_SIZE} bytes'
                        },
                        status=413
                    )
            except ValueError:
                pass
        
        # Validate HTTP method
        allowed_methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']
        if request.method not in allowed_methods:
            return JsonResponse(
                {'error': 'Method not allowed'},
                status=405
            )
        
        return None


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Log all requests for audit and debugging purposes.
    """
    
    def process_request(self, request: HttpRequest) -> None:
        """
        Log request details.
        
        Args:
            request: HTTP request object
        """
        request._start_time = time.time()
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """
        Log response details.
        
        Args:
            request: HTTP request object
            response: HTTP response object
            
        Returns:
            Response object
        """
        # Calculate request duration
        duration = None
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
        
        # Log request details
        log_data = {
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'duration': f"{duration:.3f}s" if duration else 'N/A',
            'user': request.user.username if request.user.is_authenticated else 'anonymous',
            'ip': request.META.get('REMOTE_ADDR', 'unknown'),
        }
        
        # Log at appropriate level based on status code
        if response.status_code >= 500:
            logger.error(f"Request failed: {log_data}")
        elif response.status_code >= 400:
            logger.warning(f"Client error: {log_data}")
        elif settings.DEBUG:
            logger.info(f"Request: {log_data}")
        
        return response


class APIVersionMiddleware(MiddlewareMixin):
    """
    Handle API versioning through headers or URL path.
    """
    
    SUPPORTED_VERSIONS = ['v1', 'v2']
    DEFAULT_VERSION = 'v1'
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """
        Extract and validate API version.
        
        Args:
            request: HTTP request object
            
        Returns:
            None if valid, HttpResponse with error if invalid
        """
        # Only process API requests
        if not request.path.startswith('/api/'):
            return None
        
        # Try to get version from header
        version = request.META.get('HTTP_API_VERSION')
        
        # Try to get version from URL path
        if not version:
            path_parts = request.path.split('/')
            if len(path_parts) > 2 and path_parts[2] in self.SUPPORTED_VERSIONS:
                version = path_parts[2]
        
        # Use default version if not specified
        if not version:
            version = self.DEFAULT_VERSION
        
        # Validate version
        if version not in self.SUPPORTED_VERSIONS:
            return JsonResponse(
                {
                    'error': 'Unsupported API version',
                    'detail': f'Supported versions: {", ".join(self.SUPPORTED_VERSIONS)}'
                },
                status=400
            )
        
        # Store version in request for later use
        request.api_version = version
        
        return None


class HealthCheckMiddleware(MiddlewareMixin):
    """
    Handle health check requests without authentication.
    """
    
    HEALTH_PATHS = ['/health', '/healthz', '/readiness', '/liveness']
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """
        Handle health check requests.
        
        Args:
            request: HTTP request object
            
        Returns:
            Health check response or None
        """
        if request.path in self.HEALTH_PATHS:
            return JsonResponse({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'version': getattr(settings, 'RECONPOINT_CURRENT_VERSION', 'unknown')
            })
        
        return None
