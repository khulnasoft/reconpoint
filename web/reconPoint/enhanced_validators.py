"""
Enhanced validators for reconPoint with comprehensive input validation.
"""
import re
import ipaddress
from typing import Optional, List
from urllib.parse import urlparse

import validators
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class InputValidator:
    """Comprehensive input validation utilities."""
    
    # Regex patterns
    SUBDOMAIN_PATTERN = re.compile(
        r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$'
    )
    SAFE_FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\.]+$')
    
    @staticmethod
    def validate_domain(value: str, allow_wildcards: bool = False) -> bool:
        """
        Validate domain name with optional wildcard support.
        
        Args:
            value: Domain name to validate
            allow_wildcards: Whether to allow wildcard domains (*.example.com)
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If domain is invalid
        """
        if not value:
            raise ValidationError(_('Domain cannot be empty'))
        
        # Handle wildcard domains
        if allow_wildcards and value.startswith('*.'):
            value = value[2:]
        
        if not validators.domain(value):
            raise ValidationError(
                _('%(value)s is not a valid domain name'),
                params={'value': value}
            )
        
        return True
    
    @staticmethod
    def validate_url(value: str, schemes: Optional[List[str]] = None) -> bool:
        """
        Validate URL with optional scheme restriction.
        
        Args:
            value: URL to validate
            schemes: List of allowed schemes (e.g., ['http', 'https'])
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If URL is invalid
        """
        if not value:
            raise ValidationError(_('URL cannot be empty'))
        
        if not validators.url(value):
            raise ValidationError(
                _('%(value)s is not a valid URL'),
                params={'value': value}
            )
        
        if schemes:
            parsed = urlparse(value)
            if parsed.scheme not in schemes:
                raise ValidationError(
                    _('URL scheme must be one of: %(schemes)s'),
                    params={'schemes': ', '.join(schemes)}
                )
        
        return True
    
    @staticmethod
    def validate_ip_address(value: str, version: Optional[int] = None) -> bool:
        """
        Validate IP address (IPv4 or IPv6).
        
        Args:
            value: IP address to validate
            version: IP version (4 or 6), None for both
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If IP address is invalid
        """
        if not value:
            raise ValidationError(_('IP address cannot be empty'))
        
        try:
            ip = ipaddress.ip_address(value)
            if version and ip.version != version:
                raise ValidationError(
                    _('IP address must be IPv%(version)d'),
                    params={'version': version}
                )
        except ValueError:
            raise ValidationError(
                _('%(value)s is not a valid IP address'),
                params={'value': value}
            )
        
        return True
    
    @staticmethod
    def validate_cidr(value: str, version: Optional[int] = None) -> bool:
        """
        Validate CIDR notation.
        
        Args:
            value: CIDR to validate
            version: IP version (4 or 6), None for both
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If CIDR is invalid
        """
        if not value:
            raise ValidationError(_('CIDR cannot be empty'))
        
        try:
            network = ipaddress.ip_network(value, strict=False)
            if version and network.version != version:
                raise ValidationError(
                    _('CIDR must be IPv%(version)d'),
                    params={'version': version}
                )
        except ValueError:
            raise ValidationError(
                _('%(value)s is not a valid CIDR notation'),
                params={'value': value}
            )
        
        return True
    
    @staticmethod
    def validate_port(value: int) -> bool:
        """
        Validate port number.
        
        Args:
            value: Port number to validate
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If port is invalid
        """
        if not isinstance(value, int):
            raise ValidationError(_('Port must be an integer'))
        
        if not (1 <= value <= 65535):
            raise ValidationError(
                _('Port must be between 1 and 65535')
            )
        
        return True
    
    @staticmethod
    def validate_email(value: str) -> bool:
        """
        Validate email address.
        
        Args:
            value: Email to validate
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If email is invalid
        """
        if not value:
            raise ValidationError(_('Email cannot be empty'))
        
        if not validators.email(value):
            raise ValidationError(
                _('%(value)s is not a valid email address'),
                params={'value': value}
            )
        
        return True
    
    @staticmethod
    def validate_safe_filename(value: str, max_length: int = 255) -> bool:
        """
        Validate filename for safe filesystem operations.
        
        Args:
            value: Filename to validate
            max_length: Maximum allowed length
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If filename is invalid
        """
        if not value:
            raise ValidationError(_('Filename cannot be empty'))
        
        if len(value) > max_length:
            raise ValidationError(
                _('Filename too long (max %(max)d characters)'),
                params={'max': max_length}
            )
        
        if not InputValidator.SAFE_FILENAME_PATTERN.match(value):
            raise ValidationError(
                _('Filename contains invalid characters. Only alphanumeric, dash, underscore, and dot allowed')
            )
        
        # Prevent directory traversal
        if '..' in value or value.startswith('/'):
            raise ValidationError(_('Filename contains invalid path components'))
        
        return True
    
    @staticmethod
    def validate_subdomain(value: str) -> bool:
        """
        Validate subdomain format.
        
        Args:
            value: Subdomain to validate
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If subdomain is invalid
        """
        if not value:
            raise ValidationError(_('Subdomain cannot be empty'))
        
        if not InputValidator.SUBDOMAIN_PATTERN.match(value):
            raise ValidationError(
                _('%(value)s is not a valid subdomain'),
                params={'value': value}
            )
        
        return True
    
    @staticmethod
    def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize string input by removing dangerous characters.
        
        Args:
            value: String to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
        """
        if not value:
            return ''
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Remove control characters except newline and tab
        value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\t')
        
        # Trim whitespace
        value = value.strip()
        
        # Enforce max length
        if max_length and len(value) > max_length:
            value = value[:max_length]
        
        return value
    
    @staticmethod
    def validate_json_keys(data: dict, required_keys: List[str], optional_keys: Optional[List[str]] = None) -> bool:
        """
        Validate JSON data has required keys and no unexpected keys.
        
        Args:
            data: Dictionary to validate
            required_keys: List of required keys
            optional_keys: List of optional keys
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(data, dict):
            raise ValidationError(_('Data must be a dictionary'))
        
        # Check required keys
        missing_keys = set(required_keys) - set(data.keys())
        if missing_keys:
            raise ValidationError(
                _('Missing required keys: %(keys)s'),
                params={'keys': ', '.join(missing_keys)}
            )
        
        # Check for unexpected keys
        allowed_keys = set(required_keys)
        if optional_keys:
            allowed_keys.update(optional_keys)
        
        unexpected_keys = set(data.keys()) - allowed_keys
        if unexpected_keys:
            raise ValidationError(
                _('Unexpected keys: %(keys)s'),
                params={'keys': ', '.join(unexpected_keys)}
            )
        
        return True


# Convenience functions for backward compatibility
def validate_domain(value: str) -> None:
    """Validate domain name."""
    InputValidator.validate_domain(value)


def validate_url(value: str) -> None:
    """Validate URL."""
    InputValidator.validate_url(value)


def validate_short_name(value: str) -> None:
    """Validate short name (alphanumeric with dash and underscore)."""
    regex = re.compile(r'[@!#$%^&*()<>?/\|}{~:]')
    if regex.search(value):
        raise ValidationError(
            _('%(value)s is not a valid short name, can only contain - and _'),
            params={'value': value}
        )
