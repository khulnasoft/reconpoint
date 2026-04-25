"""
Plugin models for third-party tool marketplace and custom integrations.
"""

from django.contrib.auth.models import User
from django.db import models


class PluginCategory(models.TextChoices):
    SUBDOMAIN_ENUMERATION = "subdomain", "Subdomain Enumeration"
    PORT_SCANNING = "port", "Port Scanning"
    VULNERABILITY_SCANNING = "vuln", "Vulnerability Scanning"
    OSINT = "osint", "OSINT"
    WEB_CRAWLING = "crawl", "Web Crawling"
    DATA_ANALYSIS = "analysis", "Data Analysis"
    NOTIFICATION = "notification", "Notification"
    CUSTOM = "custom", "Custom"


class Plugin(models.Model):
    """
    Plugin model for third-party tool marketplace.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        DEPRECATED = "deprecated", "Deprecated"
        REMOVED = "removed", "Removed"

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True)
    version = models.CharField(max_length=50)
    description = models.TextField()
    long_description = models.TextField(blank=True, null=True)

    author = models.CharField(max_length=255)
    author_url = models.URLField(blank=True, null=True)
    homepage_url = models.URLField(blank=True, null=True)
    repository_url = models.URLField(blank=True, null=True)

    category = models.CharField(
        max_length=50,
        choices=PluginCategory.choices,
        default=PluginCategory.CUSTOM,
    )
    tags = models.JSONField(default=list)

    config_schema = models.JSONField(
        default=dict,
        help_text="JSON schema for plugin configuration",
    )
    required_permissions = models.JSONField(default=list)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    download_count = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
    )
    rating_count = models.PositiveIntegerField(default=0)

    installed_count = models.PositiveIntegerField(default=0)

    source_code = models.TextField(blank=True, null=True)
    entry_point = models.CharField(max_length=255, default="run")

    is_verified = models.BooleanField(default=False)
    security_scanned_at = models.DateTimeField(null=True, blank=True)
    security_scan_result = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-download_count", "-rating"]
        indexes = [
            models.Index(fields=["category", "status"]),
            models.Index(fields=["-download_count"]),
            models.Index(fields=["-rating"]),
        ]

    def __str__(self):
        return f"{self.name} v{self.version}"


class PluginVersion(models.Model):
    """
    Version history for plugins.
    """

    plugin = models.ForeignKey(
        Plugin,
        on_delete=models.CASCADE,
        related_name="versions",
    )
    version = models.CharField(max_length=50)
    changelog = models.TextField()
    source_code = models.TextField()
    config_schema = models.JSONField(default=dict)

    release_date = models.DateTimeField(auto_now_add=True)
    is_latest = models.BooleanField(default=False)

    class Meta:
        unique_together = ["plugin", "version"]
        ordering = ["-release_date"]

    def __str__(self):
        return f"{self.plugin.name} v{self.version}"


class PluginInstallation(models.Model):
    """
    Tracks plugin installations per workspace/team.
    """

    class InstallStatus(models.TextChoices):
        INSTALLED = "installed", "Installed"
        UPDATE_AVAILABLE = "update", "Update Available"
        UPDATE_FAILED = "failed", "Update Failed"
        REMOVED = "removed", "Removed"

    plugin = models.ForeignKey(
        Plugin,
        on_delete=models.CASCADE,
        related_name="installations",
    )
    installed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="plugin_installations",
    )
    workspace_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Null means global installation",
    )

    installed_version = models.CharField(max_length=50)
    config = models.JSONField(default=dict, blank=True)
    is_enabled = models.BooleanField(default=True)

    status = models.CharField(
        max_length=20,
        choices=InstallStatus.choices,
        default=InstallStatus.INSTALLED,
    )

    installed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_run_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ["plugin", "workspace_id"]
        ordering = ["-installed_at"]

    def __str__(self):
        return f"{self.plugin.name} installed by {self.installed_by}"


class PluginExecutionLog(models.Model):
    """
    Logs plugin executions for auditing and debugging.
    """

    class ExecutionStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        TIMEOUT = "timeout", "Timeout"

    installation = models.ForeignKey(
        PluginInstallation,
        on_delete=models.CASCADE,
        related_name="execution_logs",
    )

    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=ExecutionStatus.choices,
        default=ExecutionStatus.PENDING,
    )

    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["installation", "-started_at"]),
            models.Index(fields=["status", "-started_at"]),
        ]

    def __str__(self):
        return f"{self.installation.plugin.name} - {self.status}"


class PluginSecurityScan(models.Model):
    """
    Stores security scan results for plugins.
    """

    class Severity(models.TextChoices):
        INFO = "info", "Info"
        WARNING = "warning", "Warning"
        ERROR = "error", "Error"
        CRITICAL = "critical", "Critical"

    plugin = models.ForeignKey(
        Plugin,
        on_delete=models.CASCADE,
        related_name="security_scans",
    )

    scan_version = models.CharField(max_length=50)
    issues_found = models.JSONField(default=list)

    severity_counts = models.JSONField(
        default=dict,
        help_text="Counts per severity: {critical: 0, error: 0, warning: 0, info: 0}",
    )

    is_passed = models.BooleanField(default=True)
    report_url = models.URLField(null=True, blank=True)

    scanned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-scanned_at"]

    def __str__(self):
        return f"{self.plugin.name} security scan - {'PASSED' if self.is_passed else 'FAILED'}"
