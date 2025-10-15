"""
Enhanced model methods for targetApp models
These can be added to the existing models or used as mixins
"""

import logging
from typing import Dict, List, Optional
from django.db import models
from django.db.models import Count, Q, Avg, Max, Min
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class DomainEnhancedMethods:
    """
    Enhanced methods for Domain model
    """
    
    def get_scan_count(self) -> int:
        """Get total number of scans for this domain"""
        from startScan.models import ScanHistory
        return ScanHistory.objects.filter(domain=self).count()
    
    def get_recent_scans(self, limit: int = 5):
        """Get recent scans for this domain"""
        from startScan.models import ScanHistory
        return (
            ScanHistory.objects
            .filter(domain=self)
            .select_related('scan_type', 'initiated_by')
            .order_by('-start_scan_date')
            [:limit]
        )
    
    def get_running_scans(self):
        """Get currently running scans"""
        from startScan.models import ScanHistory
        return ScanHistory.objects.filter(
            domain=self,
            scan_status__in=[0, 1]  # Pending or Running
        )
    
    def has_running_scan(self) -> bool:
        """Check if domain has a running scan"""
        return self.get_running_scans().exists()
    
    def get_last_scan_date(self) -> Optional[timezone.datetime]:
        """Get the date of the last scan"""
        from startScan.models import ScanHistory
        last_scan = (
            ScanHistory.objects
            .filter(domain=self)
            .order_by('-start_scan_date')
            .first()
        )
        return last_scan.start_scan_date if last_scan else None
    
    def get_subdomain_count(self) -> int:
        """Get total number of unique subdomains"""
        from startScan.models import Subdomain
        return (
            Subdomain.objects
            .filter(target_domain=self)
            .values('name')
            .distinct()
            .count()
        )
    
    def get_alive_subdomain_count(self) -> int:
        """Get number of alive subdomains"""
        from startScan.models import Subdomain
        return (
            Subdomain.objects
            .filter(target_domain=self, http_status=200)
            .values('name')
            .distinct()
            .count()
        )
    
    def get_endpoint_count(self) -> int:
        """Get total number of unique endpoints"""
        from startScan.models import EndPoint
        return (
            EndPoint.objects
            .filter(target_domain=self)
            .values('http_url')
            .distinct()
            .count()
        )
    
    def get_vulnerability_count(self) -> int:
        """Get total number of vulnerabilities"""
        from startScan.models import Vulnerability
        return Vulnerability.objects.filter(target_domain=self).count()
    
    def get_vulnerability_counts_by_severity(self) -> Dict[str, int]:
        """Get vulnerability counts grouped by severity"""
        from startScan.models import Vulnerability
        
        cache_key = f'domain_vuln_counts_{self.id}'
        cached_counts = cache.get(cache_key)
        
        if cached_counts:
            return cached_counts
        
        counts = Vulnerability.objects.filter(target_domain=self).aggregate(
            total=Count('id'),
            critical=Count('id', filter=Q(severity=4)),
            high=Count('id', filter=Q(severity=3)),
            medium=Count('id', filter=Q(severity=2)),
            low=Count('id', filter=Q(severity=1)),
            info=Count('id', filter=Q(severity=0)),
            unknown=Count('id', filter=Q(severity=-1)),
        )
        
        # Cache for 5 minutes
        cache.set(cache_key, counts, 300)
        return counts
    
    def get_risk_score(self) -> int:
        """
        Calculate risk score based on vulnerabilities
        Returns score from 0-100
        """
        vuln_counts = self.get_vulnerability_counts_by_severity()
        
        score = (
            vuln_counts['critical'] * 40 +
            vuln_counts['high'] * 20 +
            vuln_counts['medium'] * 10 +
            vuln_counts['low'] * 5
        )
        
        return min(score, 100)  # Cap at 100
    
    def get_risk_level(self) -> str:
        """Get risk level based on risk score"""
        score = self.get_risk_score()
        
        if score >= 80:
            return "🔴 Critical"
        elif score >= 60:
            return "🟠 High"
        elif score >= 40:
            return "🟡 Medium"
        elif score >= 20:
            return "🟢 Low"
        else:
            return "⚪ Minimal"
    
    def get_domain_summary(self) -> Dict:
        """Get comprehensive domain summary"""
        vuln_counts = self.get_vulnerability_counts_by_severity()
        
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'project': self.project.name if self.project else None,
            'insert_date': self.insert_date,
            'last_scan_date': self.get_last_scan_date(),
            'has_running_scan': self.has_running_scan(),
            'scan_count': self.get_scan_count(),
            'subdomain_count': self.get_subdomain_count(),
            'alive_subdomain_count': self.get_alive_subdomain_count(),
            'endpoint_count': self.get_endpoint_count(),
            'vulnerability_count': self.get_vulnerability_count(),
            'vulnerability_counts': vuln_counts,
            'risk_score': self.get_risk_score(),
            'risk_level': self.get_risk_level(),
        }
    
    def is_ip_address(self) -> bool:
        """Check if this domain is actually an IP address"""
        return self.ip_address_cidr is not None
    
    def get_organizations(self):
        """Get organizations this domain belongs to"""
        from .models import Organization
        return Organization.objects.filter(domains=self)
    
    def get_whois_info(self) -> Optional[Dict]:
        """Get WHOIS information if available"""
        if not self.domain_info:
            return None
        
        info = self.domain_info
        return {
            'dnssec': info.dnssec,
            'created': info.created,
            'updated': info.updated,
            'expires': info.expires,
            'registrar': info.registrar.name if info.registrar else None,
            'whois_server': info.whois_server,
        }
    
    def days_until_expiry(self) -> Optional[int]:
        """Get number of days until domain expires"""
        if not self.domain_info or not self.domain_info.expires:
            return None
        
        delta = self.domain_info.expires - timezone.now()
        return delta.days
    
    def is_expiring_soon(self, days: int = 30) -> bool:
        """Check if domain is expiring within specified days"""
        days_left = self.days_until_expiry()
        return days_left is not None and days_left <= days
    
    def invalidate_cache(self):
        """Invalidate all cached data for this domain"""
        cache_keys = [
            f'domain_vuln_counts_{self.id}',
            f'domain_stats_{self.id}',
        ]
        for key in cache_keys:
            cache.delete(key)


class OrganizationEnhancedMethods:
    """
    Enhanced methods for Organization model
    """
    
    def get_domain_count(self) -> int:
        """Get number of domains in this organization"""
        return self.domains.count()
    
    def get_total_subdomain_count(self) -> int:
        """Get total subdomains across all domains"""
        from startScan.models import Subdomain
        domain_ids = self.domains.values_list('id', flat=True)
        return (
            Subdomain.objects
            .filter(target_domain_id__in=domain_ids)
            .values('name')
            .distinct()
            .count()
        )
    
    def get_total_vulnerability_count(self) -> int:
        """Get total vulnerabilities across all domains"""
        from startScan.models import Vulnerability
        domain_ids = self.domains.values_list('id', flat=True)
        return Vulnerability.objects.filter(target_domain_id__in=domain_ids).count()
    
    def get_vulnerability_counts_by_severity(self) -> Dict[str, int]:
        """Get vulnerability counts grouped by severity"""
        from startScan.models import Vulnerability
        
        domain_ids = self.domains.values_list('id', flat=True)
        
        counts = Vulnerability.objects.filter(target_domain_id__in=domain_ids).aggregate(
            total=Count('id'),
            critical=Count('id', filter=Q(severity=4)),
            high=Count('id', filter=Q(severity=3)),
            medium=Count('id', filter=Q(severity=2)),
            low=Count('id', filter=Q(severity=1)),
            info=Count('id', filter=Q(severity=0)),
        )
        
        return counts
    
    def get_total_scan_count(self) -> int:
        """Get total number of scans across all domains"""
        from startScan.models import ScanHistory
        domain_ids = self.domains.values_list('id', flat=True)
        return ScanHistory.objects.filter(domain_id__in=domain_ids).count()
    
    def get_running_scan_count(self) -> int:
        """Get number of currently running scans"""
        from startScan.models import ScanHistory
        domain_ids = self.domains.values_list('id', flat=True)
        return ScanHistory.objects.filter(
            domain_id__in=domain_ids,
            scan_status__in=[0, 1]
        ).count()
    
    def get_risk_score(self) -> int:
        """Calculate organization risk score"""
        vuln_counts = self.get_vulnerability_counts_by_severity()
        
        score = (
            vuln_counts['critical'] * 40 +
            vuln_counts['high'] * 20 +
            vuln_counts['medium'] * 10 +
            vuln_counts['low'] * 5
        )
        
        # Normalize by number of domains
        domain_count = self.get_domain_count()
        if domain_count > 0:
            score = score / domain_count
        
        return min(int(score), 100)
    
    def get_risk_level(self) -> str:
        """Get risk level based on risk score"""
        score = self.get_risk_score()
        
        if score >= 80:
            return "🔴 Critical"
        elif score >= 60:
            return "🟠 High"
        elif score >= 40:
            return "🟡 Medium"
        elif score >= 20:
            return "🟢 Low"
        else:
            return "⚪ Minimal"
    
    def get_organization_summary(self) -> Dict:
        """Get comprehensive organization summary"""
        vuln_counts = self.get_vulnerability_counts_by_severity()
        
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'project': self.project.name if self.project else None,
            'insert_date': self.insert_date,
            'domain_count': self.get_domain_count(),
            'subdomain_count': self.get_total_subdomain_count(),
            'vulnerability_count': self.get_total_vulnerability_count(),
            'vulnerability_counts': vuln_counts,
            'scan_count': self.get_total_scan_count(),
            'running_scan_count': self.get_running_scan_count(),
            'risk_score': self.get_risk_score(),
            'risk_level': self.get_risk_level(),
        }
    
    def get_top_vulnerable_domains(self, limit: int = 5):
        """Get domains with most vulnerabilities"""
        from startScan.models import Vulnerability
        
        domain_ids = self.domains.values_list('id', flat=True)
        
        top_domains = (
            Vulnerability.objects
            .filter(target_domain_id__in=domain_ids)
            .values('target_domain__id', 'target_domain__name')
            .annotate(vuln_count=Count('id'))
            .order_by('-vuln_count')
            [:limit]
        )
        
        return list(top_domains)


class DomainInfoEnhancedMethods:
    """
    Enhanced methods for DomainInfo model
    """
    
    def is_dnssec_enabled(self) -> bool:
        """Check if DNSSEC is enabled"""
        return self.dnssec
    
    def get_age_in_days(self) -> Optional[int]:
        """Get domain age in days"""
        if not self.created:
            return None
        
        delta = timezone.now() - self.created
        return delta.days
    
    def get_days_since_update(self) -> Optional[int]:
        """Get days since last update"""
        if not self.updated:
            return None
        
        delta = timezone.now() - self.updated
        return delta.days
    
    def get_days_until_expiry(self) -> Optional[int]:
        """Get days until expiry"""
        if not self.expires:
            return None
        
        delta = self.expires - timezone.now()
        return delta.days
    
    def is_expired(self) -> bool:
        """Check if domain is expired"""
        days_left = self.get_days_until_expiry()
        return days_left is not None and days_left < 0
    
    def is_expiring_soon(self, days: int = 30) -> bool:
        """Check if domain is expiring within specified days"""
        days_left = self.get_days_until_expiry()
        return days_left is not None and 0 <= days_left <= days
    
    def get_name_server_list(self) -> List[str]:
        """Get list of name servers"""
        return [ns.name for ns in self.name_servers.all()]
    
    def get_dns_record_list(self) -> List[Dict]:
        """Get list of DNS records"""
        return [
            {'name': record.name, 'type': record.type}
            for record in self.dns_records.all()
        ]
    
    def get_status_list(self) -> List[str]:
        """Get list of WHOIS statuses"""
        return [status.name for status in self.status.all()]
    
    def get_related_domain_list(self) -> List[str]:
        """Get list of related domains"""
        return [domain.name for domain in self.related_domains.all()]
    
    def get_info_summary(self) -> Dict:
        """Get comprehensive domain info summary"""
        return {
            'dnssec': self.dnssec,
            'created': self.created,
            'updated': self.updated,
            'expires': self.expires,
            'age_days': self.get_age_in_days(),
            'days_until_expiry': self.get_days_until_expiry(),
            'is_expired': self.is_expired(),
            'is_expiring_soon': self.is_expiring_soon(),
            'registrar': self.registrar.name if self.registrar else None,
            'whois_server': self.whois_server,
            'name_servers': self.get_name_server_list(),
            'dns_records': self.get_dns_record_list(),
            'statuses': self.get_status_list(),
        }


# Manager classes for custom querysets

class DomainManager(models.Manager):
    """Custom manager for Domain"""
    
    def with_running_scans(self):
        """Get domains with running scans"""
        from startScan.models import ScanHistory
        return self.filter(
            id__in=ScanHistory.objects.filter(
                scan_status__in=[0, 1]
            ).values_list('domain_id', flat=True)
        )
    
    def with_vulnerabilities(self):
        """Get domains with vulnerabilities"""
        from startScan.models import Vulnerability
        return self.filter(
            id__in=Vulnerability.objects.values_list('target_domain_id', flat=True).distinct()
        )
    
    def with_critical_vulnerabilities(self):
        """Get domains with critical vulnerabilities"""
        from startScan.models import Vulnerability
        return self.filter(
            id__in=Vulnerability.objects.filter(
                severity=4
            ).values_list('target_domain_id', flat=True).distinct()
        )
    
    def expiring_soon(self, days: int = 30):
        """Get domains expiring within specified days"""
        cutoff_date = timezone.now() + timezone.timedelta(days=days)
        return self.filter(
            domain_info__expires__lte=cutoff_date,
            domain_info__expires__gte=timezone.now()
        )
    
    def recent(self, days: int = 7):
        """Get recently added domains"""
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        return self.filter(insert_date__gte=cutoff_date)
    
    def optimized_list(self):
        """Get optimized queryset for list views"""
        return self.select_related('project', 'domain_info').prefetch_related(
            'scanhistory_set'
        )


class OrganizationManager(models.Manager):
    """Custom manager for Organization"""
    
    def with_domains(self):
        """Get organizations with at least one domain"""
        return self.annotate(domain_count=Count('domains')).filter(domain_count__gt=0)
    
    def with_vulnerabilities(self):
        """Get organizations with vulnerabilities"""
        from startScan.models import Vulnerability
        domain_ids = Vulnerability.objects.values_list('target_domain_id', flat=True).distinct()
        return self.filter(domains__id__in=domain_ids).distinct()
    
    def recent(self, days: int = 7):
        """Get recently added organizations"""
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        return self.filter(insert_date__gte=cutoff_date)
    
    def optimized_list(self):
        """Get optimized queryset for list views"""
        return self.select_related('project').prefetch_related('domains')
