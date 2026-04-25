"""
Security Metrics calculation services.
"""

from datetime import datetime
from typing import Any, Dict

from django.db.models import Avg, Count, F
from django.db.models.functions import ExtractEpoch
from django.utils import timezone

from startScan.models import Vulnerability


def calculate_metric_value(metric, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """
    Calculate metric value for a date range based on metric type.
    """
    metric_type = metric.metric_type

    if metric_type == "vuln_count":
        return calculate_vulnerability_count(metric, start_date, end_date)
    elif metric_type == "severity_dist":
        return calculate_severity_distribution(metric, start_date, end_date)
    elif metric_type == "mttd":
        return calculate_mttd(metric, start_date, end_date)
    elif metric_type == "mttr":
        return calculate_mttr(metric, start_date, end_date)
    elif metric_type == "closure_rate":
        return calculate_closure_rate(metric, start_date, end_date)
    elif metric_type == "posture_score":
        return calculate_security_posture_score(metric, start_date, end_date)
    elif metric_type == "risk_score":
        return calculate_risk_score(metric, start_date, end_date)
    elif metric_type == "threat_intel":
        return calculate_threat_intel_matches(metric, start_date, end_date)
    elif metric_type == "compliance_status":
        return calculate_compliance_status(metric, start_date, end_date)
    else:
        return {"value": 0, "unit": "", "description": "Custom metric not implemented"}


def calculate_vulnerability_count(metric, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Calculate total vulnerability count."""
    count = Vulnerability.objects.filter(
        discovered_at__gte=start_date,
        discovered_at__lte=end_date,
    ).count()

    return {
        "value": count,
        "unit": "vulnerabilities",
        "description": "Total vulnerabilities discovered",
    }


def calculate_severity_distribution(metric, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Calculate severity distribution."""
    distribution = (
        Vulnerability.objects.filter(
            discovered_at__gte=start_date,
            discovered_at__lte=end_date,
        )
        .values("severity")
        .annotate(count=Count("id"))
    )

    result = {item["severity"]: item["count"] for item in distribution}
    return {
        "value": result,
        "unit": "distribution",
        "description": "Vulnerabilities by severity",
    }


def calculate_mttd(metric, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """
    Calculate Mean Time To Detect (MTTD) in hours.

    MTTD = Average time from vulnerability creation to discovery.
    """
    from startScan.models import Vulnerability

    vulns = Vulnerability.objects.filter(
        discovered_at__gte=start_date,
        discovered_at__lte=end_date,
        created_at__isnull=False,
    ).annotate(time_to_detect=F("discovered_at") - F("created_at"))

    avg_seconds = vulns.annotate(seconds=ExtractEpoch("time_to_detect")).aggregate(avg_seconds=Avg("seconds"))

    avg_hours = (avg_seconds["avg_seconds"] or 0) / 3600

    return {
        "value": round(avg_hours, 2),
        "unit": "hours",
        "description": "Mean Time To Detect",
    }


def calculate_mttr(metric, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """
    Calculate Mean Time To Remediate (MTTR) in hours.

    MTTR = Average time from discovery to closure.
    """
    from startScan.models import Vulnerability

    vulns = Vulnerability.objects.filter(
        discovered_at__gte=start_date,
        discovered_at__lte=end_date,
        status=Vulnerability.STATUS_RESOLVED,
        resolved_at__isnull=False,
    ).annotate(time_to_remediate=F("resolved_at") - F("discovered_at"))

    avg_seconds = vulns.annotate(seconds=ExtractEpoch("time_to_remediate")).aggregate(avg_seconds=Avg("seconds"))

    avg_hours = (avg_seconds["avg_seconds"] or 0) / 3600

    return {
        "value": round(avg_hours, 2),
        "unit": "hours",
        "description": "Mean Time To Remediate",
    }


def calculate_closure_rate(metric, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """
    Calculate vulnerability closure rate as percentage.
    """
    total = Vulnerability.objects.filter(
        discovered_at__gte=start_date,
        discovered_at__lte=end_date,
    ).count()

    closed = Vulnerability.objects.filter(
        discovered_at__gte=start_date,
        discovered_at__lte=end_date,
        status__in=[Vulnerability.STATUS_RESOLVED, Vulnerability.STATUS_FALSE_POSITIVE],
    ).count()

    rate = (closed / total * 100) if total > 0 else 0

    return {
        "value": round(rate, 2),
        "unit": "%",
        "description": "Vulnerability closure rate",
        "details": {"total": total, "closed": closed},
    }


def calculate_security_posture_score(metric, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """
    Calculate overall security posture score (0-100).

    Based on vulnerability severity and closure rates.
    """
    from startScan.models import Vulnerability

    severity_weights = {
        "critical": 10,
        "high": 7,
        "medium": 4,
        "low": 1,
        "info": 0,
    }

    vulns = Vulnerability.objects.filter(
        discovered_at__gte=start_date,
        discovered_at__lte=end_date,
    )

    total_weighted = 0
    for severity, weight in severity_weights.items():
        count = vulns.filter(severity=severity).count()
        total_weighted += count * weight

    open_vulns = vulns.filter(status__in=[Vulnerability.STATUS_OPEN, Vulnerability.STATUS_IN_PROGRESS])
    open_weighted = 0
    for severity, weight in severity_weights.items():
        count = open_vulns.filter(severity=severity).count()
        open_weighted += count * weight

    max_score = 100
    if total_weighted > 0:
        score = max(0, max_score - (open_weighted / total_weighted * max_score))
    else:
        score = 100

    return {
        "value": round(score, 2),
        "unit": "score",
        "description": "Security Posture Score (0-100)",
    }


def calculate_risk_score(metric, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """
    Calculate overall risk score based on open vulnerabilities.
    """
    from startScan.models import Vulnerability

    severity_weights = {
        "critical": 100,
        "high": 50,
        "medium": 25,
        "low": 10,
        "info": 5,
    }

    score = 0
    for severity, weight in severity_weights.items():
        count = Vulnerability.objects.filter(
            discovered_at__gte=start_date,
            discovered_at__lte=end_date,
            severity=severity,
            status__in=[Vulnerability.STATUS_OPEN, Vulnerability.STATUS_IN_PROGRESS],
        ).count()
        score += count * weight

    return {
        "value": score,
        "unit": "risk",
        "description": "Aggregate risk score based on open vulnerabilities",
    }


def calculate_threat_intel_matches(metric, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """
    Calculate threat intelligence matches.
    """
    from .models_threat_intel import ThreatMatch

    count = ThreatMatch.objects.filter(
        matched_at__gte=start_date,
        matched_at__lte=end_date,
    ).count()

    return {
        "value": count,
        "unit": "matches",
        "description": "Threat intelligence matches",
    }


def calculate_compliance_status(metric, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """
    Calculate compliance status based on mapped requirements.
    """
    from .models_metrics import ComplianceMapping, ComplianceRequirement

    requirements = ComplianceRequirement.objects.all()

    compliant = 0
    non_compliant = 0

    for req in requirements:
        metric_ids = list(ComplianceMapping.objects.filter(requirement=req).values_list("metric_id", flat=True))
        if metric_ids:
            compliant += 1
        else:
            non_compliant += 1

    total = compliant + non_compliant
    status = (compliant / total * 100) if total > 0 else 0

    return {
        "value": round(status, 2),
        "unit": "%",
        "description": "Compliance status",
        "details": {"compliant": compliant, "non_compliant": non_compliant},
    }


def get_sla_status(vulnerability) -> Dict[str, Any]:
    """
    Get SLA status for a vulnerability based on severity.
    """
    from .models_metrics import SLAPolicy

    severity = vulnerability.severity
    discovered_at = vulnerability.discovered_at

    sla = SLAPolicy.objects.filter(
        severity_level=severity,
        is_active=True,
    ).first()

    if not sla:
        return {
            "sla_applied": False,
            "breached": False,
            "remaining_hours": None,
        }

    is_breached = sla.is_breached(discovered_at)
    remaining = sla.get_remaining_time(discovered_at)

    return {
        "sla_applied": True,
        "breached": is_breached,
        "remaining_hours": round(remaining, 2),
        "response_time_hours": sla.response_time_hours,
        "resolution_time_hours": sla.resolution_time_hours,
        "sla_name": sla.name,
    }


def get_aggregated_metrics(
    target_id: int = None,
    workspace_id: int = None,
    days: int = 30,
) -> Dict[str, Any]:
    """
    Get aggregated metrics for a target or workspace over a period.
    """
    end_date = timezone.now()
    start_date = end_date - timezone.timedelta(days=days)

    base_qs = Vulnerability.objects.all()

    if target_id:
        base_qs = base_qs.filter(scan_history__target_id=target_id)
    if workspace_id:
        base_qs = base_qs.filter(workspace_id=workspace_id)

    base_qs = base_qs.filter(
        discovered_at__gte=start_date,
        discovered_at__lte=end_date,
    )

    total = base_qs.count()
    by_severity = list(base_qs.values("severity").annotate(count=Count("id")))

    open_count = base_qs.filter(status__in=[Vulnerability.STATUS_OPEN, Vulnerability.STATUS_IN_PROGRESS]).count()

    resolved_count = base_qs.filter(status=Vulnerability.STATUS_RESOLVED).count()

    closure_rate = (resolved_count / total * 100) if total > 0 else 0

    return {
        "period_days": days,
        "total_vulnerabilities": total,
        "open_vulnerabilities": open_count,
        "resolved_vulnerabilities": resolved_count,
        "closure_rate": round(closure_rate, 2),
        "by_severity": {item["severity"]: item["count"] for item in by_severity},
    }
