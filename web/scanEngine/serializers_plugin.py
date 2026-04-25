"""
Plugin API serializers.
"""

from rest_framework import serializers

from .models_plugin import (
    Plugin,
    PluginExecutionLog,
    PluginInstallation,
    PluginSecurityScan,
    PluginVersion,
)


class PluginSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author", read_only=True)
    is_installed = serializers.SerializerMethodField()

    class Meta:
        model = Plugin
        fields = [
            "id",
            "name",
            "slug",
            "version",
            "description",
            "long_description",
            "author",
            "author_name",
            "author_url",
            "homepage_url",
            "repository_url",
            "category",
            "tags",
            "config_schema",
            "required_permissions",
            "status",
            "download_count",
            "rating",
            "rating_count",
            "installed_count",
            "is_verified",
            "is_installed",
            "created_at",
            "updated_at",
        ]

    def get_is_installed(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return PluginInstallation.objects.filter(
            plugin=obj,
            installed_by=request.user,
            status__in=[
                PluginInstallation.InstallStatus.INSTALLED,
                PluginInstallation.InstallStatus.UPDATE_AVAILABLE,
            ],
        ).exists()


class PluginCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plugin
        fields = [
            "name",
            "slug",
            "version",
            "description",
            "long_description",
            "author",
            "author_url",
            "homepage_url",
            "repository_url",
            "category",
            "tags",
            "config_schema",
            "required_permissions",
            "source_code",
            "entry_point",
        ]


class PluginVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PluginVersion
        fields = [
            "id",
            "version",
            "changelog",
            "release_date",
            "is_latest",
        ]


class PluginInstallationSerializer(serializers.ModelSerializer):
    plugin_name = serializers.CharField(source="plugin.name", read_only=True)
    plugin_slug = serializers.CharField(source="plugin.slug", read_only=True)
    plugin_version = serializers.CharField(source="plugin.version", read_only=True)
    installer_name = serializers.CharField(source="installed_by.username", read_only=True)

    class Meta:
        model = PluginInstallation
        fields = [
            "id",
            "plugin",
            "plugin_name",
            "plugin_slug",
            "plugin_version",
            "installed_by",
            "installer_name",
            "workspace_id",
            "installed_version",
            "config",
            "is_enabled",
            "status",
            "installed_at",
            "updated_at",
            "last_run_at",
        ]
        read_only_fields = [
            "installed_by",
            "installed_version",
            "status",
            "installed_at",
            "updated_at",
            "last_run_at",
        ]


class PluginInstallSerializer(serializers.Serializer):
    plugin_id = serializers.IntegerField()
    workspace_id = serializers.IntegerField(required=False, allow_null=True)
    config = serializers.JSONField(required=False, default=dict)


class PluginConfigUpdateSerializer(serializers.Serializer):
    config = serializers.JSONField()


class PluginExecutionLogSerializer(serializers.ModelSerializer):
    plugin_name = serializers.CharField(source="installation.plugin.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = PluginExecutionLog
        fields = [
            "id",
            "installation",
            "plugin_name",
            "input_data",
            "output_data",
            "error_message",
            "status",
            "status_display",
            "duration_ms",
            "started_at",
            "completed_at",
        ]


class PluginExecuteSerializer(serializers.Serializer):
    installation_id = serializers.IntegerField()
    input_data = serializers.JSONField(required=False, default=dict)


class PluginSecurityScanSerializer(serializers.ModelSerializer):
    severity_summary = serializers.SerializerMethodField()

    class Meta:
        model = PluginSecurityScan
        fields = [
            "id",
            "plugin",
            "scan_version",
            "issues_found",
            "severity_counts",
            "severity_summary",
            "is_passed",
            "report_url",
            "scanned_at",
        ]

    def get_severity_summary(self, obj):
        counts = obj.severity_counts or {}
        return f"{counts.get('critical', 0)}C / {counts.get('error', 0)}E / {counts.get('warning', 0)}W"


class PluginSearchSerializer(serializers.Serializer):
    query = serializers.CharField(required=False)
    category = serializers.ChoiceField(
        choices=[(c, c) for c in Plugin._meta.get_field("category").choices],
        required=False,
    )
    tags = serializers.CharField(required=False)
    status = serializers.ChoiceField(
        choices=[(s, s) for s in Plugin._meta.get_field("status").choices],
        required=False,
    )
    sort_by = serializers.ChoiceField(
        choices=["downloads", "rating", "recent", "name"],
        default="downloads",
    )
