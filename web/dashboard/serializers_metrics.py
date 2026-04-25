"""
Metrics API serializers.
"""

from rest_framework import serializers

from .models_metrics import (
    ComplianceMapping,
    ComplianceRequirement,
    Metric,
    MetricHistory,
    MetricThreshold,
    SLAPolicy,
)


class MetricSerializer(serializers.ModelSerializer):
    thresholds = serializers.SerializerMethodField()

    class Meta:
        model = Metric
        fields = [
            "id",
            "name",
            "slug",
            "metric_type",
            "calculation",
            "display_config",
            "data_source",
            "is_enabled",
            "is_visible",
            "threshold_config",
            "created_at",
            "updated_at",
            "created_by",
            "thresholds",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_thresholds(self, obj):
        thresholds = obj.thresholds.filter(is_active=True)
        return MetricThresholdSerializer(thresholds, many=True).data


class MetricThresholdSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetricThreshold
        fields = [
            "id",
            "severity",
            "operator",
            "value",
            "description",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class MetricHistorySerializer(serializers.ModelSerializer):
    metric_name = serializers.CharField(source="metric.name", read_only=True)

    class Meta:
        model = MetricHistory
        fields = [
            "id",
            "metric",
            "metric_name",
            "value",
            "target_id",
            "calculated_at",
        ]
        read_only_fields = ["id", "calculated_at"]


class SLAPolicySerializer(serializers.ModelSerializer):
    breached = serializers.SerializerMethodField()
    remaining_hours = serializers.SerializerMethodField()

    class Meta:
        model = SLAPolicy
        fields = [
            "id",
            "name",
            "description",
            "severity_level",
            "response_time_hours",
            "resolution_time_hours",
            "escalation_enabled",
            "escalation_rules",
            "notification_channels",
            "is_active",
            "created_at",
            "updated_at",
            "breached",
            "remaining_hours",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_breached(self, obj):
        return False

    def get_remaining_hours(self, obj):
        return None


class SLAPolicyWithStatusSerializer(SLAPolicySerializer):
    vulnerability_count = serializers.SerializerMethodField()

    class Meta:
        model = SLAPolicy
        fields = SLAPolicySerializer.Meta.fields + ["vulnerability_count"]

    def get_vulnerability_count(self, obj):
        from startScan.models import Vulnerability

        return Vulnerability.objects.filter(
            severity=obj.severity_level,
            status__in=[Vulnerability.STATUS_OPEN, Vulnerability.STATUS_IN_PROGRESS],
        ).count()


class ComplianceRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceRequirement
        fields = [
            "id",
            "name",
            "description",
            "standard",
            "is_mandatory",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ComplianceMappingSerializer(serializers.ModelSerializer):
    metric_name = serializers.CharField(source="metric.name", read_only=True)
    requirement_name = serializers.CharField(source="requirement.name", read_only=True)
    standard = serializers.CharField(source="requirement.standard", read_only=True)

    class Meta:
        model = ComplianceMapping
        fields = [
            "id",
            "metric",
            "metric_name",
            "requirement",
            "requirement_name",
            "standard",
        ]
        read_only_fields = ["id"]


class MetricCalculationRequestSerializer(serializers.Serializer):
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    target_id = serializers.IntegerField(required=False, allow_null=True)
    workspace_id = serializers.IntegerField(required=False, allow_null=True)


class MetricTrendSerializer(serializers.Serializer):
    date = serializers.DateField()
    value = serializers.FloatField()


class AggregatedMetricsSerializer(serializers.Serializer):
    period_days = serializers.IntegerField()
    total_vulnerabilities = serializers.IntegerField()
    open_vulnerabilities = serializers.IntegerField()
    resolved_vulnerabilities = serializers.IntegerField()
    closure_rate = serializers.FloatField()
    by_severity = serializers.DictField()
