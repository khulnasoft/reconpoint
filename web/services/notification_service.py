"""
Notification service for managing in-app notifications.
"""
from typing import Optional, List, Dict, Any
from django.db import transaction
from django.utils import timezone
from dashboard.models import InAppNotification, Project
from django.contrib.auth.models import User
from reconPoint.error_handlers import ResourceNotFoundException, ValidationException
from .base_service import BaseService
import logging

logger = logging.getLogger(__name__)


class NotificationService(BaseService):
    """Service for notification operations."""
    
    @staticmethod
    @transaction.atomic
    def create_notification(
        title: str,
        description: str,
        notification_type: str = 'system',
        status: str = 'info',
        icon: str = 'mdi-information',
        project: Optional[Project] = None,
        redirect_link: Optional[str] = None,
        open_in_new_tab: bool = False
    ) -> InAppNotification:
        """
        Create a new in-app notification.
        
        Args:
            title: Notification title
            description: Notification description
            notification_type: Type ('system' or 'project')
            status: Status ('info', 'success', 'warning', 'error')
            icon: MDI icon class name
            project: Optional project for project-specific notifications
            redirect_link: Optional redirect URL
            open_in_new_tab: Whether to open link in new tab
            
        Returns:
            Created InAppNotification instance
            
        Raises:
            ValidationException: If validation fails
        """
        # Validate notification type
        valid_types = ['system', 'project']
        if notification_type not in valid_types:
            raise ValidationException(
                f"Invalid notification_type: {notification_type}. Must be one of: {valid_types}"
            )
        
        # Validate status
        valid_statuses = ['info', 'success', 'warning', 'error']
        if status not in valid_statuses:
            raise ValidationException(
                f"Invalid status: {status}. Must be one of: {valid_statuses}"
            )
        
        # Validate project requirement
        if notification_type == 'project' and not project:
            raise ValidationException(
                "Project is required for project-specific notifications"
            )
        
        # Create notification
        notification = InAppNotification.objects.create(
            title=title,
            description=description,
            notification_type=notification_type,
            status=status,
            icon=icon,
            project=project,
            redirect_link=redirect_link,
            open_in_new_tab=open_in_new_tab
        )
        
        logger.info(f"Created notification: {title} (Type: {notification_type})")
        
        return notification
    
    @staticmethod
    def get_user_notifications(
        user: User,
        project_id: Optional[int] = None,
        is_read: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get notifications for a user.
        
        Args:
            user: User instance
            project_id: Filter by project ID
            is_read: Filter by read status
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            Dictionary with notifications and metadata
        """
        # Get system-wide notifications
        queryset = InAppNotification.objects.filter(
            notification_type='system'
        )
        
        # Add project-specific notifications if project_id provided
        if project_id:
            project_notifications = InAppNotification.objects.filter(
                notification_type='project',
                project_id=project_id
            )
            queryset = queryset | project_notifications
        
        # Apply read filter
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read)
        
        # Get total count
        total_count = queryset.count()
        
        # Apply pagination
        notifications = queryset.order_by('-created_at')[offset:offset + limit]
        
        return {
            'count': total_count,
            'unread_count': queryset.filter(is_read=False).count(),
            'limit': limit,
            'offset': offset,
            'results': [
                {
                    'id': notif.id,
                    'title': notif.title,
                    'description': notif.description,
                    'icon': notif.icon,
                    'notification_type': notif.notification_type,
                    'status': notif.status,
                    'is_read': notif.is_read,
                    'created_at': notif.created_at,
                    'redirect_link': notif.redirect_link,
                    'open_in_new_tab': notif.open_in_new_tab,
                    'project': notif.project.name if notif.project else None
                }
                for notif in notifications
            ]
        }
    
    @staticmethod
    @transaction.atomic
    def mark_as_read(notification_id: int) -> InAppNotification:
        """
        Mark a notification as read.
        
        Args:
            notification_id: Notification ID
            
        Returns:
            Updated InAppNotification instance
            
        Raises:
            ResourceNotFoundException: If notification not found
        """
        try:
            notification = InAppNotification.objects.get(id=notification_id)
        except InAppNotification.DoesNotExist:
            raise ResourceNotFoundException('InAppNotification', notification_id)
        
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        
        return notification
    
    @staticmethod
    @transaction.atomic
    def mark_all_as_read(user: User, project_id: Optional[int] = None) -> int:
        """
        Mark all notifications as read for a user.
        
        Args:
            user: User instance
            project_id: Optional project ID to filter
            
        Returns:
            Number of notifications marked as read
        """
        queryset = InAppNotification.objects.filter(
            is_read=False,
            notification_type='system'
        )
        
        if project_id:
            project_notifications = InAppNotification.objects.filter(
                is_read=False,
                notification_type='project',
                project_id=project_id
            )
            queryset = queryset | project_notifications
        
        count = queryset.update(is_read=True)
        
        logger.info(f"Marked {count} notifications as read for user {user.username}")
        
        return count
    
    @staticmethod
    @transaction.atomic
    def delete_notification(notification_id: int) -> None:
        """
        Delete a notification.
        
        Args:
            notification_id: Notification ID
            
        Raises:
            ResourceNotFoundException: If notification not found
        """
        try:
            notification = InAppNotification.objects.get(id=notification_id)
        except InAppNotification.DoesNotExist:
            raise ResourceNotFoundException('InAppNotification', notification_id)
        
        notification.delete()
        
        logger.info(f"Deleted notification {notification_id}")
    
    @staticmethod
    def create_scan_notification(
        scan_id: int,
        domain_name: str,
        project: Project,
        status: str,
        message: str
    ) -> InAppNotification:
        """
        Create a scan-related notification.
        
        Args:
            scan_id: Scan ID
            domain_name: Domain name
            project: Project instance
            status: Notification status
            message: Notification message
            
        Returns:
            Created InAppNotification instance
        """
        icon_map = {
            'info': 'mdi-information',
            'success': 'mdi-check-circle',
            'warning': 'mdi-alert',
            'error': 'mdi-alert-circle'
        }
        
        return NotificationService.create_notification(
            title=f"Scan Update: {domain_name}",
            description=message,
            notification_type='project',
            status=status,
            icon=icon_map.get(status, 'mdi-information'),
            project=project,
            redirect_link=f"/scan/{scan_id}/",
            open_in_new_tab=False
        )
    
    @staticmethod
    def create_vulnerability_notification(
        domain_name: str,
        project: Project,
        severity: str,
        count: int
    ) -> InAppNotification:
        """
        Create a vulnerability discovery notification.
        
        Args:
            domain_name: Domain name
            project: Project instance
            severity: Vulnerability severity
            count: Number of vulnerabilities
            
        Returns:
            Created InAppNotification instance
        """
        severity_icons = {
            'critical': 'mdi-alert-octagon',
            'high': 'mdi-alert',
            'medium': 'mdi-alert-circle-outline',
            'low': 'mdi-information-outline'
        }
        
        severity_status = {
            'critical': 'error',
            'high': 'error',
            'medium': 'warning',
            'low': 'info'
        }
        
        return NotificationService.create_notification(
            title=f"Vulnerabilities Discovered: {domain_name}",
            description=f"Found {count} {severity} severity vulnerabilities",
            notification_type='project',
            status=severity_status.get(severity, 'info'),
            icon=severity_icons.get(severity, 'mdi-shield-alert'),
            project=project
        )
