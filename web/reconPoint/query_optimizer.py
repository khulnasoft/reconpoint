"""
Database query optimization utilities for reconPoint.
"""
import logging
from typing import List, Optional, Type, Any
from functools import wraps
from django.db import models, connection
from django.db.models import Prefetch, QuerySet
from django.core.cache import cache
from django.conf import settings


logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Utilities for optimizing Django ORM queries."""
    
    @staticmethod
    def optimize_queryset(
        queryset: QuerySet,
        select_related_fields: Optional[List[str]] = None,
        prefetch_related_fields: Optional[List[str]] = None,
        only_fields: Optional[List[str]] = None,
        defer_fields: Optional[List[str]] = None
    ) -> QuerySet:
        """
        Apply common query optimizations to a queryset.
        
        Args:
            queryset: QuerySet to optimize
            select_related_fields: Fields for select_related (foreign keys)
            prefetch_related_fields: Fields for prefetch_related (many-to-many, reverse FK)
            only_fields: Fields to include (only these will be loaded)
            defer_fields: Fields to exclude (all except these will be loaded)
            
        Returns:
            Optimized QuerySet
        """
        if select_related_fields:
            queryset = queryset.select_related(*select_related_fields)
        
        if prefetch_related_fields:
            queryset = queryset.prefetch_related(*prefetch_related_fields)
        
        if only_fields:
            queryset = queryset.only(*only_fields)
        
        if defer_fields:
            queryset = queryset.defer(*defer_fields)
        
        return queryset
    
    @staticmethod
    def get_or_none(model: Type[models.Model], **kwargs) -> Optional[models.Model]:
        """
        Get model instance or None if not found.
        
        Args:
            model: Model class
            **kwargs: Lookup parameters
            
        Returns:
            Model instance or None
        """
        try:
            return model.objects.get(**kwargs)
        except model.DoesNotExist:
            return None
        except model.MultipleObjectsReturned:
            logger.warning(f"Multiple {model.__name__} objects returned for {kwargs}")
            return model.objects.filter(**kwargs).first()
    
    @staticmethod
    def bulk_create_or_update(
        model: Type[models.Model],
        objects: List[dict],
        unique_fields: List[str],
        batch_size: int = 1000
    ) -> tuple:
        """
        Bulk create or update objects efficiently.
        
        Args:
            model: Model class
            objects: List of dictionaries with object data
            unique_fields: Fields that uniquely identify an object
            batch_size: Number of objects to process per batch
            
        Returns:
            Tuple of (created_count, updated_count)
        """
        created_count = 0
        updated_count = 0
        
        # Group objects by unique key
        existing_objects = {}
        unique_values = [
            tuple(obj.get(field) for field in unique_fields)
            for obj in objects
        ]
        
        # Build Q object for filtering
        from django.db.models import Q
        q_objects = Q()
        for values in unique_values:
            q_dict = dict(zip(unique_fields, values))
            q_objects |= Q(**q_dict)
        
        # Get existing objects
        for obj in model.objects.filter(q_objects):
            key = tuple(getattr(obj, field) for field in unique_fields)
            existing_objects[key] = obj
        
        # Separate into create and update lists
        to_create = []
        to_update = []
        
        for obj_data in objects:
            key = tuple(obj_data.get(field) for field in unique_fields)
            
            if key in existing_objects:
                # Update existing object
                existing_obj = existing_objects[key]
                for field, value in obj_data.items():
                    setattr(existing_obj, field, value)
                to_update.append(existing_obj)
            else:
                # Create new object
                to_create.append(model(**obj_data))
        
        # Bulk create
        if to_create:
            model.objects.bulk_create(to_create, batch_size=batch_size)
            created_count = len(to_create)
        
        # Bulk update
        if to_update:
            update_fields = list(objects[0].keys()) if objects else []
            update_fields = [f for f in update_fields if f not in unique_fields]
            model.objects.bulk_update(to_update, update_fields, batch_size=batch_size)
            updated_count = len(to_update)
        
        return created_count, updated_count
    
    @staticmethod
    def count_efficiently(queryset: QuerySet) -> int:
        """
        Count queryset results efficiently.
        Uses exists() check before count() for better performance.
        
        Args:
            queryset: QuerySet to count
            
        Returns:
            Count of objects
        """
        # For small querysets, len() on evaluated queryset is faster
        if queryset._result_cache is not None:
            return len(queryset)
        
        # For large querysets, use count()
        return queryset.count()
    
    @staticmethod
    def iterator_with_prefetch(
        queryset: QuerySet,
        chunk_size: int = 2000,
        prefetch_related_fields: Optional[List[str]] = None
    ):
        """
        Iterate over large queryset with prefetch_related support.
        
        Args:
            queryset: QuerySet to iterate
            chunk_size: Number of objects per chunk
            prefetch_related_fields: Fields to prefetch
            
        Yields:
            Model instances
        """
        if prefetch_related_fields:
            queryset = queryset.prefetch_related(*prefetch_related_fields)
        
        # Use iterator for memory efficiency
        for obj in queryset.iterator(chunk_size=chunk_size):
            yield obj


class CachedQueryMixin:
    """Mixin to add caching capabilities to querysets."""
    
    @staticmethod
    def get_cache_key(model_name: str, method: str, *args, **kwargs) -> str:
        """
        Generate cache key for query.
        
        Args:
            model_name: Name of the model
            method: Method name
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Cache key string
        """
        import hashlib
        import json
        
        # Create a deterministic key from arguments
        key_data = {
            'model': model_name,
            'method': method,
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"query_cache:{model_name}:{method}:{key_hash}"
    
    @staticmethod
    def cached_query(timeout: int = 300):
        """
        Decorator to cache query results.
        
        Args:
            timeout: Cache timeout in seconds
            
        Returns:
            Decorated function
        """
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                # Skip caching if disabled
                if not getattr(settings, 'RECONPOINT_CACHE_ENABLED', False):
                    return func(self, *args, **kwargs)
                
                # Generate cache key
                model_name = self.__class__.__name__
                cache_key = CachedQueryMixin.get_cache_key(
                    model_name, func.__name__, *args, **kwargs
                )
                
                # Try to get from cache
                result = cache.get(cache_key)
                if result is not None:
                    logger.debug(f"Cache hit for {cache_key}")
                    return result
                
                # Execute query and cache result
                result = func(self, *args, **kwargs)
                cache.set(cache_key, result, timeout)
                logger.debug(f"Cached result for {cache_key}")
                
                return result
            
            return wrapper
        return decorator
    
    @staticmethod
    def invalidate_cache(model_name: str, method: Optional[str] = None):
        """
        Invalidate cached queries for a model.
        
        Args:
            model_name: Name of the model
            method: Optional specific method to invalidate
        """
        if method:
            pattern = f"query_cache:{model_name}:{method}:*"
        else:
            pattern = f"query_cache:{model_name}:*"
        
        # Note: This requires Redis and django-redis
        try:
            cache.delete_pattern(pattern)
            logger.info(f"Invalidated cache for pattern: {pattern}")
        except AttributeError:
            # Fallback if delete_pattern is not available
            logger.warning("Cache invalidation by pattern not supported")


def log_queries(func):
    """
    Decorator to log SQL queries executed by a function.
    Only works when DEBUG=True.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not settings.DEBUG:
            return func(*args, **kwargs)
        
        # Reset queries
        connection.queries_log.clear()
        
        # Execute function
        result = func(*args, **kwargs)
        
        # Log queries
        query_count = len(connection.queries)
        if query_count > 0:
            logger.info(f"{func.__name__} executed {query_count} queries")
            
            # Log slow queries
            for query in connection.queries:
                time = float(query['time'])
                if time > 0.1:  # Log queries slower than 100ms
                    logger.warning(
                        f"Slow query ({time}s): {query['sql'][:200]}"
                    )
        
        return result
    
    return wrapper


def explain_query(queryset: QuerySet) -> str:
    """
    Get EXPLAIN output for a queryset.
    
    Args:
        queryset: QuerySet to explain
        
    Returns:
        EXPLAIN output as string
    """
    sql, params = queryset.query.sql_with_params()
    
    with connection.cursor() as cursor:
        cursor.execute(f"EXPLAIN ANALYZE {sql}", params)
        return '\n'.join([row[0] for row in cursor.fetchall()])


class QueryProfiler:
    """Profile database queries for performance analysis."""
    
    def __init__(self, name: str = "Query Profile"):
        self.name = name
        self.start_query_count = 0
        self.start_time = None
    
    def __enter__(self):
        if settings.DEBUG:
            self.start_query_count = len(connection.queries)
            import time
            self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if settings.DEBUG:
            import time
            end_time = time.time()
            end_query_count = len(connection.queries)
            
            query_count = end_query_count - self.start_query_count
            duration = end_time - self.start_time
            
            logger.info(
                f"{self.name}: {query_count} queries in {duration:.3f}s"
            )
            
            # Log individual queries if count is high
            if query_count > 10:
                logger.warning(f"High query count detected: {query_count} queries")
                for query in connection.queries[self.start_query_count:]:
                    logger.debug(f"Query: {query['sql'][:200]}")


def optimize_scan_history_queries(scan_history_id: int):
    """
    Example: Optimize queries for scan history detail view.
    
    Args:
        scan_history_id: ScanHistory ID
        
    Returns:
        Dictionary with optimized querysets
    """
    from startScan.models import ScanHistory, Subdomain, EndPoint, Vulnerability
    from targetApp.models import Domain
    
    # Get scan with related data in one query
    scan = (
        ScanHistory.objects
        .select_related('domain', 'scan_type', 'initiated_by')
        .prefetch_related(
            'emails',
            'employees',
            Prefetch(
                'subdomain_set',
                queryset=Subdomain.objects.select_related('target_domain')
            ),
            Prefetch(
                'endpoint_set',
                queryset=EndPoint.objects.only('url', 'http_status', 'content_length')
            ),
            Prefetch(
                'vulnerability_set',
                queryset=Vulnerability.objects.select_related('subdomain')
            )
        )
        .get(id=scan_history_id)
    )
    
    return {
        'scan': scan,
        'subdomains': scan.subdomain_set.all(),
        'endpoints': scan.endpoint_set.all(),
        'vulnerabilities': scan.vulnerability_set.all()
    }
