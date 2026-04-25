"""
Workspace API views.
"""

from datetime import timedelta
from secrets import token_urlsafe

from django.db.models import Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models_workspace import (
    ActivityFeed,
    FindingComment,
    Workspace,
    WorkspaceInvitation,
    WorkspaceMembership,
)
from .serializers_workspace import (
    ActivityFeedSerializer,
    FindingCommentSerializer,
    InviteUserSerializer,
    WorkspaceCreateSerializer,
    WorkspaceInvitationSerializer,
    WorkspaceMembershipSerializer,
    WorkspaceSerializer,
)


class WorkspaceViewSet(viewsets.ModelViewSet):
    """
    API endpoints for workspace management.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = WorkspaceSerializer

    def get_queryset(self):
        user = self.request.user
        return Workspace.objects.filter(
            Q(owner=user) | Q(memberships__user=user, memberships__is_active=True),
            is_active=True,
        ).distinct()

    def get_serializer_class(self):
        if self.action == "create":
            return WorkspaceCreateSerializer
        return WorkspaceSerializer

    def perform_create(self, serializer):
        workspace = serializer.save()
        ActivityFeed.objects.create(
            workspace=workspace,
            user=self.request.user,
            action=ActivityFeed.Action.CREATED,
            target_type="Workspace",
            target_id=workspace.id,
            target_name=workspace.name,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.owner != request.user:
            return Response(
                {"error": "Only workspace owner can delete the workspace"},
                status=status.HTTP_403_FORBIDDEN,
            )
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"])
    def activity(self, request, pk=None):
        """Get activity feed for a workspace."""
        workspace = self.get_object()
        activities = ActivityFeed.objects.filter(workspace=workspace)[:50]
        serializer = ActivityFeedSerializer(activities, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def members(self, request, pk=None):
        """Get members of a workspace."""
        workspace = self.get_object()
        members = WorkspaceMembership.objects.filter(workspace=workspace, is_active=True)
        serializer = WorkspaceMembershipSerializer(members, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def invite(self, request, pk=None):
        """Invite a user to the workspace."""
        workspace = self.get_object()
        if not workspace.can_user_manage_members(request.user):
            return Response(
                {"error": "You don't have permission to invite members"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = InviteUserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        role = serializer.validated_data["role"]

        if WorkspaceMembership.objects.filter(workspace=workspace, user__email=email, is_active=True).exists():
            return Response(
                {"error": "User is already a member of this workspace"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing_invitation = WorkspaceInvitation.objects.filter(
            workspace=workspace,
            email=email,
            status=WorkspaceInvitation.Status.PENDING,
        ).first()
        if existing_invitation:
            return Response(
                {"error": "Invitation already pending for this email"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = token_urlsafe(32)
        expires_at = timezone.now() + timedelta(days=7)

        invitation = WorkspaceInvitation.objects.create(
            workspace=workspace,
            email=email,
            role=role,
            token=token,
            invited_by=request.user,
            expires_at=expires_at,
        )

        ActivityFeed.objects.create(
            workspace=workspace,
            user=request.user,
            action=ActivityFeed.Action.INVITATION_SENT,
            target_type="WorkspaceMembership",
            target_name=email,
            metadata={"role": role},
        )

        return Response(
            WorkspaceInvitationSerializer(invitation).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def update_member_role(self, request, pk=None):
        """Update a member's role in the workspace."""
        workspace = self.get_object()
        if not workspace.can_user_manage_members(request.user):
            return Response(
                {"error": "You don't have permission to manage members"},
                status=status.HTTP_403_FORBIDDEN,
            )

        member_id = request.data.get("member_id")
        new_role = request.data.get("role")

        if not member_id or not new_role:
            return Response(
                {"error": "member_id and role are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            membership = WorkspaceMembership.objects.get(workspace=workspace, id=member_id, is_active=True)
        except WorkspaceMembership.DoesNotExist:
            return Response(
                {"error": "Member not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if new_role == Workspace.Role.OWNER:
            return Response(
                {"error": "Use transfer_ownership to change owner"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_role = membership.role
        membership.role = new_role
        membership.save()

        ActivityFeed.objects.create(
            workspace=workspace,
            user=request.user,
            action=ActivityFeed.Action.UPDATED,
            target_type="WorkspaceMembership",
            target_id=membership.id,
            target_name=membership.user.username,
            metadata={"old_role": old_role, "new_role": new_role},
        )

        return Response(WorkspaceMembershipSerializer(membership).data)

    @action(detail=True, methods=["post"])
    def remove_member(self, request, pk=None):
        """Remove a member from the workspace."""
        workspace = self.get_object()
        if not workspace.can_user_manage_members(request.user):
            return Response(
                {"error": "You don't have permission to manage members"},
                status=status.HTTP_403_FORBIDDEN,
            )

        member_id = request.data.get("member_id")
        if not member_id:
            return Response(
                {"error": "member_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            membership = WorkspaceMembership.objects.get(workspace=workspace, id=member_id, is_active=True)
        except WorkspaceMembership.DoesNotExist:
            return Response(
                {"error": "Member not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if membership.role == Workspace.Role.OWNER:
            return Response(
                {"error": "Cannot remove workspace owner"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        membership.is_active = False
        membership.save()

        ActivityFeed.objects.create(
            workspace=workspace,
            user=request.user,
            action=ActivityFeed.Action.MEMBER_LEFT,
            target_type="WorkspaceMembership",
            target_name=membership.user.username,
        )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def transfer_ownership(self, request, pk=None):
        """Transfer workspace ownership to another member."""
        workspace = self.get_object()
        if workspace.owner != request.user:
            return Response(
                {"error": "Only workspace owner can transfer ownership"},
                status=status.HTTP_403_FORBIDDEN,
            )

        member_id = request.data.get("member_id")
        if not member_id:
            return Response(
                {"error": "member_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            membership = WorkspaceMembership.objects.get(workspace=workspace, id=member_id, is_active=True)
        except WorkspaceMembership.DoesNotExist:
            return Response(
                {"error": "Member not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        old_owner = workspace.owner
        workspace.owner = membership.user
        workspace.save()

        membership.role = Workspace.Role.OWNER
        membership.save()

        WorkspaceMembership.objects.update_or_create(
            workspace=workspace,
            user=old_owner,
            defaults={
                "role": Workspace.Role.ADMIN,
                "is_active": True,
            },
        )

        ActivityFeed.objects.create(
            workspace=workspace,
            user=request.user,
            action=ActivityFeed.Action.UPDATED,
            target_type="Workspace",
            target_id=workspace.id,
            target_name=workspace.name,
            metadata={"action": "ownership_transferred", "new_owner": membership.user.username},
        )

        return Response(WorkspaceSerializer(workspace, context={"request": request}).data)


class InvitationAcceptView(APIView):
    """Accept a workspace invitation."""

    permission_classes = [IsAuthenticated]

    def post(self, request, token):
        try:
            invitation = WorkspaceInvitation.objects.get(
                token=token,
                status=WorkspaceInvitation.Status.PENDING,
            )
        except WorkspaceInvitation.DoesNotExist:
            return Response(
                {"error": "Invalid or expired invitation"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if invitation.is_expired():
            invitation.status = WorkspaceInvitation.Status.EXPIRED
            invitation.save()
            return Response(
                {"error": "Invitation has expired"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_email = request.user.email
        if user_email.lower() != invitation.email.lower():
            return Response(
                {"error": "This invitation is for a different email address"},
                status=status.HTTP_403_FORBIDDEN,
            )

        existing = WorkspaceMembership.objects.filter(
            workspace=invitation.workspace,
            user=request.user,
            is_active=True,
        ).exists()
        if existing:
            return Response(
                {"error": "You are already a member of this workspace"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        WorkspaceMembership.objects.create(
            workspace=invitation.workspace,
            user=request.user,
            role=invitation.role,
            invited_by=invitation.invited_by,
        )

        invitation.status = WorkspaceInvitation.Status.ACCEPTED
        invitation.responded_at = timezone.now()
        invitation.save()

        ActivityFeed.objects.create(
            workspace=invitation.workspace,
            user=request.user,
            action=ActivityFeed.Action.INVITATION_ACCEPTED,
            target_type="WorkspaceMembership",
            target_name=request.user.username,
        )

        return Response({"message": "Successfully joined workspace"})


class FindingCommentViewSet(viewsets.ModelViewSet):
    """API for comments on findings."""

    permission_classes = [IsAuthenticated]
    serializer_class = FindingCommentSerializer

    def get_queryset(self):
        user = self.request.user
        workspace_id = self.request.query_params.get("workspace_id")
        content_type = self.request.query_params.get("content_type")
        object_id = self.request.query_params.get("object_id")

        queryset = FindingComment.objects.filter(
            workspace__memberships__user=user,
            workspace__memberships__is_active=True,
            workspace__is_active=True,
        ).distinct()

        if workspace_id:
            queryset = queryset.filter(workspace_id=workspace_id)
        if content_type:
            queryset = queryset.filter(content_type=content_type)
        if object_id:
            queryset = queryset.filter(object_id=object_id)

        return queryset

    def perform_create(self, serializer):
        comment = serializer.save(user=self.request.user)
        ActivityFeed.objects.create(
            workspace=comment.workspace,
            user=self.request.user,
            action=ActivityFeed.Action.COMMENT_ADDED,
            target_type=comment.content_type,
            target_id=comment.object_id,
            target_name=f"Comment by {self.request.user.username}",
        )

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        """Mark a comment as resolved."""
        comment = self.get_object()
        comment.mark_resolved(request.user)
        return Response(FindingCommentSerializer(comment).data)
