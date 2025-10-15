"""
Health check endpoints for reconPoint.
Provides health, readiness, and liveness probes for container orchestration.
"""
import logging
from typing import Dict, Any
from datetime import datetime

from django.conf import settings
from django.db import connection
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from reconPoint.celery import app as celery_app
from reconPoint.metrics import get_system_metrics, get_performance_metrics

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """
    Basic health check endpoint.
    Returns 200 if the application is running.
    """
    
    permission_classes = []  # Allow unauthenticated access
    authentication_classes = []
    
    def get(self, request):
        """
        GET /health
        
        Returns:
            200 OK with basic health status
        """
        return Response({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': getattr(settings, 'RECONPOINT_CURRENT_VERSION', 'unknown')
        })


class ReadinessCheckView(APIView):
    """
    Readiness check endpoint.
    Returns 200 if the application is ready to serve traffic.
    Checks database, cache, and Celery connectivity.
    """
    
    permission_classes = []
    authentication_classes = []
    
    def get(self, request):
        """
        GET /readiness
        
        Returns:
            200 OK if ready, 503 Service Unavailable if not ready
        """
        checks = {
            'database': self._check_database(),
            'cache': self._check_cache(),
            'celery': self._check_celery()
        }
        
        all_healthy = all(check['healthy'] for check in checks.values())
        
        response_data = {
            'status': 'ready' if all_healthy else 'not_ready',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': checks
        }
        
        status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return Response(response_data, status=status_code)
    
    def _check_database(self) -> Dict[str, Any]:
        """
        Check database connectivity.
        
        Returns:
            Dictionary with health status
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            return {
                'healthy': True,
                'message': 'Database connection successful'
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'healthy': False,
                'message': f'Database connection failed: {str(e)}'
            }
    
    def _check_cache(self) -> Dict[str, Any]:
        """
        Check cache connectivity.
        
        Returns:
            Dictionary with health status
        """
        try:
            test_key = 'health_check_test'
            test_value = 'test'
            
            cache.set(test_key, test_value, 10)
            retrieved_value = cache.get(test_key)
            
            if retrieved_value == test_value:
                cache.delete(test_key)
                return {
                    'healthy': True,
                    'message': 'Cache connection successful'
                }
            else:
                return {
                    'healthy': False,
                    'message': 'Cache read/write test failed'
                }
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                'healthy': False,
                'message': f'Cache connection failed: {str(e)}'
            }
    
    def _check_celery(self) -> Dict[str, Any]:
        """
        Check Celery connectivity.
        
        Returns:
            Dictionary with health status
        """
        try:
            # Check if Celery workers are available
            inspect = celery_app.control.inspect()
            stats = inspect.stats()
            
            if stats:
                worker_count = len(stats)
                return {
                    'healthy': True,
                    'message': f'Celery workers available: {worker_count}'
                }
            else:
                return {
                    'healthy': False,
                    'message': 'No Celery workers available'
                }
        except Exception as e:
            logger.error(f"Celery health check failed: {e}")
            return {
                'healthy': False,
                'message': f'Celery connection failed: {str(e)}'
            }


class LivenessCheckView(APIView):
    """
    Liveness check endpoint.
    Returns 200 if the application process is alive.
    This is a simple check that doesn't verify dependencies.
    """
    
    permission_classes = []
    authentication_classes = []
    
    def get(self, request):
        """
        GET /liveness
        
        Returns:
            200 OK if alive
        """
        return Response({
            'status': 'alive',
            'timestamp': datetime.utcnow().isoformat()
        })


class MetricsView(APIView):
    """
    Metrics endpoint for monitoring.
    Returns application metrics in JSON format.
    """
    
    permission_classes = []
    authentication_classes = []
    
    def get(self, request):
        """
        GET /metrics
        
        Returns:
            200 OK with metrics data
        """
        try:
            system_metrics = get_system_metrics()
            performance_metrics = get_performance_metrics()
            
            return Response({
                'system': system_metrics,
                'performance': performance_metrics,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            return Response(
                {
                    'error': 'Failed to collect metrics',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PrometheusMetricsView(APIView):
    """
    Prometheus metrics endpoint.
    Returns metrics in Prometheus text format.
    """
    
    permission_classes = []
    authentication_classes = []
    
    def get(self, request):
        """
        GET /metrics/prometheus
        
        Returns:
            200 OK with Prometheus-formatted metrics
        """
        from reconPoint.metrics import export_prometheus_metrics
        
        try:
            metrics_text = export_prometheus_metrics()
            
            from django.http import HttpResponse
            return HttpResponse(
                metrics_text,
                content_type='text/plain; version=0.0.4'
            )
        except Exception as e:
            logger.error(f"Failed to export Prometheus metrics: {e}")
            return Response(
                {
                    'error': 'Failed to export metrics',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SystemStatusView(APIView):
    """
    Comprehensive system status endpoint.
    Returns detailed information about the system state.
    """
    
    def get(self, request):
        """
        GET /api/system/status
        
        Returns:
            200 OK with system status
        """
        try:
            system_metrics = get_system_metrics()
            
            # Get database info
            from django.db import connection
            db_vendor = connection.vendor
            
            # Get Celery info
            inspect = celery_app.control.inspect()
            active_tasks = inspect.active()
            scheduled_tasks = inspect.scheduled()
            
            active_task_count = sum(len(tasks) for tasks in (active_tasks or {}).values())
            scheduled_task_count = sum(len(tasks) for tasks in (scheduled_tasks or {}).values())
            
            return Response({
                'status': 'operational',
                'version': getattr(settings, 'RECONPOINT_CURRENT_VERSION', 'unknown'),
                'debug_mode': settings.DEBUG,
                'database': {
                    'vendor': db_vendor,
                    'connected': True
                },
                'celery': {
                    'active_tasks': active_task_count,
                    'scheduled_tasks': scheduled_task_count
                },
                'metrics': system_metrics,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return Response(
                {
                    'status': 'error',
                    'error': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
