"""
Webhook management and notification system for reconPoint.
"""
import json
import hmac
import hashlib
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime

from django.conf import settings
from django.core.cache import cache
from celery import shared_task


logger = logging.getLogger(__name__)


class WebhookEvent:
    """Webhook event types."""
    SCAN_STARTED = 'scan.started'
    SCAN_COMPLETED = 'scan.completed'
    SCAN_FAILED = 'scan.failed'
    SUBDOMAIN_DISCOVERED = 'subdomain.discovered'
    VULNERABILITY_FOUND = 'vulnerability.found'
    TARGET_ADDED = 'target.added'


class WebhookManager:
    """Manage webhook subscriptions and deliveries."""
    
    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        self.timeout = 30  # seconds
    
    def send_webhook(
        self,
        url: str,
        event: str,
        payload: Dict[str, Any],
        secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send webhook to URL.
        
        Args:
            url: Webhook URL
            event: Event type
            payload: Event payload
            secret: Secret for signature verification
            headers: Additional headers
            
        Returns:
            True if successful, False otherwise
        """
        # Prepare payload
        webhook_payload = {
            'event': event,
            'timestamp': datetime.utcnow().isoformat(),
            'data': payload
        }
        
        # Prepare headers
        webhook_headers = {
            'Content-Type': 'application/json',
            'User-Agent': f'reconPoint-Webhook/{settings.RECONPOINT_CURRENT_VERSION}',
            'X-Webhook-Event': event
        }
        
        if headers:
            webhook_headers.update(headers)
        
        # Add signature if secret provided
        if secret:
            signature = self._generate_signature(webhook_payload, secret)
            webhook_headers['X-Webhook-Signature'] = signature
        
        # Send webhook with retries
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    url,
                    json=webhook_payload,
                    headers=webhook_headers,
                    timeout=self.timeout
                )
                
                if response.status_code in [200, 201, 202, 204]:
                    logger.info(f"Webhook delivered successfully to {url}")
                    self._log_webhook_delivery(url, event, True, response.status_code)
                    return True
                else:
                    logger.warning(
                        f"Webhook delivery failed with status {response.status_code}: {response.text}"
                    )
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Webhook delivery error (attempt {attempt + 1}/{self.max_retries}): {e}")
                
                if attempt < self.max_retries - 1:
                    import time
                    time.sleep(self.retry_delay * (attempt + 1))
        
        # All retries failed
        self._log_webhook_delivery(url, event, False, None)
        return False
    
    def _generate_signature(self, payload: Dict[str, Any], secret: str) -> str:
        """
        Generate HMAC signature for payload.
        
        Args:
            payload: Webhook payload
            secret: Secret key
            
        Returns:
            Signature string
        """
        payload_bytes = json.dumps(payload, sort_keys=True).encode('utf-8')
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"
    
    def verify_signature(self, payload: str, signature: str, secret: str) -> bool:
        """
        Verify webhook signature.
        
        Args:
            payload: Webhook payload as string
            signature: Signature to verify
            secret: Secret key
            
        Returns:
            True if valid, False otherwise
        """
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Remove 'sha256=' prefix if present
        if signature.startswith('sha256='):
            signature = signature[7:]
        
        return hmac.compare_digest(signature, expected_signature)
    
    def _log_webhook_delivery(
        self,
        url: str,
        event: str,
        success: bool,
        status_code: Optional[int]
    ):
        """
        Log webhook delivery attempt.
        
        Args:
            url: Webhook URL
            event: Event type
            success: Whether delivery was successful
            status_code: HTTP status code
        """
        log_entry = {
            'url': url,
            'event': event,
            'success': success,
            'status_code': status_code,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Store in cache for recent deliveries
        cache_key = f'webhook_log:{url}:{event}'
        recent_logs = cache.get(cache_key, [])
        recent_logs.append(log_entry)
        
        # Keep only last 10 deliveries
        recent_logs = recent_logs[-10:]
        cache.set(cache_key, recent_logs, timeout=86400)  # 24 hours


class WebhookSubscription:
    """Manage webhook subscriptions."""
    
    @staticmethod
    def get_subscriptions(event: str) -> List[Dict[str, Any]]:
        """
        Get all subscriptions for an event.
        
        Args:
            event: Event type
            
        Returns:
            List of subscription dictionaries
        """
        # This should be stored in database in production
        # For now, using cache as example
        cache_key = f'webhook_subscriptions:{event}'
        subscriptions = cache.get(cache_key, [])
        return subscriptions
    
    @staticmethod
    def add_subscription(
        url: str,
        events: List[str],
        secret: Optional[str] = None,
        active: bool = True
    ) -> Dict[str, Any]:
        """
        Add webhook subscription.
        
        Args:
            url: Webhook URL
            events: List of event types to subscribe to
            secret: Secret for signature verification
            active: Whether subscription is active
            
        Returns:
            Subscription dictionary
        """
        subscription = {
            'id': hashlib.md5(url.encode()).hexdigest(),
            'url': url,
            'events': events,
            'secret': secret,
            'active': active,
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Store subscription for each event
        for event in events:
            cache_key = f'webhook_subscriptions:{event}'
            subscriptions = cache.get(cache_key, [])
            
            # Check if already subscribed
            if not any(sub['url'] == url for sub in subscriptions):
                subscriptions.append(subscription)
                cache.set(cache_key, subscriptions, timeout=None)
        
        return subscription
    
    @staticmethod
    def remove_subscription(url: str, event: Optional[str] = None):
        """
        Remove webhook subscription.
        
        Args:
            url: Webhook URL
            event: Specific event to unsubscribe from (None for all)
        """
        if event:
            events = [event]
        else:
            # Remove from all events
            events = [
                WebhookEvent.SCAN_STARTED,
                WebhookEvent.SCAN_COMPLETED,
                WebhookEvent.SCAN_FAILED,
                WebhookEvent.SUBDOMAIN_DISCOVERED,
                WebhookEvent.VULNERABILITY_FOUND,
                WebhookEvent.TARGET_ADDED
            ]
        
        for evt in events:
            cache_key = f'webhook_subscriptions:{evt}'
            subscriptions = cache.get(cache_key, [])
            subscriptions = [sub for sub in subscriptions if sub['url'] != url]
            cache.set(cache_key, subscriptions, timeout=None)


@shared_task(name='send_webhook_notification')
def send_webhook_notification(event: str, payload: Dict[str, Any]):
    """
    Celery task to send webhook notifications.
    
    Args:
        event: Event type
        payload: Event payload
    """
    manager = WebhookManager()
    subscriptions = WebhookSubscription.get_subscriptions(event)
    
    for subscription in subscriptions:
        if not subscription.get('active', True):
            continue
        
        try:
            manager.send_webhook(
                url=subscription['url'],
                event=event,
                payload=payload,
                secret=subscription.get('secret')
            )
        except Exception as e:
            logger.error(f"Failed to send webhook to {subscription['url']}: {e}")


def trigger_webhook(event: str, payload: Dict[str, Any], async_send: bool = True):
    """
    Trigger webhook for an event.
    
    Args:
        event: Event type
        payload: Event payload
        async_send: Whether to send asynchronously via Celery
    """
    if async_send:
        send_webhook_notification.delay(event, payload)
    else:
        send_webhook_notification(event, payload)


# Convenience functions for common events

def notify_scan_started(scan_id: int, domain: str, engine: str):
    """
    Notify that a scan has started.
    
    Args:
        scan_id: Scan history ID
        domain: Domain name
        engine: Engine name
    """
    payload = {
        'scan_id': scan_id,
        'domain': domain,
        'engine': engine
    }
    trigger_webhook(WebhookEvent.SCAN_STARTED, payload)


def notify_scan_completed(
    scan_id: int,
    domain: str,
    duration: float,
    results: Dict[str, int]
):
    """
    Notify that a scan has completed.
    
    Args:
        scan_id: Scan history ID
        domain: Domain name
        duration: Scan duration in seconds
        results: Dictionary with result counts
    """
    payload = {
        'scan_id': scan_id,
        'domain': domain,
        'duration': duration,
        'results': results
    }
    trigger_webhook(WebhookEvent.SCAN_COMPLETED, payload)


def notify_scan_failed(scan_id: int, domain: str, error: str):
    """
    Notify that a scan has failed.
    
    Args:
        scan_id: Scan history ID
        domain: Domain name
        error: Error message
    """
    payload = {
        'scan_id': scan_id,
        'domain': domain,
        'error': error
    }
    trigger_webhook(WebhookEvent.SCAN_FAILED, payload)


def notify_vulnerability_found(
    scan_id: int,
    vulnerability: Dict[str, Any]
):
    """
    Notify that a vulnerability was found.
    
    Args:
        scan_id: Scan history ID
        vulnerability: Vulnerability details
    """
    payload = {
        'scan_id': scan_id,
        'vulnerability': vulnerability
    }
    trigger_webhook(WebhookEvent.VULNERABILITY_FOUND, payload)


def notify_subdomain_discovered(
    scan_id: int,
    subdomain: str,
    http_status: Optional[int] = None
):
    """
    Notify that a subdomain was discovered.
    
    Args:
        scan_id: Scan history ID
        subdomain: Subdomain name
        http_status: HTTP status code
    """
    payload = {
        'scan_id': scan_id,
        'subdomain': subdomain,
        'http_status': http_status
    }
    trigger_webhook(WebhookEvent.SUBDOMAIN_DISCOVERED, payload)


class WebhookTestHelper:
    """Helper for testing webhooks."""
    
    @staticmethod
    def test_webhook(url: str, secret: Optional[str] = None) -> Dict[str, Any]:
        """
        Test webhook endpoint.
        
        Args:
            url: Webhook URL
            secret: Secret for signature verification
            
        Returns:
            Test result dictionary
        """
        manager = WebhookManager()
        
        test_payload = {
            'test': True,
            'message': 'This is a test webhook from reconPoint'
        }
        
        success = manager.send_webhook(
            url=url,
            event='webhook.test',
            payload=test_payload,
            secret=secret
        )
        
        return {
            'success': success,
            'url': url,
            'timestamp': datetime.utcnow().isoformat()
        }
