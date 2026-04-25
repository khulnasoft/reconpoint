"""
Comparison Scans & Change Tracking for security posture evolution.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from django.db.models import Count
from django.utils import timezone

from reconPoint.utilities.logger import get_module_logger
from startScan.models import (
    EndPoint,
    ScanHistory,
    Subdomain,
    Technology,
    Vulnerability,
)


PREFIX_DIFF = "[SCAN_DIFF]"
logger = get_module_logger(__name__)


@dataclass
class DiffResult:
    """Result of comparing two scan states."""

    added: List[Dict[str, Any]]
    removed: List[Dict[str, Any]]
    changed: List[Dict[str, Any]]
    stats: Dict[str, Any]


@dataclass
class ChangeEvent:
    """A detected change event."""

    change_type: str
    entity_type: str
    entity_id: int
    entity_name: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    severity: Optional[str] = None
    timestamp: Optional[datetime] = None


class ScanDiffer:
    """
    Compares two scan states and reports changes.
    """

    def __init__(self, old_scan: ScanHistory, new_scan: ScanHistory):
        self.old_scan = old_scan
        self.new_scan = new_scan

    def diff_subdomains(self) -> DiffResult:
        """Compare subdomains between two scans."""
        old_subdomains = {s.name: s for s in Subdomain.objects.filter(scan_history=self.old_scan)}
        new_subdomains = {s.name: s for s in Subdomain.objects.filter(scan_history=self.new_scan)}

        added = []
        removed = []
        changed = []

        for name, subdomain in new_subdomains.items():
            if name not in old_subdomains:
                added.append(self._subdomain_to_dict(subdomain, is_new=True))
            else:
                old_sub = old_subdomains[name]
                changes = self._check_subdomain_changes(old_sub, subdomain)
                if changes:
                    changed.append(
                        {
                            "name": name,
                            "id": subdomain.id,
                            "changes": changes,
                        }
                    )

        for name, subdomain in old_subdomains.items():
            if name not in new_subdomains:
                removed.append(self._subdomain_to_dict(subdomain, is_new=False))

        return DiffResult(
            added=added,
            removed=removed,
            changed=changed,
            stats=self._compute_diff_stats(added, removed, changed),
        )

    def diff_endpoints(self) -> DiffResult:
        """Compare endpoints between two scans."""
        old_endpoints = {e.http_url: e for e in EndPoint.objects.filter(scan_history=self.old_scan)}
        new_endpoints = {e.http_url: e for e in EndPoint.objects.filter(scan_history=self.new_scan)}

        added = []
        removed = []
        changed = []

        for url, endpoint in new_endpoints.items():
            if url not in old_endpoints:
                added.append(self._endpoint_to_dict(endpoint, is_new=True))
            else:
                old_ep = old_endpoints[url]
                changes = self._check_endpoint_changes(old_ep, endpoint)
                if changes:
                    changed.append(
                        {
                            "url": url,
                            "id": endpoint.id,
                            "changes": changes,
                        }
                    )

        for url, endpoint in old_endpoints.items():
            if url not in new_endpoints:
                removed.append(self._endpoint_to_dict(endpoint, is_new=False))

        return DiffResult(
            added=added,
            removed=removed,
            changed=changed,
            stats=self._compute_diff_stats(added, removed, changed),
        )

    def diff_vulnerabilities(self) -> DiffResult:
        """Compare vulnerabilities between two scans."""
        old_vulns = {(v.name, v.severity): v for v in Vulnerability.objects.filter(scan_history=self.old_scan)}
        new_vulns = {(v.name, v.severity): v for v in Vulnerability.objects.filter(scan_history=self.new_scan)}

        added = []
        removed = []
        changed = []

        for key, vuln in new_vulns.items():
            if key not in old_vulns:
                added.append(self._vuln_to_dict(vuln, is_new=True))
            else:
                old_v = old_vulns[key]
                changes = self._check_vuln_changes(old_v, vuln)
                if changes:
                    changed.append(
                        {
                            "name": vuln.name,
                            "severity": vuln.severity,
                            "id": vuln.id,
                            "changes": changes,
                        }
                    )

        for key, vuln in old_vulns.items():
            if key not in new_vulns:
                removed.append(self._vuln_to_dict(vuln, is_new=False))

        return DiffResult(
            added=added,
            removed=removed,
            changed=changed,
            stats=self._compute_diff_stats(added, removed, changed),
        )

    def diff_technologies(self) -> DiffResult:
        """Compare technologies between two scans."""
        old_techs = {t.name: t for t in Technology.objects.filter(scan_history=self.old_scan)}
        new_techs = {t.name: t for t in Technology.objects.filter(scan_history=self.new_scan)}

        added_names = set(new_techs.keys()) - set(old_techs.keys())
        removed_names = set(old_techs.keys()) - set(new_techs.keys())

        added = [{"name": name, "version": new_techs[name].version} for name in added_names]
        removed = [{"name": name, "version": old_techs[name].version} for name in removed_names]

        return DiffResult(
            added=added,
            removed=removed,
            changed=[],
            stats={"added": len(added), "removed": len(removed), "total_changes": len(added) + len(removed)},
        )

    def _subdomain_to_dict(self, subdomain: Subdomain, is_new: bool) -> Dict:
        return {
            "id": subdomain.id,
            "name": subdomain.name,
            "is_new": is_new,
            "content_type": subdomain.content_type,
            "http_status": subdomain.http_status,
            "page_title": subdomain.page_title,
            "web_server": subdomain.web_server,
        }

    def _endpoint_to_dict(self, endpoint: EndPoint, is_new: bool) -> Dict:
        return {
            "id": endpoint.id,
            "url": endpoint.http_url,
            "is_new": is_new,
            "status_code": endpoint.status_code,
            "content_type": endpoint.content_type,
            "content_length": endpoint.content_length,
        }

    def _vuln_to_dict(self, vuln: Vulnerability, is_new: bool) -> Dict:
        return {
            "id": vuln.id,
            "name": vuln.name,
            "severity": vuln.severity,
            "is_new": is_new,
            "cvss_score": float(vuln.cvss_score) if vuln.cvss_score else None,
            "template": vuln.template,
        }

    def _check_subdomain_changes(self, old: Subdomain, new: Subdomain) -> List[Dict]:
        changes = []

        if old.http_status != new.http_status:
            changes.append(
                {
                    "field": "http_status",
                    "old": old.http_status,
                    "new": new.http_status,
                    "severity": "high" if new.http_status == 200 else "low",
                }
            )

        if old.page_title != new.page_title:
            changes.append(
                {
                    "field": "page_title",
                    "old": old.page_title,
                    "new": new.page_title,
                    "severity": "medium",
                }
            )

        if old.web_server != new.web_server:
            changes.append(
                {
                    "field": "web_server",
                    "old": old.web_server,
                    "new": new.web_server,
                    "severity": "high",
                }
            )

        return changes

    def _check_endpoint_changes(self, old: EndPoint, new: EndPoint) -> List[Dict]:
        changes = []

        if old.status_code != new.status_code:
            changes.append(
                {
                    "field": "status_code",
                    "old": old.status_code,
                    "new": new.status_code,
                    "severity": "high",
                }
            )

        if old.content_length != new.content_length:
            changes.append(
                {
                    "field": "content_length",
                    "old": old.content_length,
                    "new": new.content_length,
                    "severity": "medium",
                }
            )

        return changes

    def _check_vuln_changes(self, old: Vulnerability, new: Vulnerability) -> List[Dict]:
        changes = []

        if old.open_status != new.open_status:
            changes.append(
                {
                    "field": "status",
                    "old": "open" if old.open_status else "closed",
                    "new": "open" if new.open_status else "closed",
                    "severity": "high",
                }
            )

        return changes

    def _compute_diff_stats(
        self,
        added: List,
        removed: List,
        changed: List,
    ) -> Dict[str, Any]:
        return {
            "added_count": len(added),
            "removed_count": len(removed),
            "changed_count": len(changed),
            "total_changes": len(added) + len(removed) + len(changed),
        }


class SecurityPostureTracker:
    """
    Tracks security posture over time with trend analysis.
    """

    def __init__(self, target_id: int):
        self.target_id = target_id

    def get_posture_history(
        self,
        days: int = 90,
    ) -> List[Dict[str, Any]]:
        """Get security posture history for trend analysis."""
        from datetime import timedelta

        cutoff = timezone.now() - timedelta(days=days)
        scans = (
            ScanHistory.objects.filter(
                target_id=self.target_id,
                scan_status=2,
                start_scan_date__gte=cutoff,
            )
            .order_by("start_scan_date")
            .select_related("scan_type")
        )

        history = []
        for scan in scans:
            vuln_counts = self._get_vulnerability_counts(scan)
            history.append(
                {
                    "scan_id": scan.id,
                    "date": scan.start_scan_date,
                    "total_vulnerabilities": sum(vuln_counts.values()),
                    "critical": vuln_counts.get("critical", 0),
                    "high": vuln_counts.get("high", 0),
                    "medium": vuln_counts.get("medium", 0),
                    "low": vuln_counts.get("low", 0),
                    "info": vuln_counts.get("info", 0),
                    "subdomain_count": Subdomain.objects.filter(scan_history=scan).count(),
                    "endpoint_count": EndPoint.objects.filter(scan_history=scan).count(),
                }
            )

        return history

    def calculate_posture_score(self, scan: ScanHistory) -> float:
        """Calculate overall security posture score (0-100)."""
        vuln_counts = self._get_vulnerability_counts(scan)

        weights = {
            "critical": 40,
            "high": 25,
            "medium": 15,
            "low": 5,
            "info": 0,
        }

        penalty = sum(vuln_counts.get(severity, 0) * weight for severity, weight in weights.items())

        score = max(0, 100 - penalty)

        if vuln_counts.get("critical", 0) > 0:
            score = min(score, 50)
        elif vuln_counts.get("high", 0) > 0:
            score = min(score, 70)

        return round(score, 1)

    def detect_suspicious_changes(
        self,
        old_scan: ScanHistory,
        new_scan: ScanHistory,
    ) -> List[ChangeEvent]:
        """Detect suspicious changes that may indicate security issues."""
        events = []

        diff = ScanDiffer(old_scan, new_scan)

        vuln_diff = diff.diff_vulnerabilities()
        for vuln in vuln_diff.added:
            if vuln.get("severity") in ["critical", "high"]:
                events.append(
                    ChangeEvent(
                        change_type="new_high_severity_vuln",
                        entity_type="vulnerability",
                        entity_id=vuln.get("id"),
                        entity_name=vuln.get("name"),
                        severity="high",
                    )
                )

        tech_diff = diff.diff_technologies()
        for tech in tech_diff.removed:
            events.append(
                ChangeEvent(
                    change_type="technology_removed",
                    entity_type="technology",
                    entity_id=0,
                    entity_name=tech.get("name"),
                    severity="medium",
                )
            )

        subdomain_diff = diff.diff_subdomains()
        for sub in subdomain_diff.removed:
            if "admin" in sub.get("name", "").lower() or "console" in sub.get("name", "").lower():
                events.append(
                    ChangeEvent(
                        change_type="admin_panel_removed",
                        entity_type="subdomain",
                        entity_id=sub.get("id"),
                        entity_name=sub.get("name"),
                        severity="medium",
                    )
                )

        return events

    def _get_vulnerability_counts(self, scan: ScanHistory) -> Dict[str, int]:
        """Get vulnerability counts by severity for a scan."""
        vulns = Vulnerability.objects.filter(scan_history=scan)
        counts = {}

        severity_map = {
            4: "critical",
            3: "high",
            2: "medium",
            1: "low",
            0: "info",
        }

        for severity_label, count in vulns.values("severity").annotate(count=Count("id")):
            key = severity_map.get(severity_label, "unknown")
            counts[key] = count

        return counts


class ScanComparisonReport:
    """
    Generates comparison reports between scans.
    """

    def __init__(self, old_scan: ScanHistory, new_scan: ScanHistory):
        self.old_scan = old_scan
        self.new_scan = new_scan
        self.differ = ScanDiffer(old_scan, new_scan)

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive comparison report."""
        subdomain_diff = self.differ.diff_subdomains()
        endpoint_diff = self.differ.diff_endpoints()
        vuln_diff = self.differ.diff_vulnerabilities()
        tech_diff = self.differ.diff_technologies()

        old_tracker = SecurityPostureTracker(self.old_scan.target_id)
        new_tracker = SecurityPostureTracker(self.new_scan.target_id)

        old_score = old_tracker.calculate_posture_score(self.old_scan)
        new_score = new_tracker.calculate_posture_score(self.new_scan)

        suspicious_changes = new_tracker.detect_suspicious_changes(self.old_scan, self.new_scan)

        return {
            "scan_info": {
                "old_scan": {
                    "id": self.old_scan.id,
                    "date": self.old_scan.start_scan_date,
                    "status": self.old_scan.scan_status,
                },
                "new_scan": {
                    "id": self.new_scan.id,
                    "date": self.new_scan.start_scan_date,
                    "status": self.new_scan.scan_status,
                },
            },
            "subdomains": subdomain_diff.stats,
            "endpoints": endpoint_diff.stats,
            "vulnerabilities": vuln_diff.stats,
            "technologies": tech_diff.stats,
            "posture_scores": {
                "old": old_score,
                "new": new_score,
                "change": new_score - old_score,
                "improved": new_score > old_score,
            },
            "suspicious_changes": [
                {
                    "type": c.change_type,
                    "entity": c.entity_name,
                    "severity": c.severity,
                }
                for c in suspicious_changes
            ],
            "change_summary": self._generate_change_summary(subdomain_diff, endpoint_diff, vuln_diff, tech_diff),
        }

    def _generate_change_summary(
        self,
        subdomains: DiffResult,
        endpoints: DiffResult,
        vulns: DiffResult,
        techs: DiffResult,
    ) -> str:
        """Generate human-readable change summary."""
        parts = []

        total_added = subdomains.stats["added_count"] + endpoints.stats["added_count"] + vulns.stats["added_count"]
        total_removed = (
            subdomains.stats["removed_count"] + endpoints.stats["removed_count"] + vulns.stats["removed_count"]
        )

        if total_added > 0:
            parts.append(f"Found {total_added} new items")
        if total_removed > 0:
            parts.append(f"Removed {total_removed} items")

        if vulns.stats["added_count"] > 0:
            parts.append(f"Detected {vulns.stats['added_count']} new vulnerabilities")
        if vulns.stats["removed_count"] > 0:
            parts.append(f"Resolved {vulns.stats['removed_count']} vulnerabilities")

        return ". ".join(parts) if parts else "No significant changes detected."
