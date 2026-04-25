"""
Metrics URL configuration.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views_metrics import (
    ComplianceMappingViewSet,
    ComplianceRequirementViewSet,
    MetricHistoryViewSet,
    MetricThresholdViewSet,
    MetricViewSet,
    SLAPolicyViewSet,
    aggregated_metrics_view,
    vulnerability_sla_status_view,
)


router = DefaultRouter()
router.register(r"metrics", MetricViewSet, basename="metric")
router.register(r"metric-thresholds", MetricThresholdViewSet, basename="metric-threshold")
router.register(r"metric-history", MetricHistoryViewSet, basename="metric-history")
router.register(r"sla-policies", SLAPolicyViewSet, basename="sla-policy")
router.register(
    r"compliance-requirements",
    ComplianceRequirementViewSet,
    basename="compliance-requirement",
)
router.register(
    r"compliance-mappings",
    ComplianceMappingViewSet,
    basename="compliance-mapping",
)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "aggregated-metrics/",
        aggregated_metrics_view,
        name="aggregated-metrics",
    ),
    path(
        "vulnerability/<int:vuln_id>/sla-status/",
        vulnerability_sla_status_view,
        name="vulnerability-sla-status",
    ),
]
