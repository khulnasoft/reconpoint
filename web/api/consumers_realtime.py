"""
Real-time WebSocket consumers for live scan updates and vulnerability alerts.
"""

import json
import re
from typing import Optional

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.utils import timezone

from reconPoint.utilities.logger import get_module_logger


PREFIX_API = "[RT]"
logger = get_module_logger(__name__)

CHANNEL_NAME_PATTERN = r"[^a-zA-Z0-9\-\.]"


class LiveScanConsumer(WebsocketConsumer):
    """
    Enhanced WebSocket consumer for real-time scan dashboard.
    Provides live progress updates, vulnerability alerts, and heartbeat monitoring.
    """

    HEARTBEAT_INTERVAL = 30
    HEARTBEAT_TIMEOUT = 90

    def clean_channel_name(self, name: str) -> str:
        return re.sub(CHANNEL_NAME_PATTERN, "-", (name or "").strip())

    @property
    def scan_id(self) -> Optional[str]:
        return self.scope.get("url_route", {}).get("kwargs", {}).get("scan_id")

    @property
    def project_slug(self) -> Optional[str]:
        return self.scope.get("url_route", {}).get("kwargs", {}).get("project_slug")

    def connect(self):
        try:
            self.authenticated = False
            self.last_heartbeat = timezone.now()
            self.scan_ids: set[str] = set()
            self.project_slugs: set[str] = set()

            if self.scan_id:
                room_group_name = f"live-scan-{self.clean_channel_name(str(self.scan_id))}"
                self.scan_ids.add(str(self.scan_id))
            elif self.project_slug:
                room_group_name = f"live-project-{self.clean_channel_name(self.project_slug)}"
                self.project_slugs.add(self.project_slug)
            else:
                room_group_name = "live-scan-all"
                self._subscribe_to_all_scans()

            self.room_group_name = room_group_name
            async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
            self.accept()

            self._send_initial_state()

        except Exception as e:
            logger.log_line(PREFIX_API, "LIVE_SCAN", f"Connect failed: {e}", level="error")
            raise

    def disconnect(self, close_code):
        try:
            if hasattr(self, "room_group_name"):
                async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)
            self._cleanup_subscriptions()
        except Exception as e:
            logger.log_line(PREFIX_API, "LIVE_SCAN", f"Disconnect failed: {e}", level="error")

    def receive(self, text_data):
        try:
            data = json.loads(text_data)
            msg_type = data.get("type")

            if msg_type == "heartbeat":
                self.last_heartbeat = timezone.now()
                self.send(text_data=json.dumps({"type": "heartbeat_ack", "ts": self.last_heartbeat.isoformat()}))

            elif msg_type == "subscribe":
                self._handle_subscribe(data)

            elif msg_type == "unsubscribe":
                self._handle_unsubscribe(data)

            elif msg_type == "ping":
                self.send(text_data=json.dumps({"type": "pong", "ts": timezone.now().isoformat()}))

        except json.JSONDecodeError:
            self.send(text_data=json.dumps({"type": "error", "message": "Invalid JSON"}))
        except Exception as e:
            logger.log_line(PREFIX_API, "LIVE_SCAN", f"Receive error: {e}", level="error")

    def live_scan_progress(self, event):
        """Handle scan progress updates."""
        self._send_safe(event.get("payload", {}))

    def live_vulnerability_found(self, event):
        """Handle new vulnerability discoveries."""
        self._send_safe(event.get("payload", {}))

    def live_scan_event(self, event):
        """Handle general scan events."""
        self._send_safe(event.get("payload", {}))

    def live_heartbeat_check(self, event):
        """Handle heartbeat check requests."""
        elapsed = (timezone.now() - self.last_heartbeat).total_seconds()
        if elapsed > self.HEARTBEAT_TIMEOUT:
            self.send(text_data=json.dumps({"type": "connection_timeout", "message": "No heartbeat received"}))
            self.close()

    def _send_safe(self, payload: dict):
        try:
            self.send(text_data=json.dumps(payload))
        except Exception as e:
            logger.log_line(PREFIX_API, "LIVE_SCAN", f"Send failed: {e}", level="error")

    def _send_initial_state(self):
        self.send(
            text_data=json.dumps(
                {
                    "type": "connected",
                    "scan_ids": list(self.scan_ids),
                    "project_slugs": list(self.project_slugs),
                    "heartbeat_interval": self.HEARTBEAT_INTERVAL,
                    "timestamp": timezone.now().isoformat(),
                }
            )
        )

    def _subscribe_to_all_scans(self):
        pass

    def _handle_subscribe(self, data: dict):
        scan_id = data.get("scan_id")
        project_slug = data.get("project_slug")

        if scan_id:
            self.scan_ids.add(str(scan_id))
        if project_slug:
            self.project_slugs.add(project_slug)

        self.send(
            text_data=json.dumps(
                {
                    "type": "subscribed",
                    "scan_ids": list(self.scan_ids),
                    "project_slugs": list(self.project_slugs),
                }
            )
        )

    def _handle_unsubscribe(self, data: dict):
        scan_id = data.get("scan_id")
        project_slug = data.get("project_slug")

        if scan_id:
            self.scan_ids.discard(str(scan_id))
        if project_slug:
            self.project_slugs.discard(project_slug)

    def _cleanup_subscriptions(self):
        self.scan_ids.clear()
        self.project_slugs.clear()


class VulnerabilityAlertConsumer(WebsocketConsumer):
    """
    WebSocket consumer for real-time vulnerability alerts and notifications.
    """

    def connect(self):
        try:
            project_slug = self.scope["url_route"]["kwargs"].get("project_slug")
            self.room_group_name = f"vuln-alerts-{self.clean_channel_name(project_slug or 'all')}"

            async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
            self.accept()

            self.send(
                text_data=json.dumps(
                    {
                        "type": "connected",
                        "group": self.room_group_name,
                    }
                )
            )
        except Exception as e:
            logger.log_line(PREFIX_API, "VULN_ALERT", f"Connect failed: {e}", level="error")
            raise

    def disconnect(self, close_code):
        try:
            if hasattr(self, "room_group_name"):
                async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)
        except Exception as e:
            logger.log_line(PREFIX_API, "VULN_ALERT", f"Disconnect failed: {e}", level="error")

    def vuln_alert(self, event):
        """Handle vulnerability alert notifications."""
        try:
            payload = event.get("payload", {})
            self.send(text_data=json.dumps(payload))
        except Exception as e:
            logger.log_line(PREFIX_API, "VULN_ALERT", f"Send alert failed: {e}", level="error")

    def vuln_critical(self, event):
        """Handle critical vulnerability alerts."""
        try:
            payload = event.get("payload", {})
            self.send(text_data=json.dumps(payload))
        except Exception as e:
            logger.log_line(PREFIX_API, "VULN_ALERT", f"Send critical failed: {e}", level="error")


class ScanHeartbeatMonitor:
    """
    Background task to monitor scan heartbeats and detect stalled scans.
    """

    @staticmethod
    def check_stalled_scans():
        """
        Check for scans that haven't sent heartbeat and may be stalled.
        Called periodically by Celery beat.
        """
        from channels.layers import get_channel_layer

        try:
            channel_layer = get_channel_layer()
            if channel_layer is None:
                return

            async_to_sync(channel_layer.group_send)("live-scan-all", {"type": "live_heartbeat_check"})
        except Exception as e:
            logger.log_line(PREFIX_API, "HEARTBEAT", f"Monitor check failed: {e}", level="error")
