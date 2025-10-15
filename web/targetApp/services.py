"""
Service layer for targetApp module
Separates business logic from views for better maintainability and testing
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from django.db.models import Count, Q, Prefetch, QuerySet
from django.core.cache import cache
from django.utils import timezone
from django.db import transaction

from .models import Domain, Organization, DomainInfo, Registrar
from startScan.models import ScanHistory, Subdomain, EndPoint, Vulnerability

logger = logging.getLogger(__name__)


class DomainService:
    """
    Service for domain operations
    """
    
    @staticmethod
    @transaction.atomic
    def create_domain(
        name: str,
        project,
        description: str = None,
        h1_team_handle: str = None,
        ip_address_cidr: str = None
    ) -> Tuple[Domain, bool]:
        """
        Create a new domain with proper validation
        
        Args:
            name: Domain name
            project: Project object
            description: Optional description
            h1_team_handle: Optional HackerOne team handle
            ip_address_cidr: Optional IP/CIDR
            
        Returns:
            Tuple of (Domain object, created boolean)
        """
        try:
            domain, created = Domain.objects.get_or_create(
                name=name,
                defaults={
                    'description': description,
                    'h1_team_handle': h1_team_handle,
                    'ip_address_cidr': ip_address_cidr,
                    'project': project,
                    'insert_date': timezone.now()
                }
            )
            
            if created:
                logger.info(f"Created new domain: {name}")
            else:
                logger.debug(f"Domain already exists: {name}")
            
            return domain, created
            
        except Exception as e:
            logger.error(f"Error creating domain {name}: {e}")
            raise
    
    @staticmethod
    def get_domain_statistics(domain_id: int, use_cache: bool = True) -> Dict:
        """
        Get comprehensive domain statistics with caching
        
        Args:
            domain_id: Domain ID
            use_cache: Whether to use cached results
            
        Returns:
            Dictionary containing domain statistics
        """
        cache_key = f'domain_stats_{domain_id}'
        
        if use_cache:
            cached_stats = cache.get(cache_key)
            if cached_stats:
                logger.debug(f"Returning cached statistics for domain {domain_id}")
                return cached_stats
        
        try:
            domain = Domain.objects.select_related('project', 'domain_info').get(id=domain_id)
            
            # Get scan statistics
            scans = ScanHistory.objects.filter(domain_id=domain_id)
            last_week = timezone.now() - timezone.timedelta(days=7)
            
            # Get subdomain statistics
            subdomains = Subdomain.objects.filter(target_domain_id=domain_id)
            subdomain_stats = subdomains.aggregate(
                total=Count('name', distinct=True),
                alive=Count('name', distinct=True, filter=Q(http_status=200)),
                important=Count('name', distinct=True, filter=Q(is_important=True)),
            )
            
            # Get endpoint statistics
            endpoints = EndPoint.objects.filter(target_domain_id=domain_id)
            endpoint_stats = endpoints.aggregate(
                total=Count('http_url', distinct=True),
                alive=Count('http_url', distinct=True, filter=Q(http_status=200)),
            )
            
            # Get vulnerability statistics
            vulns = Vulnerability.objects.filter(target_domain_id=domain_id)
            vuln_stats = vulns.aggregate(
                total=Count('id'),
                critical=Count('id', filter=Q(severity=4)),
                high=Count('id', filter=Q(severity=3)),
                medium=Count('id', filter=Q(severity=2)),
                low=Count('id', filter=Q(severity=1)),
                info=Count('id', filter=Q(severity=0)),
                unknown=Count('id', filter=Q(severity=-1)),
            )
            
            stats = {
                'domain_id': domain_id,
                'domain_name': domain.name,
                'project': domain.project.name if domain.project else None,
                'scans': {
                    'total': scans.count(),
                    'this_week': scans.filter(start_scan_date__gte=last_week).count(),
                    'running': scans.filter(scan_status__in=[0, 1]).count(),
                    'completed': scans.filter(scan_status=2).count(),
                },
                'subdomains': subdomain_stats,
                'endpoints': endpoint_stats,
                'vulnerabilities': vuln_stats,
                'last_scan': scans.order_by('-start_scan_date').first(),
            }
            
            # Cache for 5 minutes
            if use_cache:
                cache.set(cache_key, stats, 300)
            
            return stats
            
        except Domain.DoesNotExist:
            logger.error(f"Domain {domain_id} not found")
            raise
        except Exception as e:
            logger.error(f"Error getting domain statistics for domain {domain_id}: {e}")
            raise
    
    @staticmethod
    def invalidate_domain_cache(domain_id: int):
        """Invalidate cached statistics for a domain"""
        cache_key = f'domain_stats_{domain_id}'
        cache.delete(cache_key)
        logger.debug(f"Invalidated cache for domain {domain_id}")
    
    @staticmethod
    def get_domains_with_relations(project_slug: str) -> QuerySet:
        """
        Get domains with optimized queries
        
        Args:
            project_slug: Project slug
            
        Returns:
            QuerySet of domains with prefetched relations
        """
        return (
            Domain.objects
            .filter(project__slug=project_slug)
            .select_related('project', 'domain_info')
            .prefetch_related(
                Prefetch('scanhistory_set', queryset=ScanHistory.objects.order_by('-start_scan_date')[:5]),
            )
            .order_by('-insert_date')
        )
    
    @staticmethod
    @transaction.atomic
    def delete_domain(domain_id: int, delete_scan_results: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Delete a domain and optionally its scan results
        
        Args:
            domain_id: Domain ID
            delete_scan_results: Whether to delete scan result files
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            domain = Domain.objects.get(id=domain_id)
            domain_name = domain.name
            
            # Delete scan result files if requested
            if delete_scan_results:
                import os
                import shutil
                from django.conf import settings
                
                results_path = os.path.join(settings.TOOL_LOCATION, 'scan_results', f'{domain_name}*')
                if os.path.exists(results_path):
                    shutil.rmtree(results_path)
                    logger.info(f"Deleted scan results for domain: {domain_name}")
            
            # Invalidate cache
            DomainService.invalidate_domain_cache(domain_id)
            
            # Delete domain (cascade will delete related objects)
            domain.delete()
            logger.info(f"Deleted domain: {domain_name}")
            
            return True, None
            
        except Domain.DoesNotExist:
            return False, f"Domain with ID {domain_id} not found"
        except Exception as e:
            logger.error(f"Error deleting domain {domain_id}: {e}")
            return False, str(e)
    
    @staticmethod
    def bulk_delete_domains(domain_ids: List[int]) -> Tuple[int, List[str]]:
        """
        Delete multiple domains
        
        Args:
            domain_ids: List of domain IDs
            
        Returns:
            Tuple of (deleted_count, error_messages)
        """
        deleted_count = 0
        errors = []
        
        for domain_id in domain_ids:
            success, error = DomainService.delete_domain(domain_id, delete_scan_results=False)
            if success:
                deleted_count += 1
            else:
                errors.append(f"Domain {domain_id}: {error}")
        
        return deleted_count, errors


class OrganizationService:
    """
    Service for organization operations
    """
    
    @staticmethod
    @transaction.atomic
    def create_organization(
        name: str,
        project,
        description: str = None,
        domain_ids: List[int] = None
    ) -> Tuple[Organization, bool]:
        """
        Create a new organization with domains
        
        Args:
            name: Organization name
            project: Project object
            description: Optional description
            domain_ids: List of domain IDs to add
            
        Returns:
            Tuple of (Organization object, created boolean)
        """
        try:
            organization, created = Organization.objects.get_or_create(
                name=name,
                project=project,
                defaults={
                    'description': description,
                    'insert_date': timezone.now()
                }
            )
            
            if created:
                logger.info(f"Created new organization: {name}")
                
                # Add domains if provided
                if domain_ids:
                    domains = Domain.objects.filter(id__in=domain_ids)
                    organization.domains.add(*domains)
                    logger.info(f"Added {len(domain_ids)} domains to organization {name}")
            else:
                logger.debug(f"Organization already exists: {name}")
            
            return organization, created
            
        except Exception as e:
            logger.error(f"Error creating organization {name}: {e}")
            raise
    
    @staticmethod
    def get_organization_statistics(organization_id: int) -> Dict:
        """
        Get organization statistics
        
        Args:
            organization_id: Organization ID
            
        Returns:
            Dictionary containing organization statistics
        """
        try:
            organization = Organization.objects.prefetch_related('domains').get(id=organization_id)
            
            domains = organization.domains.all()
            domain_ids = list(domains.values_list('id', flat=True))
            
            # Aggregate statistics across all domains
            scans = ScanHistory.objects.filter(domain_id__in=domain_ids)
            subdomains = Subdomain.objects.filter(target_domain_id__in=domain_ids)
            endpoints = EndPoint.objects.filter(target_domain_id__in=domain_ids)
            vulns = Vulnerability.objects.filter(target_domain_id__in=domain_ids)
            
            stats = {
                'organization_id': organization_id,
                'organization_name': organization.name,
                'domain_count': domains.count(),
                'domains': [{'id': d.id, 'name': d.name} for d in domains],
                'scans': {
                    'total': scans.count(),
                    'running': scans.filter(scan_status__in=[0, 1]).count(),
                    'completed': scans.filter(scan_status=2).count(),
                },
                'subdomains': {
                    'total': subdomains.values('name').distinct().count(),
                    'alive': subdomains.filter(http_status=200).values('name').distinct().count(),
                },
                'endpoints': {
                    'total': endpoints.values('http_url').distinct().count(),
                    'alive': endpoints.filter(http_status=200).values('http_url').distinct().count(),
                },
                'vulnerabilities': vulns.aggregate(
                    total=Count('id'),
                    critical=Count('id', filter=Q(severity=4)),
                    high=Count('id', filter=Q(severity=3)),
                    medium=Count('id', filter=Q(severity=2)),
                    low=Count('id', filter=Q(severity=1)),
                ),
            }
            
            return stats
            
        except Organization.DoesNotExist:
            logger.error(f"Organization {organization_id} not found")
            raise
        except Exception as e:
            logger.error(f"Error getting organization statistics: {e}")
            raise
    
    @staticmethod
    @transaction.atomic
    def update_organization_domains(
        organization_id: int,
        domain_ids: List[int]
    ) -> Tuple[bool, Optional[str]]:
        """
        Update organization domains
        
        Args:
            organization_id: Organization ID
            domain_ids: New list of domain IDs
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            organization = Organization.objects.get(id=organization_id)
            
            # Remove all existing domains
            organization.domains.clear()
            
            # Add new domains
            if domain_ids:
                domains = Domain.objects.filter(id__in=domain_ids)
                organization.domains.add(*domains)
                logger.info(f"Updated organization {organization.name} with {len(domain_ids)} domains")
            
            return True, None
            
        except Organization.DoesNotExist:
            return False, f"Organization with ID {organization_id} not found"
        except Exception as e:
            logger.error(f"Error updating organization domains: {e}")
            return False, str(e)


class DomainInfoService:
    """
    Service for domain information operations
    """
    
    @staticmethod
    def get_whois_info(domain_id: int) -> Optional[Dict]:
        """
        Get WHOIS information for a domain
        
        Args:
            domain_id: Domain ID
            
        Returns:
            Dictionary with WHOIS information or None
        """
        try:
            domain = Domain.objects.select_related('domain_info').get(id=domain_id)
            
            if not domain.domain_info:
                return None
            
            info = domain.domain_info
            
            return {
                'dnssec': info.dnssec,
                'created': info.created,
                'updated': info.updated,
                'expires': info.expires,
                'registrar': {
                    'name': info.registrar.name if info.registrar else None,
                    'email': info.registrar.email if info.registrar else None,
                    'phone': info.registrar.phone if info.registrar else None,
                    'url': info.registrar.url if info.registrar else None,
                } if info.registrar else None,
                'registrant': {
                    'name': info.registrant.name if info.registrant else None,
                    'organization': info.registrant.organization if info.registrant else None,
                    'email': info.registrant.email if info.registrant else None,
                } if info.registrant else None,
                'name_servers': [ns.name for ns in info.name_servers.all()],
                'whois_server': info.whois_server,
            }
            
        except Domain.DoesNotExist:
            logger.error(f"Domain {domain_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error getting WHOIS info: {e}")
            return None
    
    @staticmethod
    @transaction.atomic
    def update_domain_info(domain_id: int, whois_data: Dict) -> Tuple[bool, Optional[str]]:
        """
        Update domain WHOIS information
        
        Args:
            domain_id: Domain ID
            whois_data: WHOIS data dictionary
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            domain = Domain.objects.get(id=domain_id)
            
            # Create or update DomainInfo
            if domain.domain_info:
                domain_info = domain.domain_info
            else:
                domain_info = DomainInfo.objects.create()
                domain.domain_info = domain_info
                domain.save()
            
            # Update fields
            domain_info.dnssec = whois_data.get('dnssec', False)
            domain_info.created = whois_data.get('created')
            domain_info.updated = whois_data.get('updated')
            domain_info.expires = whois_data.get('expires')
            domain_info.whois_server = whois_data.get('whois_server')
            domain_info.save()
            
            logger.info(f"Updated domain info for {domain.name}")
            return True, None
            
        except Domain.DoesNotExist:
            return False, f"Domain with ID {domain_id} not found"
        except Exception as e:
            logger.error(f"Error updating domain info: {e}")
            return False, str(e)


class TargetImportService:
    """
    Service for importing targets from various sources
    """
    
    @staticmethod
    def import_from_text(
        text_content: str,
        project,
        description: str = None
    ) -> Tuple[int, List[str]]:
        """
        Import targets from text content
        
        Args:
            text_content: Text content with one target per line
            project: Project object
            description: Optional description for all targets
            
        Returns:
            Tuple of (imported_count, error_messages)
        """
        imported_count = 0
        errors = []
        
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        
        for line in lines:
            try:
                domain, created = DomainService.create_domain(
                    name=line,
                    project=project,
                    description=description
                )
                if created:
                    imported_count += 1
            except Exception as e:
                errors.append(f"{line}: {str(e)}")
        
        return imported_count, errors
    
    @staticmethod
    def import_from_csv(
        csv_content: str,
        project
    ) -> Tuple[int, List[str]]:
        """
        Import targets from CSV content
        Expected format: domain,description,organization
        
        Args:
            csv_content: CSV content
            project: Project object
            
        Returns:
            Tuple of (imported_count, error_messages)
        """
        import csv
        import io
        
        imported_count = 0
        errors = []
        
        io_string = io.StringIO(csv_content)
        reader = csv.reader(io_string, delimiter=',')
        
        for row in reader:
            if not row:
                continue
            
            try:
                domain_name = row[0].strip()
                description = row[1].strip() if len(row) > 1 else None
                organization_name = row[2].strip() if len(row) > 2 else None
                
                # Create domain
                domain, created = DomainService.create_domain(
                    name=domain_name,
                    project=project,
                    description=description
                )
                
                if created:
                    imported_count += 1
                    
                    # Add to organization if specified
                    if organization_name:
                        org, _ = OrganizationService.create_organization(
                            name=organization_name,
                            project=project
                        )
                        org.domains.add(domain)
                
            except Exception as e:
                errors.append(f"Row {reader.line_num}: {str(e)}")
        
        return imported_count, errors
