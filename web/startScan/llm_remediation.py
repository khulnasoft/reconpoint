"""
LLM-powered remediation suggestions service.
"""

from dataclasses import dataclass
from typing import Any, Dict, List

from reconPoint.llm.utils import get_llm_config
from reconPoint.utilities.logger import get_module_logger


PREFIX_LLM = "[LLM_REMED]"
logger = get_module_logger(__name__)


@dataclass
class RemediationSuggestion:
    """LLM-generated remediation suggestion."""

    title: str
    description: str
    steps: List[str]
    effort_estimate: str
    priority: str
    confidence: float
    references: List[Dict[str, str]]


class LLMRemediationEngine:
    """
    Uses LLM to generate remediation suggestions for vulnerabilities.
    """

    SYSTEM_PROMPT = """You are a security expert specializing in vulnerability remediation.
Given a vulnerability description, provide actionable remediation steps.
Consider:
- Root cause analysis
- Fix implementation steps (code changes, config updates)
- Testing recommendations
- Prevention measures

Respond with structured JSON containing:
- title: Brief fix title
- description: Detailed explanation
- steps: Ordered list of fix steps
- effort_estimate: Time estimate (e.g., "2 hours", "1 day")
- priority: critical/high/medium/low
- confidence: How confident you are (0-1)
- references: Useful links or documentation
"""

    def __init__(self):
        self.llm_config = get_llm_config() if hasattr(__import__("reconPoint.llm.utils"), "get_llm_config") else {}

    def generate_remediation(
        self,
        vulnerability_name: str,
        vulnerability_description: str,
        severity: str,
        cvss_score: float = None,
        template: str = None,
        endpoint: str = None,
    ) -> RemediationSuggestion:
        """
        Generate remediation suggestion for a vulnerability.
        """
        user_prompt = self._build_prompt(
            vulnerability_name,
            vulnerability_description,
            severity,
            cvss_score,
            template,
            endpoint,
        )

        try:
            response = self._call_llm(user_prompt)
            return self._parse_response(response)
        except Exception as e:
            logger.log_line(
                PREFIX_LLM,
                "GENERATE",
                f"Failed to generate remediation: {e}",
                level="error",
            )
            return self._fallback_suggestion(vulnerability_name, severity)

    def _build_prompt(
        self,
        name: str,
        description: str,
        severity: str,
        cvss_score: float,
        template: str,
        endpoint: str,
    ) -> str:
        """Build the prompt for LLM."""
        prompt_parts = [
            f"Vulnerability: {name}",
            f"Severity: {severity}",
        ]

        if cvss_score:
            prompt_parts.append(f"CVSS Score: {cvss_score}")

        if template:
            prompt_parts.append(f"Template: {template}")

        if endpoint:
            prompt_parts.append(f"Affected Endpoint: {endpoint}")

        if description:
            prompt_parts.append(f"Description: {description}")

        prompt_parts.append("\nProvide remediation steps in JSON format.")

        return "\n\n".join(prompt_parts)

    def _call_llm(self, prompt: str) -> str:
        """Call LLM for remediation generation."""
        from llm import LLMResponse

        llm = self.llm_config.get("llm_instance")
        if not llm:
            raise ValueError("LLM not configured")

        response: LLMResponse = llm.chat(
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        return response.content

    def _parse_response(self, response: str) -> RemediationSuggestion:
        """Parse LLM response into structured suggestion."""
        import json
        import re

        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return RemediationSuggestion(
                    title=data.get("title", "Remediation"),
                    description=data.get("description", ""),
                    steps=data.get("steps", []),
                    effort_estimate=data.get("effort_estimate", "1 hour"),
                    priority=data.get("priority", "medium"),
                    confidence=data.get("confidence", 0.8),
                    references=[
                        {"title": r.get("title", ""), "url": r.get("url", "")} for r in data.get("references", [])
                    ],
                )
            except json.JSONDecodeError:
                pass

        return self._fallback_suggestion_from_text(response)

    def _fallback_suggestion(
        self,
        name: str,
        severity: str,
    ) -> RemediationSuggestion:
        """Generate fallback suggestion based on severity."""
        effort_map = {
            "critical": "4 hours",
            "high": "2 hours",
            "medium": "1 hour",
            "low": "30 minutes",
            "info": "15 minutes",
        }

        priority_map = {
            "critical": "critical",
            "high": "high",
            "medium": "medium",
            "low": "low",
            "info": "info",
        }

        return RemediationSuggestion(
            title=f"Fix {name}",
            description=f"Implement security fix for {name}",
            steps=[
                "Review vulnerability details",
                "Implement fix according to security best practices",
                "Test the fix in staging environment",
                "Deploy to production",
                "Verify fix effectiveness",
            ],
            effort_estimate=effort_map.get(severity.lower(), "1 hour"),
            priority=priority_map.get(severity.lower(), "medium"),
            confidence=0.5,
            references=[],
        )

    def _fallback_suggestion_from_text(
        self,
        text: str,
    ) -> RemediationSuggestion:
        """Create suggestion from unstructured LLM text."""
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        return RemediationSuggestion(
            title=lines[0] if lines else "Remediation",
            description="\n".join(lines[1:5]) if len(lines) > 1 else "",
            steps=lines[5:] if len(lines) > 5 else ["Review and implement fix"],
            effort_estimate="1 hour",
            priority="medium",
            confidence=0.6,
            references=[],
        )


class BatchRemediationGenerator:
    """
    Generate remediations for multiple vulnerabilities at once.
    """

    def __init__(self, batch_size: int = 5):
        self.batch_size = batch_size
        self.engine = LLMRemediationEngine()

    def generate_batch(
        self,
        vulnerabilities: List[Dict[str, Any]],
    ) -> List[RemediationSuggestion]:
        """Generate remediations for a batch of vulnerabilities."""
        results = []

        for vuln in vulnerabilities:
            try:
                suggestion = self.engine.generate_remediation(
                    vulnerability_name=vuln.get("name", ""),
                    vulnerability_description=vuln.get("description", ""),
                    severity=vuln.get("severity", "medium"),
                    cvss_score=vuln.get("cvss_score"),
                    template=vuln.get("template"),
                    endpoint=vuln.get("endpoint"),
                )
                results.append(suggestion)
            except Exception as e:
                logger.log_line(
                    PREFIX_LLM,
                    "BATCH",
                    f"Failed to generate for {vuln.get('name')}: {e}",
                    level="error",
                )
                results.append(
                    self.engine._fallback_suggestion(
                        vuln.get("name", "Unknown"),
                        vuln.get("severity", "medium"),
                    )
                )

        return results


def get_llm_remediation_for_vulnerability(vulnerability) -> RemediationSuggestion:
    """
    Convenience function to get LLM remediation for a vulnerability model.
    """
    engine = LLMRemediationEngine()

    return engine.generate_remediation(
        vulnerability_name=vulnerability.name,
        vulnerability_description=vulnerability.description or "",
        severity=vulnerability.severity,
        cvss_score=float(vulnerability.cvss_score) if vulnerability.cvss_score else None,
        template=vulnerability.template,
        endpoint=vulnerability.endpoint,
    )
