from django.db.models import Q
from .models import Project, Task


class ProjectSearch:
    def __init__(self, queryset, user):
        self.queryset = queryset.filter(organization=user.organization)
        self.user = user

    def search(self, query, filters=None):
        # Text search
        if query:
            self.queryset = self.queryset.filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(tags__icontains=query)
            )

        # Filter by status
        if filters and filters.get("status"):
            self.queryset = self.queryset.filter(status=filters["status"])

        # Filter by date range
        if filters and filters.get("date_from"):
            self.queryset = self.queryset.filter(created_at__gte=filters["date_from"])
        if filters and filters.get("date_to"):
            self.queryset = self.queryset.filter(created_at__lte=filters["date_to"])

        return self.queryset


class TaskSearch:
    def __init__(self, queryset, user):
        self.queryset = queryset.filter(project__organization=user.organization)

    def search(self, query, filters=None):
        if query:
            self.queryset = self.queryset.filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )

        if filters:
            if filters.get("status"):
                self.queryset = self.queryset.filter(status=filters["status"])
            if filters.get("priority"):
                self.queryset = self.queryset.filter(priority=filters["priority"])
            if filters.get("assigned_to"):
                self.queryset = self.queryset.filter(
                    assigned_to_id=filters["assigned_to"]
                )

        return self.queryset
