"""
Models for AI-Powered Proof-of-Concept generation and execution.
"""

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class PoCRequest(models.Model):
    """
    Request to generate a PoC for a vulnerability.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        GENERATING = "generating", "Generating"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"
        EXECUTING = "executing", "Executing"
        EXECUTED = "executed", "Executed"

    vulnerability = models.ForeignKey(
        "startScan.Vulnerability",
        on_delete=models.CASCADE,
        related_name="poc_requests",
    )

    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="poc_requests",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    prompt_context = models.JSONField(
        default=dict,
        help_text="Context provided to LLM for generation",
    )

    generated_code = models.TextField(blank=True, null=True)
    language = models.CharField(max_length=50, default="python")

    error_message = models.TextField(blank=True, null=True)

    llm_model = models.CharField(max_length=100, blank=True, null=True)
    generation_time_ms = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["vulnerability", "status"]),
            models.Index(fields=["requested_by", "status"]),
        ]

    def __str__(self):
        return f"PoC Request for {self.vulnerability.name} ({self.status})"


class PoCExecution(models.Model):
    """
    Execution of a generated PoC.
    """

    class ExecutionStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        TIMEOUT = "timeout", "Timeout"
        BLOCKED = "blocked", "Blocked"

    class ExecutionMode(models.TextChoices):
        SANDBOX = "sandbox", "Sandboxed"
        SIMULATION = "sim", "Simulation"
        LIVE = "live", "Live"

    poc_request = models.ForeignKey(
        PoCRequest,
        on_delete=models.CASCADE,
        related_name="executions",
    )

    executed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="poc_executions",
    )

    execution_mode = models.CharField(
        max_length=20,
        choices=ExecutionMode.choices,
        default=ExecutionMode.SANDBOX,
    )

    status = models.CharField(
        max_length=20,
        choices=ExecutionStatus.choices,
        default=ExecutionStatus.PENDING,
    )

    target_url = models.URLField(blank=True, null=True)
    target_params = models.JSONField(default=dict, blank=True)

    output = models.TextField(blank=True, null=True)
    error_output = models.TextField(blank=True, null=True)

    execution_time_ms = models.PositiveIntegerField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    resource_usage = models.JSONField(default=dict, blank=True)

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_pocs",
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    is_auto_approved = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["poc_request", "status"]),
            models.Index(fields=["executed_by", "status"]),
        ]

    def __str__(self):
        return f"PoC Execution {self.id} ({self.status})"

    def mark_running(self):
        self.status = self.ExecutionStatus.RUNNING
        self.started_at = timezone.now()
        self.save()

    def mark_success(self, output: str, time_ms: int):
        self.status = self.ExecutionStatus.SUCCESS
        self.output = output
        self.execution_time_ms = time_ms
        self.completed_at = timezone.now()
        self.save()

    def mark_failed(self, error: str, time_ms: int = None):
        self.status = self.ExecutionStatus.FAILED
        self.error_output = error
        if time_ms:
            self.execution_time_ms = time_ms
        self.completed_at = timezone.now()
        self.save()

    def mark_timeout(self, output: str):
        self.status = self.ExecutionStatus.TIMEOUT
        self.output = output
        self.completed_at = timezone.now()
        self.save()


class PoCTemplate(models.Model):
    """
    Pre-built PoC templates for common vulnerability types.
    """

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()

    category = models.CharField(max_length=100)

    vulnerability_pattern = models.CharField(
        max_length=255,
        help_text="Pattern to match vulnerability names",
    )

    template_code = models.TextField()

    language = models.CharField(max_length=50, default="python")

    requirements = models.JSONField(default=list, blank=True)

    is_sandbox_only = models.BooleanField(
        default=True,
        help_text="Requires sandbox execution",
    )

    risk_level = models.CharField(
        max_length=20,
        choices=[
            ("safe", "Safe"),
            ("low", "Low Risk"),
            ("medium", "Medium Risk"),
            ("high", "High Risk"),
        ],
        default="low",
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
        """Get built-in PoC templates."""
        return [
            {
                "name": "SQL Injection Test",
                "description": "Basic SQL injection test payload",
                "category": "injection",
                "vuln_pattern": "sql",
                "code": "# SQL Injection Test Payload\npayload = \"' OR '1'='1\"\n# Test for SQL injection",
                "language": "python",
                "requirements": ["requests"],
                "risk": "low",
            },
            {
                "name": "XSS Basic Test",
                "description": "Basic XSS test payload",
                "category": "xss",
                "vuln_pattern": "xss|cross",
                "code": "# XSS Test Payload\npayload = \"<script>alert('XSS')</script>\"",
                "language": "javascript",
                "risk": "safe",
            },
            {
                "name": "Path Traversal Test",
                "description": "Path traversal test",
                "category": "file",
                "vuln_pattern": "path|traversal|lfi",
                "code": '# Path Traversal Test\npayload = "../../../etc/passwd"',
                "language": "text",
                "risk": "medium",
            },
        ]


class PoCApproval(models.Model):
    """
    Approval workflow for running PoCs.
    """

    class ApprovalStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    poc_execution = models.ForeignKey(
        PoCExecution,
        on_delete=models.CASCADE,
        related_name="approvals",
    )

    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="poc_approval_requests",
    )

    status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
    )

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="poc_approvals",
    )

    notes = models.TextField(blank=True, null=True)

    requested_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-requested_at"]

    def __str__(self):
        return f"Approval for {self.poc_execution.id} ({self.status})"

    def approve(self, user, notes: str = None):
        self.status = self.ApprovalStatus.APPROVED
        self.approved_by = user
        self.responded_at = timezone.now()
        if notes:
            self.notes = notes
        self.save()

    def reject(self, user, notes: str = None):
        self.status = self.ApprovalStatus.REJECTED
        self.approved_by = user
        self.responded_at = timezone.now()
        if notes:
            self.notes = notes
        self.save()
