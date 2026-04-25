"""
Plugin API views.
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models_plugin import (
    Plugin,
    PluginExecutionLog,
    PluginInstallation,
    PluginSecurityScan,
    PluginVersion,
)
from .plugin_registry import PluginRegistry, PluginSecurityScanner
from .serializers_plugin import (
    PluginConfigUpdateSerializer,
    PluginCreateSerializer,
    PluginInstallationSerializer,
    PluginInstallSerializer,
    PluginSerializer,
    PluginVersionSerializer,
)


class PluginViewSet(viewsets.ModelViewSet):
    """
    API endpoints for plugin marketplace management.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = PluginSerializer

    def get_queryset(self):
        queryset = Plugin.objects.filter(status=Plugin.Status.PUBLISHED)

        query = self.request.query_params.get("query")
        category = self.request.query_params.get("category")
        tags = self.request.query_params.get("tags")
        sort_by = self.request.query_params.get("sort_by", "downloads")

        if query:
            queryset = (
                queryset.filter(name__icontains=query)
                | queryset.filter(description__icontains=query)
                | queryset.filter(tags__contains=[query])
            )

        if category:
            queryset = queryset.filter(category=category)

        if tags:
            for tag in tags.split(","):
                queryset = queryset.filter(tags__contains=[tag.strip()])

        if sort_by == "downloads":
            queryset = queryset.order_by("-download_count")
        elif sort_by == "rating":
            queryset = queryset.order_by("-rating")
        elif sort_by == "recent":
            queryset = queryset.order_by("-created_at")
        elif sort_by == "name":
            queryset = queryset.order_by("name")

        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return PluginCreateSerializer
        return PluginSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        source_code = serializer.validated_data.get("source_code")
        if source_code:
            scan_result = PluginSecurityScanner.scan_source(source_code)
            if not scan_result["is_passed"]:
                return Response(
                    {"security_scan": scan_result, "message": "Security scan failed"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        instance = serializer.save()
        return Response(
            PluginSerializer(instance, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"])
    def versions(self, request, pk=None):
        """Get all versions of a plugin."""
        plugin = self.get_object()
        versions = PluginVersion.objects.filter(plugin=plugin)
        return Response(PluginVersionSerializer(versions, many=True).data)

    @action(detail=True, methods=["post"])
    def install(self, request, pk=None):
        """Install a plugin."""
        plugin = self.get_object()
        serializer = PluginInstallSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        installation = PluginInstallation.objects.filter(
            plugin=plugin,
            workspace_id=serializer.validated_data.get("workspace_id"),
            status__in=[
                PluginInstallation.InstallStatus.INSTALLED,
                PluginInstallation.InstallStatus.UPDATE_AVAILABLE,
            ],
        ).first()

        if installation:
            return Response(
                {"error": "Plugin already installed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        installation = PluginInstallation.objects.create(
            plugin=plugin,
            installed_by=request.user,
            workspace_id=serializer.validated_data.get("workspace_id"),
            installed_version=plugin.version,
            config=serializer.validated_data.get("config", {}),
        )

        plugin.installed_count += 1
        plugin.save()

        PluginRegistry.register(
            name=plugin.name,
            slug=plugin.slug,
            version=plugin.version,
            description=plugin.description,
            category=plugin.category,
            author=plugin.author,
            entry_point=plugin.entry_point,
            config_schema=plugin.config_schema,
            required_permissions=plugin.required_permissions,
            tags=plugin.tags,
        )

        return Response(
            PluginInstallationSerializer(installation).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def update_config(self, request, pk=None):
        """Update plugin configuration."""
        plugin = self.get_object()
        serializer = PluginConfigUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        installation = PluginInstallation.objects.filter(
            plugin=plugin,
            installed_by=request.user,
        ).first()

        if not installation:
            return Response(
                {"error": "Plugin not installed"},
                status=status.HTTP_404_NOT_FOUND,
            )

        installation.config = serializer.validated_data["config"]
        installation.save()

        return Response(PluginInstallationSerializer(installation).data)

    @action(detail=True, methods=["post"])
    def scan_security(self, request, pk=None):
        """Run security scan on plugin source code."""
        plugin = self.get_object()

        if not plugin.source_code:
            return Response(
                {"error": "No source code available for scanning"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        scan_result = PluginSecurityScanner.scan_source(plugin.source_code)

        security_scan = PluginSecurityScan.objects.create(
            plugin=plugin,
            scan_version="1.0",
            issues_found=scan_result["issues_found"],
            severity_counts=scan_result["severity_counts"],
            is_passed=scan_result["is_passed"],
        )

        plugin.security_scanned_at = security_scan.scanned_at
        plugin.security_scan_result = scan_result
        plugin.save()

        return Response(scan_result)


class PluginInstallationViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing plugin installations.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = PluginInstallationSerializer
    http_method_names = ["get", "delete", "patch"]

    def get_queryset(self):
        return PluginInstallation.objects.filter(
            installed_by=self.request.user,
            status__in=[
                PluginInstallation.InstallStatus.INSTALLED,
                PluginInstallation.InstallStatus.UPDATE_AVAILABLE,
            ],
        )

    @action(detail=True, methods=["post"])
    def execute(self, request, pk=None):
        """Execute an installed plugin."""
        installation = self.get_object()

        if installation.status == PluginInstallation.InstallStatus.REMOVED:
            return Response(
                {"error": "Plugin is not installed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        input_data = request.data.get("input_data", {})

        execution_log = PluginExecutionLog.objects.create(
            installation=installation,
            input_data=input_data,
            status=PluginExecutionLog.ExecutionStatus.PENDING,
        )

        result = PluginRegistry.execute(
            installation.plugin.slug,
            {**installation.config, **input_data},
            context={"user_id": request.user.id},
        )

        execution_log.status = (
            PluginExecutionLog.ExecutionStatus.SUCCESS if result.success else PluginExecutionLog.ExecutionStatus.FAILED
        )
        execution_log.output_data = result.output or {}
        execution_log.error_message = result.error
        execution_log.duration_ms = result.duration_ms
        execution_log.completed_at = execution_log.started_at

        if result.success:
            installation.last_run_at = execution_log.started_at
            installation.save()

        execution_log.save()

        return Response(
            {
                "success": result.success,
                "output": result.output,
                "error": result.error,
                "duration_ms": result.duration_ms,
                "log_id": execution_log.id,
            }
        )

    @action(detail=True, methods=["post"])
    def uninstall(self, request, pk=None):
        """Uninstall a plugin."""
        installation = self.get_object()

        installation.status = PluginInstallation.InstallStatus.REMOVED
        installation.save()

        PluginRegistry.unregister(installation.plugin.slug)

        return Response({"message": "Plugin uninstalled successfully"})

    @action(detail=True, methods=["post"])
    def enable(self, request, pk=None):
        """Enable an installed plugin."""
        installation = self.get_object()
        installation.is_enabled = True
        installation.save()
        return Response(PluginInstallationSerializer(installation).data)

    @action(detail=True, methods=["post"])
    def disable(self, request, pk=None):
        """Disable an installed plugin."""
        installation = self.get_object()
        installation.is_enabled = False
        installation.save()
        return Response(PluginInstallationSerializer(installation).data)

    @action(detail=True, methods=["get"])
    def logs(self, request, pk=None):
        """Get execution logs for an installation."""
        installation = self.get_object()
        logs = PluginExecutionLog.objects.filter(installation=installation)[:50]
        from .serializers_plugin import PluginExecutionLogSerializer

        return Response(PluginExecutionLogSerializer(logs, many=True).data)
