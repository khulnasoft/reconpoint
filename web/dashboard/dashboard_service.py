"""
Dashboard service for data visualization.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict

from django.db.models import Avg, Count, Q
from django.utils import timezone

from reconPoint.utilities.logger import get_module_logger
from startScan.models import (
    EndPoint,
    ScanHistory,
    Subdomain,
    Technology,
    Vulnerability,
)
from startScan.models_threat_intel import ThreatMatch


PREFIX_DASH = "[DASHBOARD]"
logger = get_module_logger(__name__)


@dataclass
class DashboardData:
    """Data container for dashboard widgets."""

    widget_type: str
    data: Dict[str, Any]
    updated_at: datetime


class DashboardDataService:
    """Service for generating dashboard widget data."""

    def __init__(self, target_id: int):
        self.target_id = target_id

    def get_vuln_count(self) -> Dict[str, Any]:
        """Get vulnerability counts by severity."""
        vulns = Vulnerability.objects.filter(scan_history__target_id=self.target_id)
        counts = {"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

        severity_map = {
            "critical": "critical",
            "high": "high",
            "medium": "medium",
            "low": "low",
            "info": "info",
            4: "critical",
            3: "high",
            2: "medium",
            1: "low",
            0: "info",
        }

        for sev, count in vulns.values("severity").annotate(count=Count("id")):
            key = severity_map.get(sev, "total")
            counts[key] = count
            counts["total"] += count

        severity_map_reverse = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
        for severity in ["critical", "high", "medium", "low", "info"]:
            severity_code = severity_map_reverse[severity]
            open_count = vulns.filter(severity=severity_code, open_status=True).count()
            counts[f"{severity}_open"] = open_count
            counts[f"{severity}_resolved"] = counts[severity] - open_count

        return counts

    def get_severity_pie(self) -> Dict[str, Any]:
        """Get severity distribution for pie chart."""
        vulns = Vulnerability.objects.filter(scan_history__target_id=self.target_id)
        data = []

        for severity in ["critical", "high", "medium", "low", "info"]:
            severity_map = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
            count = vulns.filter(severity=severity_map[severity]).count()
            if count > 0:
                data.append({"name": severity.capitalize(), "value": count})

        return {"series": data}

    def get_timeline(self, days: int = 30) -> Dict[str, Any]:
        """Get vulnerability trend over time."""
        cutoff = timezone.now() - timedelta(days=days)
        scans = ScanHistory.objects.filter(
            target_id=self.target_id,
            start_scan_date__gte=cutoff,
            scan_status=2,
        ).order_by("start_scan_date")

        timeline = []
        for scan in scans:
            vulns = Vulnerability.objects.filter(scan_history=scan)
            critical = vulns.filter(severity=4).count()
            high = vulns.filter(severity=3).count()
            medium = vulns.filter(severity=2).count()
            low = vulns.filter(severity=1).count()
            info = vulns.filter(severity=0).count()

            timeline.append(
                {
                    "date": scan.start_scan_date.isoformat(),
                    "critical": critical,
                    "high": high,
                    "medium": medium,
                    "low": low,
                    "info": info,
                    "total": critical + high + medium + low + info,
                }
            )

        return {"timeline": timeline, "days": days}

    def get_top_targets(self, limit: int = 10) -> Dict[str, Any]:
        """Get most vulnerable targets."""
        targets = (
            Vulnerability.objects.filter(
                scan_history__target_id=self.target_id,
            )
            .values("endpoint", "template")
            .annotate(vuln_count=Count("id"))
            .order_by("-vuln_count")[:limit]
        )

        data = [
            {
                "target": item["endpoint"] or "Unknown",
                "template": item["template"],
                "count": item["vuln_count"],
            }
            for item in targets
        ]

        return {"targets": data, "total": len(data)}

    def get_recent_scans(self, limit: int = 10) -> Dict[str, Any]:
        """Get recent scan history."""
        scans = (
            ScanHistory.objects.filter(
                target_id=self.target_id,
            )
            .select_related("scan_type")
            .order_by("-start_scan_date")[:limit]
        )

        data = [
            {
                "id": scan.id,
                "date": scan.start_scan_date.isoformat(),
                "status": scan.scan_status,
                "scan_type": scan.scan_type.name if scan.scan_type else "Unknown",
            }
            for scan in scans
        ]

        return {"scans": data, "total": len(data)}

    def get_posture_score(self) -> Dict[str, Any]:
        """Calculate security posture score."""
        vulns = Vulnerability.objects.filter(scan_history__target_id=self.target_id)
        severity_map = {"critical": 40, "high": 25, "medium": 15, "low": 5, "info": 0}

        penalty = 0
        for severity_label, count in vulns.values("severity").annotate(count=Count("id")):
            key = (
                ["info", "low", "medium", "high", "critical"][severity_label]
                if severity_label in [0, 1, 2, 3, 4]
                else "info"
            )
            penalty += severity_map.get(key, 0) * count

        score = max(0, 100 - penalty)
        score = min(score, 100)

        trend = self._calculate_trend()

        return {
            "score": score,
            "trend": trend,
            "level": "good" if score >= 70 else "warning" if score >= 50 else "critical",
        }

    def _calculate_trend(self) -> str:
        """Calculate score trend compared to last scan."""
        scans = ScanHistory.objects.filter(target_id=self.target_id, scan_status=2).order_by("-start_scan_date")[:2]
        if len(scans) < 2:
            return "stable"

        old_vuln_count = Vulnerability.objects.filter(scan_history=scans[1]).count()
        new_vuln_count = Vulnerability.objects.filter(scan_history=scans[0]).count()

        if new_vuln_count < old_vuln_count:
            return "improving"
        elif new_vuln_count > old_vuln_count:
            return "declining"
        return "stable"

    def get_technology(self) -> Dict[str, Any]:
        """Get technology distribution."""
        techs = Technology.objects.filter(scan_history__target_id=self.target_id)
        distribution = techs.values("name").annotate(count=Count("id")).order_by("-count")[:20]

        data = [{"name": item["name"], "value": item["count"]} for item in distribution]
        return {"technologies": data}

    def get_subdomain_stats(self) -> Dict[str, Any]:
        """Get subdomain statistics."""
        scan = ScanHistory.objects.filter(target_id=self.target_id, scan_status=2).order_by("-start_scan_date").first()

        if not scan:
            return {"total": 0, "alive": 0, "interesting": 0}

        total = Subdomain.objects.filter(scan_history=scan).count()
        alive = Subdomain.objects.filter(scan_history=scan, http_status__gte=200, http_status__lt=400).count()
        interesting = Subdomain.objects.filter(scan_history=scan, is_interesting=True).count()

        return {"total": total, "alive": alive, "interesting": interesting}

    def get_endpoint_stats(self) -> Dict[str, Any]:
        """Get endpoint statistics."""
        scan = ScanHistory.objects.filter(target_id=self.target_id, scan_status=2).order_by("-start_scan_date").first()

        if not scan:
            return {"total": 0, "with_vulns": 0}

        total = EndPoint.objects.filter(scan_history=scan).count()
        with_vulns = EndPoint.objects.filter(scan_history=scan, vulnerability_count__gt=0).count()

        return {"total": total, "with_vulns": with_vulns, "clean": total - with_vulns}

    def get_threat_intel_summary(self) -> Dict[str, Any]:
        """Get threat intelligence summary."""
        matches = ThreatMatch.objects.filter(matched_type="ip", status__in=["new", "reviewed"]).select_related(
            "indicator"
        )

        critical_count = matches.filter(risk_score__gte=70).count()
        total_count = matches.count()

        return {
            "total_matches": total_count,
            "critical_indicators": critical_count,
            "risk_score_avg": round(matches.aggregate(p=Avg("risk_score"))["p"], 1) if total_count else 0,
        }

    def get_widget_data(self, widget_type: str, config: Dict = None) -> Dict[str, Any]:
        """Get data for a specific widget type."""
        methods = {
            "vuln_count": self.get_vuln_count,
            "severity_pie": self.get_severity_pie,
            "timeline": lambda: self.get_timeline(config.get("days", 30) if config else 30),
            "top_targets": lambda: self.get_top_targets(config.get("limit", 10) if config else 10),
            "recent_scans": lambda: self.get_recent_scans(config.get("limit", 10) if config else 10),
            "posture_score": self.get_posture_score,
            "technology": self.get_technology,
            "subdomain_stats": self.get_subdomain_stats,
            "endpoint_stats": self.get_endpoint_stats,
        }

        method = methods.get(widget_type)
        if method:
            return method()
        return {"error": f"Unknown widget type: {widget_type}"}


def get_dashboard_for_user(user, dashboard_id: int = None):
    """Get dashboard for user (owned or shared)."""
    from .models_dashboard import Dashboard

    if dashboard_id:
        return Dashboard.objects.filter(
            Q(owner=user) | Q(shared_with=user),
            id=dashboard_id,
        ).first()

    return Dashboard.objects.filter(
        Q(owner=user) | Q(shared_with=user),
        is_default=True,
    ).first()


def create_dashboard_from_template(user, template_id: str):
    """Create a new dashboard from a template."""
    from .models_dashboard import Dashboard, DashboardTemplate, DashboardWidget

    template = DashboardTemplate.objects.filter(id=template_id).first()
    if not template:
        raise ValueError(f"Template not found: {template_id}")

    dashboard = Dashboard.objects.create(
        name=template.name,
        description=template.description,
        owner=user,
        is_default=False,
        template_id=template_id,
        layout=template.layout_config,
    )

    for idx, widget_config in enumerate(template.widgets_config):
        DashboardWidget.objects.create(
            dashboard=dashboard,
            widget_type=widget_config.get("type"),
            title=widget_config.get("title"),
            config=widget_config.get("config", {}),
            position_x=(idx % 2) * 6,
            position_y=idx * 4,
            width=widget_config.get("width", 6),
            height=widget_config.get("height", 4),
        )

    template.usage_count += 1
    template.save()

    return dashboard
