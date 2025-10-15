"""
Validators for targetApp module
Provides input validation for target and organization operations
"""

import logging
import validators
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from reconPoint.enhanced_validators import InputValidator

logger = logging.getLogger(__name__)


class TargetValidator:
    """
    Validator for target (domain) operations
    """
    
    @staticmethod
    def validate_target_input(target: str) -> Tuple[bool, Optional[str], Dict]:
        """
        Validate and classify target input
        
        Args:
            target: Target string (domain, IP, URL, or CIDR)
            
        Returns:
            Tuple of (is_valid, error_message, classification_dict)
        """
        target = target.strip()
        
        if not target:
            return False, "Target cannot be empty", {}
        
        # Check what type of target it is
        is_domain = bool(validators.domain(target))
        is_ip = bool(validators.ipv4(target)) or bool(validators.ipv6(target))
        is_cidr = bool(validators.ipv4_cidr(target)) or bool(validators.ipv6_cidr(target))
        is_url = bool(validators.url(target))
        
        classification = {
            'is_domain': is_domain,
            'is_ip': is_ip,
            'is_cidr': is_cidr,
            'is_url': is_url,
            'target': target
        }
        
        # Must be at least one valid type
        if not any([is_domain, is_ip, is_cidr, is_url]):
            return False, f"{target} is not a valid domain, IP, URL, or CIDR range", classification
        
        # Additional validation for URLs
        if is_url:
            try:
                parsed = urlparse(target)
                classification['url_parts'] = {
                    'scheme': parsed.scheme,
                    'netloc': parsed.netloc,
                    'path': parsed.path,
                    'domain': parsed.netloc.split(':')[0]
                }
            except Exception as e:
                return False, f"Invalid URL format: {e}", classification
        
        return True, None, classification
    
    @staticmethod
    def validate_bulk_targets(targets: List[str]) -> Tuple[List[Dict], List[Dict]]:
        """
        Validate a list of targets
        
        Args:
            targets: List of target strings
            
        Returns:
            Tuple of (valid_targets, invalid_targets)
        """
        valid_targets = []
        invalid_targets = []
        
        for target in targets:
            is_valid, error, classification = TargetValidator.validate_target_input(target)
            
            if is_valid:
                valid_targets.append(classification)
            else:
                invalid_targets.append({
                    'target': target,
                    'error': error
                })
        
        return valid_targets, invalid_targets
    
    @staticmethod
    def validate_domain_name(domain: str) -> Tuple[bool, Optional[str]]:
        """
        Validate domain name format
        
        Args:
            domain: Domain name
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not domain:
            return False, "Domain name cannot be empty"
        
        # Check length
        if len(domain) > 253:
            return False, "Domain name too long (max 253 characters)"
        
        # Validate format
        if not InputValidator.validate_domain(domain):
            return False, f"Invalid domain name format: {domain}"
        
        return True, None
    
    @staticmethod
    def validate_ip_address(ip: str) -> Tuple[bool, Optional[str]]:
        """
        Validate IP address format
        
        Args:
            ip: IP address
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not ip:
            return False, "IP address cannot be empty"
        
        if not InputValidator.validate_ip_address(ip):
            return False, f"Invalid IP address format: {ip}"
        
        return True, None
    
    @staticmethod
    def validate_cidr_range(cidr: str) -> Tuple[bool, Optional[str]]:
        """
        Validate CIDR range format
        
        Args:
            cidr: CIDR range
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not cidr:
            return False, "CIDR range cannot be empty"
        
        is_ipv4_cidr = bool(validators.ipv4_cidr(cidr))
        is_ipv6_cidr = bool(validators.ipv6_cidr(cidr))
        
        if not (is_ipv4_cidr or is_ipv6_cidr):
            return False, f"Invalid CIDR range format: {cidr}"
        
        return True, None
    
    @staticmethod
    def validate_url(url: str) -> Tuple[bool, Optional[str]]:
        """
        Validate URL format
        
        Args:
            url: URL string
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not url:
            return False, "URL cannot be empty"
        
        if not InputValidator.validate_url(url):
            return False, f"Invalid URL format: {url}"
        
        # Check for dangerous protocols
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ['http', 'https']:
                return False, f"Invalid URL scheme: {parsed.scheme}. Only http and https are allowed"
        except Exception as e:
            return False, f"Error parsing URL: {e}"
        
        return True, None
    
    @staticmethod
    def sanitize_target_description(description: str) -> str:
        """
        Sanitize target description
        
        Args:
            description: Description string
            
        Returns:
            Sanitized description
        """
        if not description:
            return ""
        
        return InputValidator.sanitize_string(description, max_length=500)
    
    @staticmethod
    def validate_h1_team_handle(handle: str) -> Tuple[bool, Optional[str]]:
        """
        Validate HackerOne team handle format
        
        Args:
            handle: Team handle
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not handle:
            return True, None  # Optional field
        
        # Basic validation: alphanumeric, underscore, hyphen
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', handle):
            return False, "Invalid team handle format. Use only letters, numbers, underscore, and hyphen"
        
        if len(handle) > 100:
            return False, "Team handle too long (max 100 characters)"
        
        return True, None


class OrganizationValidator:
    """
    Validator for organization operations
    """
    
    @staticmethod
    def validate_organization_name(name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate organization name
        
        Args:
            name: Organization name
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not name:
            return False, "Organization name cannot be empty"
        
        if len(name) > 300:
            return False, "Organization name too long (max 300 characters)"
        
        # Check for invalid characters
        sanitized = InputValidator.sanitize_string(name, max_length=300)
        if sanitized != name:
            return False, "Organization name contains invalid characters"
        
        return True, None
    
    @staticmethod
    def validate_organization_description(description: str) -> Tuple[bool, Optional[str]]:
        """
        Validate organization description
        
        Args:
            description: Description string
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not description:
            return True, None  # Optional field
        
        if len(description) > 1000:
            return False, "Description too long (max 1000 characters)"
        
        return True, None
    
    @staticmethod
    def sanitize_organization_description(description: str) -> str:
        """
        Sanitize organization description
        
        Args:
            description: Description string
            
        Returns:
            Sanitized description
        """
        if not description:
            return ""
        
        return InputValidator.sanitize_string(description, max_length=1000)


class FileUploadValidator:
    """
    Validator for file uploads
    """
    
    @staticmethod
    def validate_txt_file(file) -> Tuple[bool, Optional[str]]:
        """
        Validate TXT file upload
        
        Args:
            file: Uploaded file object
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file:
            return False, "No file provided"
        
        # Check file extension
        if not file.name.endswith('.txt'):
            return False, "File must have .txt extension"
        
        # Check content type
        if file.content_type not in ['text/plain', 'application/octet-stream']:
            return False, f"Invalid content type: {file.content_type}"
        
        # Check file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if file.size > max_size:
            return False, f"File too large. Maximum size is 10MB"
        
        return True, None
    
    @staticmethod
    def validate_csv_file(file) -> Tuple[bool, Optional[str]]:
        """
        Validate CSV file upload
        
        Args:
            file: Uploaded file object
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file:
            return False, "No file provided"
        
        # Check file extension
        if not file.name.endswith('.csv'):
            return False, "File must have .csv extension"
        
        # Check content type
        if file.content_type not in ['text/csv', 'application/csv', 'application/octet-stream']:
            return False, f"Invalid content type: {file.content_type}"
        
        # Check file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if file.size > max_size:
            return False, f"File too large. Maximum size is 10MB"
        
        return True, None
    
    @staticmethod
    def read_and_validate_txt_content(file) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Read and validate TXT file content
        
        Args:
            file: Uploaded file object
            
        Returns:
            Tuple of (is_valid, error_message, content)
        """
        try:
            # Validate file
            is_valid, error = FileUploadValidator.validate_txt_file(file)
            if not is_valid:
                return False, error, None
            
            # Read content
            content = file.read().decode('UTF-8')
            
            # Validate content
            if not content.strip():
                return False, "File is empty", None
            
            # Check line count (max 10,000 lines)
            lines = content.split('\n')
            if len(lines) > 10000:
                return False, "File has too many lines (max 10,000)", None
            
            return True, None, content
            
        except UnicodeDecodeError:
            return False, "File encoding error. Please use UTF-8 encoding", None
        except Exception as e:
            logger.error(f"Error reading TXT file: {e}")
            return False, f"Error reading file: {e}", None
    
    @staticmethod
    def read_and_validate_csv_content(file) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Read and validate CSV file content
        
        Args:
            file: Uploaded file object
            
        Returns:
            Tuple of (is_valid, error_message, content)
        """
        try:
            # Validate file
            is_valid, error = FileUploadValidator.validate_csv_file(file)
            if not is_valid:
                return False, error, None
            
            # Read content
            content = file.read().decode('UTF-8')
            
            # Validate content
            if not content.strip():
                return False, "File is empty", None
            
            # Check line count (max 10,000 lines)
            lines = content.split('\n')
            if len(lines) > 10000:
                return False, "File has too many lines (max 10,000)", None
            
            return True, None, content
            
        except UnicodeDecodeError:
            return False, "File encoding error. Please use UTF-8 encoding", None
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            return False, f"Error reading file: {e}", None


class TargetInputParser:
    """
    Parser for target input
    """
    
    @staticmethod
    def parse_target(target: str) -> Dict:
        """
        Parse target and extract relevant information
        
        Args:
            target: Target string
            
        Returns:
            Dictionary with parsed information
        """
        is_valid, error, classification = TargetValidator.validate_target_input(target)
        
        if not is_valid:
            return {
                'valid': False,
                'error': error,
                'target': target
            }
        
        result = {
            'valid': True,
            'target': target,
            'type': None,
            'domains': [],
            'ips': [],
            'urls': [],
            'ports': []
        }
        
        # Determine type and extract information
        if classification['is_url']:
            result['type'] = 'url'
            url_parts = classification.get('url_parts', {})
            result['urls'].append(target)
            result['domains'].append(url_parts.get('domain', ''))
            
            # Extract port if present
            netloc = url_parts.get('netloc', '')
            if ':' in netloc:
                parts = netloc.split(':')
                if len(parts) == 2:
                    try:
                        port = int(parts[1])
                        result['ports'].append(port)
                    except ValueError:
                        pass
        
        elif classification['is_cidr']:
            result['type'] = 'cidr'
            # CIDR ranges will be expanded later
            result['cidr'] = target
        
        elif classification['is_ip']:
            result['type'] = 'ip'
            result['ips'].append(target)
            result['domains'].append(target)  # Treat IP as domain
        
        elif classification['is_domain']:
            result['type'] = 'domain'
            result['domains'].append(target)
        
        return result
    
    @staticmethod
    def parse_bulk_targets(targets: List[str]) -> Dict:
        """
        Parse multiple targets
        
        Args:
            targets: List of target strings
            
        Returns:
            Dictionary with parsed results
        """
        results = {
            'valid': [],
            'invalid': [],
            'summary': {
                'total': len(targets),
                'valid': 0,
                'invalid': 0,
                'domains': 0,
                'ips': 0,
                'urls': 0,
                'cidrs': 0
            }
        }
        
        for target in targets:
            parsed = TargetInputParser.parse_target(target)
            
            if parsed['valid']:
                results['valid'].append(parsed)
                results['summary']['valid'] += 1
                
                # Count by type
                target_type = parsed['type']
                if target_type == 'domain':
                    results['summary']['domains'] += 1
                elif target_type == 'ip':
                    results['summary']['ips'] += 1
                elif target_type == 'url':
                    results['summary']['urls'] += 1
                elif target_type == 'cidr':
                    results['summary']['cidrs'] += 1
            else:
                results['invalid'].append(parsed)
                results['summary']['invalid'] += 1
        
        return results
