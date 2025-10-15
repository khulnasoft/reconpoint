"""
Scan service for business logic related to scans.
"""
from typing import Optional, List, Dict, Any
from django.db import transaction
from django.utils import timezone
from django.db.models import Count, Q, Prefetch
from startScan.models import ScanHistory, Subdomain, Vulnerability, EndPoint
from targetApp.models import Domain
from scanEngine.models import EngineType
from reconPoint.error_handlers import ResourceNotFoundException, ValidationException
from .base_service import BaseService
import logging

logger = logging.getLogger(__name__)


class ScanService(BaseService):
    """Service for scan-related operations."""
    
    @staticmethod
    @transaction.atomic
    def create_scan(
        domain_id: int,
        scan_type_id: int,
        initiated_by_user,
        out_of_scope_subdomains: Optional[List[str]] = None,
        imported_subdomains: Optional[List[str]] = None,
        **kwargs
    ) -> ScanHistory:
        """
        Create a new scan.
        
        Args:
            domain_id: Target domain ID
            scan_type_id: Scan engine type ID
            initiated_by_user: User initiating the scan
            out_of_scope_subdomains: List of out-of-scope subdomains
            imported_subdomains: List of imported subdomains
            **kwargs: Additional scan configuration
            
        Returns:
            Created ScanHistory instance
            
        Raises:
            ResourceNotFoundException: If domain or scan type not found
            ValidationException: If validation fails
        """
        # Validate domain exists
        try:
            domain = Domain.objects.select_for_update().get(id=domain_id)
        except Domain.DoesNotExist:
            raise ResourceNotFoundException('Domain', domain_id)
        
        # Validate scan type exists
        try:
            scan_type = EngineType.objects.get(id=scan_type_id)
        except EngineType.DoesNotExist:
            raise ResourceNotFoundException('EngineType', scan_type_id)
        
        # Check if there's already a running scan for this domain
        running_scans = ScanHistory.objects.filter(
            domain=domain,
            scan_status__in=[-1, 1]  # Pending or Running
        ).exists()
        
        if running_scans:
            raise ValidationException(
                f"There is already a running scan for domain '{domain.name}'"
            )
        
        # Create scan
        scan = ScanHistory.objects.create(
            domain=domain,
            scan_type=scan_type,
            start_scan_date=timezone.now(),
            scan_status=-1,  # Pending
            initiated_by=initiated_by_user,
            cfg_out_of_scope_subdomains=out_of_scope_subdomains or [],
            cfg_imported_subdomains=imported_subdomains or [],
            tasks=scan_type.tasks if hasattr(scan_type, 'tasks') else [],
            **kwargs
        )
        
        # Update domain's last scan date
        domain.start_scan_date = timezone.now()
        domain.save(update_fields=['start_scan_date'])
        
        logger.info(
            f"Created scan {scan.id} for domain {domain.name} "
            f"using engine {scan_type.engine_name} by user {initiated_by_user.username}"
        )
        
        return scan
    
    @staticmethod
    def get_scan_details(scan_id: int) -> Dict[str, Any]:
        """
        Get detailed scan information.
        
        Args:
            scan_id: Scan history ID
            
        Returns:
            Dictionary with scan details
            
        Raises:
            ResourceNotFoundException: If scan not found
        """
        try:
            scan = ScanHistory.objects.select_related(
                'domain',
                'domain__project',
                'scan_type',
                'initiated_by',
                'aborted_by'
            ).prefetch_related(
                'scanactivity_set'
            ).annotate(
                subdomain_count=Count('subdomain', distinct=True),
                endpoint_count=Count('endpoint', distinct=True),
                vuln_count=Count('vulnerability', distinct=True),
                critical_count=Count('vulnerability', filter=Q(vulnerability__severity=4), distinct=True),
                high_count=Count('vulnerability', filter=Q(vulnerability__severity=3), distinct=True),
                medium_count=Count('vulnerability', filter=Q(vulnerability__severity=2), distinct=True),
                low_count=Count('vulnerability', filter=Q(vulnerability__severity=1), distinct=True),
                info_count=Count('vulnerability', filter=Q(vulnerability__severity=0), distinct=True)
            ).get(id=scan_id)
        except ScanHistory.DoesNotExist:
            raise ResourceNotFoundException('ScanHistory', scan_id)
        
        # Get scan activities
        activities = scan.scanactivity_set.all().order_by('time')
        
        # Calculate progress
        total_tasks = len(scan.tasks) if scan.tasks else 0
        completed_tasks = activities.filter(status=2).count()
        progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            'id': scan.id,
            'domain': {
                'id': scan.domain.id,
                'name': scan.domain.name,
                'project': scan.domain.project.name
            },
            'scan_type': {
                'id': scan.scan_type.id,
                'name': scan.scan_type.engine_name
            },
            'status': scan.scan_status,
            'start_date': scan.start_scan_date,
            'stop_date': scan.stop_scan_date,
            'initiated_by': scan.initiated_by.username if scan.initiated_by else None,
            'aborted_by': scan.aborted_by.username if scan.aborted_by else None,
            'error_message': scan.error_message,
            'progress': {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'percentage': round(progress_percentage, 2)
            },
            'statistics': {
                'subdomains': scan.subdomain_count,
                'endpoints': scan.endpoint_count,
                'vulnerabilities': {
                    'total': scan.vuln_count,
                    'critical': scan.critical_count,
                    'high': scan.high_count,
                    'medium': scan.medium_count,
                    'low': scan.low_count,
                    'info': scan.info_count
                }
            },
            'activities': [
                {
                    'title': activity.title,
                    'name': activity.name,
                    'status': activity.status,
                    'time': activity.time,
                    'error_message': activity.error_message
                }
                for activity in activities
            ],
            'configuration': {
                'out_of_scope_subdomains': scan.cfg_out_of_scope_subdomains,
                'imported_subdomains': scan.cfg_imported_subdomains,
                'excluded_paths': scan.cfg_excluded_paths,
                'starting_point_path': scan.cfg_starting_point_path
            }
        }
    
    @staticmethod
    @transaction.atomic
    def update_scan_status(
        scan_id: int,
        status: int,
        error_message: Optional[str] = None
    ) -> ScanHistory:
        """
        Update scan status.
        
        Args:
            scan_id: Scan history ID
            status: New status (-1: pending, 0: failed, 1: running, 2: completed, 3: aborted)
            error_message: Optional error message
            
        Returns:
            Updated ScanHistory instance
            
        Raises:
            ResourceNotFoundException: If scan not found
            ValidationException: If status is invalid
        """
        if status not in [-1, 0, 1, 2, 3]:
            raise ValidationException(
                f"Invalid scan status: {status}. Must be -1, 0, 1, 2, or 3"
            )
        
        try:
            scan = ScanHistory.objects.select_for_update().get(id=scan_id)
        except ScanHistory.DoesNotExist:
            raise ResourceNotFoundException('ScanHistory', scan_id)
        
        scan.scan_status = status
        
        if error_message:
            scan.error_message = error_message[:300]  # Limit length
        
        # Set stop date if scan is completed, failed, or aborted
        if status in [0, 2, 3] and not scan.stop_scan_date:
            scan.stop_scan_date = timezone.now()
        
        scan.save()
        
        logger.info(f"Updated scan {scan_id} status to {status}")
        
        return scan
    
    @staticmethod
    @transaction.atomic
    def abort_scan(scan_id: int, user) -> ScanHistory:
        """
        Abort a running scan.
        
        Args:
            scan_id: Scan history ID
            user: User aborting the scan
            
        Returns:
            Updated ScanHistory instance
            
        Raises:
            ResourceNotFoundException: If scan not found
            ValidationException: If scan cannot be aborted
        """
        try:
            scan = ScanHistory.objects.select_for_update().get(id=scan_id)
        except ScanHistory.DoesNotExist:
            raise ResourceNotFoundException('ScanHistory', scan_id)
        
        # Check if scan can be aborted
        if scan.scan_status not in [-1, 1]:  # Pending or Running
            raise ValidationException(
                f"Cannot abort scan with status {scan.scan_status}. "
                "Only pending or running scans can be aborted."
            )
        
        # Abort celery tasks
        from reconPoint.celery import app
        for celery_id in scan.celery_ids:
            try:
                app.control.revoke(celery_id, terminate=True)
            except Exception as e:
                logger.error(f"Failed to revoke celery task {celery_id}: {e}")
        
        # Update scan
        scan.scan_status = 3  # Aborted
        scan.stop_scan_date = timezone.now()
        scan.aborted_by = user
        scan.save()
        
        logger.info(f"User {user.username} aborted scan {scan_id}")
        
        return scan
    
    @staticmethod
    def get_scan_vulnerabilities(
        scan_id: int,
        severity: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get vulnerabilities for a scan.
        
        Args:
            scan_id: Scan history ID
            severity: Filter by severity (0-4)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            Dictionary with vulnerabilities and metadata
            
        Raises:
            ResourceNotFoundException: If scan not found
        """
        # Verify scan exists
        if not ScanHistory.objects.filter(id=scan_id).exists():
            raise ResourceNotFoundException('ScanHistory', scan_id)
        
        queryset = Vulnerability.objects.filter(
            scan_history_id=scan_id
        ).select_related(
            'subdomain',
            'endpoint'
        ).prefetch_related(
            'tags',
            'cve_ids',
            'cwe_ids'
        )
        
        # Apply severity filter
        if severity is not None:
            queryset = queryset.filter(severity=severity)
        
        # Get total count
        total_count = queryset.count()
        
        # Apply pagination
        vulnerabilities = queryset.order_by('-severity', '-discovered_date')[offset:offset + limit]
        
        return {
            'count': total_count,
            'limit': limit,
            'offset': offset,
            'results': [
                {
                    'id': vuln.id,
                    'name': vuln.name,
                    'severity': vuln.severity,
                    'http_url': vuln.http_url,
                    'subdomain': vuln.subdomain.name if vuln.subdomain else None,
                    'discovered_date': vuln.discovered_date,
                    'cvss_score': vuln.cvss_score,
                    'cve_ids': [cve.name for cve in vuln.cve_ids.all()],
                    'cwe_ids': [cwe.name for cwe in vuln.cwe_ids.all()],
                    'tags': [tag.name for tag in vuln.tags.all()],
                    'open_status': vuln.open_status
                }
                for vuln in vulnerabilities
            ]
        }
    
    @staticmethod
    def get_scan_subdomains(
        scan_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get subdomains discovered in a scan.
        
        Args:
            scan_id: Scan history ID
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            Dictionary with subdomains and metadata
            
        Raises:
            ResourceNotFoundException: If scan not found
        """
        # Verify scan exists
        if not ScanHistory.objects.filter(id=scan_id).exists():
            raise ResourceNotFoundException('ScanHistory', scan_id)
        
        queryset = Subdomain.objects.filter(
            scan_history_id=scan_id
        ).select_related(
            'target_domain'
        ).prefetch_related(
            'technologies',
            'ip_addresses'
        ).annotate(
            endpoint_count=Count('endpoint', distinct=True),
            vuln_count=Count('vulnerability', distinct=True)
        )
        
        # Get total count
        total_count = queryset.count()
        
        # Apply pagination
        subdomains = queryset.order_by('name')[offset:offset + limit]
        
        return {
            'count': total_count,
            'limit': limit,
            'offset': offset,
            'results': [
                {
                    'id': subdomain.id,
                    'name': subdomain.name,
                    'http_url': subdomain.http_url,
                    'http_status': subdomain.http_status,
                    'page_title': subdomain.page_title,
                    'discovered_date': subdomain.discovered_date,
                    'is_important': subdomain.is_important,
                    'endpoint_count': subdomain.endpoint_count,
                    'vulnerability_count': subdomain.vuln_count,
                    'technologies': [tech.name for tech in subdomain.technologies.all()],
                    'ip_addresses': [ip.address for ip in subdomain.ip_addresses.all()]
                }
                for subdomain in subdomains
            ]
        }
