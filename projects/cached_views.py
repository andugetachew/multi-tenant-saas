# projects/cached_views.py
from rest_framework import generics, permissions
from rest_framework.response import Response
from core.cache_config import cache_service
from .models import Project
from .serializers import ProjectSerializer
from django.core.cache import cache
import hashlib


class CachedProjectListView(generics.ListAPIView):
    """FAANG-level: Organization-based caching with invalidation"""

    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):

        return Project.objects.none()

    def list(self, request, *args, **kwargs):
        org_id = request.user.organization_id
        status_filter = request.query_params.get("status", "all")

        cache_key = f"projects:org:{org_id}:status:{status_filter}"

        cached_response = cache.get(cache_key)
        if cached_response:
            return Response(cached_response)

        queryset = Project.objects.filter(organization_id=org_id)
        if status_filter != "all":
            queryset = queryset.filter(status=status_filter)

        queryset = queryset.select_related("created_by").prefetch_related("tasks")

        serializer = self.get_serializer(queryset, many=True)

        cache.set(cache_key, serializer.data, 120)

        return Response(serializer.data)


class CachedProjectCreateView(generics.CreateAPIView):
    """FAANG-level: Invalidates cache on write"""

    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        project = serializer.save(
            organization=self.request.user.organization, created_by=self.request.user
        )

        org_id = self.request.user.organization_id
        cache_service.invalidate_pattern(f"projects:org:{org_id}:*")
        cache_service.invalidate_pattern(f"stats:org:{org_id}")

        return project
