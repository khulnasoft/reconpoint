"""
Workspace API serializers.
"""

from rest_framework import serializers

from .models_workspace import (
    ActivityFeed,
    FindingComment,
    Workspace,
    WorkspaceInvitation,
    WorkspaceMembership,
)


class WorkspaceSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source="owner.username", read_only=True)
    member_count = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = [
            "id",
            "name",
            "description",
            "slug",
            "created_at",
            "updated_at",
            "owner",
            "owner_username",
            "workspace_settings",
            "is_active",
            "member_count",
            "user_role",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "owner"]

    def get_member_count(self, obj):
        return obj.memberships.filter(is_active=True).count()

    def get_user_role(self, obj):
        request = self.context.get("request")
        if request and request.user:
            return obj.get_user_role(request.user)
        return None


class WorkspaceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        fields = ["name", "description", "slug", "workspace_settings"]

    def create(self, validated_data):
        user = self.context["request"].user
        workspace = Workspace.objects.create(owner=user, **validated_data)
        WorkspaceMembership.objects.create(
            workspace=workspace,
            user=user,
            role=Workspace.Role.OWNER,
        )
        return workspace


class WorkspaceMembershipSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = WorkspaceMembership
        fields = [
            "id",
            "workspace",
            "user",
            "username",
            "email",
            "role",
            "joined_at",
            "invited_by",
            "is_active",
        ]
        read_only_fields = ["id", "joined_at", "invited_by"]


class WorkspaceInvitationSerializer(serializers.ModelSerializer):
    workspace_name = serializers.CharField(source="workspace.name", read_only=True)
    invited_by_username = serializers.CharField(source="invited_by.username", read_only=True)
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = WorkspaceInvitation
        fields = [
            "id",
            "workspace",
            "workspace_name",
            "email",
            "role",
            "token",
            "status",
            "invited_by",
            "invited_by_username",
            "created_at",
            "expires_at",
            "responded_at",
            "is_expired",
        ]
        read_only_fields = [
            "id",
            "token",
            "status",
            "invited_by",
            "created_at",
            "expires_at",
            "responded_at",
        ]

    def get_is_expired(self, obj):
        return obj.is_expired()


class ActivityFeedSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    user_avatar = serializers.SerializerMethodField()

    class Meta:
        model = ActivityFeed
        fields = [
            "id",
            "workspace",
            "user",
            "username",
            "user_avatar",
            "action",
            "target_type",
            "target_id",
            "target_name",
            "metadata",
            "created_at",
        ]

    def get_user_avatar(self, obj):
        if obj.user and obj.user.profile:
            return obj.user.profile.avatar.url if hasattr(obj.user.profile, "avatar") else None
        return None


class FindingCommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    resolved_by_username = serializers.CharField(source="resolved_by.username", read_only=True, allow_null=True)

    class Meta:
        model = FindingComment
        fields = [
            "id",
            "workspace",
            "user",
            "username",
            "content_type",
            "object_id",
            "content",
            "created_at",
            "updated_at",
            "is_resolved",
            "resolved_by",
            "resolved_by_username",
            "resolved_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "user", "resolved_by"]


class InviteUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=[(r, r) for r in [Workspace.Role.ADMIN, Workspace.Role.MEMBER, Workspace.Role.VIEWER]],
        default=Workspace.Role.MEMBER,
    )
    invite_message = serializers.CharField(required=False, allow_blank=True)
