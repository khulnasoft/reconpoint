"""
Real-time WebSocket broadcast utilities for live scan updates and vulnerability alerts.
"""

from typing import Any, Optional

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

from reconPoint.utilities.logger import get_module_logger


PREFIX_RT = "[RT]"
logger = get_module_logger(__name__)

LIVESCAN_GROUP_ALL = "live-scan-all"


def _get_channel_layer():
    try:
        return get_channel_layer()
    except Exception:
        return None


def send_live_scan_progress(
    scan_id: int,
    progress: float,
    current_task: str,
    status: str,
    **extra: Any,
) -> bool:
    """
    Broadcast live scan progress update.

    Args:
        scan_id: The scan history ID
        progress: Progress percentage (0-100)
        current_task: Name of current task being executed
        status: Current status (running, completed, failed, etc.)
        **extra: Additional data to include
    """
    channel_layer = _get_channel_layer()
    if not channel_layer:
        return False

    payload = {
        "type": "live_scan_progress",
        "payload": {
            "event_type": "progress",
            "scan_id": scan_id,
            "progress": progress,
            "current_task": current_task,
            "status": status,
            "timestamp": timezone.now().isoformat(),
            **extra,
        },
    }

    try:
        async_to_sync(channel_layer.group_send)(
            f"live-scan-{scan_id}",
            payload,
        )
        return True
    except Exception as e:
        logger.log_line(PREFIX_RT, "LIVE_PROGRESS", f"Send failed: {e}", level="error")
        return False


def send_vulnerability_alert(
    scan_id: int,
    vulnerability_id: int,
    name: str,
    severity: str,
    target: str,
    description: str,
    cvss_score: Optional[float] = None,
    **extra: Any,
) -> bool:
    """
    Broadcast new vulnerability discovery alert.

    Args:
        scan_id: The scan history ID
        vulnerability_id: The vulnerability record ID
        name: Vulnerability name
        severity: Severity level (critical, high, medium, low, info)
        target: Target hostname/IP
        description: Brief description
        cvss_score: Optional CVSS score
        **extra: Additional data
    """
    channel_layer = _get_channel_layer()
    if not channel_layer:
        return False

    severity_priority = {
        "critical": 4,
        "high": 3,
        "medium": 2,
        "low": 1,
        "info": 0,
    }.get(severity.lower(), 0)

    payload = {
        "type": "live_vulnerability_found",
        "payload": {
            "event_type": "vulnerability_found",
            "scan_id": scan_id,
            "vulnerability_id": vulnerability_id,
            "name": name,
            "severity": severity,
            "severity_priority": severity_priority,
            "target": target,
            "description": description[:200] if description else "",
            "cvss_score": cvss_score,
            "timestamp": timezone.now().isoformat(),
            **extra,
        },
    }

    try:
        async_to_sync(channel_layer.group_send)(
            f"live-scan-{scan_id}",
            payload,
        )
        if severity_priority >= 3:
            async_to_sync(channel_layer.group_send)(
                "vuln-alerts-all",
                {"type": "vuln_critical", "payload": payload["payload"]},
            )
        return True
    except Exception as e:
        logger.log_line(PREFIX_RT, "VULN_ALERT", f"Send failed: {e}", level="error")
        return False


def send_scan_event(
    scan_id: int,
    event_name: str,
    message: str,
    level: str = "info",
    **extra: Any,
) -> bool:
    """
    Broadcast general scan event (start, stop, error, etc.).

    Args:
        scan_id: The scan history ID
        event_name: Event identifier
        message: Human-readable message
        level: Log level (debug, info, warning, error)
        **extra: Additional data
    """
    channel_layer = _get_channel_layer()
    if not channel_layer:
        return False

    payload = {
        "type": "live_scan_event",
        "payload": {
            "event_type": event_name,
            "scan_id": scan_id,
            "message": message,
            "level": level,
            "timestamp": timezone.now().isoformat(),
            **extra,
        },
    }

    try:
        async_to_sync(channel_layer.group_send)(
            f"live-scan-{scan_id}",
            payload,
        )
        return True
    except Exception as e:
        logger.log_line(PREFIX_RT, "SCAN_EVENT", f"Send failed: {e}", level="error")
        return False


def send_scan_started(scan_id: int, target: str, workflow_name: str = None, **extra: Any) -> bool:
    """Broadcast scan started event."""
    return send_scan_event(
        scan_id,
        "scan_started",
        f"Scan started for {target}",
        "info",
        target=target,
        workflow_name=workflow_name,
        **extra,
    )


def send_scan_completed(
    scan_id: int,
    target: str,
    duration_seconds: float = None,
    results_summary: dict = None,
    **extra: Any,
) -> bool:
    """Broadcast scan completed event."""
    return send_scan_event(
        scan_id,
        "scan_completed",
        f"Scan completed for {target}",
        "info",
        target=target,
        duration_seconds=duration_seconds,
        results_summary=results_summary or {},
        **extra,
    )


def send_scan_failed(scan_id: int, target: str, error_message: str, **extra: Any) -> bool:
    """Broadcast scan failed event."""
    return send_scan_event(
        scan_id,
        "scan_failed",
        f"Scan failed: {error_message}",
        "error",
        target=target,
        error_message=error_message,
        **extra,
    )


def send_scan_aborted(scan_id: int, target: str, aborted_by: str = None, **extra: Any) -> bool:
    """Broadcast scan aborted event."""
    return send_scan_event(
        scan_id,
        "scan_aborted",
        f"Scan aborted for {target}",
        "warning",
        target=target,
        aborted_by=aborted_by,
        **extra,
    )


def broadcast_to_all_scans(event_type: str, payload: dict) -> bool:
    """Broadcast event to all connected scan watchers."""
    channel_layer = _get_channel_layer()
    if not channel_layer:
        return False

    try:
        async_to_sync(channel_layer.group_send)(
            LIVESCAN_GROUP_ALL,
            {"type": "live_scan_event", "payload": {**payload, "event_type": event_type}},
        )
        return True
    except Exception as e:
        logger.log_line(PREFIX_RT, "BROADCAST", f"Broadcast failed: {e}", level="error")
        return False
