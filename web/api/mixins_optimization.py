"""
Mixin for optimizing database queries with select_related and prefetch_related.
"""


class QuerySetOptimizationMixin:
    """
    Mixin that adds common query optimizations.

    Subclasses can override `select_related_fields` and `prefetch_related_fields`
    to specify which related fields should be eager-loaded.
    """

    select_related_fields: tuple = ()
    prefetch_related_fields: tuple = ()

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.select_related_fields:
            queryset = queryset.select_related(*self.select_related_fields)
        if self.prefetch_related_fields:
            queryset = queryset.prefetch_related(*self.prefetch_related_fields)
        return queryset
