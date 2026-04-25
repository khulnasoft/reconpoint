"""
Ticketing integration service for external issue tracking.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

from reconPoint.utilities.logger import get_module_logger


PREFIX_TICKET = "[TICKET]"
logger = get_module_logger(__name__)


@dataclass
class TicketResult:
    """Result of ticket creation/update."""

    success: bool
    ticket_id: Optional[str] = None
    ticket_url: Optional[str] = None
    error: Optional[str] = None


class JiraIntegration:
    """Jira ticketing integration."""

    def __init__(self, integration):
        self.integration = integration
        self.config = integration.config
        self.url = self.config.get("url")
        self.username = self.config.get("username")
        self.api_token = self.config.get("api_token")

    def _get_auth(self):
        import requests.auth

        return requests.auth.HTTPBasicAuth(self.username, self.api_token)

    def create_ticket(
        self,
        summary: str,
        description: str,
        priority: str = None,
        assignee: str = None,
        labels: List[str] = None,
        vulnerability_id: int = None,
    ) -> TicketResult:
        """Create a ticket in Jira."""
        try:
            project_key = self.integration.default_project or "SEC"
            issue_type = self.integration.default_issue_type or "Bug"
            priority_id = self._map_priority_to_jira(priority)

            payload = {
                "fields": {
                    "project": {"key": project_key},
                    "summary": summary[:255],
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [{"type": "paragraph", "content": [{"type": "text", "text": description[:32000]}]}],
                    },
                    "issuetype": {"name": issue_type},
                }
            }

            if priority_id:
                payload["fields"]["priority"] = {"id": priority_id}
            if assignee:
                payload["fields"]["assignee"] = {"name": assignee}
            if labels:
                payload["fields"]["labels"] = labels

            response = requests.post(
                f"{self.url}/rest/api/3/issue",
                json=payload,
                auth=self._get_auth(),
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            ticket_key = data.get("key")
            return TicketResult(
                success=True,
                ticket_id=ticket_key,
                ticket_url=f"{self.url}/browse/{ticket_key}",
            )

        except Exception as e:
            logger.log_line(PREFIX_TICKET, "JIRA_CREATE", f"Failed: {e}", level="error")
            return TicketResult(success=False, error=str(e))

    def update_ticket(
        self,
        ticket_id: str,
        status: str = None,
        comment: str = None,
    ) -> TicketResult:
        """Update a ticket in Jira."""
        try:
            if status:
                transitions = self._get_available_transitions(ticket_id)
                transition_id = transitions.get(status.lower())
                if transition_id:
                    requests.post(
                        f"{self.url}/rest/api/3/issue/{ticket_id}/transitions",
                        json={"transition": {"id": transition_id}},
                        auth=self._get_auth(),
                        timeout=10,
                    )

            if comment:
                requests.post(
                    f"{self.url}/rest/api/3/issue/{ticket_id}/comment",
                    json={
                        "body": {
                            "type": "doc",
                            "content": [{"type": "paragraph", "content": [{"type": "text", "text": comment}]}],
                        }
                    },
                    auth=self._get_auth(),
                    timeout=10,
                )

            return TicketResult(success=True, ticket_id=ticket_id)

        except Exception as e:
            return TicketResult(success=False, error=str(e))

    def _get_available_transitions(self, ticket_id: str) -> Dict[str, str]:
        """Get available transitions for a ticket."""
        try:
            response = requests.get(
                f"{self.url}/rest/api/3/issue/{ticket_id}/transitions",
                auth=self._get_auth(),
                timeout=10,
            )
            transitions = response.json().get("transitions", [])
            return {t.get("to", {}).get("name", "").lower(): str(t.get("id")) for t in transitions}
        except Exception:
            return {}

    def _map_priority_to_jira(self, priority: str) -> Optional[str]:
        """Map reconPoint priority to Jira priority ID."""
        if not priority:
            return None
        priority_map = {"highest": "1", "high": "2", "medium": "3", "low": "4", "lowest": "5"}
        return priority_map.get(priority.lower())


class GitHubIntegration:
    """GitHub Issues ticketing integration."""

    def __init__(self, integration):
        self.integration = integration
        self.config = integration.config
        self.repo = self.config.get("repo")
        self.token = self.config.get("token")

    def _get_headers(self):
        return {
            "Authorization": f"Token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def create_ticket(
        self,
        summary: str,
        description: str,
        priority: str = None,
        labels: List[str] = None,
        vulnerability_id: int = None,
    ) -> TicketResult:
        """Create a GitHub issue."""
        try:
            payload = {
                "title": summary[:255],
                "body": description[:65536],
                "labels": labels or [],
            }

            if priority:
                priority_labels = {"critical": "critical", "high": "high-priority", "medium": "medium-priority"}
                if priority.lower() in priority_labels:
                    payload["labels"].append(priority_labels[priority.lower()])

            response = requests.post(
                f"https://api.github.com/repos/{self.repo}/issues",
                json=payload,
                headers=self._get_headers(),
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            return TicketResult(
                success=True,
                ticket_id=str(data.get("number")),
                ticket_url=data.get("html_url"),
            )

        except Exception as e:
            logger.log_line(PREFIX_TICKET, "GITHUB_CREATE", f"Failed: {e}", level="error")
            return TicketResult(success=False, error=str(e))

    def update_ticket(
        self,
        ticket_id: str,
        status: str = None,
        comment: str = None,
    ) -> TicketResult:
        """Update a GitHub issue."""
        try:
            if comment:
                requests.post(
                    f"https://api.github.com/repos/{self.repo}/issues/{ticket_id}/comments",
                    json={"body": comment},
                    headers=self._get_headers(),
                    timeout=10,
                )

            return TicketResult(success=True, ticket_id=ticket_id)

        except Exception as e:
            return TicketResult(success=False, error=str(e))


class LinearIntegration:
    """Linear ticketing integration."""

    def __init__(self, integration):
        self.integration = integration
        self.config = integration.config
        self.api_key = self.config.get("api_key")
        self.team_id = self.config.get("team_id")

    def _get_headers(self):
        return {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }

    def create_ticket(
        self,
        summary: str,
        description: str,
        priority: int = None,
        labels: List[str] = None,
        vulnerability_id: int = None,
    ) -> TicketResult:
        """Create a Linear issue."""
        try:
            priority_value = priority or 2
            query = "mutation IssueCreate($input: IssueCreateInput!) { issueCreate(input: $input) { success issue { id title } } }"

            variables = {
                "input": {
                    "title": summary[:255],
                    "description": description[:65000],
                    "teamId": self.team_id,
                    "priority": priority_value,
                }
            }

            response = requests.post(
                "https://api.linear.app/graphql",
                json={"query": query, "variables": variables},
                headers=self._get_headers(),
                timeout=30,
            )
            data = response.json()

            if data.get("errors"):
                return TicketResult(success=False, error=str(data.get("errors")))

            issue = data.get("data", {}).get("issueCreate", {}).get("issue", {})
            issue_id = issue.get("id")

            return TicketResult(
                success=True,
                ticket_id=issue_id,
                ticket_url=f"https://linear.app/team/issue/{issue_id}",
            )

        except Exception as e:
            logger.log_line(PREFIX_TICKET, "LINEAR_CREATE", f"Failed: {e}", level="error")
            return TicketResult(success=False, error=str(e))


def get_integration(integration) -> Any:
    """Get the integration handler for a provider."""
    provider = integration.provider
    if provider == "jira":
        return JiraIntegration(integration)
    elif provider == "github":
        return GitHubIntegration(integration)
    elif provider == "linear":
        return LinearIntegration(integration)
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def create_ticket_for_vulnerability(
    vulnerability, integration, assignee: str = None, labels: List[str] = None
) -> TicketResult:
    """Create a ticket for a vulnerability."""
    handler = get_integration(integration)
    summary = f"[{vulnerability.severity.upper()}] {vulnerability.name} - {vulnerability.template}"
    description = f"""## Vulnerability Details

**Severity:** {vulnerability.severity}
**CVSS Score:** {vulnerability.cvss_score or "N/A"}
**Template:** {vulnerability.template}
**Endpoint:** {vulnerability.endpoint or "N/A"}
**Description:** {vulnerability.description or "No description"}

## Technical Details
- **Scan ID:** {vulnerability.scan_history_id}
- **Discovered:** {vulnerability.insert_date}

## Remediation Recommendations
{vulnerability.remediation or "Review and fix according to best practices."}
"""
    return handler.create_ticket(
        summary=summary, description=description, priority=vulnerability.severity, assignee=assignee, labels=labels
    )


def apply_rules_and_create_tickets(vulnerability, target_id: int) -> List[TicketResult]:
    """Apply ticket creation rules and create tickets for matching vulnerabilities."""
    from .models_ticketing import CreatedTicket, TicketCreationRule

    results = []
    rules = TicketCreationRule.objects.filter(integration__is_enabled=True, integration__is_default=True)

    for rule in rules:
        if not rule.matches_finding(vulnerability):
            continue

        if CreatedTicket.objects.filter(vulnerability=vulnerability, integration=rule.integration).exists():
            continue

        result = create_ticket_for_vulnerability(
            vulnerability,
            rule.integration,
            assignee=rule.assignee.username if rule.assign_to else None,
            labels=rule.labels,
        )

        if result.success:
            CreatedTicket.objects.create(
                integration=rule.integration,
                vulnerability=vulnerability,
                external_ticket_id=result.ticket_id,
                external_ticket_url=result.ticket_url,
            )

        results.append(result)

    return results


def get_sla_status(target_id: int) -> List[Dict[str, Any]]:
    """Get SLA status for all vulnerabilities with tickets."""
    from .models_ticketing import CreatedTicket, SLAPolicy

    tickets = CreatedTicket.objects.filter(
        vulnerability__scan_history__target_id=target_id,
        status__in=[CreatedTicket.TicketStatus.OPEN, CreatedTicket.TicketStatus.IN_PROGRESS],
    ).select_related("vulnerability", "integration")

    status_list = []
    for ticket in tickets:
        severity = ticket.vulnerability.severity.lower()
        sla = SLAPolicy.objects.filter(severity=severity, is_enabled=True).first()

        if not sla:
            continue

        remaining_hours = sla.get_remaining_time(ticket.created_at)
        is_breached = sla.is_breached(ticket.created_at)

        status_list.append(
            {
                "ticket_id": ticket.external_ticket_id,
                "ticket_url": ticket.external_ticket_url,
                "vulnerability": ticket.vulnerability.name,
                "severity": severity,
                "status": ticket.status,
                "remaining_hours": round(remaining_hours, 1),
                "is_breached": is_breached,
                "policy": sla.name,
            }
        )

    return status_list
