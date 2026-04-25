"""
Threat Intelligence models for integrating with external threat feeds.
"""

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class ThreatFeed(models.Model):
    """
    External threat intelligence feed configuration.
    """

    class FeedSource(models.TextChoices):
        ABUSE_CH = "abuse_ch", "ABUSE.ch"
        SHODAN = "shodan", "Shodan"
        ALIENVAULT = "alienvault", "AlienVault OTX"
        VIRUSTOTAL = "virustotal", "VirusTotal"
        THREATFOX = "threatfox", "THREATFOX"
        MALWARE_BAZAAR = "malware_bazaar", "MalwareBazaar"
        URLHAUS = "urlhaus", "URLhaus"
        CUSTOM = "custom", "Custom Feed"

    class SyncStatus(models.TextChoices):
        NEVER = "never", "Never Synced"
        PENDING = "pending", "Pending"
        SYNCING = "syncing", "Syncing"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    name = models.CharField(max_length=255)
    source = models.CharField(
        max_length=50,
        choices=FeedSource.choices,
    )
    api_key = models.CharField(max_length=500, blank=True, null=True)
    api_endpoint = models.URLField(blank=True, null=True)

    config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Feed-specific configuration (filters, tags, etc.)",
    )

    is_enabled = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    sync_status = models.CharField(
        max_length=20,
        choices=SyncStatus.choices,
        default=SyncStatus.NEVER,
    )
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_sync_error = models.TextField(blank=True, null=True)
    sync_interval_hours = models.PositiveIntegerField(default=24)

    indicators_count = models.PositiveIntegerField(default=0)
    last_indicators_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_feeds",
    )

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["source", "is_enabled"]),
            models.Index(fields=["-last_sync_at"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.source})"


class ThreatIndicator(models.Model):
    """
    Individual threat indicators (IOCs) from threat feeds.
    """

    class IndicatorType(models.TextChoices):
        IP = "ip", "IP Address"
        DOMAIN = "domain", "Domain"
        URL = "url", "URL"
        FILE_HASH = "file_hash", "File Hash"
        EMAIL = "email", "Email"
        CVE = "cve", "CVE ID"

    class ThreatType(models.TextChoices):
        MALWARE = "malware", "Malware"
        C2 = "c2", "C2 Server"
        PHISHING = "phishing", "Phishing"
        BOTNET = "botnet", "Botnet"
        SPAM = "spam", "Spam"
        RANSOMWARE = "ransomware", "Ransomware"
        EXPLOIT = "exploit", "Exploit"
        THREAT_ACTOR = "threat_actor", "Threat Actor"
        UNKNOWN = "unknown", "Unknown"

    class Confidence(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CERTAIN = "certain", "Certain"

    feed = models.ForeignKey(
        ThreatFeed,
        on_delete=models.CASCADE,
        related_name="indicators",
    )

    indicator_type = models.CharField(
        max_length=20,
        choices=IndicatorType.choices,
    )
    indicator_value = models.CharField(max_length=1000)
    normalized_value = models.CharField(max_length=1000, db_index=True)

    threat_type = models.CharField(
        max_length=20,
        choices=ThreatType.choices,
        default=ThreatType.UNKNOWN,
    )

    confidence = models.CharField(
        max_length=20,
        choices=Confidence.choices,
        default=Confidence.MEDIUM,
    )

    title = models.CharField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    tags = models.JSONField(default=list)
    malware_family = models.CharField(max_length=255, blank=True, null=True)
    threat_actor = models.CharField(max_length=255, blank=True, null=True)

    first_seen = models.DateTimeField(null=True, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)

    external_reference = models.URLField(blank=True, null=True)
    external_id = models.CharField(max_length=255, blank=True, null=True)

    raw_data = models.JSONField(default=dict, blank=True)

    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fetched_at"]
        indexes = [
            models.Index(fields=["indicator_type", "normalized_value"]),
            models.Index(fields=["threat_type", "-last_seen"]),
            models.Index(fields=["-confidence"]),
            models.Index(fields=["threat_actor"]),
        ]

    def __str__(self):
        return f"{self.indicator_type}: {self.indicator_value}"


class ThreatMatch(models.Model):
    """
    Matches between threat indicators and reconPoint findings.
    """

    class MatchStatus(models.TextChoices):
        NEW = "new", "New"
        REVIEWED = "reviewed", "Reviewed"
        FALSE_POSITIVE = "false_positive", "False Positive"
        CONFIRMED = "confirmed", "Confirmed"
        MITIGATED = "mitigated", "Mitigated"

    indicator = models.ForeignKey(
        ThreatIndicator,
        on_delete=models.CASCADE,
        related_name="matches",
    )

    matched_type = models.CharField(max_length=50)
    matched_id = models.PositiveIntegerField()
    matched_value = models.CharField(max_length=1000)

    matched_subdomain = models.ForeignKey(
        "startScan.Subdomain",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="threat_matches",
    )
    matched_endpoint = models.ForeignKey(
        "startScan.EndPoint",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="threat_matches",
    )
    matched_ip = models.ForeignKey(
        "startScan.IpAddress",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="threat_matches",
    )

    risk_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    status = models.CharField(
        max_length=20,
        choices=MatchStatus.choices,
        default=MatchStatus.NEW,
    )

    notes = models.TextField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_threat_matches",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-risk_score", "-created_at"]
        indexes = [
            models.Index(fields=["matched_type", "matched_id"]),
            models.Index(fields=["-risk_score", "status"]),
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["reviewed_by", "status"]),
        ]

    def __str__(self):
        return f"{self.matched_value} matched {self.indicator.indicator_value}"

    def mark_false_positive(self, user, notes=None):
        self.status = self.MatchStatus.FALSE_POSITIVE
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        if notes:
            self.notes = notes
        self.save()

    def confirm(self, user, notes=None):
        self.status = self.MatchStatus.CONFIRMED
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        if notes:
            self.notes = notes
        self.save()


class ThreatActor(models.Model):
    """
    Known threat actors and their associated indicators.
    """

    name = models.CharField(max_length=255, unique=True)
    aliases = models.JSONField(default=list)
    description = models.TextField(blank=True, null=True)

    motivation = models.CharField(max_length=255, blank=True, null=True)
    target_sectors = models.JSONField(default=list)
    target_geographies = models.JSONField(default=list)

    associated_malware = models.JSONField(default=list)
    associated_tools = models.JSONField(default=list)

    confidence = models.CharField(
        max_length=20,
        choices=ThreatIndicator.Confidence.choices,
        default=ThreatIndicator.Confidence.MEDIUM,
    )

    external_references = models.JSONField(default=list)

    active_since = models.DateField(null=True, blank=True)
    last_activity = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["-last_activity"]),
        ]

    def __str__(self):
        return self.name


class MalwareSignature(models.Model):
    """
    Malware signatures and patterns for detection.
    """

    name = models.CharField(max_length=255)
    family = models.CharField(max_length=255, blank=True, null=True)

    signature_type = models.CharField(max_length=50)
    pattern = models.TextField()
    pattern_type = models.CharField(
        max_length=20,
        choices=[
            ("yara", "YARA"),
            ("regex", "Regex"),
            ("hash", "Hash"),
            ("behavior", "Behavior"),
        ],
        default="yara",
    )

    severity = models.CharField(
        max_length=20,
        choices=[
            ("critical", "Critical"),
            ("high", "High"),
            ("medium", "Medium"),
            ("low", "Low"),
        ],
        default="high",
    )

    description = models.TextField(blank=True, null=True)
    references = models.JSONField(default=list)

    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-severity", "name"]

    def __str__(self):
        return f"{self.name} ({self.family or 'Unknown'})"
