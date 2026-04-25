"""
Vulnerability correlation and attack chain analysis services.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from reconPoint.utilities.logger import get_module_logger
from startScan.models import Vulnerability


PREFIX_VULN = "[VULN_CORR]"
logger = get_module_logger(__name__)


@dataclass
class VulnerabilityNode:
    """Node in attack chain graph."""

    id: int
    name: str
    severity: int
    cvss_score: float
    template: str
    endpoint: Optional[str] = None
    discovered_at: Optional[datetime] = None
    relations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AttackChainResult:
    """Result of attack chain analysis."""

    chains: List[Dict[str, Any]]
    critical_paths: List[List[int]]
    highest_risk_score: float
    total_vulnerabilities_analyzed: int
    attack_surface_reduction: Dict[str, Any]


class VulnerabilityCorrelator:
    """
    Analyzes vulnerability relationships and generates attack chains.
    """

    SEVERITY_WEIGHTS = {
        "critical": 10,
        "high": 7,
        "medium": 4,
        "low": 1,
        "info": 0,
    }

    RELATION_WEIGHTS = {
        "causes": 0.9,
        "enables": 0.85,
        "escalates": 0.8,
        "leads_to": 0.75,
        "prerequisite": 0.7,
        "related": 0.3,
    }

    def __init__(self, target_id: int):
        self.target_id = target_id
        self.vulnerabilities: List[Vulnerability] = []
        self.relations: Dict[int, List[Dict]] = defaultdict(list)
        self.graph: Dict[int, List[int]] = defaultdict(list)

    def load_vulnerabilities(self) -> int:
        """Load all vulnerabilities for the target."""
        self.vulnerabilities = list(
            Vulnerability.objects.filter(
                scan_history__target_id=self.target_id,
                open_status=True,
            )
            .select_related("scan_history")
            .prefetch_related("endpoints")
        )
        return len(self.vulnerabilities)

    def build_dependency_graph(self) -> None:
        """Build the vulnerability dependency graph."""
        from .models_vuln_correlation import VulnerabilityRelation

        relation_objects = VulnerabilityRelation.objects.filter(
            parent__scan_history__target_id=self.target_id
        ).select_related("parent", "child")

        for rel in relation_objects:
            self.relations[rel.parent_id].append(
                {
                    "child_id": rel.child_id,
                    "type": rel.relation_type,
                    "confidence": float(rel.confidence),
                    "evidence": rel.evidence,
                }
            )
            self.graph[rel.parent_id].append(rel.child_id)

    def detect_attack_chains(self) -> AttackChainResult:
        """
        Detect attack chains using graph traversal.
        Identifies paths from entry points to critical assets.
        """
        chains = []
        critical_paths = []
        visited_paths: Set[Tuple[int, ...]] = set()

        entry_points = self._find_entry_points()
        critical_nodes = self._find_critical_nodes()

        for entry_id in entry_points:
            for critical_id in critical_nodes:
                paths = self._find_all_paths(entry_id, critical_id)
                for path in paths:
                    path_key = tuple(path)
                    if path_key not in visited_paths:
                        visited_paths.add(path_key)
                        chain_risk = self._calculate_chain_risk(path)
                        chains.append(
                            {
                                "path": path,
                                "risk_score": chain_risk,
                                "entry_point": entry_id,
                                "critical_target": critical_id,
                                "length": len(path),
                            }
                        )

                        if len(path) >= 2:
                            critical_paths.append(path)

        chains.sort(key=lambda x: x["risk_score"], reverse=True)

        return AttackChainResult(
            chains=chains,
            critical_paths=critical_paths,
            highest_risk_score=chains[0]["risk_score"] if chains else 0,
            total_vulnerabilities_analyzed=len(self.vulnerabilities),
            attack_surface_reduction=self._calculate_attack_surface_reduction(chains),
        )

    def _find_entry_points(self) -> List[int]:
        """Find vulnerabilities that could be entry points for attacks."""
        entry_points = []

        for vuln in self.vulnerabilities:
            if self._is_entry_point(vuln):
                entry_points.append(vuln.id)

        return entry_points

    def _is_entry_point(self, vuln: Vulnerability) -> bool:
        """Check if vulnerability is an entry point."""
        has_no_dependencies = not self.relations.get(vuln.id)
        is_external = "xss" in vuln.name.lower() or "ssrf" in vuln.name.lower()
        is_info_disclosure = "disclosure" in vuln.name.lower() or "info" in vuln.severity.lower()
        return has_no_dependencies or is_external or is_info_disclosure

    def _find_critical_nodes(self) -> List[int]:
        """Find vulnerabilities that lead to critical assets."""
        critical = []

        for vuln in self.vulnerabilities:
            if self._is_critical(vuln):
                critical.append(vuln.id)

        return critical

    def _is_critical(self, vuln: Vulnerability) -> bool:
        """Check if vulnerability is critical."""
        is_high_severity = vuln.severity in ["critical", "high"]
        is_privileged = "admin" in vuln.name.lower() or "privilege" in vuln.name.lower()
        is_data_exposure = "data" in vuln.name.lower() or "database" in vuln.name.lower()
        return is_high_severity or is_privileged or is_data_exposure

    def _find_all_paths(
        self,
        start: int,
        end: int,
        max_depth: int = 10,
    ) -> List[List[int]]:
        """Find all paths between two nodes."""
        paths = []
        stack = [(start, [start])]
        visited_in_path: Set[int] = set()

        while stack:
            node, path = stack.pop()

            if len(path) > max_depth:
                continue

            if node == end:
                paths.append(path)
                continue

            visited_in_path.update(path)

            for neighbor in self.graph.get(node, []):
                if neighbor not in visited_in_path or neighbor == end:
                    stack.append((neighbor, path + [neighbor]))

        return paths

    def _calculate_chain_risk(self, path: List[int]) -> float:
        """Calculate risk score for an attack chain path."""
        if not path:
            return 0

        vuln_map = {v.id: v for v in self.vulnerabilities}

        chain_risk = 0.0
        for vuln_id in path:
            vuln = vuln_map.get(vuln_id)
            if not vuln:
                continue

            severity_weight = self.SEVERITY_WEIGHTS.get(vuln.severity.lower(), 0)

            cvss_contribution = float(vuln.cvss_score or 0) * 10

            chain_risk += severity_weight + cvss_contribution

        chain_risk *= 1 + (len(path) - 1) * 0.1

        return min(chain_risk, 100)

    def _calculate_attack_surface_reduction(
        self,
        chains: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculate attack surface reduction recommendations."""
        vulnerable_paths = len(chains)

        if not chains:
            return {
                "total_chains": 0,
                "critical_chains": 0,
                "blocking_points": [],
                "recommended_fixes": [],
            }

        blocking_points: Dict[int, int] = defaultdict(int)

        for chain in chains:
            for vuln_id in chain["path"][:-1]:
                blocking_points[vuln_id] += 1

        sorted_blocking = sorted(
            blocking_points.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        recommended_fixes = []
        for vuln_id, block_count in sorted_blocking[:5]:
            vuln = next((v for v in self.vulnerabilities if v.id == vuln_id), None)
            if vuln:
                recommended_fixes.append(
                    {
                        "vulnerability_id": vuln_id,
                        "name": vuln.name,
                        "severity": vuln.severity,
                        "blocks_chains": block_count,
                        "priority": "high" if block_count > 5 else "medium",
                    }
                )

        critical_chains = sum(1 for c in chains if c["risk_score"] > 70)

        return {
            "total_chains": vulnerable_paths,
            "critical_chains": critical_chains,
            "blocking_points": [{"vulnerability_id": v[0], "blocks": v[1]} for v in sorted_blocking[:10]],
            "recommended_fixes": recommended_fixes,
        }

    def get_vulnerability_graph(self) -> Dict[str, Any]:
        """Get graph data for visualization."""
        nodes = []
        edges = []

        for vuln in self.vulnerabilities:
            nodes.append(
                {
                    "id": vuln.id,
                    "name": vuln.name,
                    "severity": vuln.severity,
                    "cvss": float(vuln.cvss_score or 0),
                    "template": vuln.template,
                    "url": vuln.endpoint,
                }
            )

        for parent_id, relations in self.relations.items():
            for rel in relations:
                edges.append(
                    {
                        "source": parent_id,
                        "target": rel["child_id"],
                        "type": rel["type"],
                        "confidence": rel["confidence"],
                    }
                )

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_vulnerabilities": len(self.vulnerabilities),
                "total_relations": sum(len(r) for r in self.relations.values()),
            },
        }


class RemediationPriorityQueue:
    """
    Prioritizes remediation based on exploitability and attack chains.
    """

    def __init__(self, target_id: int):
        self.target_id = target_id
        self.correlator = VulnerabilityCorrelator(target_id)

    def get_prioritized_list(self) -> List[Dict[str, Any]]:
        """Get vulnerabilities prioritized by remediation importance."""
        self.correlator.load_vulnerabilities()
        self.correlator.build_dependency_graph()

        chain_result = self.correlator.detect_attack_chains()
        blocking_map = {
            bp["vulnerability_id"]: bp["blocks"]
            for bp in chain_result.attack_surface_reduction.get("blocking_points", [])
        }

        prioritized = []

        for vuln in self.correlator.vulnerabilities:
            blocking_count = blocking_map.get(vuln.id, 0)

            exploitability = self._calculate_exploitability(vuln)

            priority_score = (
                self.correlator.SEVERITY_WEIGHTS.get(vuln.severity.lower(), 0) * 10
                + exploitability * 20
                + blocking_count * 5
            )

            prioritized.append(
                {
                    "id": vuln.id,
                    "name": vuln.name,
                    "severity": vuln.severity,
                    "cvss_score": float(vuln.cvss_score or 0),
                    "template": vuln.template,
                    "priority_score": priority_score,
                    "exploitability": exploitability,
                    "blocks_attack_chains": blocking_count,
                    "estimated_fix_time": self._estimate_fix_time(vuln),
                    "in_attack_chain": blocking_count > 0,
                }
            )

        prioritized.sort(key=lambda x: x["priority_score"], reverse=True)

        return prioritized

    def _calculate_exploitability(self, vuln: Vulnerability) -> float:
        """Calculate exploitability score (0-1)."""
        base_score = 0.5

        if "remote" in vuln.name.lower():
            base_score += 0.2
        if "auth" in vuln.name.lower():
            base_score += 0.1
        if "inject" in vuln.name.lower():
            base_score += 0.15
        if "exec" in vuln.name.lower():
            base_score += 0.25
        if "default" in vuln.name.lower():
            base_score += 0.15

        return min(base_score, 1.0)

    def _estimate_fix_time(self, vuln: Vulnerability) -> str:
        """Estimate time to fix vulnerability."""
        severity = vuln.severity.lower()
        name_lower = vuln.name.lower()

        if severity == "critical":
            base_time = 240
        elif severity == "high":
            base_time = 120
        elif severity == "medium":
            base_time = 60
        else:
            base_time = 30

        if "config" in name_lower:
            base_time = base_time // 2
        if "code" in name_lower or "inject" in name_lower:
            base_time = base_time * 2

        if base_time < 60:
            return f"{base_time} minutes"
        elif base_time < 240:
            hours = base_time // 60
            return f"{hours} hour{'s' if hours > 1 else ''}"
        else:
            days = base_time // 480
            return f"{days} day{'s' if days > 1 else ''}"


class VulnerabilityDeduplicator:
    """
    Deduplicates vulnerabilities across different scanners.
    """

    SIMILARITY_THRESHOLD = 0.8

    def __init__(self, target_id: int):
        self.target_id = target_id

    def find_duplicates(self) -> List[Dict[str, Any]]:
        """Find duplicate vulnerabilities."""
        vulnerabilities = Vulnerability.objects.filter(
            scan_history__target_id=self.target_id,
        ).select_related("scan_history")

        duplicates: List[Dict[str, Any]] = []
        canonical_map: Dict[str, int] = {}
        processed: Set[int] = set()

        for vuln in vulnerabilities:
            if vuln.id in processed:
                continue

            canonical_key = self._get_canonical_key(vuln)

            if canonical_key in canonical_map:
                canonical_vuln_id = canonical_map[canonical_key]
                if canonical_vuln_id != vuln.id:
                    duplicates.append(
                        {
                            "canonical_id": canonical_vuln_id,
                            "duplicate_id": vuln.id,
                            "canonical_name": vuln.name,
                            "similarity": 1.0,
                        }
                    )
            else:
                canonical_map[canonical_key] = vuln.id

            processed.add(vuln.id)

        return duplicates

    def _get_canonical_key(self, vuln: Vulnerability) -> str:
        """Generate canonical key for deduplication."""
        name_lower = vuln.name.lower()
        template_lower = (vuln.template or "").lower()
        return f"{name_lower}|{template_lower}"
