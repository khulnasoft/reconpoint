"""
Security Metrics and SLAs models.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict

from django.conf import settings
from django.db import models
from django.utils import timezone


@dataclass
class MetricCalculation:
    """Configuration for a calculated metric."""

    name: str
    sql_expression: str
    display_name: str
    unit: str = ""
    description: str = ""


class MetricType(models.TextChoices):
    VULNERABILITY_COUNT = "vuln_count", "Vulnerability Count"
    VULNERABILITY_SEVERITY_DISTRIBUTION = "severity_dist", "Severity Distribution"
    TIME_TO_DETECT = "mttd", "Mean Time To Detect"
    TIME_TO_REMEDIATE = "mttr", "Mean Time To Remediate"
    CLOSURE_RATE = "closure_rate", "Closure Rate"
    SECURITY_POSTURE_SCORE = "posture_score", "Security Posture Score"
    RISK_SCORE = "risk_score", "Risk Score"
    THREAT_INTEL_MATCHES = "threat_intel", "Threat Intelligence Matches"
    COMPLIANCE_STATUS = "compliance_status", "Compliance Status"
    CUSTOM = "custom", "Custom Metric"


class Metric(models.Model):
    """
    Custom metric definition for security monitoring.
    """

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    metric_type = models.CharField(max_length=50, choices=MetricType.choices)

    calculation = models.JSONField(
        default=dict,
        help_text="Calculation configuration (SQL expression, aggregation, etc.)",
    )

    display_config = models.JSONField(
        default=dict,
        help_text="Display configuration (chart type, colors, thresholds)",
    )

    data_source = models.JSONField(
        default=dict,
        help_text="Source tables/views and field mappings",
    )

    is_enabled = models.BooleanField(default=True)
    is_visible = models.BooleanField(default=True)

    threshold_config = models.JSONField(
        default=dict,
        help_text="Alert thresholds and warning levels",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_metrics",
    )

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["metric_type"]),
            models.Index(fields=["is_enabled", "is_visible"]),
        ]

    def __str__(self):
        return self.name

    def calculate(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate metric value for a date range."""
        from . import metrics_services

        return metrics_services.calculate_metric_value(self, start_date, end_date)


class MetricThreshold(models.Model):
    """
    Thresholds that trigger alerts for metrics.
    """

    class Severity(models.TextChoices):
        INFO = "info", "Info"
        WARNING = "warning", "Warning"
        CRITICAL = "critical", "Critical"

    metric = models.ForeignKey(
        Metric,
        on_delete=models.CASCADE,
        related_name="thresholds",
    )

    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.WARNING)
    operator = models.CharField(max_length=10, default="gt")
    value = models.FloatField()

    description = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["metric", "severity"]

    def __str__(self):
        return f"{self.metric.name} {self.get_severity_display()}: {self.operator} {self.value}"


class MetricHistory(models.Model):
    """
    Historical values of calculated metrics.
    """

    metric = models.ForeignKey(
        Metric,
        on_delete=models.CASCADE,
        related_name="history",
    )

    value = models.FloatField()
    target_id = models.PositiveIntegerField(null=True, blank=True)
    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-calculated_at"]
        indexes = [
            models.Index(fields=["metric", "-calculated_at"]),
        ]

    def __str__(self):
        return f"{self.metric.name}: {self.value} @ {self.calculated_at}"


class SLAPolicy(models.Model):
    """
    Service Level Agreement policies for vulnerability remediation.
    """

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    severity_level = models.CharField(
        max_length=20,
        choices=[
            ("critical", "Critical"),
            ("high", "High"),
            ("medium", "Medium"),
            ("low", "Low"),
        ],
    )

    response_time_hours = models.PositiveIntegerField(
        help_text="Expected response time in hours",
    )
    resolution_time_hours = models.PositiveIntegerField(
        help_text="Expected resolution time in hours",
    )

    escalation_enabled = models.BooleanField(default=False)
    escalation_rules = models.JSONField(default=dict, blank=True)

    notification_channels = models.JSONField(
        default=list,
        help_text="Email, Slack, Teams channels for notifications",
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["severity_level"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "severity_level"],
                name="unique_sla_name_severity",
            ),
        ]

    def __str__(self):
        return f"{self.name} - {self.severity_level} ({self.response_time_hours}h response)"

    def is_breached(self, start_time: datetime) -> bool:
        """Check if SLA would be breached given the start time."""
        deadline = start_time + timedelta(hours=self.resolution_time_hours)
        return timezone.now() > deadline

    def get_remaining_time(self, start_time: datetime) -> float:
        """Get remaining time in hours before SLA breach."""
        deadline = start_time + timedelta(hours=self.resolution_time_hours)
        remaining = deadline - timezone.now()
        return max(0, remaining.total_seconds() / 3600)


class ComplianceRequirement(models.Model):
    """
    Compliance requirements with related metrics.
    """

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    standard = models.CharField(max_length=100)

    is_mandatory = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["standard", "name"]

    def __str__(self):
        return f"{self.standard}: {self.name}"


class ComplianceMapping(models.Model):
    """
    Maps metrics to compliance requirements.
    """

    metric = models.ForeignKey(
        Metric,
        on_delete=models.CASCADE,
        related_name="compliance_mappings",
    )
    requirement = models.ForeignKey(
        ComplianceRequirement,
        on_delete=models.CASCADE,
        related_name="metric_mappings",
    )

    class Meta:
        unique_together = ["metric", "requirement"]
        indexes = [
            models.Index(fields=["requirement"]),
        ]

    def __str__(self):
        return f"{self.metric.name} -> {self.requirement.name}"
