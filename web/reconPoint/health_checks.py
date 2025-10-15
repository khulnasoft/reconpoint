"""
Health check and system monitoring utilities for reconPoint.
"""
import logging
import psutil
from datetime import datetime
from typing import Dict, Any, List, Tuple

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.views import View
from celery import current_app as celery_app

try:
    from .platform_utils import get_platform_detector, get_performance_monitor
    PLATFORM_UTILS_AVAILABLE = True
except ImportError:
    PLATFORM_UTILS_AVAILABLE = False

logger = logging.getLogger(__name__)


class HealthStatus:
    """Health status constants."""
    HEALTHY = 'healthy'
    DEGRADED = 'degraded'
    UNHEALTHY = 'unhealthy'


class HealthCheck:
    """Base health check class."""
    
    def __init__(self, name: str):
        self.name = name
    
    def check(self) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Perform health check.
        
        Returns:
            Tuple of (is_healthy, status_message, details_dict)
        """
        raise NotImplementedError


class DatabaseHealthCheck(HealthCheck):
    """Check database connectivity and performance."""
    
    def __init__(self):
        super().__init__('database')
    
    def check(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Check database health."""
        try:
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            # Get database stats
            details = {
                'connected': True,
                'vendor': connection.vendor,
                'queries_executed': len(connection.queries) if settings.DEBUG else 'N/A'
            }
            
            return True, 'Database is healthy', details
        
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False, f'Database error: {str(e)}', {'connected': False}


class RedisHealthCheck(HealthCheck):
    """Check Redis connectivity and performance."""
    
    def __init__(self):
        super().__init__('redis')
    
    def check(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Check Redis health."""
        try:
            # Test cache connection
            test_key = 'health_check_test'
            test_value = 'test'
            
            cache.set(test_key, test_value, 10)
            retrieved_value = cache.get(test_key)
            cache.delete(test_key)
            
            if retrieved_value != test_value:
                return False, 'Redis read/write test failed', {'connected': True, 'rw_test': False}
            
            details = {
                'connected': True,
                'rw_test': True
            }
            
            return True, 'Redis is healthy', details
        
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False, f'Redis error: {str(e)}', {'connected': False}


class CeleryHealthCheck(HealthCheck):
    """Check Celery worker status."""
    
    def __init__(self):
        super().__init__('celery')
    
    def check(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Check Celery health."""
        try:
            # Get active workers
            inspect = celery_app.control.inspect()
            active_workers = inspect.active()
            
            if not active_workers:
                return False, 'No active Celery workers', {'workers': 0}
            
            worker_count = len(active_workers)
            
            # Get stats
            stats = inspect.stats()
            
            details = {
                'workers': worker_count,
                'worker_names': list(active_workers.keys()),
                'stats_available': stats is not None
            }
            
            return True, f'{worker_count} Celery worker(s) active', details
        
        except Exception as e:
            logger.error(f"Celery health check failed: {e}")
            return False, f'Celery error: {str(e)}', {'workers': 0}


class DiskSpaceHealthCheck(HealthCheck):
    """Check available disk space."""
    
    def __init__(self, threshold_percent: int = 90):
        super().__init__('disk_space')
        self.threshold_percent = threshold_percent
    
    def check(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Check disk space."""
        try:
            # Get disk usage
            disk_usage = psutil.disk_usage('/')
            
            percent_used = disk_usage.percent
            
            details = {
                'total_gb': round(disk_usage.total / (1024**3), 2),
                'used_gb': round(disk_usage.used / (1024**3), 2),
                'free_gb': round(disk_usage.free / (1024**3), 2),
                'percent_used': percent_used
            }
            
            if percent_used >= self.threshold_percent:
                return False, f'Disk space critical: {percent_used}% used', details
            
            return True, f'Disk space healthy: {percent_used}% used', details
        
        except Exception as e:
            logger.error(f"Disk space health check failed: {e}")
            return False, f'Disk space check error: {str(e)}', {}


class MemoryHealthCheck(HealthCheck):
    """Check available memory."""
    
    def __init__(self, threshold_percent: int = 90):
        super().__init__('memory')
        self.threshold_percent = threshold_percent
    
    def check(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Check memory usage."""
        try:
            # Get memory usage
            memory = psutil.virtual_memory()
            
            percent_used = memory.percent
            
            details = {
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'percent_used': percent_used
            }
            
            if percent_used >= self.threshold_percent:
                return False, f'Memory critical: {percent_used}% used', details
            
            return True, f'Memory healthy: {percent_used}% used', details
        
        except Exception as e:
            logger.error(f"Memory health check failed: {e}")
            return False, f'Memory check error: {str(e)}', {}


class HealthCheckManager:
    """Manage and execute all health checks."""
    
    def __init__(self):
        self.checks: List[HealthCheck] = [
            DatabaseHealthCheck(),
            RedisHealthCheck(),
            CeleryHealthCheck(),
            DiskSpaceHealthCheck(threshold_percent=90),
            MemoryHealthCheck(threshold_percent=90)
        ]
    
    def run_all_checks(self) -> Dict[str, Any]:
        """
        Run all health checks.
        
        Returns:
            Dictionary with health check results
        """
        results = {}
        overall_healthy = True
        
        for check in self.checks:
            try:
                is_healthy, message, details = check.check()
                
                results[check.name] = {
                    'status': HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY,
                    'message': message,
                    'details': details
                }
                
                if not is_healthy:
                    overall_healthy = False
            
            except Exception as e:
                logger.error(f"Health check {check.name} failed with exception: {e}")
                results[check.name] = {
                    'status': HealthStatus.UNHEALTHY,
                    'message': f'Check failed: {str(e)}',
                    'details': {}
                }
                overall_healthy = False
        
        return {
            'status': HealthStatus.HEALTHY if overall_healthy else HealthStatus.UNHEALTHY,
            'timestamp': datetime.utcnow().isoformat(),
            'version': getattr(settings, 'RECONPOINT_CURRENT_VERSION', 'unknown'),
            'checks': results
        }
    
    def run_check(self, check_name: str) -> Dict[str, Any]:
        """
        Run a specific health check.
        
        Args:
            check_name: Name of the check to run
            
        Returns:
            Dictionary with health check result
        """
        for check in self.checks:
            if check.name == check_name:
                try:
                    is_healthy, message, details = check.check()
                    return {
                        'status': HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY,
                        'message': message,
                        'details': details
                    }
                except Exception as e:
                    return {
                        'status': HealthStatus.UNHEALTHY,
                        'message': f'Check failed: {str(e)}',
                        'details': {}
                    }
        
        return {
            'status': HealthStatus.UNHEALTHY,
            'message': f'Check {check_name} not found',
            'details': {}
        }


class HealthCheckView(View):
    """View for health check endpoint."""
    
    def get(self, request):
        """Handle GET request for health check."""
        manager = HealthCheckManager()
        
        # Check if specific check is requested
        check_name = request.GET.get('check')
        
        if check_name:
            result = manager.run_check(check_name)
            status_code = 200 if result['status'] == HealthStatus.HEALTHY else 503
        else:
            result = manager.run_all_checks()
            status_code = 200 if result['status'] == HealthStatus.HEALTHY else 503
        
        return JsonResponse(result, status=status_code)


class ReadinessCheckView(View):
    """View for Kubernetes readiness probe."""
    
    def get(self, request):
        """Handle GET request for readiness check."""
        manager = HealthCheckManager()
        
        # Only check critical services for readiness
        critical_checks = ['database', 'redis', 'celery']
        
        all_ready = True
        results = {}
        
        for check_name in critical_checks:
            result = manager.run_check(check_name)
            results[check_name] = result
            if result['status'] != HealthStatus.HEALTHY:
                all_ready = False
        
        response_data = {
            'ready': all_ready,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': results
        }
        
        status_code = 200 if all_ready else 503
        return JsonResponse(response_data, status=status_code)


class LivenessCheckView(View):
    """View for Kubernetes liveness probe."""
    
    def get(self, request):
        """Handle GET request for liveness check."""
        # Simple liveness check - just verify the application is running
        return JsonResponse({
            'alive': True,
            'timestamp': datetime.utcnow().isoformat(),
            'version': getattr(settings, 'RECONPOINT_CURRENT_VERSION', 'unknown')
        })


class MetricsView(View):
    """View for application metrics."""
    
    def get(self, request):
        """Handle GET request for metrics."""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Database metrics
            from startScan.models import ScanHistory
            from targetApp.models import Domain
            
            total_scans = ScanHistory.objects.count()
            total_domains = Domain.objects.count()
            
            # Celery metrics
            inspect = celery_app.control.inspect()
            active_tasks = inspect.active()
            scheduled_tasks = inspect.scheduled()
            
            active_task_count = sum(len(tasks) for tasks in (active_tasks or {}).values())
            scheduled_task_count = sum(len(tasks) for tasks in (scheduled_tasks or {}).values())
            
            metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_gb': round(memory.available / (1024**3), 2),
                    'disk_percent': disk.percent,
                    'disk_free_gb': round(disk.free / (1024**3), 2)
                },
                'application': {
                    'total_scans': total_scans,
                    'total_domains': total_domains,
                    'version': getattr(settings, 'RECONPOINT_CURRENT_VERSION', 'unknown')
                },
                'celery': {
                    'active_tasks': active_task_count,
                    'scheduled_tasks': scheduled_task_count,
                    'workers': len(active_tasks or {})
                }
            }
            
            # Add platform information if available
            if PLATFORM_UTILS_AVAILABLE:
                try:
                    detector = get_platform_detector()
                    monitor = get_performance_monitor()
                    
                    platform_info = detector.get_platform_info()
                    metrics['platform'] = {
                        'type': platform_info['platform_type'],
                        'architecture': platform_info['architecture'],
                        'is_arm': platform_info['is_arm'],
                        'is_raspberry_pi': platform_info['is_raspberry_pi'],
                        'cpu_cores': platform_info['cpu_count'],
                        'total_memory_gb': platform_info['total_memory_gb']
                    }
                    
                    # Add temperature for Raspberry Pi
                    temp = monitor.get_temperature()
                    if temp is not None:
                        metrics['platform']['temperature_celsius'] = round(temp, 1)
                    
                    # Add resource warnings
                    warnings = monitor.get_resource_warnings()
                    if warnings:
                        metrics['warnings'] = warnings
                    
                except Exception as e:
                    logger.warning(f"Failed to add platform info to metrics: {e}")
            
            return JsonResponse(metrics)
        
        except Exception as e:
            logger.error(f"Metrics collection failed: {e}")
            return JsonResponse({
                'error': 'Failed to collect metrics',
                'detail': str(e)
            }, status=500)
