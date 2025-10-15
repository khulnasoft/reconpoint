"""
Domain service for business logic related to domains.
"""
from typing import Optional, List, Dict, Any
from django.db import transaction
from django.utils import timezone
from django.db.models import Count, Q, Prefetch
from targetApp.models import Domain, Organization
from dashboard.models import Project
from reconPoint.enhanced_validators import InputValidator
from reconPoint.error_handlers import ValidationException, ResourceNotFoundException
from .base_service import BaseService
import logging

logger = logging.getLogger(__name__)


class DomainService(BaseService):
    """Service for domain-related operations."""
    
    @staticmethod
    @transaction.atomic
    def create_domain(
        name: str,
        project_id: int,
        description: Optional[str] = None,
        h1_team_handle: Optional[str] = None,
        ip_address_cidr: Optional[str] = None,
        request_headers: Optional[Dict] = None
    ) -> Domain:
        """
        Create a new domain with validation.
        
        Args:
            name: Domain name
            project_id: Project ID
            description: Optional description
            h1_team_handle: HackerOne team handle
            ip_address_cidr: IP address CIDR
            request_headers: Custom request headers
            
        Returns:
            Created Domain instance
            
        Raises:
            ValidationException: If validation fails
            ResourceNotFoundException: If project not found
        """
        # Validate domain name
        try:
            InputValidator.validate_domain(name)
        except Exception as e:
            raise ValidationException(f"Invalid domain name: {str(e)}")
        
        # Check if domain already exists
        if Domain.objects.filter(name=name).exists():
            raise ValidationException(
                f"Domain '{name}' already exists",
                field='name'
            )
        
        # Get project
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            raise ResourceNotFoundException('Project', project_id)
        
        # Validate CIDR if provided
        if ip_address_cidr:
            try:
                InputValidator.validate_cidr(ip_address_cidr)
            except Exception as e:
                raise ValidationException(f"Invalid CIDR: {str(e)}", field='ip_address_cidr')
        
        # Create domain
        domain = Domain.objects.create(
            name=name,
            project=project,
            description=description,
            h1_team_handle=h1_team_handle,
            ip_address_cidr=ip_address_cidr,
            request_headers=request_headers,
            insert_date=timezone.now()
        )
        
        logger.info(f"Created domain: {name} (ID: {domain.id}) for project: {project.name}")
        
        return domain
    
    @staticmethod
    def get_domain_with_stats(domain_id: int) -> Dict[str, Any]:
        """
        Get domain with comprehensive statistics.
        
        Args:
            domain_id: Domain ID
            
        Returns:
            Dictionary with domain data and statistics
            
        Raises:
            ResourceNotFoundException: If domain not found
        """
        try:
            domain = Domain.objects.select_related(
                'project',
                'domain_info'
            ).annotate(
                total_scans=Count('scanhistory', distinct=True),
                total_subdomains=Count('scanhistory__subdomain', distinct=True),
                total_endpoints=Count('scanhistory__endpoint', distinct=True),
                total_vulnerabilities=Count('scanhistory__vulnerability', distinct=True),
                critical_vulns=Count(
                    'scanhistory__vulnerability',
                    filter=Q(scanhistory__vulnerability__severity=4),
                    distinct=True
                ),
                high_vulns=Count(
                    'scanhistory__vulnerability',
                    filter=Q(scanhistory__vulnerability__severity=3),
                    distinct=True
                ),
                medium_vulns=Count(
                    'scanhistory__vulnerability',
                    filter=Q(scanhistory__vulnerability__severity=2),
                    distinct=True
                ),
                low_vulns=Count(
                    'scanhistory__vulnerability',
                    filter=Q(scanhistory__vulnerability__severity=1),
                    distinct=True
                ),
                info_vulns=Count(
                    'scanhistory__vulnerability',
                    filter=Q(scanhistory__vulnerability__severity=0),
                    distinct=True
                )
            ).get(id=domain_id)
        except Domain.DoesNotExist:
            raise ResourceNotFoundException('Domain', domain_id)
        
        # Get organizations
        organizations = Organization.objects.filter(domains__id=domain_id).values_list('name', flat=True)
        
        return {
            'id': domain.id,
            'name': domain.name,
            'description': domain.description,
            'project': {
                'id': domain.project.id,
                'name': domain.project.name,
                'slug': domain.project.slug
            },
            'organizations': list(organizations),
            'statistics': {
                'total_scans': domain.total_scans,
                'total_subdomains': domain.total_subdomains,
                'total_endpoints': domain.total_endpoints,
                'total_vulnerabilities': domain.total_vulnerabilities,
                'vulnerabilities_by_severity': {
                    'critical': domain.critical_vulns,
                    'high': domain.high_vulns,
                    'medium': domain.medium_vulns,
                    'low': domain.low_vulns,
                    'info': domain.info_vulns
                }
            },
            'last_scan_date': domain.start_scan_date,
            'insert_date': domain.insert_date,
            'h1_team_handle': domain.h1_team_handle,
            'ip_address_cidr': domain.ip_address_cidr
        }
    
    @staticmethod
    def list_domains(
        project_id: Optional[int] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List domains with filtering and pagination.
        
        Args:
            project_id: Filter by project ID
            search: Search term for domain name
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            Dictionary with domains list and metadata
        """
        queryset = Domain.objects.select_related('project').annotate(
            scan_count=Count('scanhistory', distinct=True),
            vuln_count=Count('scanhistory__vulnerability', distinct=True)
        )
        
        # Apply filters
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        # Get total count
        total_count = queryset.count()
        
        # Apply pagination
        domains = queryset.order_by('-insert_date')[offset:offset + limit]
        
        return {
            'count': total_count,
            'limit': limit,
            'offset': offset,
            'results': [
                {
                    'id': domain.id,
                    'name': domain.name,
                    'description': domain.description,
                    'project': domain.project.name,
                    'scan_count': domain.scan_count,
                    'vuln_count': domain.vuln_count,
                    'insert_date': domain.insert_date,
                    'last_scan_date': domain.start_scan_date
                }
                for domain in domains
            ]
        }
    
    @staticmethod
    @transaction.atomic
    def update_domain(
        domain_id: int,
        **update_fields
    ) -> Domain:
        """
        Update domain fields.
        
        Args:
            domain_id: Domain ID
            **update_fields: Fields to update
            
        Returns:
            Updated Domain instance
            
        Raises:
            ResourceNotFoundException: If domain not found
            ValidationException: If validation fails
        """
        try:
            domain = Domain.objects.select_for_update().get(id=domain_id)
        except Domain.DoesNotExist:
            raise ResourceNotFoundException('Domain', domain_id)
        
        # Validate fields
        if 'name' in update_fields:
            try:
                InputValidator.validate_domain(update_fields['name'])
            except Exception as e:
                raise ValidationException(f"Invalid domain name: {str(e)}")
            
            # Check for duplicates
            if Domain.objects.filter(name=update_fields['name']).exclude(id=domain_id).exists():
                raise ValidationException(f"Domain '{update_fields['name']}' already exists")
        
        if 'ip_address_cidr' in update_fields and update_fields['ip_address_cidr']:
            try:
                InputValidator.validate_cidr(update_fields['ip_address_cidr'])
            except Exception as e:
                raise ValidationException(f"Invalid CIDR: {str(e)}")
        
        # Update fields
        for field, value in update_fields.items():
            if hasattr(domain, field):
                setattr(domain, field, value)
        
        domain.save()
        
        logger.info(f"Updated domain {domain.name} (ID: {domain_id})")
        
        return domain
    
    @staticmethod
    @transaction.atomic
    def delete_domain(domain_id: int, user) -> None:
        """
        Delete domain with audit logging.
        
        Args:
            domain_id: Domain ID
            user: User performing the deletion
            
        Raises:
            ResourceNotFoundException: If domain not found
        """
        try:
            domain = Domain.objects.select_for_update().get(id=domain_id)
        except Domain.DoesNotExist:
            raise ResourceNotFoundException('Domain', domain_id)
        
        domain_name = domain.name
        project_name = domain.project.name
        
        # Delete domain (cascades to related objects)
        domain.delete()
        
        logger.info(
            f"User {user.username} deleted domain: {domain_name} "
            f"(ID: {domain_id}) from project: {project_name}"
        )
    
    @staticmethod
    def get_domain_scan_history(domain_id: int, limit: int = 10) -> List[Dict]:
        """
        Get recent scan history for a domain.
        
        Args:
            domain_id: Domain ID
            limit: Maximum number of scans to return
            
        Returns:
            List of scan history dictionaries
            
        Raises:
            ResourceNotFoundException: If domain not found
        """
        try:
            domain = Domain.objects.get(id=domain_id)
        except Domain.DoesNotExist:
            raise ResourceNotFoundException('Domain', domain_id)
        
        from startScan.models import ScanHistory
        
        scans = ScanHistory.objects.filter(
            domain=domain
        ).select_related(
            'scan_type'
        ).annotate(
            subdomain_count=Count('subdomain', distinct=True),
            vuln_count=Count('vulnerability', distinct=True)
        ).order_by('-start_scan_date')[:limit]
        
        return [
            {
                'id': scan.id,
                'scan_type': scan.scan_type.engine_name,
                'status': scan.scan_status,
                'start_date': scan.start_scan_date,
                'stop_date': scan.stop_scan_date,
                'subdomain_count': scan.subdomain_count,
                'vulnerability_count': scan.vuln_count,
                'error_message': scan.error_message
            }
            for scan in scans
        ]
