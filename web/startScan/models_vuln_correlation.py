"""
Vulnerability correlation models for attack chain analysis.
"""

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class VulnerabilityRelation(models.Model):
    """
    Defines relationships between vulnerabilities for attack chain analysis.
    """

    class RelationType(models.TextChoices):
        CAUSES = "causes", "Causes"
        ENABLES = "enables", "Enables"
        ESCALATES = "escalates", "Escalates"
        LEADS_TO = "leads_to", "Leads To"
        PREREQUISITE = "prerequisite", "Prerequisite"
        RELATED = "related", "Related"
        DUPLICATE = "duplicate", "Duplicate"
        SAME_AS = "same_as", "Same As"

    parent = models.ForeignKey(
        "startScan.Vulnerability",
        on_delete=models.CASCADE,
        related_name="child_relations",
    )
    child = models.ForeignKey(
        "startScan.Vulnerability",
        on_delete=models.CASCADE,
        related_name="parent_relations",
    )
    relation_type = models.CharField(
        max_length=20,
        choices=RelationType.choices,
    )
    confidence = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1.0,
        help_text="Confidence score (0-1)",
    )
    evidence = models.JSONField(
        default=dict,
        blank=True,
        help_text="Evidence supporting the relationship",
    )
    detected_by = models.CharField(
        max_length=100,
        blank=True,
        help_text="Detection method or tool",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["parent", "child", "relation_type"]
        indexes = [
            models.Index(fields=["parent", "relation_type"]),
            models.Index(fields=["child", "relation_type"]),
            models.Index(fields=["-confidence"]),
        ]

    def __str__(self):
        return f"{self.parent.name} --{self.relation_type}--> {self.child.name}"


class AttackChain(models.Model):
    """
    Represents a complete attack chain from vulnerability analysis.
    """

    class Status(models.TextChoices):
        DETECTED = "detected", "Detected"
        ANALYZING = "analyzing", "Analyzing"
        MITIGATING = "mitigating", "Mitigating"
        MITIGATED = "mitigated", "Mitigated"
        EXPLOITED = "exploited", "Exploited"

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    target = models.ForeignKey(
        "targetApp.Target",
        on_delete=models.CASCADE,
        related_name="attack_chains",
    )
    scan = models.ForeignKey(
        "startScan.ScanHistory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attack_chains",
    )

    chain_data = models.JSONField(
        default=list,
        help_text="Ordered list of vulnerabilities in the attack chain",
    )
    entry_points = models.JSONField(
        default=list,
        help_text="Initial vulnerabilities that start the chain",
    )
    critical_assets = models.JSONField(
        default=list,
        help_text="Assets that would be compromised if chain succeeds",
    )

    risk_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Calculated risk score for the chain",
    )
    exploitability = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        help_text="Ease of exploitation (0-1)",
    )
    impact = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        help_text="Potential impact (0-1)",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DETECTED,
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-risk_score", "-created_at"]
        indexes = [
            models.Index(fields=["target", "-risk_score"]),
            models.Index(fields=["-risk_score"]),
        ]

    def __str__(self):
        return f"Attack Chain: {self.name}"


class RemediationRecommendation(models.Model):
    """
    LLM-generated or manually created remediation recommendations.
    """

    class Priority(models.TextChoices):
        CRITICAL = "critical", "Critical"
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"
        INFO = "info", "Informational"

    vulnerability = models.ForeignKey(
        "startScan.Vulnerability",
        on_delete=models.CASCADE,
        related_name="remediations",
    )
    attack_chain = models.ForeignKey(
        AttackChain,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="remediations",
    )

    title = models.CharField(max_length=255)
    description = models.TextField()
    remediation_steps = models.JSONField(
        default=list,
        help_text="Ordered list of remediation steps",
    )
    effort_estimate = models.CharField(
        max_length=50,
        help_text="Estimated effort (e.g., '2 hours', '1 day')",
    )
    cost_estimate = models.CharField(
        max_length=50,
        blank=True,
        help_text="Estimated cost if known",
    )

    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    cvss_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
    )

    is_automated = models.BooleanField(
        default=False,
        help_text="Generated by LLM",
    )
    confidence = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1.0,
    )
    source = models.CharField(
        max_length=100,
        default="manual",
        help_text="Source of recommendation (llm, manual, cvrf)",
    )

    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_remediations",
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("verified", "Verified"),
            ("wont_fix", "Won't Fix"),
        ],
        default="pending",
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_remediations",
    )
    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-priority", "-created_at"]
        indexes = [
            models.Index(fields=["vulnerability", "-priority"]),
            models.Index(fields=["-priority", "status"]),
            models.Index(fields=["assigned_to", "status"]),
        ]

    def __str__(self):
        return f"Remediation: {self.title}"

    def mark_completed(self):
        self.status = "completed"
        self.completed_at = timezone.now()
        self.save()


class VulnerabilityDeduplication(models.Model):
    """
    Tracks duplicate vulnerability records across different scanners.
    """

    class CanonicalVulnerability(models.Model):
        canonical_name = models.CharField(max_length=255)
        canonical_description = models.TextField()
        cve_id = models.CharField(max_length=50, blank=True, null=True)
        cvss_score = models.DecimalField(
            max_digits=3,
            decimal_places=1,
            null=True,
            blank=True,
        )
        first_seen = models.DateTimeField(auto_now_add=True)
        last_updated = models.DateTimeField(auto_now=True)

        class Meta:
            ordering = ["-first_seen"]

        def __str__(self):
            return f"Canonical: {self.canonical_name}"

    canonical = models.ForeignKey(
        CanonicalVulnerability,
        on_delete=models.CASCADE,
        related_name="duplicates",
    )
    vulnerability = models.ForeignKey(
        "startScan.Vulnerability",
        on_delete=models.CASCADE,
        related_name="deduplication_record",
    )
    similarity_score = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1.0,
    )
    match_method = models.CharField(
        max_length=50,
        help_text="How the match was determined (fuzzy, exact, semantic)",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["canonical", "vulnerability"]

    def __str__(self):
        return f"Duplicate link: {self.vulnerability.name} -> {self.canonical.canonical_name}"


class CVREFixReference(models.Model):
    """
    References to known fixes from CVRF/OVAL feeds.
    """

    vulnerability = models.ForeignKey(
        "startScan.Vulnerability",
        on_delete=models.CASCADE,
        related_name="cvrf_references",
    )

    cvrf_id = models.CharField(max_length=100)
    cve_id = models.CharField(max_length=50, blank=True, null=True)
    advisory_url = models.URLField()
    severity = models.CharField(max_length=20, blank=True, null=True)

    fix_publisher = models.CharField(max_length=255, blank=True, null=True)
    fix_product = models.CharField(max_length=255, blank=True, null=True)
    fix_version = models.CharField(max_length=100, blank=True, null=True)

    remediated_date = models.DateField(null=True, blank=True)
    remediated_version = models.CharField(max_length=100, blank=True, null=True)

    workarounds = models.JSONField(default=list, blank=True)
    mitigations = models.JSONField(default=list, blank=True)

    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "CVRF Fix Reference"
        ordering = ["-fetched_at"]
        indexes = [
            models.Index(fields=["cve_id"]),
            models.Index(fields=["vulnerability"]),
        ]

    def __str__(self):
        return f"CVRF: {self.cve_id or self.cvrf_id}"
