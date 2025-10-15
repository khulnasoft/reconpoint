"""
Enhanced model methods for startScan models
These can be added to the existing models or used as mixins
"""

import logging
from typing import Dict, List, Optional
from django.db import models
from django.db.models import Count, Q, Avg, Max, Min
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class ScanHistoryEnhancedMethods:
    """
    Enhanced methods for ScanHistory model
    Add these methods to the ScanHistory model class
    """
    
    def get_vulnerability_counts_optimized(self) -> Dict[str, int]:
        """
        Get all vulnerability counts in a single query
        More efficient than calling individual count methods
        """
        from targetApp.models import Vulnerability
        
        cache_key = f'vuln_counts_{self.id}'
        cached_counts = cache.get(cache_key)
        
        if cached_counts:
            return cached_counts
        
        counts = Vulnerability.objects.filter(scan_history=self).aggregate(
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
    
    def get_scan_duration(self) -> Optional[int]:
        """
        Get scan duration in seconds
        Returns None if scan is still running
        """
        if self.stop_scan_date:
            return (self.stop_scan_date - self.start_scan_date).total_seconds()
        return None
    
    def get_scan_duration_formatted(self) -> str:
        """
        Get formatted scan duration (e.g., "2h 30m 15s")
        """
        duration = self.get_scan_duration()
        if duration is None:
            return "In progress"
        
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}s")
        
        return " ".join(parts)
    
    def is_running(self) -> bool:
        """Check if scan is currently running"""
        return self.scan_status in [0, 1]  # Pending or Running
    
    def is_completed(self) -> bool:
        """Check if scan is completed"""
        return self.scan_status == 2
    
    def is_failed(self) -> bool:
        """Check if scan failed"""
        return self.scan_status == 3
    
    def is_aborted(self) -> bool:
        """Check if scan was aborted"""
        return self.scan_status == 4
    
    def get_status_display_with_icon(self) -> str:
        """Get status display with emoji icon"""
        status_icons = {
            -1: "⏳ Pending",
            0: "⏳ Pending",
            1: "🔄 Running",
            2: "✅ Completed",
            3: "❌ Failed",
            4: "🛑 Aborted",
        }
        return status_icons.get(self.scan_status, "❓ Unknown")
    
    def get_scan_efficiency_score(self) -> Optional[float]:
        """
        Calculate scan efficiency score based on:
        - Vulnerabilities found per minute
        - Subdomains discovered per minute
        - Endpoints found per minute
        """
        duration = self.get_scan_duration()
        if not duration or duration == 0:
            return None
        
        duration_minutes = duration / 60
        
        vuln_count = self.get_vulnerability_count()
        subdomain_count = self.get_subdomain_count()
        endpoint_count = self.get_endpoint_count()
        
        # Weighted score
        score = (
            (vuln_count * 10) +  # Vulnerabilities are most valuable
            (subdomain_count * 2) +
            (endpoint_count * 1)
        ) / duration_minutes
        
        return round(score, 2)
    
    def get_scan_summary(self) -> Dict:
        """
        Get comprehensive scan summary
        """
        vuln_counts = self.get_vulnerability_counts_optimized()
        
        return {
            'scan_id': self.id,
            'domain': self.domain.name,
            'scan_type': self.scan_type.engine_name,
            'status': self.get_status_display_with_icon(),
            'started': self.start_scan_date,
            'completed': self.stop_scan_date,
            'duration': self.get_scan_duration_formatted(),
            'initiated_by': self.initiated_by.username if self.initiated_by else 'System',
            'counts': {
                'subdomains': self.get_subdomain_count(),
                'endpoints': self.get_endpoint_count(),
                'vulnerabilities': vuln_counts,
            },
            'efficiency_score': self.get_scan_efficiency_score(),
        }
    
    def get_previous_scan(self):
        """Get the previous scan for this domain"""
        return (
            ScanHistory.objects
            .filter(domain=self.domain, start_scan_date__lt=self.start_scan_date)
            .order_by('-start_scan_date')
            .first()
        )
    
    def get_next_scan(self):
        """Get the next scan for this domain"""
        return (
            ScanHistory.objects
            .filter(domain=self.domain, start_scan_date__gt=self.start_scan_date)
            .order_by('start_scan_date')
            .first()
        )
    
    def get_comparison_with_previous(self) -> Optional[Dict]:
        """
        Compare this scan with the previous scan
        """
        previous = self.get_previous_scan()
        if not previous:
            return None
        
        current_vulns = self.get_vulnerability_counts_optimized()
        previous_vulns = previous.get_vulnerability_counts_optimized()
        
        return {
            'subdomains': {
                'current': self.get_subdomain_count(),
                'previous': previous.get_subdomain_count(),
                'change': self.get_subdomain_count() - previous.get_subdomain_count(),
            },
            'endpoints': {
                'current': self.get_endpoint_count(),
                'previous': previous.get_endpoint_count(),
                'change': self.get_endpoint_count() - previous.get_endpoint_count(),
            },
            'vulnerabilities': {
                'current': current_vulns['total'],
                'previous': previous_vulns['total'],
                'change': current_vulns['total'] - previous_vulns['total'],
                'by_severity': {
                    'critical': current_vulns['critical'] - previous_vulns['critical'],
                    'high': current_vulns['high'] - previous_vulns['high'],
                    'medium': current_vulns['medium'] - previous_vulns['medium'],
                    'low': current_vulns['low'] - previous_vulns['low'],
                }
            }
        }
    
    def invalidate_cache(self):
        """Invalidate all cached data for this scan"""
        cache_keys = [
            f'vuln_counts_{self.id}',
            f'scan_stats_{self.id}',
            f'subdomain_stats_{self.id}',
        ]
        for key in cache_keys:
            cache.delete(key)


class SubdomainEnhancedMethods:
    """
    Enhanced methods for Subdomain model
    """
    
    def is_alive(self) -> bool:
        """
        Check if subdomain is alive
        More comprehensive than just checking http_status == 200
        """
        return self.http_status in [200, 201, 202, 203, 204, 301, 302, 307, 308]
    
    def get_risk_score(self) -> int:
        """
        Calculate risk score based on vulnerabilities
        Returns score from 0-100
        """
        vuln_counts = self.get_vulnerabilities.aggregate(
            critical=Count('id', filter=Q(severity=4)),
            high=Count('id', filter=Q(severity=3)),
            medium=Count('id', filter=Q(severity=2)),
            low=Count('id', filter=Q(severity=1)),
        )
        
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
    
    def get_technology_stack(self) -> List[str]:
        """Get list of detected technologies"""
        return [tech.name for tech in self.technologies.all()]
    
    def get_ip_addresses_list(self) -> List[str]:
        """Get list of IP addresses"""
        return [ip.address for ip in self.ip_addresses.all()]
    
    def has_waf(self) -> bool:
        """Check if subdomain has WAF protection"""
        return self.waf.exists()
    
    def get_waf_names(self) -> List[str]:
        """Get list of detected WAFs"""
        return [waf.name for waf in self.waf.all()]
    
    def get_subdomain_info(self) -> Dict:
        """Get comprehensive subdomain information"""
        return {
            'name': self.name,
            'http_url': self.http_url,
            'status': self.http_status,
            'is_alive': self.is_alive(),
            'is_important': self.is_important,
            'is_cdn': self.is_cdn,
            'cdn_name': self.cdn_name,
            'webserver': self.webserver,
            'content_type': self.content_type,
            'content_length': self.content_length,
            'response_time': self.response_time,
            'page_title': self.page_title,
            'technologies': self.get_technology_stack(),
            'ip_addresses': self.get_ip_addresses_list(),
            'has_waf': self.has_waf(),
            'waf_names': self.get_waf_names(),
            'risk_score': self.get_risk_score(),
            'risk_level': self.get_risk_level(),
            'vulnerability_count': self.get_total_vulnerability_count,
            'endpoint_count': self.get_endpoint_count,
        }


class VulnerabilityEnhancedMethods:
    """
    Enhanced methods for Vulnerability model
    """
    
    def get_severity_color(self) -> str:
        """Get color code for severity"""
        colors = {
            4: '#dc3545',  # Critical - Red
            3: '#fd7e14',  # High - Orange
            2: '#ffc107',  # Medium - Yellow
            1: '#17a2b8',  # Low - Blue
            0: '#6c757d',  # Info - Gray
            -1: '#6c757d',  # Unknown - Gray
        }
        return colors.get(self.severity, '#6c757d')
    
    def get_severity_icon(self) -> str:
        """Get emoji icon for severity"""
        icons = {
            4: '🔴',  # Critical
            3: '🟠',  # High
            2: '🟡',  # Medium
            1: '🔵',  # Low
            0: '⚪',  # Info
            -1: '❓',  # Unknown
        }
        return icons.get(self.severity, '❓')
    
    def get_cvss_score_range(self) -> Optional[str]:
        """Get CVSS score range based on severity"""
        ranges = {
            4: '9.0-10.0',  # Critical
            3: '7.0-8.9',   # High
            2: '4.0-6.9',   # Medium
            1: '0.1-3.9',   # Low
            0: '0.0',       # Info
            -1: 'N/A',      # Unknown
        }
        return ranges.get(self.severity)
    
    def is_critical(self) -> bool:
        """Check if vulnerability is critical"""
        return self.severity == 4
    
    def is_exploitable(self) -> bool:
        """
        Check if vulnerability is likely exploitable
        Based on severity and other factors
        """
        # Critical and High are generally exploitable
        if self.severity >= 3:
            return True
        
        # Check if there are known exploits (CVEs)
        if hasattr(self, 'cve_ids') and self.cve_ids.exists():
            return True
        
        return False
    
    def get_remediation_priority(self) -> str:
        """Get remediation priority"""
        if self.severity == 4:
            return "🚨 Immediate"
        elif self.severity == 3:
            return "⚠️ Urgent"
        elif self.severity == 2:
            return "📋 Scheduled"
        elif self.severity == 1:
            return "📝 Optional"
        else:
            return "ℹ️ Informational"
    
    def get_vulnerability_summary(self) -> Dict:
        """Get comprehensive vulnerability summary"""
        return {
            'id': self.id,
            'name': self.name,
            'severity': self.get_severity_display(),
            'severity_icon': self.get_severity_icon(),
            'severity_color': self.get_severity_color(),
            'cvss_range': self.get_cvss_score_range(),
            'is_critical': self.is_critical(),
            'is_exploitable': self.is_exploitable(),
            'remediation_priority': self.get_remediation_priority(),
            'subdomain': self.subdomain.name if self.subdomain else None,
            'endpoint': self.endpoint.http_url if hasattr(self, 'endpoint') and self.endpoint else None,
            'discovered_date': self.discovered_date,
        }


# Manager classes for custom querysets

class ScanHistoryManager(models.Manager):
    """Custom manager for ScanHistory"""
    
    def running_scans(self):
        """Get all running scans"""
        return self.filter(scan_status__in=[0, 1])
    
    def completed_scans(self):
        """Get all completed scans"""
        return self.filter(scan_status=2)
    
    def failed_scans(self):
        """Get all failed scans"""
        return self.filter(scan_status=3)
    
    def recent_scans(self, days=7):
        """Get scans from last N days"""
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(start_scan_date__gte=cutoff)
    
    def with_vulnerabilities(self):
        """Get scans that found vulnerabilities"""
        from targetApp.models import Vulnerability
        return self.filter(
            id__in=Vulnerability.objects.values_list('scan_history_id', flat=True).distinct()
        )
    
    def optimized_list(self):
        """Get optimized queryset for list views"""
        return self.select_related(
            'domain',
            'scan_type',
            'initiated_by'
        ).prefetch_related(
            'emails',
            'employees'
        )


class SubdomainManager(models.Manager):
    """Custom manager for Subdomain"""
    
    def alive(self):
        """Get alive subdomains"""
        return self.filter(http_status__in=[200, 201, 202, 203, 204, 301, 302, 307, 308])
    
    def important(self):
        """Get important subdomains"""
        return self.filter(is_important=True)
    
    def with_vulnerabilities(self):
        """Get subdomains with vulnerabilities"""
        from targetApp.models import Vulnerability
        return self.filter(
            name__in=Vulnerability.objects.values_list('subdomain__name', flat=True).distinct()
        )
    
    def with_waf(self):
        """Get subdomains with WAF"""
        return self.filter(waf__isnull=False).distinct()
    
    def cdn_protected(self):
        """Get CDN-protected subdomains"""
        return self.filter(is_cdn=True)
    
    def optimized_list(self):
        """Get optimized queryset for list views"""
        return self.select_related(
            'target_domain',
            'scan_history'
        ).prefetch_related(
            'technologies',
            'ip_addresses',
            'waf'
        )


class VulnerabilityManager(models.Manager):
    """Custom manager for Vulnerability"""
    
    def critical(self):
        """Get critical vulnerabilities"""
        return self.filter(severity=4)
    
    def high(self):
        """Get high severity vulnerabilities"""
        return self.filter(severity=3)
    
    def medium(self):
        """Get medium severity vulnerabilities"""
        return self.filter(severity=2)
    
    def low(self):
        """Get low severity vulnerabilities"""
        return self.filter(severity=1)
    
    def exploitable(self):
        """Get exploitable vulnerabilities"""
        return self.filter(severity__gte=3)
    
    def with_cves(self):
        """Get vulnerabilities with CVEs"""
        return self.filter(cve_ids__isnull=False).distinct()
    
    def recent(self, days=7):
        """Get vulnerabilities from last N days"""
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(discovered_date__gte=cutoff)
    
    def optimized_list(self):
        """Get optimized queryset for list views"""
        return self.select_related(
            'subdomain',
            'scan_history'
        ).prefetch_related(
            'cve_ids',
            'cwe_ids',
            'tags'
        )
