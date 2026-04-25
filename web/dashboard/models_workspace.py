"""
Workspace models for multi-team collaboration.
"""

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Workspace(models.Model):
    """
    Top-level organizational unit for isolating clients/engagements.
    Contains multiple Projects and allows team collaboration.
    """

    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        MEMBER = "member", "Member"
        VIEWER = "viewer", "Viewer"

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_workspaces",
    )
    workspace_settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Workspace settings like default permissions, invite restrictions",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def get_user_role(self, user):
        """Get the role of a user in this workspace."""
        membership = self.memberships.filter(user=user).first()
        return membership.role if membership else None

    def is_user_member(self, user):
        """Check if user is a member of this workspace."""
        return self.memberships.filter(user=user).exists()

    def can_user_edit(self, user):
        """Check if user can edit workspace settings."""
        role = self.get_user_role(user)
        return role in [self.Role.OWNER, self.Role.ADMIN]

    def can_user_manage_members(self, user):
        """Check if user can manage workspace members."""
        role = self.get_user_role(user)
        return role in [self.Role.OWNER, self.Role.ADMIN]


class WorkspaceMembership(models.Model):
    """
    Links users to workspaces with specific roles.
    """

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="workspace_memberships",
    )
    role = models.CharField(
        max_length=20,
        choices=Workspace.Role.choices,
        default=Workspace.Role.MEMBER,
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_invitations",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ["workspace", "user"]
        ordering = ["-joined_at"]

    def __str__(self):
        return f"{self.user.username} - {self.workspace.name} ({self.role})"


class WorkspaceInvitation(models.Model):
    """
    Pending invitations to join a workspace.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        EXPIRED = "expired", "Expired"

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    email = models.EmailField()
    role = models.CharField(
        max_length=20,
        choices=Workspace.Role.choices,
        default=Workspace.Role.MEMBER,
    )
    token = models.CharField(max_length=64, unique=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_workspace_invitations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} -> {self.workspace.name}"

    def is_expired(self):
        return timezone.now() > self.expires_at


class ActivityFeed(models.Model):
    """
    Activity log for workspace events and collaboration.
    """

    class Action(models.TextChoices):
        CREATED = "created", "Created"
        UPDATED = "updated", "Updated"
        DELETED = "deleted", "Deleted"
        SCAN_STARTED = "scan_started", "Scan Started"
        SCAN_COMPLETED = "scan_completed", "Scan Completed"
        VULNERABILITY_FOUND = "vulnerability_found", "Vulnerability Found"
        MEMBER_JOINED = "member_joined", "Member Joined"
        MEMBER_LEFT = "member_left", "Member Left"
        INVITATION_SENT = "invitation_sent", "Invitation Sent"
        INVITATION_ACCEPTED = "invitation_accepted", "Invitation Accepted"
        COMMENT_ADDED = "comment_added", "Comment Added"
        STATUS_CHANGED = "status_changed", "Status Changed"
        EXPORTED = "exported", "Exported"

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="activity_feed",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workspace_actions",
    )
    action = models.CharField(max_length=50, choices=Action.choices)
    target_type = models.CharField(
        max_length=50,
        help_text="Model type (Project, Target, Vulnerability, etc.)",
    )
    target_id = models.PositiveIntegerField(null=True, blank=True)
    target_name = models.CharField(max_length=500, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Activity feeds"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["workspace", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["target_type", "target_id"]),
        ]

    def __str__(self):
        return f"{self.user} {self.action} {self.target_type} at {self.created_at}"


class FindingComment(models.Model):
    """
    Comments on vulnerabilities and other findings for collaboration.
    """

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="finding_comments",
    )
    content_type = models.CharField(
        max_length=50,
        help_text="Model type (Vulnerability, Subdomain, etc.)",
    )
    object_id = models.PositiveIntegerField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_comments",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["workspace", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.content[:50]}..."

    def mark_resolved(self, user):
        self.is_resolved = True
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.save()
