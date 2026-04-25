"""
Workspace permission classes.
"""

from rest_framework import permissions

from .models_workspace import Workspace


class IsWorkspaceMember(permissions.BasePermission):
    """
    Check if user is a member of the workspace.
    """

    def has_permission(self, request, view):
        workspace_id = view.kwargs.get("workspace_id") or request.data.get("workspace")
        if not workspace_id:
            return True
        return Workspace.objects.filter(
            id=workspace_id,
            memberships__user=request.user,
            memberships__is_active=True,
        ).exists()


class IsWorkspaceAdmin(permissions.BasePermission):
    """
    Check if user is an admin or owner of the workspace.
    """

    def has_permission(self, request, view):
        workspace_id = view.kwargs.get("workspace_id") or request.data.get("workspace")
        if not workspace_id:
            return False
        return Workspace.objects.filter(
            id=workspace_id,
            memberships__user=request.user,
            memberships__is_active=True,
            memberships__role__in=[Workspace.Role.OWNER, Workspace.Role.ADMIN],
        ).exists()


class IsWorkspaceOwner(permissions.BasePermission):
    """
    Check if user is the owner of the workspace.
    """

    def has_permission(self, request, view):
        workspace_id = view.kwargs.get("workspace_id") or request.data.get("workspace")
        if not workspace_id:
            return False
        return Workspace.objects.filter(
            id=workspace_id,
            owner=request.user,
        ).exists()


class CanManageWorkspaceMembers(permissions.BasePermission):
    """
    Check if user can manage workspace members (owner or admin).
    """

    def has_permission(self, request, view):
        workspace_id = view.kwargs.get("workspace_id") or request.data.get("workspace")
        if not workspace_id:
            return False
        try:
            workspace = Workspace.objects.get(id=workspace_id)
            return workspace.can_user_manage_members(request.user)
        except Workspace.DoesNotExist:
            return False


def get_user_workspaces(user):
    """Get all workspaces a user is a member of."""
    return Workspace.objects.filter(
        memberships__user=user,
        memberships__is_active=True,
        is_active=True,
    ).distinct()


def can_access_workspace(user, workspace_id):
    """Check if user can access a workspace."""
    return Workspace.objects.filter(
        id=workspace_id,
        memberships__user=user,
        memberships__is_active=True,
        is_active=True,
    ).exists()


def get_workspace_for_user(user, workspace_id):
    """Get workspace if user has access, otherwise None."""
    try:
        workspace = Workspace.objects.get(
            id=workspace_id,
            memberships__user=user,
            memberships__is_active=True,
            is_active=True,
        )
        return workspace
    except Workspace.DoesNotExist:
        return None
