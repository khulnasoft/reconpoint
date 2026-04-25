"""
Input validation utilities for data imports.
"""

import re
from typing import List, Optional, Tuple

import validators


class ImportValidationError(Exception):
    """Raised when import validation fails."""

    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(f"Validation failed: {'; '.join(errors)}")


class DomainValidator:
    """Validates domain names for import."""

    DOMAIN_REGEX = re.compile(
        r"^(?:[a-zA-Z0-9]"  # First char
        r"(?:[a-zA-Z0-9-_]{0,61}[a-zA-Z0-9])?\.)"  # Second-level domain
        r"(?:[a-zA-Z]{2,}\.?|[a-zA-Z0-9-]{2,}\.?)$"  # TLD
    )

    IP_REGEX = re.compile(
        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )

    @classmethod
    def validate(cls, value: str) -> Tuple[bool, Optional[str]]:
        """Validate a single domain/hostname/IP."""
        value = value.strip()

        if not value:
            return False, "Empty value"

        if value.startswith(("http://", "https://")):
            try:
                result = validators.url(value)
                if result:
                    return True, None
                return False, "Invalid URL format"
            except Exception:
                return False, "Invalid URL format"

        if cls.IP_REGEX.match(value):
            return True, None

        if cls.DOMAIN_REGEX.match(value):
            return True, None

        try:
            if validators.domain(value):
                return True, None
        except Exception:
            pass

        return False, f"Invalid domain format: {value}"

    @classmethod
    def validate_batch(cls, values: List[str], max_count: int = 10000) -> Tuple[List[str], List[Tuple[str, str]]]:
        """Validate a batch of domains. Returns (valid, invalid_with_errors)."""
        if len(values) > max_count:
            raise ImportValidationError([f"Max {max_count} items allowed"])

        valid = []
        invalid = []

        for value in values:
            is_valid, error = cls.validate(value)
            if is_valid:
                valid.append(value.strip())
            else:
                invalid.append((value, error or "Unknown error"))

        return valid, invalid


class URLValidator:
    """Validates URLs for import."""

    @classmethod
    def validate(cls, value: str) -> Tuple[bool, Optional[str]]:
        """Validate a single URL."""
        value = value.strip()

        if not value:
            return False, "Empty value"

        if not value.startswith(("http://", "https://")):
            value = f"https://{value}"

        try:
            result = validators.url(value)
            if result:
                return True, None
            return False, "Invalid URL format"
        except Exception as e:
            return False, f"Invalid URL: {str(e)}"

    @classmethod
    def validate_batch(cls, values: List[str], max_count: int = 10000) -> Tuple[List[str], List[Tuple[str, str]]]:
        """Validate a batch of URLs."""
        if len(values) > max_count:
            raise ImportValidationError([f"Max {max_count} items allowed"])

        valid = []
        invalid = []

        for value in values:
            is_valid, error = cls.validate(value)
            if is_valid:
                valid.append(value.strip())
            else:
                invalid.append((value, error or "Unknown error"))

        return valid, invalid


class CIDRValidator:
    """Validates CIDR notation for import."""

    @classmethod
    def validate(cls, value: str) -> Tuple[bool, Optional[str]]:
        """Validate a CIDR block."""
        value = value.strip()

        if not value:
            return False, "Empty value"

        try:
            if "/" in value:
                parts = value.split("/")
                if len(parts) != 2:
                    return False, "Invalid CIDR format"
                ip, prefix = parts
                prefix = int(prefix)
                if prefix < 0 or prefix > 32:
                    return False, "Prefix must be 0-32"
                return True, None
            else:
                return False, "Missing CIDR prefix"
        except ValueError:
            return False, "Invalid CIDR format"
        except Exception as e:
            return False, f"Invalid CIDR: {str(e)}"

    @classmethod
    def validate_batch(cls, values: List[str], max_count: int = 10000) -> Tuple[List[str], List[Tuple[str, str]]]:
        """Validate a batch of CIDR blocks."""
        if len(values) > max_count:
            raise ImportValidationError([f"Max {max_count} items allowed"])

        valid = []
        invalid = []

        for value in values:
            is_valid, error = cls.validate(value)
            if is_valid:
                valid.append(value.strip())
            else:
                invalid.append((value, error or "Unknown error"))

        return valid, invalid
