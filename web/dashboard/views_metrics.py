"""
Metrics API views.
"""

from datetime import timedelta

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .metrics_services import (
    calculate_metric_value,
    get_aggregated_metrics,
    get_sla_status,
)
from .models_metrics import (
    ComplianceMapping,
    ComplianceRequirement,
    Metric,
    MetricHistory,
    MetricThreshold,
    SLAPolicy,
)
from .serializers_metrics import (
    AggregatedMetricsSerializer,
    ComplianceMappingSerializer,
    ComplianceRequirementSerializer,
    MetricCalculationRequestSerializer,
    MetricHistorySerializer,
    MetricSerializer,
    MetricThresholdSerializer,
    SLAPolicySerializer,
    SLAPolicyWithStatusSerializer,
)


class MetricViewSet(viewsets.ModelViewSet):
    """
    API endpoints for metric management.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = MetricSerializer

    def get_queryset(self):
        return Metric.objects.filter(
            is_visible=True,
        ).order_by("name")

    def get_serializer_class(self):
        if self.action == "update" or self.action == "partial_update":
            from .serializers_metrics import MetricSerializer

            return MetricSerializer
        return MetricSerializer

    @action(detail=True, methods=["post"])
    def calculate(self, request, pk=None):
        """
        Calculate metric value for a date range.
        """
        metric = self.get_object()
        serializer = MetricCalculationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        result = calculate_metric_value(
            metric,
            data["start_date"],
            data["end_date"],
        )

        MetricHistory.objects.create(
            metric=metric,
            value=result.get("value", 0),
            target_id=data.get("target_id"),
        )

        return Response(result)

    @action(detail=False, methods=["get"])
    def history(self, request):
        """
        Get historical values for a metric.
        """
        metric_id = request.query_params.get("metric_id")
        days = int(request.query_params.get("days", 30))

        queryset = MetricHistory.objects.filter(
            metric_id=metric_id,
            calculated_at__gte=timezone.now() - timedelta(days=days),
        ).order_by("-calculated_at")

        serializer = MetricHistorySerializer(queryset, many=True)
        return Response(serializer.data)


class MetricThresholdViewSet(viewsets.ModelViewSet):
    """
    API endpoints for metric thresholds.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = MetricThresholdSerializer

    def get_queryset(self):
        return MetricThreshold.objects.all()


class MetricHistoryViewSet(viewsets.ModelViewSet):
    """
    API endpoints for metric history.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = MetricHistorySerializer

    def get_queryset(self):
        return MetricHistory.objects.all()


class SLAPolicyViewSet(viewsets.ModelViewSet):
    """
    API endpoints for SLA policies.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = SLAPolicySerializer

    def get_queryset(self):
        return SLAPolicy.objects.filter(is_active=True).order_by("severity_level")

    def get_serializer_class(self):
        if self.action == "list":
            return SLAPolicyWithStatusSerializer
        return SLAPolicySerializer


class ComplianceRequirementViewSet(viewsets.ModelViewSet):
    """
    API endpoints for compliance requirements.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ComplianceRequirementSerializer

    def get_queryset(self):
        return ComplianceRequirement.objects.all()


class ComplianceMappingViewSet(viewsets.ModelViewSet):
    """
    API endpoints for compliance mappings.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ComplianceMappingSerializer

    def get_queryset(self):
        return ComplianceMapping.objects.all()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def aggregated_metrics_view(request):
    """
    Get aggregated metrics for a target or workspace.
    """
    target_id = request.query_params.get("target_id")
    workspace_id = request.query_params.get("workspace_id")
    days = int(request.query_params.get("days", 30))

    if not target_id and not workspace_id:
        return Response(
            {"error": "target_id or workspace_id required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    result = get_aggregated_metrics(
        target_id=int(target_id) if target_id else None,
        workspace_id=int(workspace_id) if workspace_id else None,
        days=days,
    )

    serializer = AggregatedMetricsSerializer(result)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def vulnerability_sla_status_view(request, vuln_id):
    """
    Get SLA status for a specific vulnerability.
    """
    from startScan.models import Vulnerability

    try:
        vuln = Vulnerability.objects.get(pk=vuln_id)
    except Vulnerability.DoesNotExist:
        return Response(
            {"error": "Vulnerability not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    sla_status = get_sla_status(vuln)
    return Response(sla_status)
