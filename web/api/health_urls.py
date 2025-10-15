"""
URL configuration for health check and monitoring endpoints.
"""
from django.urls import path
from api.health import (
    HealthCheckView,
    ReadinessCheckView,
    LivenessCheckView,
    MetricsView,
    PrometheusMetricsView,
    SystemStatusView
)

urlpatterns = [
    # Health check endpoints
    path('health/', HealthCheckView.as_view(), name='health'),
    path('healthz/', HealthCheckView.as_view(), name='healthz'),
    path('readiness/', ReadinessCheckView.as_view(), name='readiness'),
    path('liveness/', LivenessCheckView.as_view(), name='liveness'),
    
    # Metrics endpoints
    path('metrics/', MetricsView.as_view(), name='metrics'),
    path('metrics/prometheus/', PrometheusMetricsView.as_view(), name='prometheus-metrics'),
    
    # System status
    path('api/system/status/', SystemStatusView.as_view(), name='system-status'),
]
