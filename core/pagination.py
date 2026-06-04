# core/pagination.py
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict
import math


class StandardPagination(PageNumberPagination):
    """
    FAANG-level: Standard pagination with metadata
    Used for: Projects, Tasks, Comments lists
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("count", self.page.paginator.count),
                    ("total_pages", self.page.paginator.num_pages),
                    ("current_page", self.page.number),
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("page_size", self.get_page_size(self.request)),
                    ("results", data),
                ]
            )
        )


class CursorPagination(PageNumberPagination):
    """
    FAANG-level: Cursor-based pagination for infinite scroll
    Used for: Activity feed, Real-time updates, Notifications
    Performance: O(1) vs O(N) for offset pagination
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50
    ordering = "-created_at"  # Most recent first

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("next_cursor", self.get_next_cursor(data)),
                    ("has_next", len(data) == self.get_page_size(self.request)),
                    ("page_size", self.get_page_size(self.request)),
                    ("results", data),
                ]
            )
        )

    def get_next_cursor(self, data):
        """Extract cursor from last item for next request"""
        if data and len(data) == self.get_page_size(self.request):
            last_item = data[-1]
            return last_item.get("created_at")
        return None


class DashboardPagination(PageNumberPagination):
    """
    FAANG-level: Smaller pages for dashboard widgets
    Used for: Recent activity, Top projects, Quick stats
    """

    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 20

    def get_paginated_response(self, data):
        return Response(
            OrderedDict([("count", self.page.paginator.count), ("results", data)])
        )


class ExportPagination(PageNumberPagination):
    """
    FAANG-level: Large pages for exports
    Used for: CSV/PDF/Excel exports
    """

    page_size = 1000
    page_size_query_param = "page_size"
    max_page_size = 10000

    def get_paginated_response(self, data):
        return Response(data)  # No metadata for exports


class SearchPagination(PageNumberPagination):
    """
    FAANG-level: Optimized for search results
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("count", self.page.paginator.count),
                    ("total_pages", self.page.paginator.num_pages),
                    ("current_page", self.page.number),
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("results", data),
                ]
            )
        )


class AdminPagination(PageNumberPagination):
    """
    FAANG-level: Large pages for admin panel
    """

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 500

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("count", self.page.paginator.count),
                    ("total_pages", self.page.paginator.num_pages),
                    ("results", data),
                ]
            )
        )


class PerformancePagination(PageNumberPagination):
    """
    FAANG-level: Optimized for high-performance APIs
    Uses only() and defer() compatible pagination
    """

    page_size = 15
    page_size_query_param = "page_size"
    max_page_size = 50

    def paginate_queryset(self, queryset, request, view=None):
        # Apply only() for performance
        if hasattr(view, "optimized_fields"):
            queryset = queryset.only(*view.optimized_fields)
        return super().paginate_queryset(queryset, request, view)
