"""
Metrics collection and monitoring utilities for reconPoint.
Provides Prometheus-compatible metrics and performance tracking.
"""
import time
import logging
from typing import Dict, Any, Optional, Callable
from functools import wraps
from collections import defaultdict
from datetime import datetime, timedelta
from django.core.cache import cache
from django.db.models import Count, Avg, Max, Min
from django.utils import timezone

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Centralized metrics collector for reconPoint.
    Stores metrics in cache for retrieval by monitoring systems.
    """
    
    CACHE_PREFIX = 'metrics:'
    CACHE_TIMEOUT = 300  # 5 minutes
    
    def __init__(self):
        self.metrics = defaultdict(lambda: defaultdict(int))
    
    def increment(self, metric_name: str, value: int = 1, labels: Optional[Dict[str, str]] = None):
        """
        Increment a counter metric.
        
        Args:
            metric_name: Name of the metric
            value: Value to increment by
            labels: Optional labels for the metric
            
        Example:
            >>> collector = MetricsCollector()
            >>> collector.increment('api_requests_total', labels={'endpoint': '/api/scans/'})
        """
        cache_key = self._get_cache_key(metric_name, labels)
        current_value = cache.get(cache_key, 0)
        cache.set(cache_key, current_value + value, self.CACHE_TIMEOUT)
        
        logger.debug(f"Incremented metric {metric_name} by {value}")
    
    def gauge(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        Set a gauge metric.
        
        Args:
            metric_name: Name of the metric
            value: Value to set
            labels: Optional labels for the metric
            
        Example:
            >>> collector = MetricsCollector()
            >>> collector.gauge('active_scans', 5)
        """
        cache_key = self._get_cache_key(metric_name, labels)
        cache.set(cache_key, value, self.CACHE_TIMEOUT)
        
        logger.debug(f"Set gauge {metric_name} to {value}")
    
    def histogram(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        Record a histogram observation.
        
        Args:
            metric_name: Name of the metric
            value: Value to observe
            labels: Optional labels for the metric
            
        Example:
            >>> collector = MetricsCollector()
            >>> collector.histogram('request_duration_seconds', 0.234)
        """
        cache_key = self._get_cache_key(f"{metric_name}_sum", labels)
        current_sum = cache.get(cache_key, 0.0)
        cache.set(cache_key, current_sum + value, self.CACHE_TIMEOUT)
        
        count_key = self._get_cache_key(f"{metric_name}_count", labels)
        current_count = cache.get(count_key, 0)
        cache.set(count_key, current_count + 1, self.CACHE_TIMEOUT)
        
        logger.debug(f"Recorded histogram {metric_name}: {value}")
    
    def get_metric(self, metric_name: str, labels: Optional[Dict[str, str]] = None) -> Any:
        """
        Get current value of a metric.
        
        Args:
            metric_name: Name of the metric
            labels: Optional labels for the metric
            
        Returns:
            Current metric value
        """
        cache_key = self._get_cache_key(metric_name, labels)
        return cache.get(cache_key, 0)
    
    def _get_cache_key(self, metric_name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """
        Generate cache key for metric.
        
        Args:
            metric_name: Name of the metric
            labels: Optional labels for the metric
            
        Returns:
            Cache key string
        """
        if labels:
            label_str = ','.join(f"{k}={v}" for k, v in sorted(labels.items()))
            return f"{self.CACHE_PREFIX}{metric_name}{{{label_str}}}"
        return f"{self.CACHE_PREFIX}{metric_name}"


# Global metrics collector instance
metrics_collector = MetricsCollector()


def track_execution_time(metric_name: str = None, labels: Optional[Dict[str, str]] = None):
    """
    Decorator to track function execution time.
    
    Args:
        metric_name: Name of the metric (defaults to function name)
        labels: Optional labels for the metric
        
    Returns:
        Decorated function
        
    Example:
        >>> @track_execution_time('scan_duration_seconds')
        ... def run_scan():
        ...     # scan logic
        ...     pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                _metric_name = metric_name or f"{func.__name__}_duration_seconds"
                metrics_collector.histogram(_metric_name, duration, labels)
                
                logger.debug(f"{func.__name__} executed in {duration:.3f}s")
        
        return wrapper
    return decorator


def track_api_request(endpoint: str, method: str, status_code: int, duration: float):
    """
    Track API request metrics.
    
    Args:
        endpoint: API endpoint path
        method: HTTP method
        status_code: HTTP status code
        duration: Request duration in seconds
        
    Example:
        >>> track_api_request('/api/scans/', 'GET', 200, 0.123)
    """
    labels = {
        'endpoint': endpoint,
        'method': method,
        'status': str(status_code)
    }
    
    metrics_collector.increment('api_requests_total', labels=labels)
    metrics_collector.histogram('api_request_duration_seconds', duration, labels=labels)
    
    if status_code >= 500:
        metrics_collector.increment('api_errors_total', labels=labels)
    elif status_code >= 400:
        metrics_collector.increment('api_client_errors_total', labels=labels)


def track_scan_metrics(scan_type: str, status: str, duration: Optional[float] = None):
    """
    Track scan-related metrics.
    
    Args:
        scan_type: Type of scan
        status: Scan status
        duration: Optional scan duration in seconds
        
    Example:
        >>> track_scan_metrics('subdomain_discovery', 'completed', 120.5)
    """
    labels = {
        'scan_type': scan_type,
        'status': status
    }
    
    metrics_collector.increment('scans_total', labels=labels)
    
    if duration:
        metrics_collector.histogram('scan_duration_seconds', duration, labels=labels)


def track_database_query(query_type: str, duration: float, rows: int = 0):
    """
    Track database query metrics.
    
    Args:
        query_type: Type of query (select, insert, update, delete)
        duration: Query duration in seconds
        rows: Number of rows affected
        
    Example:
        >>> track_database_query('select', 0.045, 150)
    """
    labels = {'query_type': query_type}
    
    metrics_collector.increment('db_queries_total', labels=labels)
    metrics_collector.histogram('db_query_duration_seconds', duration, labels=labels)
    
    if rows > 0:
        metrics_collector.histogram('db_query_rows', rows, labels=labels)


def get_system_metrics() -> Dict[str, Any]:
    """
    Get current system metrics.
    
    Returns:
        Dictionary of system metrics
        
    Example:
        >>> metrics = get_system_metrics()
        >>> print(metrics['active_scans'])
    """
    from startScan.models import ScanHistory, SubScan
    from dashboard.models import Subdomain, Vulnerability
    
    # Get scan metrics
    active_scans = ScanHistory.objects.filter(scan_status=1).count()
    pending_scans = ScanHistory.objects.filter(scan_status=-1).count()
    completed_scans_today = ScanHistory.objects.filter(
        stop_scan_date__gte=timezone.now() - timedelta(days=1),
        scan_status__in=[0, 2, 3]
    ).count()
    
    # Get vulnerability metrics
    total_vulnerabilities = Vulnerability.objects.count()
    critical_vulnerabilities = Vulnerability.objects.filter(severity=4).count()
    high_vulnerabilities = Vulnerability.objects.filter(severity=3).count()
    
    # Get subdomain metrics
    total_subdomains = Subdomain.objects.count()
    active_subdomains = Subdomain.objects.filter(
        http_status__gte=200,
        http_status__lt=400
    ).count()
    
    return {
        'scans': {
            'active': active_scans,
            'pending': pending_scans,
            'completed_today': completed_scans_today
        },
        'vulnerabilities': {
            'total': total_vulnerabilities,
            'critical': critical_vulnerabilities,
            'high': high_vulnerabilities
        },
        'subdomains': {
            'total': total_subdomains,
            'active': active_subdomains
        },
        'timestamp': timezone.now().isoformat()
    }


def get_performance_metrics() -> Dict[str, Any]:
    """
    Get performance metrics.
    
    Returns:
        Dictionary of performance metrics
    """
    return {
        'api_requests': {
            'total': metrics_collector.get_metric('api_requests_total'),
            'errors': metrics_collector.get_metric('api_errors_total'),
        },
        'database': {
            'queries': metrics_collector.get_metric('db_queries_total'),
        },
        'scans': {
            'total': metrics_collector.get_metric('scans_total'),
        }
    }


class PerformanceMonitor:
    """
    Context manager for monitoring performance of code blocks.
    """
    
    def __init__(self, operation_name: str, labels: Optional[Dict[str, str]] = None):
        self.operation_name = operation_name
        self.labels = labels
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        metrics_collector.histogram(
            f"{self.operation_name}_duration_seconds",
            duration,
            self.labels
        )
        
        if exc_type is not None:
            metrics_collector.increment(
                f"{self.operation_name}_errors_total",
                labels=self.labels
            )
        
        logger.debug(f"{self.operation_name} completed in {duration:.3f}s")
        
        return False  # Don't suppress exceptions


def export_prometheus_metrics() -> str:
    """
    Export metrics in Prometheus format.
    
    Returns:
        Metrics in Prometheus text format
        
    Example:
        >>> metrics_text = export_prometheus_metrics()
        >>> print(metrics_text)
    """
    metrics = []
    
    # Add system metrics
    system_metrics = get_system_metrics()
    
    metrics.append(f"# HELP reconpoint_active_scans Number of active scans")
    metrics.append(f"# TYPE reconpoint_active_scans gauge")
    metrics.append(f"reconpoint_active_scans {system_metrics['scans']['active']}")
    
    metrics.append(f"# HELP reconpoint_total_vulnerabilities Total number of vulnerabilities")
    metrics.append(f"# TYPE reconpoint_total_vulnerabilities gauge")
    metrics.append(f"reconpoint_total_vulnerabilities {system_metrics['vulnerabilities']['total']}")
    
    metrics.append(f"# HELP reconpoint_critical_vulnerabilities Number of critical vulnerabilities")
    metrics.append(f"# TYPE reconpoint_critical_vulnerabilities gauge")
    metrics.append(f"reconpoint_critical_vulnerabilities {system_metrics['vulnerabilities']['critical']}")
    
    return '\n'.join(metrics)
