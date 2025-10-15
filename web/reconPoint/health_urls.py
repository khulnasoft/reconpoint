"""
URL configuration for health check and monitoring endpoints.
"""
from django.urls import path
from reconPoint.health_checks import (
    HealthCheckView,
    ReadinessCheckView,
    LivenessCheckView,
    MetricsView
)


urlpatterns = [
    # Health check endpoints
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('healthz/', HealthCheckView.as_view(), name='health-check-alt'),
    
    # Kubernetes probes
    path('readiness/', ReadinessCheckView.as_view(), name='readiness-check'),
    path('liveness/', LivenessCheckView.as_view(), name='liveness-check'),
    
    # Metrics endpoint
    path('metrics/', MetricsView.as_view(), name='metrics'),
]
