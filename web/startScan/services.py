"""
Service layer for startScan module
Separates business logic from views for better maintainability and testing
"""

import logging
from typing import Dict, List, Optional, Tuple
from django.db.models import Count, Q, Prefetch, QuerySet
from django.core.cache import cache
from django.utils import timezone

from reconPoint.query_optimizer import QueryOptimizer
from .models import (
    ScanHistory, Subdomain, EndPoint, Vulnerability,
    Email, Employee, S3Bucket, Dork, ScanActivity
)
from targetApp.models import Domain, CountryISO, IpAddress
from scanEngine.models import EngineType

logger = logging.getLogger(__name__)


class ScanStatisticsService:
    """
    Service for calculating scan statistics with optimized queries
    """
    
    @staticmethod
    def get_scan_statistics(scan_id: int, use_cache: bool = True) -> Dict:
        """
        Get comprehensive scan statistics with caching
        
        Args:
            scan_id: ScanHistory ID
            use_cache: Whether to use cached results
            
        Returns:
            Dictionary containing all scan statistics
        """
        cache_key = f'scan_stats_{scan_id}'
        
        if use_cache:
            cached_stats = cache.get(cache_key)
            if cached_stats:
                logger.debug(f"Returning cached statistics for scan {scan_id}")
                return cached_stats
        
        try:
            scan = ScanHistory.objects.select_related('domain', 'scan_type').get(id=scan_id)
            
            # Optimize queries with select_related and prefetch_related
            subdomains = Subdomain.objects.filter(scan_history=scan).select_related('target_domain')
            endpoints = EndPoint.objects.filter(scan_history=scan)
            vulns = Vulnerability.objects.filter(scan_history=scan).select_related('subdomain')
            
            stats = {
                'scan_id': scan_id,
                'domain': scan.domain.name,
                'scan_type': scan.scan_type.engine_name,
                'start_date': scan.start_scan_date,
                'status': scan.scan_status,
                
                # Subdomain statistics
                'subdomains': ScanStatisticsService._get_subdomain_stats(subdomains),
                
                # Endpoint statistics
                'endpoints': ScanStatisticsService._get_endpoint_stats(endpoints),
                
                # Vulnerability statistics
                'vulnerabilities': ScanStatisticsService._get_vulnerability_stats(vulns),
                
                # Additional data
                'emails': Email.objects.filter(emails__in=[scan]).count(),
                'employees': Employee.objects.filter(employees__in=[scan]).count(),
                'buckets': S3Bucket.objects.filter(buckets__in=[scan]).count(),
                'dorks': Dork.objects.filter(dorks__in=[scan]).count(),
            }
            
            # Cache for 5 minutes
            if use_cache:
                cache.set(cache_key, stats, 300)
            
            return stats
            
        except ScanHistory.DoesNotExist:
            logger.error(f"Scan {scan_id} not found")
            raise
        except Exception as e:
            logger.error(f"Error getting scan statistics for scan {scan_id}: {e}")
            raise
    
    @staticmethod
    def _get_subdomain_stats(subdomains: QuerySet) -> Dict:
        """Calculate subdomain statistics"""
        return {
            'total': subdomains.values('name').distinct().count(),
            'alive': subdomains.filter(http_status=200).values('name').distinct().count(),
            'important': subdomains.filter(is_important=True).values('name').distinct().count(),
            'with_ip': subdomains.filter(ip_addresses__isnull=False).values('name').distinct().count(),
            'cdn': subdomains.filter(is_cdn=True).count(),
        }
    
    @staticmethod
    def _get_endpoint_stats(endpoints: QuerySet) -> Dict:
        """Calculate endpoint statistics"""
        return {
            'total': endpoints.values('http_url').distinct().count(),
            'alive': endpoints.filter(http_status=200).values('http_url').distinct().count(),
            'unique_paths': endpoints.values('http_url').distinct().count(),
        }
    
    @staticmethod
    def _get_vulnerability_stats(vulns: QuerySet) -> Dict:
        """Calculate vulnerability statistics using a single query"""
        # Use aggregation to get all counts in one query
        severity_counts = vulns.aggregate(
            total=Count('id'),
            critical=Count('id', filter=Q(severity=4)),
            high=Count('id', filter=Q(severity=3)),
            medium=Count('id', filter=Q(severity=2)),
            low=Count('id', filter=Q(severity=1)),
            info=Count('id', filter=Q(severity=0)),
            unknown=Count('id', filter=Q(severity=-1)),
        )
        
        severity_counts['total_excluding_info'] = (
            severity_counts['total'] - severity_counts['info']
        )
        
        return severity_counts
    
    @staticmethod
    def invalidate_scan_cache(scan_id: int):
        """Invalidate cached statistics for a scan"""
        cache_key = f'scan_stats_{scan_id}'
        cache.delete(cache_key)
        logger.debug(f"Invalidated cache for scan {scan_id}")


class ScanQueryService:
    """
    Service for optimized scan queries
    """
    
    @staticmethod
    def get_scan_with_relations(scan_id: int) -> ScanHistory:
        """
        Get scan with all related objects using optimized queries
        
        Args:
            scan_id: ScanHistory ID
            
        Returns:
            ScanHistory object with prefetched relations
        """
        try:
            scan = (
                ScanHistory.objects
                .select_related('domain', 'scan_type', 'initiated_by', 'aborted_by')
                .prefetch_related(
                    'emails',
                    'employees',
                    'buckets',
                    'dorks',
                    Prefetch('subdomain_set', queryset=Subdomain.objects.select_related('target_domain')),
                    Prefetch('endpoint_set', queryset=EndPoint.objects.select_related('subdomain')),
                    Prefetch('vulnerability_set', queryset=Vulnerability.objects.select_related('subdomain')),
                )
                .get(id=scan_id)
            )
            return scan
        except ScanHistory.DoesNotExist:
            logger.error(f"Scan {scan_id} not found")
            raise
    
    @staticmethod
    def get_recent_scans(domain_id: int, limit: int = 10) -> QuerySet:
        """
        Get recent scans for a domain with optimized query
        
        Args:
            domain_id: Domain ID
            limit: Number of scans to return
            
        Returns:
            QuerySet of recent scans
        """
        return (
            ScanHistory.objects
            .filter(domain__id=domain_id)
            .select_related('domain', 'scan_type', 'initiated_by')
            .order_by('-start_scan_date')
            [:limit]
        )
    
    @staticmethod
    def get_vulnerability_breakdown(scan_id: int) -> Dict:
        """
        Get detailed vulnerability breakdown
        
        Args:
            scan_id: ScanHistory ID
            
        Returns:
            Dictionary with vulnerability breakdown
        """
        vulns = Vulnerability.objects.filter(scan_history_id=scan_id)
        
        # Get common vulnerabilities
        common_vulns = (
            vulns
            .exclude(severity=0)
            .values('name', 'severity')
            .annotate(count=Count('name'))
            .order_by('-count')
            [:10]
        )
        
        # Get common CVEs
        from targetApp.models import CveId
        cves = CveId.objects.filter(cve_ids__scan_history_id=scan_id)
        common_cves = (
            cves
            .annotate(nused=Count('cve_ids'))
            .order_by('-nused')
            .values('name', 'nused')
            [:10]
        )
        
        # Get common CWEs
        from targetApp.models import CweId
        cwes = CweId.objects.filter(cwe_ids__scan_history_id=scan_id)
        common_cwes = (
            cwes
            .annotate(nused=Count('cwe_ids'))
            .order_by('-nused')
            .values('name', 'nused')
            [:10]
        )
        
        # Get common tags
        from targetApp.models import VulnerabilityTags
        tags = VulnerabilityTags.objects.filter(vuln_tags__scan_history_id=scan_id)
        common_tags = (
            tags
            .annotate(nused=Count('vuln_tags'))
            .order_by('-nused')
            .values('name', 'nused')
            [:7]
        )
        
        return {
            'common_vulnerabilities': list(common_vulns),
            'common_cves': list(common_cves),
            'common_cwes': list(common_cwes),
            'common_tags': list(common_tags),
        }


class ScanValidationService:
    """
    Service for validating scan operations
    """
    
    @staticmethod
    def validate_scan_start(domain_id: int, scan_type_id: int, user) -> Tuple[bool, Optional[str]]:
        """
        Validate if a scan can be started
        
        Args:
            domain_id: Domain ID
            scan_type_id: Scan type ID
            user: User object
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if domain exists
            domain = Domain.objects.get(id=domain_id)
            
            # Check if scan type exists
            scan_type = EngineType.objects.get(id=scan_type_id)
            
            # Check if there's already a running scan for this domain
            running_scans = ScanHistory.objects.filter(
                domain=domain,
                scan_status__in=[0, 1]  # Pending or Running
            ).count()
            
            if running_scans > 0:
                return False, f"There is already a running scan for {domain.name}"
            
            # Check user permissions (if needed)
            # Add your permission checks here
            
            return True, None
            
        except Domain.DoesNotExist:
            return False, f"Domain with ID {domain_id} not found"
        except EngineType.DoesNotExist:
            return False, f"Scan type with ID {scan_type_id} not found"
        except Exception as e:
            logger.error(f"Error validating scan start: {e}")
            return False, str(e)
    
    @staticmethod
    def validate_scan_stop(scan_id: int, user) -> Tuple[bool, Optional[str]]:
        """
        Validate if a scan can be stopped
        
        Args:
            scan_id: Scan ID
            user: User object
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            scan = ScanHistory.objects.get(id=scan_id)
            
            # Check if scan is running
            if scan.scan_status not in [0, 1]:  # Not pending or running
                return False, "Scan is not running"
            
            # Check user permissions
            # Add your permission checks here
            
            return True, None
            
        except ScanHistory.DoesNotExist:
            return False, f"Scan with ID {scan_id} not found"
        except Exception as e:
            logger.error(f"Error validating scan stop: {e}")
            return False, str(e)


class ScanCleanupService:
    """
    Service for cleaning up scan data
    """
    
    @staticmethod
    def delete_scan_data(scan_id: int, delete_files: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Delete scan data and optionally associated files
        
        Args:
            scan_id: Scan ID
            delete_files: Whether to delete associated files
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            scan = ScanHistory.objects.get(id=scan_id)
            
            # Delete associated files if requested
            if delete_files and scan.results_dir:
                import shutil
                import os
                results_path = os.path.join('/usr/src/scan_results', scan.results_dir)
                if os.path.exists(results_path):
                    shutil.rmtree(results_path)
                    logger.info(f"Deleted scan results directory: {results_path}")
            
            # Invalidate cache
            ScanStatisticsService.invalidate_scan_cache(scan_id)
            
            # Delete scan
            scan.delete()
            logger.info(f"Deleted scan {scan_id}")
            
            return True, None
            
        except ScanHistory.DoesNotExist:
            return False, f"Scan with ID {scan_id} not found"
        except Exception as e:
            logger.error(f"Error deleting scan {scan_id}: {e}")
            return False, str(e)
    
    @staticmethod
    def cleanup_old_scans(days: int = 30) -> int:
        """
        Clean up scans older than specified days
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of scans deleted
        """
        try:
            cutoff_date = timezone.now() - timezone.timedelta(days=days)
            old_scans = ScanHistory.objects.filter(
                start_scan_date__lt=cutoff_date,
                scan_status=2  # Completed
            )
            
            count = old_scans.count()
            
            for scan in old_scans:
                ScanCleanupService.delete_scan_data(scan.id, delete_files=True)
            
            logger.info(f"Cleaned up {count} old scans")
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up old scans: {e}")
            return 0


class ScanExportService:
    """
    Service for exporting scan data
    """
    
    @staticmethod
    def export_subdomains(scan_id: int, format: str = 'json') -> Dict:
        """
        Export subdomains in specified format
        
        Args:
            scan_id: Scan ID
            format: Export format (json, csv, xml)
            
        Returns:
            Dictionary with export data
        """
        try:
            subdomains = (
                Subdomain.objects
                .filter(scan_history_id=scan_id)
                .select_related('target_domain')
                .prefetch_related('ip_addresses', 'technologies')
            )
            
            data = []
            for subdomain in subdomains:
                data.append({
                    'name': subdomain.name,
                    'http_url': subdomain.http_url,
                    'http_status': subdomain.http_status,
                    'ip_addresses': [ip.address for ip in subdomain.ip_addresses.all()],
                    'technologies': [tech.name for tech in subdomain.technologies.all()],
                    'is_important': subdomain.is_important,
                    'content_type': subdomain.content_type,
                    'webserver': subdomain.webserver,
                    'page_title': subdomain.page_title,
                })
            
            return {
                'scan_id': scan_id,
                'export_date': timezone.now().isoformat(),
                'format': format,
                'count': len(data),
                'data': data
            }
            
        except Exception as e:
            logger.error(f"Error exporting subdomains for scan {scan_id}: {e}")
            raise
    
    @staticmethod
    def export_vulnerabilities(scan_id: int, format: str = 'json') -> Dict:
        """
        Export vulnerabilities in specified format
        
        Args:
            scan_id: Scan ID
            format: Export format (json, csv, xml)
            
        Returns:
            Dictionary with export data
        """
        try:
            vulns = (
                Vulnerability.objects
                .filter(scan_history_id=scan_id)
                .select_related('subdomain', 'endpoint')
                .prefetch_related('cve_ids', 'cwe_ids', 'tags')
            )
            
            data = []
            for vuln in vulns:
                data.append({
                    'name': vuln.name,
                    'severity': vuln.get_severity_display(),
                    'description': vuln.description,
                    'subdomain': vuln.subdomain.name if vuln.subdomain else None,
                    'endpoint': vuln.endpoint.http_url if vuln.endpoint else None,
                    'cves': [cve.name for cve in vuln.cve_ids.all()],
                    'cwes': [cwe.name for cwe in vuln.cwe_ids.all()],
                    'tags': [tag.name for tag in vuln.tags.all()],
                    'discovered_date': vuln.discovered_date.isoformat() if vuln.discovered_date else None,
                })
            
            return {
                'scan_id': scan_id,
                'export_date': timezone.now().isoformat(),
                'format': format,
                'count': len(data),
                'data': data
            }
            
        except Exception as e:
            logger.error(f"Error exporting vulnerabilities for scan {scan_id}: {e}")
            raise
