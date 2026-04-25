"""
Threat Intelligence service for integrating external feeds.
"""

from dataclasses import dataclass
from datetime import datetime
import hashlib
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from django.utils import timezone
import requests

from reconPoint.utilities.logger import get_module_logger


PREFIX_THREAT = "[THREAT_INTEL]"
logger = get_module_logger(__name__)


@dataclass
class FeedSyncResult:
    """Result of a threat feed sync operation."""

    success: bool
    indicators_added: int
    indicators_updated: int
    errors: List[str]
    duration_seconds: float


@dataclass
class ThreatMatchResult:
    """Result of threat indicator matching."""

    matched: bool
    indicator_id: Optional[int]
    indicator_value: Optional[str]
    threat_type: Optional[str]
    confidence: Optional[str]
    risk_score: float
    context: Dict[str, Any]


class ThreatFeedIntegrator:
    """
    Integrator for external threat intelligence feeds.
    """

    FEED_CONFIGS = {
        "abuse_ch": {
            "name": "ABUSE.ch",
            "api_endpoint": "https://api.abuse.ch/api/v1/",
            "indicator_types": ["ip", "domain", "url"],
            "requires_api_key": False,
        },
        "shodan": {
            "name": "Shodan",
            "api_endpoint": "https://api.shodan.io",
            "indicator_types": ["ip"],
            "requires_api_key": True,
        },
        "alienvault": {
            "name": "AlienVault OTX",
            "api_endpoint": "https://otx.alienvault.com/api/v1",
            "indicator_types": ["ip", "domain", "url", "file_hash"],
            "requires_api_key": True,
        },
        "virustotal": {
            "name": "VirusTotal",
            "api_endpoint": "https://www.virustotal.com/api/v3",
            "indicator_types": ["ip", "domain", "url", "file_hash"],
            "requires_api_key": True,
        },
        "threatfox": {
            "name": "THREATFOX",
            "api_endpoint": "https://api.threatfox.xyz/api/v1/",
            "indicator_types": ["ip", "domain", "url", "file_hash"],
            "requires_api_key": False,
        },
        "urlhaus": {
            "name": "URLhaus",
            "api_endpoint": "https://urlhaus-api.abuse.ch/api/v1/",
            "indicator_types": ["url", "domain"],
            "requires_api_key": False,
        },
        "malware_bazaar": {
            "name": "MalwareBazaar",
            "api_endpoint": "https://mb-api.abuse.ch/api/v1/",
            "indicator_types": ["file_hash"],
            "requires_api_key": False,
        },
    }

    def __init__(self, feed_model):
        self.feed = feed_model
        self.source = feed_model.source
        self.config = self.FEED_CONFIGS.get(self.source, {})

    def sync(self) -> FeedSyncResult:
        """Sync indicators from the threat feed."""
        import time

        start_time = time.time()

        if not self.feed.is_enabled:
            return FeedSyncResult(False, 0, 0, ["Feed is disabled"], 0)

        errors = []
        added = 0
        updated = 0

        try:
            if self.source == "abuse_ch":
                added, updated, errors = self._sync_abuse_ch()
            elif self.source == "shodan":
                added, updated, errors = self._sync_shodan()
            elif self.source == "alienvault":
                added, updated, errors = self._sync_alienvault()
            elif self.source == "virustotal":
                added, updated, errors = self._sync_virustotal()
            elif self.source == "threatfox":
                added, updated, errors = self._sync_threatfox()
            elif self.source == "urlhaus":
                added, updated, errors = self._sync_urlhaus()
            elif self.source == "malware_bazaar":
                added, updated, errors = self._sync_malware_bazaar()

            self.feed.sync_status = "success"
            self.feed.last_sync_at = timezone.now()
            self.feed.last_indicators_count = self.feed.indicators_count
            self.feed.indicators_count += added

        except Exception as e:
            errors.append(str(e))
            self.feed.sync_status = "failed"
            self.feed.last_sync_error = str(e)

        self.feed.save()
        duration = time.time() - start_time

        return FeedSyncResult(
            success=len(errors) == 0,
            indicators_added=added,
            indicators_updated=updated,
            errors=errors,
            duration_seconds=duration,
        )

    def _sync_abuse_ch(self) -> Tuple[int, int, List[str]]:
        """Sync from ABUSE.ch (IOCYARA / URLhaus)."""
        from .models_threat_intel import ThreatIndicator

        added = 0
        updated = 0
        errors = []

        try:
            response = requests.post(
                f"{self.config['api_endpoint']}ioc_search/",
                data={"json": 1},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("query_status") == "ok":
                for ioc in data.get("data", []):
                    indicator = self._create_or_update_indicator(
                        ThreatIndicator,
                        ioc,
                        "abuse_ch",
                    )
                    if indicator:
                        added += 1

        except Exception as e:
            errors.append(f"ABUSE.ch sync failed: {e}")

        return added, updated, errors

    def _sync_shodan(self) -> Tuple[int, int, List[str]]:
        """Sync from Shodan."""
        return 0, 0, []

    def _sync_alienvault(self) -> Tuple[int, int, List[str]]:
        """Sync from AlienVault OTX."""
        return 0, 0, []

    def _sync_virustotal(self) -> Tuple[int, int, List[str]]:
        """Sync from VirusTotal."""
        return 0, 0, []

    def _sync_threatfox(self) -> Tuple[int, int, List[str]]:
        """Sync from THREATFOX."""
        from .models_threat_intel import ThreatIndicator

        added = 0
        updated = 0
        errors = []

        try:
            response = requests.post(
                f"{self.config['api_endpoint']}query/samples/latest",
                data={"json": 1, "limit": 1000},
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("query_status") == "ok":
                for sample in data.get("data", []):
                    indicator = self._create_or_update_indicator(
                        ThreatIndicator,
                        sample,
                        "threatfox",
                    )
                    if indicator:
                        added += 1

        except Exception as e:
            errors.append(f"THREATFOX sync failed: {e}")

        return added, updated, errors

    def _sync_urlhaus(self) -> Tuple[int, int, List[str]]:
        """Sync from URLhaus."""
        from .models_threat_intel import ThreatIndicator

        added = 0
        updated = 0
        errors = []

        try:
            response = requests.get(
                f"{self.config['api_endpoint']}recent/100/json/",
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            for entry in data:
                indicator = self._create_or_update_indicator(
                    ThreatIndicator,
                    entry,
                    "urlhaus",
                )
                if indicator:
                    added += 1

        except Exception as e:
            errors.append(f"URLhaus sync failed: {e}")

        return added, updated, errors

    def _sync_malware_bazaar(self) -> Tuple[int, int, List[str]]:
        """Sync from MalwareBazaar."""
        return 0, 0, []

    def _create_or_update_indicator(self, model, data: dict, source: str):
        """Create or update a threat indicator."""
        indicator_value = data.get("ioc_value") or data.get("url") or data.get("domain") or ""
        if not indicator_value:
            return None

        indicator_type = self._determine_indicator_type(indicator_value)

        obj, created = model.objects.update_or_create(
            feed=self.feed,
            indicator_type=indicator_type,
            indicator_value=indicator_value,
            defaults={
                "normalized_value": self._normalize_indicator(indicator_value),
                "threat_type": self._map_threat_type(data.get("malware_type") or data.get("threat_type")),
                "confidence": self._map_confidence(data.get("confidence")),
                "title": data.get("description") or data.get("threat"),
                "tags": data.get("tags", []),
                "malware_family": data.get("malware_family") or data.get("signature"),
                "last_seen": self._parse_date(data.get("date_added") or data.get("last_online")),
                "raw_data": data,
            },
        )
        return obj

    def _determine_indicator_type(self, value: str) -> str:
        """Determine indicator type from value."""
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", value):
            return "ip"
        if re.match(r"^[a-fA-F0-9]{32}$|^[a-fA-F0-9]{40}$|^[a-fA-F0-9]{64}$", value):
            return "file_hash"
        if value.startswith(("http://", "https://")):
            return "url"
        if "@" in value:
            return "email"
        return "domain"

    def _normalize_indicator(self, value: str) -> str:
        """Normalize indicator value for matching."""
        value = value.lower().strip()
        if value.startswith(("http://", "https://")):
            parsed = urlparse(value)
            value = parsed.netloc
        if value.startswith("www."):
            value = value[4:]
        return hashlib.md5(value.encode()).hexdigest()

    def _map_threat_type(self, raw_type: str) -> str:
        """Map raw threat type to standard type."""
        if not raw_type:
            return "unknown"
        raw = raw_type.lower()
        if "malware" in raw or "virus" in raw:
            return "malware"
        if "phish" in raw:
            return "phishing"
        if "botnet" in raw:
            return "botnet"
        if "spam" in raw:
            return "spam"
        if "c2" in raw or "command" in raw:
            return "c2"
        if "ransom" in raw:
            return "ransomware"
        return "unknown"

    def _map_confidence(self, raw_confidence: str) -> str:
        """Map raw confidence to standard."""
        if not raw_confidence:
            return "medium"
        raw = str(raw_confidence).lower()
        if raw in ["high", "100", "90"]:
            return "high"
        if raw in ["medium", "70", "50"]:
            return "medium"
        if raw in ["low", "30", "20"]:
            return "low"
        return "medium"

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None


class ThreatMatcher:
    """
    Matches threat indicators against reconPoint findings.
    """

    def __init__(self, target_id: int):
        self.target_id = target_id

    def check_ip(self, ip_address: str) -> ThreatMatchResult:
        """Check if IP matches any threat indicators."""
        return self._check_indicator(ip_address, "ip")

    def check_domain(self, domain: str) -> ThreatMatchResult:
        """Check if domain matches any threat indicators."""
        normalized = hashlib.md5(domain.lower().encode()).hexdigest()
        return self._check_indicator(domain, "domain", normalized)

    def check_url(self, url: str) -> ThreatMatchResult:
        """Check if URL matches any threat indicators."""
        return self._check_indicator(url, "url", hashlib.md5(url.lower().encode()).hexdigest())

    def check_hash(self, file_hash: str) -> ThreatMatchResult:
        """Check if file hash matches any threat indicators."""
        return self._check_indicator(file_hash, "file_hash")

    def _check_indicator(
        self,
        value: str,
        indicator_type: str,
        normalized_value: str = None,
    ) -> ThreatMatchResult:
        """Check a single indicator against threat feeds."""
        from .models_threat_intel import ThreatIndicator

        query = ThreatIndicator.objects.filter(
            indicator_type=indicator_type,
            feed__is_enabled=True,
        )

        if normalized_value:
            query = query.filter(normalized_value=normalized_value)
        else:
            query = query.filter(indicator_value=value)

        indicator = query.first()

        if not indicator:
            return ThreatMatchResult(
                matched=False,
                indicator_id=None,
                indicator_value=None,
                threat_type=None,
                confidence=None,
                risk_score=0,
                context={},
            )

        risk_score = self._calculate_risk_score(indicator)

        return ThreatMatchResult(
            matched=True,
            indicator_id=indicator.id,
            indicator_value=indicator.indicator_value,
            threat_type=indicator.threat_type,
            confidence=indicator.confidence,
            risk_score=risk_score,
            context={
                "title": indicator.title,
                "description": indicator.description,
                "malware_family": indicator.malware_family,
                "threat_actor": indicator.threat_actor,
                "tags": indicator.tags,
                "last_seen": indicator.last_seen.isoformat() if indicator.last_seen else None,
            },
        )

    def _calculate_risk_score(self, indicator) -> float:
        """Calculate risk score for an indicator match."""
        base_score = 0

        confidence_map = {"certain": 40, "high": 30, "medium": 20, "low": 10}
        base_score += confidence_map.get(indicator.confidence, 0)

        threat_map = {
            "c2": 30,
            "ransomware": 25,
            "malware": 20,
            "exploit": 20,
            "botnet": 15,
            "phishing": 10,
            "spam": 5,
        }
        base_score += threat_map.get(indicator.threat_type, 0)

        if indicator.last_seen:
            days_since = (timezone.now() - indicator.last_seen).days
            if days_since < 7:
                base_score += 10
            elif days_since < 30:
                base_score += 5

        return min(base_score, 100)

    def scan_target(self) -> List[ThreatMatchResult]:
        """Scan all findings in a target for threat matches."""
        from startScan.models import IpAddress, Subdomain

        matches = []

        ips = IpAddress.objects.filter(scan_history__target_id=self.target_id)
        for ip in ips:
            result = self.check_ip(ip.address)
            if result.matched:
                result.context["finding_type"] = "ip"
                result.context["finding_id"] = ip.id
                matches.append(result)

        subdomains = Subdomain.objects.filter(scan_history__target_id=self.target_id)
        for subdomain in subdomains:
            result = self.check_domain(subdomain.name)
            if result.matched:
                result.context["finding_type"] = "subdomain"
                result.context["finding_id"] = subdomain.id
                matches.append(result)

        return matches


def sync_all_feeds():
    """Sync all enabled threat feeds."""
    from .models_threat_intel import ThreatFeed

    feeds = ThreatFeed.objects.filter(is_enabled=True)
    results = []

    for feed in feeds:
        integrator = ThreatFeedIntegrator(feed)
        result = integrator.sync()
        results.append(
            {
                "feed": feed.name,
                "result": result,
            }
        )

    return results
