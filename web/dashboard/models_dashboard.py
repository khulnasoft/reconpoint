"""
Dashboard models for custom data visualization.
"""

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Dashboard(models.Model):
    """
    Custom dashboard configuration for data visualization.
    """

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_dashboards",
    )

    layout = models.JSONField(
        default=dict,
        help_text="Grid layout configuration",
    )

    is_default = models.BooleanField(default=False)
    is_public = models.BooleanField(
        default=False,
        help_text="Allow other users to view",
    )

    shared_with = models.ManyToManyField(
        User,
        related_name="shared_dashboards",
        blank=True,
    )

    template_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Template this dashboard was created from",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["owner", "-updated_at"]),
        ]

    def __str__(self):
        return self.name


class DashboardWidget(models.Model):
    """
    Individual widget on a dashboard.
    """

    class WidgetType(models.TextChoices):
        VULN_COUNT = "vuln_count", "Vulnerability Count"
        SEVERITY_PIE = "severity_pie", "Severity Distribution"
        TIMELINE = "timeline", "Vulnerability Timeline"
        TOP_TARGETS = "top_targets", "Most Vulnerable Targets"
        RECENT_SCANS = "recent_scans", "Recent Scans"
        POSTURE_SCORE = "posture_score", "Security Posture Score"
        TECHNOLOGY = "technology", "Technology Distribution"
        SUBDOMAIN_STATS = "subdomain_stats", "Subdomain Statistics"
        ENDPOINT_STATS = "endpoint_stats", "Endpoint Statistics"
        CUSTOM_QUERY = "custom_query", "Custom Data Query"
        METRIC = "metric", "KPI Metric Card"
        NOTES = "notes", "Notes/Text"

    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name="widgets",
    )

    widget_type = models.CharField(
        max_length=50,
        choices=WidgetType.choices,
    )

    title = models.CharField(max_length=255, blank=True, null=True)

    config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Widget-specific configuration",
    )

    position_x = models.PositiveIntegerField(default=0)
    position_y = models.PositiveIntegerField(default=0)
    width = models.PositiveIntegerField(default=4)
    height = models.PositiveIntegerField(default=3)

    is_enabled = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position_y", "position_x"]

    def __str__(self):
        return f"{self.widget_type} on {self.dashboard.name}"


class DashboardTemplate(models.Model):
    """
    Pre-built dashboard templates.
    """

    class TemplateCategory(models.TextChoices):
        EXECUTIVE = "executive", "Executive Summary"
        SECURITY = "security", "Security Operations"
        COMPLIANCE = "compliance", "Compliance"
        PENETRATION = "penetration", "Penetration Testing"
        RECON = "recon", "Reconnaissance"
        CUSTOM = "custom", "Custom"

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()

    category = models.CharField(
        max_length=50,
        choices=TemplateCategory.choices,
    )

    thumbnail = models.URLField(blank=True, null=True)

    widgets_config = models.JSONField(
        default=list,
        help_text="List of widget configurations",
    )

    layout_config = models.JSONField(
        default=dict,
        help_text="Default layout configuration",
    )

    is_system = models.BooleanField(
        default=False,
        help_text="System template vs user-created",
    )

    usage_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        return f"Template: {self.name}"

    @classmethod
    def get_default_templates(cls):
        """Get built-in default templates."""
        return [
            {
                "id": "executive-summary",
                "name": "Executive Summary",
                "description": "High-level security overview for executives",
                "category": cls.TemplateCategory.EXECUTIVE,
                "widgets": [
                    {"type": "posture_score", "title": "Security Score", "width": 3},
                    {"type": "vuln_count", "title": "Total Vulnerabilities", "width": 3},
                    {"type": "severity_pie", "title": "Severity Distribution", "width": 3},
                    {"type": "top_targets", "title": "Most Vulnerable Targets", "width": 6},
                    {"type": "timeline", "title": "Vulnerability Trend", "width": 6},
                ],
            },
            {
                "id": "security-ops",
                "name": "Security Operations",
                "description": "Daily security operations dashboard",
                "category": cls.TemplateCategory.SECURITY,
                "widgets": [
                    {"type": "recent_scans", "title": "Recent Scans", "width": 4},
                    {"type": "vuln_count", "title": "Open Vulnerabilities", "width": 4},
                    {"type": "posture_score", "title": "Posture Score", "width": 4},
                    {"type": "timeline", "title": "Vulnerability Timeline", "width": 6},
                    {"type": "technology", "title": "Tech Stack", "width": 6},
                ],
            },
            {
                "id": "recon-overview",
                "name": "Reconnaissance Overview",
                "description": "Reconnaissance findings summary",
                "category": cls.TemplateCategory.RECON,
                "widgets": [
                    {"type": "subdomain_stats", "title": "Subdomain Stats", "width": 4},
                    {"type": "endpoint_stats", "title": "Endpoint Stats", "width": 4},
                    {"type": "vuln_count", "title": "Findings", "width": 4},
                    {"type": "top_targets", "title": "Targets", "width": 6},
                    {"type": "recent_scans", "title": "Scan History", "width": 6},
                ],
            },
        ]


class WidgetDataCache(models.Model):
    """
    Cached data for widgets to reduce query load.
    """

    class CacheStatus(models.TextChoices):
        FRESH = "fresh", "Fresh"
        STALE = "stale", "Stale"
        ERROR = "error", "Error"

    widget = models.ForeignKey(
        DashboardWidget,
        on_delete=models.CASCADE,
        related_name="data_cache",
    )

    data = models.JSONField(default=dict)
    status = models.CharField(
        max_length=20,
        choices=CacheStatus.choices,
        default=CacheStatus.FRESH,
    )

    error_message = models.TextField(blank=True, null=True)

    cached_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-cached_at"]
        indexes = [
            models.Index(fields=["widget", "-cached_at"]),
        ]

    def __str__(self):
        return f"Cache for {self.widget.widget_type} ({self.status})"

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    @classmethod
    def get_or_compute(cls, widget, compute_func, ttl_seconds: int = 300):
        """Get cached data or compute fresh data."""
        cache = cls.objects.filter(
            widget=widget,
            status=cls.CacheStatus.FRESH,
            expires_at__gt=timezone.now(),
        ).first()

        if cache:
            return cache.data

        data = compute_func()
        expires_at = timezone.now() + timezone.timedelta(seconds=ttl_seconds)

        cls.objects.update_or_create(
            widget=widget,
            defaults={
                "data": data,
                "status": cls.CacheStatus.FRESH,
                "expires_at": expires_at,
                "error_message": None,
            },
        )

        return data
