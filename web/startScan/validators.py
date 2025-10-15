"""
Validators for startScan module
Provides input validation for scan operations
"""

import logging
from typing import Dict, List, Optional, Tuple
from django.core.exceptions import ValidationError

from reconPoint.enhanced_validators import InputValidator

logger = logging.getLogger(__name__)


class ScanInputValidator:
    """
    Validator for scan input parameters
    """
    
    @staticmethod
    def validate_scan_configuration(config: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate scan configuration parameters
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate out of scope subdomains
            if 'out_of_scope_subdomains' in config:
                for subdomain in config['out_of_scope_subdomains']:
                    if not InputValidator.validate_domain(subdomain):
                        return False, f"Invalid out of scope subdomain: {subdomain}"
            
            # Validate imported subdomains
            if 'imported_subdomains' in config:
                for subdomain in config['imported_subdomains']:
                    if not InputValidator.validate_domain(subdomain):
                        return False, f"Invalid imported subdomain: {subdomain}"
            
            # Validate starting point path
            if 'starting_point_path' in config:
                path = config['starting_point_path']
                if path and not InputValidator.validate_url(path):
                    return False, f"Invalid starting point path: {path}"
            
            # Validate excluded paths
            if 'excluded_paths' in config:
                for path in config['excluded_paths']:
                    if not isinstance(path, str) or len(path) > 200:
                        return False, f"Invalid excluded path: {path}"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating scan configuration: {e}")
            return False, str(e)
    
    @staticmethod
    def validate_subdomain_list(subdomains: List[str]) -> Tuple[bool, Optional[str], List[str]]:
        """
        Validate a list of subdomains
        
        Args:
            subdomains: List of subdomain strings
            
        Returns:
            Tuple of (is_valid, error_message, valid_subdomains)
        """
        valid_subdomains = []
        invalid_subdomains = []
        
        for subdomain in subdomains:
            if InputValidator.validate_domain(subdomain):
                valid_subdomains.append(subdomain)
            else:
                invalid_subdomains.append(subdomain)
        
        if invalid_subdomains:
            error_msg = f"Invalid subdomains: {', '.join(invalid_subdomains[:5])}"
            if len(invalid_subdomains) > 5:
                error_msg += f" and {len(invalid_subdomains) - 5} more"
            return False, error_msg, valid_subdomains
        
        return True, None, valid_subdomains
    
    @staticmethod
    def validate_scan_schedule(schedule_config: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate scan schedule configuration
        
        Args:
            schedule_config: Schedule configuration dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate schedule type
            schedule_type = schedule_config.get('schedule_type')
            if schedule_type not in ['interval', 'crontab', 'clocked']:
                return False, f"Invalid schedule type: {schedule_type}"
            
            # Validate interval schedule
            if schedule_type == 'interval':
                period = schedule_config.get('period')
                every = schedule_config.get('every')
                
                if period not in ['seconds', 'minutes', 'hours', 'days']:
                    return False, f"Invalid period: {period}"
                
                if not isinstance(every, int) or every <= 0:
                    return False, f"Invalid interval value: {every}"
            
            # Validate crontab schedule
            elif schedule_type == 'crontab':
                # Basic crontab validation
                minute = schedule_config.get('minute', '*')
                hour = schedule_config.get('hour', '*')
                day_of_week = schedule_config.get('day_of_week', '*')
                day_of_month = schedule_config.get('day_of_month', '*')
                month_of_year = schedule_config.get('month_of_year', '*')
                
                # Add more sophisticated crontab validation if needed
            
            # Validate clocked schedule
            elif schedule_type == 'clocked':
                clocked_time = schedule_config.get('clocked_time')
                if not clocked_time:
                    return False, "Clocked time is required for clocked schedule"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating scan schedule: {e}")
            return False, str(e)
    
    @staticmethod
    def validate_export_format(format: str) -> Tuple[bool, Optional[str]]:
        """
        Validate export format
        
        Args:
            format: Export format string
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        valid_formats = ['json', 'csv', 'xml', 'pdf', 'html']
        
        if format.lower() not in valid_formats:
            return False, f"Invalid export format. Must be one of: {', '.join(valid_formats)}"
        
        return True, None
    
    @staticmethod
    def sanitize_scan_name(name: str) -> str:
        """
        Sanitize scan name for safe storage
        
        Args:
            name: Scan name
            
        Returns:
            Sanitized scan name
        """
        return InputValidator.sanitize_string(name, max_length=200)
    
    @staticmethod
    def validate_scan_filters(filters: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate scan filter parameters
        
        Args:
            filters: Filter dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate severity filter
            if 'severity' in filters:
                severity = filters['severity']
                if severity not in [-1, 0, 1, 2, 3, 4]:
                    return False, f"Invalid severity: {severity}"
            
            # Validate status filter
            if 'status' in filters:
                status = filters['status']
                if status not in [-1, 0, 1, 2, 3]:
                    return False, f"Invalid status: {status}"
            
            # Validate date range
            if 'start_date' in filters or 'end_date' in filters:
                from datetime import datetime
                
                if 'start_date' in filters:
                    try:
                        datetime.fromisoformat(filters['start_date'])
                    except ValueError:
                        return False, "Invalid start_date format. Use ISO format."
                
                if 'end_date' in filters:
                    try:
                        datetime.fromisoformat(filters['end_date'])
                    except ValueError:
                        return False, "Invalid end_date format. Use ISO format."
            
            # Validate limit and offset
            if 'limit' in filters:
                limit = filters['limit']
                if not isinstance(limit, int) or limit <= 0 or limit > 1000:
                    return False, "Limit must be between 1 and 1000"
            
            if 'offset' in filters:
                offset = filters['offset']
                if not isinstance(offset, int) or offset < 0:
                    return False, "Offset must be non-negative"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating scan filters: {e}")
            return False, str(e)


class SubdomainValidator:
    """
    Validator for subdomain operations
    """
    
    @staticmethod
    def validate_subdomain_data(data: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate subdomain data
        
        Args:
            data: Subdomain data dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate subdomain name
            if 'name' not in data:
                return False, "Subdomain name is required"
            
            if not InputValidator.validate_domain(data['name']):
                return False, f"Invalid subdomain name: {data['name']}"
            
            # Validate HTTP URL if provided
            if 'http_url' in data and data['http_url']:
                if not InputValidator.validate_url(data['http_url']):
                    return False, f"Invalid HTTP URL: {data['http_url']}"
            
            # Validate HTTP status
            if 'http_status' in data:
                status = data['http_status']
                if not isinstance(status, int) or status < 0 or status > 999:
                    return False, f"Invalid HTTP status: {status}"
            
            # Validate IP addresses
            if 'ip_addresses' in data:
                for ip in data['ip_addresses']:
                    if not InputValidator.validate_ip_address(ip):
                        return False, f"Invalid IP address: {ip}"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating subdomain data: {e}")
            return False, str(e)


class VulnerabilityValidator:
    """
    Validator for vulnerability operations
    """
    
    @staticmethod
    def validate_vulnerability_data(data: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate vulnerability data
        
        Args:
            data: Vulnerability data dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate vulnerability name
            if 'name' not in data:
                return False, "Vulnerability name is required"
            
            name = data['name']
            if not isinstance(name, str) or len(name) > 500:
                return False, "Vulnerability name must be a string with max 500 characters"
            
            # Validate severity
            if 'severity' in data:
                severity = data['severity']
                if severity not in [-1, 0, 1, 2, 3, 4]:
                    return False, f"Invalid severity: {severity}. Must be -1 to 4"
            
            # Validate URL if provided
            if 'url' in data and data['url']:
                if not InputValidator.validate_url(data['url']):
                    return False, f"Invalid URL: {data['url']}"
            
            # Validate CVE IDs
            if 'cve_ids' in data:
                for cve_id in data['cve_ids']:
                    if not VulnerabilityValidator._validate_cve_format(cve_id):
                        return False, f"Invalid CVE ID format: {cve_id}"
            
            # Validate CWE IDs
            if 'cwe_ids' in data:
                for cwe_id in data['cwe_ids']:
                    if not VulnerabilityValidator._validate_cwe_format(cwe_id):
                        return False, f"Invalid CWE ID format: {cwe_id}"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating vulnerability data: {e}")
            return False, str(e)
    
    @staticmethod
    def _validate_cve_format(cve_id: str) -> bool:
        """Validate CVE ID format (CVE-YYYY-NNNNN)"""
        import re
        pattern = r'^CVE-\d{4}-\d{4,}$'
        return bool(re.match(pattern, cve_id))
    
    @staticmethod
    def _validate_cwe_format(cwe_id: str) -> bool:
        """Validate CWE ID format (CWE-NNN)"""
        import re
        pattern = r'^CWE-\d+$'
        return bool(re.match(pattern, cwe_id))
    
    @staticmethod
    def validate_severity_change(old_severity: int, new_severity: int, user) -> Tuple[bool, Optional[str]]:
        """
        Validate severity change
        
        Args:
            old_severity: Current severity
            new_severity: New severity
            user: User making the change
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate new severity
        if new_severity not in [-1, 0, 1, 2, 3, 4]:
            return False, f"Invalid severity: {new_severity}"
        
        # Add permission checks if needed
        # For example, only allow certain users to change critical vulnerabilities
        
        return True, None
