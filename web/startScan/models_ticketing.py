"""
Ticketing integration models for external issue tracking.
"""

from datetime import datetime

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class TicketingProvider(models.TextChoices):
    JIRA = "jira", "Jira"
    GITHUB = "github", "GitHub Issues"
    LINEAR = "linear", "Linear"
    ZENDESK = "zendesk", "Zendesk"
    SERVICE_NOW = "service_now", "ServiceNow"
    CUSTOM = "custom", "Custom Webhook"


class TicketIntegration(models.Model):
    """External ticketing system configuration."""

    name = models.CharField(max_length=255)
    provider = models.CharField(max_length=50, choices=TicketingProvider.choices)
    config = models.JSONField(default=dict, help_text="API credentials and provider-specific settings")
    webhook_url = models.URLField(blank=True, null=True)
    webhook_secret = models.CharField(max_length=500, blank=True, null=True)
    default_project = models.CharField(max_length=255, blank=True, null=True)
    default_issue_type = models.CharField(max_length=100, blank=True, null=True)
    is_enabled = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_ticket_integrations"
    )

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["provider", "is_enabled"])]

    def __str__(self):
        return f"{self.name} ({self.provider})"

    def test_connection(self) -> bool:
        """Test the ticketing connection."""
        try:
            if self.provider == TicketingProvider.JIRA:
                return self._test_jira()
            elif self.provider == TicketingProvider.GITHUB:
                return self._test_github()
            elif self.provider == TicketingProvider.LINEAR:
                return self._test_linear()
            return False
        except Exception:
            return False

    def _test_jira(self) -> bool:
        import requests.auth

        auth = requests.auth.HTTPBasicAuth(self.config.get("username"), self.config.get("api_token"))
        url = f"{self.config.get('url')}/rest/api/3/myself"
        response = requests.get(url, auth=auth, timeout=10)
        return response.status_code == 200

    def _test_github(self) -> bool:
        import requests

        headers = {"Authorization": f"Token {self.config.get('token')}", "Accept": "application/vnd.github.v3+json"}
        response = requests.get("https://api.github.com/user", headers=headers, timeout=10)
        return response.status_code == 200

    def _test_linear(self) -> bool:
        import requests

        headers = {"Authorization": self.config.get("api_key"), "Content-Type": "application/json"}
        response = requests.post(
            "https://api.linear.app/graphql", json={"query": "{ me { id } }"}, headers=headers, timeout=10
        )
        return response.status_code == 200


class TicketCreationRule(models.Model):
    """Rules for automatic ticket creation based on scan findings."""

    name = models.CharField(max_length=255)
    integration = models.ForeignKey(TicketIntegration, on_delete=models.CASCADE, related_name="rules")
    is_enabled = models.BooleanField(default=True)
    priority_threshold = models.CharField(
        max_length=20,
        choices=[("critical", "Critical"), ("high", "High"), ("medium", "Medium"), ("low", "Low")],
        default="high",
    )
    vulnerability_type_filter = models.JSONField(default=list, blank=True)
    target_filter = models.JSONField(default=list, blank=True)
    create_subtasks = models.BooleanField(default=False)
    assign_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="ticket_rules")
    labels = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["integration", "is_enabled"])]

    def __str__(self):
        return f"{self.name} -> {self.integration.name}"

    def matches_finding(self, vulnerability) -> bool:
        if vulnerability.severity_priority < self._get_priority_value():
            return False
        if self.vulnerability_type_filter:
            if vulnerability.name not in self.vulnerability_type_filter:
                return False
        if self.target_filter:
            if vulnerability.endpoint not in self.target_filter:
                return False
        return True

    def _get_priority_value(self) -> int:
        priority_map = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        return priority_map.get(self.priority_threshold, 0)


class CreatedTicket(models.Model):
    """Tracks tickets created in external systems."""

    class TicketStatus(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In Progress"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    integration = models.ForeignKey(TicketIntegration, on_delete=models.CASCADE, related_name="created_tickets")
    vulnerability = models.ForeignKey("startScan.Vulnerability", on_delete=models.CASCADE, related_name="tickets")
    external_ticket_id = models.CharField(max_length=100)
    external_ticket_url = models.URLField()
    status = models.CharField(max_length=20, choices=TicketStatus.choices, default=TicketStatus.OPEN)
    externalassignee = models.CharField(max_length=255, blank=True, null=True)
    synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["integration", "vulnerability"]
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["integration", "status"]), models.Index(fields=["vulnerability", "status"])]

    def __str__(self):
        return f"{self.external_ticket_id} ({self.status})"


class SLAPolicy(models.Model):
    """Service Level Agreement policies for remediation."""

    name = models.CharField(max_length=255)
    severity = models.CharField(max_length=20, unique=True)
    response_time_hours = models.PositiveIntegerField(help_text="Time to first response (hours)")
    resolution_time_hours = models.PositiveIntegerField(help_text="Time to complete resolution (hours)")
    escalation_rule = models.JSONField(default=dict, blank=True)
    notification_channels = models.JSONField(default=list, blank=True)
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["severity"]

    def __str__(self):
        return f"{self.name}: {self.severity} ({self.resolution_time_hours}h)"

    def is_breached(self, created_at: datetime) -> bool:
        from datetime import timedelta

        deadline = created_at + timedelta(hours=self.resolution_time_hours)
        return timezone.now() > deadline

    def get_remaining_time(self, created_at: datetime) -> float:
        from datetime import timedelta

        deadline = created_at + timedelta(hours=self.resolution_time_hours)
        remaining = deadline - timezone.now()
        return remaining.total_seconds() / 3600


class TicketComment(models.Model):
    """Comments synced between reconPoint and tickets."""

    ticket = models.ForeignKey(CreatedTicket, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_internal = models.BooleanField(default=False)
    external_comment_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment on {self.ticket.external_ticket_id}"
