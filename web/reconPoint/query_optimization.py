"""
Database query optimization utilities for reconPoint.
Provides helpers for efficient database queries.
"""
from typing import List, Optional, Type
from django.db.models import QuerySet, Prefetch, Model
from django.db.models.query import prefetch_related_objects
import logging

logger = logging.getLogger(__name__)


def optimize_queryset(
    queryset: QuerySet,
    select_related_fields: Optional[List[str]] = None,
    prefetch_related_fields: Optional[List[str]] = None,
    only_fields: Optional[List[str]] = None,
    defer_fields: Optional[List[str]] = None
) -> QuerySet:
    """
    Optimize a queryset with select_related, prefetch_related, only, and defer.
    
    Args:
        queryset: The queryset to optimize
        select_related_fields: Fields to select_related
        prefetch_related_fields: Fields to prefetch_related
        only_fields: Fields to include (only)
        defer_fields: Fields to exclude (defer)
        
    Returns:
        Optimized queryset
        
    Example:
        >>> queryset = Subdomain.objects.all()
        >>> optimized = optimize_queryset(
        ...     queryset,
        ...     select_related_fields=['target_domain', 'scan_history'],
        ...     only_fields=['id', 'name', 'http_status']
        ... )
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


def get_related_objects_efficiently(
    instance: Model,
    related_field: str,
    select_related: Optional[List[str]] = None,
    prefetch_related: Optional[List[str]] = None
) -> QuerySet:
    """
    Get related objects efficiently with optimizations.
    
    Args:
        instance: Model instance
        related_field: Name of the related field
        select_related: Fields to select_related on the related objects
        prefetch_related: Fields to prefetch_related on the related objects
        
    Returns:
        Optimized queryset of related objects
        
    Example:
        >>> subdomain = Subdomain.objects.get(id=1)
        >>> vulnerabilities = get_related_objects_efficiently(
        ...     subdomain,
        ...     'vulnerability_set',
        ...     select_related=['target_domain']
        ... )
    """
    related_manager = getattr(instance, related_field)
    queryset = related_manager.all()
    
    return optimize_queryset(
        queryset,
        select_related_fields=select_related,
        prefetch_related_fields=prefetch_related
    )


def bulk_create_with_return(
    model_class: Type[Model],
    objects: List[Model],
    batch_size: int = 1000,
    ignore_conflicts: bool = False
) -> List[Model]:
    """
    Bulk create objects and return them with IDs.
    
    Args:
        model_class: Model class to create
        objects: List of model instances to create
        batch_size: Number of objects to create per batch
        ignore_conflicts: Whether to ignore conflicts
        
    Returns:
        List of created objects with IDs
        
    Example:
        >>> subdomains = [Subdomain(name=f'sub{i}.example.com') for i in range(100)]
        >>> created = bulk_create_with_return(Subdomain, subdomains)
    """
    created_objects = model_class.objects.bulk_create(
        objects,
        batch_size=batch_size,
        ignore_conflicts=ignore_conflicts
    )
    
    logger.info(f"Bulk created {len(created_objects)} {model_class.__name__} objects")
    
    return created_objects


def bulk_update_efficiently(
    objects: List[Model],
    fields: List[str],
    batch_size: int = 1000
) -> int:
    """
    Bulk update objects efficiently.
    
    Args:
        objects: List of model instances to update
        fields: List of field names to update
        batch_size: Number of objects to update per batch
        
    Returns:
        Number of objects updated
        
    Example:
        >>> subdomains = Subdomain.objects.filter(http_status=200)
        >>> for subdomain in subdomains:
        ...     subdomain.is_important = True
        >>> bulk_update_efficiently(list(subdomains), ['is_important'])
    """
    if not objects:
        return 0
    
    model_class = type(objects[0])
    count = model_class.objects.bulk_update(
        objects,
        fields,
        batch_size=batch_size
    )
    
    logger.info(f"Bulk updated {count} {model_class.__name__} objects")
    
    return count


def get_or_create_efficiently(
    model_class: Type[Model],
    defaults: dict,
    **lookup_fields
) -> tuple:
    """
    Get or create with better error handling.
    
    Args:
        model_class: Model class
        defaults: Default values for creation
        **lookup_fields: Fields to lookup by
        
    Returns:
        Tuple of (instance, created)
        
    Example:
        >>> subdomain, created = get_or_create_efficiently(
        ...     Subdomain,
        ...     defaults={'http_status': 200},
        ...     name='example.com'
        ... )
    """
    try:
        instance, created = model_class.objects.get_or_create(
            defaults=defaults,
            **lookup_fields
        )
        return instance, created
    except Exception as e:
        logger.error(f"Error in get_or_create for {model_class.__name__}: {e}")
        raise


def count_efficiently(queryset: QuerySet) -> int:
    """
    Count queryset results efficiently.
    Uses exists() check first to avoid unnecessary counting.
    
    Args:
        queryset: Queryset to count
        
    Returns:
        Count of objects
        
    Example:
        >>> count = count_efficiently(Subdomain.objects.filter(http_status=200))
    """
    # For small counts, exists() + count() can be faster
    if not queryset.exists():
        return 0
    
    return queryset.count()


def exists_efficiently(queryset: QuerySet) -> bool:
    """
    Check if queryset has any results efficiently.
    
    Args:
        queryset: Queryset to check
        
    Returns:
        True if queryset has results, False otherwise
        
    Example:
        >>> has_vulns = exists_efficiently(
        ...     Vulnerability.objects.filter(severity__gte=3)
        ... )
    """
    return queryset.exists()


class QueryOptimizationMixin:
    """
    Mixin for ViewSets to add query optimization methods.
    """
    
    # Override these in your ViewSet
    select_related_fields = []
    prefetch_related_fields = []
    
    def get_queryset(self):
        """
        Get optimized queryset.
        """
        queryset = super().get_queryset()
        
        return optimize_queryset(
            queryset,
            select_related_fields=self.select_related_fields,
            prefetch_related_fields=self.prefetch_related_fields
        )
    
    def optimize_for_list(self, queryset: QuerySet) -> QuerySet:
        """
        Optimize queryset for list view.
        Override this method to add list-specific optimizations.
        """
        return queryset
    
    def optimize_for_detail(self, queryset: QuerySet) -> QuerySet:
        """
        Optimize queryset for detail view.
        Override this method to add detail-specific optimizations.
        """
        return queryset


def create_custom_prefetch(
    lookup: str,
    queryset: Optional[QuerySet] = None,
    to_attr: Optional[str] = None
) -> Prefetch:
    """
    Create a custom Prefetch object for complex prefetching.
    
    Args:
        lookup: The relationship to prefetch
        queryset: Custom queryset for the prefetch
        to_attr: Attribute name to store the prefetched results
        
    Returns:
        Prefetch object
        
    Example:
        >>> from django.db.models import Prefetch
        >>> active_vulns = Vulnerability.objects.filter(is_false_positive=False)
        >>> prefetch = create_custom_prefetch(
        ...     'vulnerability_set',
        ...     queryset=active_vulns,
        ...     to_attr='active_vulnerabilities'
        ... )
        >>> subdomains = Subdomain.objects.prefetch_related(prefetch)
    """
    return Prefetch(lookup, queryset=queryset, to_attr=to_attr)
