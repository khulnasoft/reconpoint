"""
Modern ViewSets using service layer pattern.
"""

from .domain_viewset import DomainViewSet
from .scan_viewset import ScanViewSet
from .notification_viewset import NotificationViewSet

__all__ = [
    'DomainViewSet',
    'ScanViewSet',
    'NotificationViewSet',
]
