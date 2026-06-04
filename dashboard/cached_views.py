# dashboard/cached_views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.cache_config import cache_service
from .views import RealTimeDashboardView, DashboardStatsView
from django.db import models
from django.utils import timezone
from datetime import timedelta
import json


class CachedRealTimeDashboardView(APIView):
    """FAANG-level: 3-layer cache for dashboard"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = request.user.id
        org_id = request.user.organization_id

        # Layer 1: User-specific cache (5 seconds)
        user_cache_key = f"dashboard:user:{user_id}"
        user_cached = cache_service.redis_client.get(user_cache_key)
        if user_cached:
            return Response(json.loads(user_cached))

        # Layer 2: Organization cache (30 seconds)
        org_cache_key = f"dashboard:org:{org_id}"
        org_cached = cache_service.redis_client.get(org_cache_key)
        if org_cached:
            result = json.loads(org_cached)
            # Cache user-specific for 5 seconds
            cache_service.redis_client.setex(user_cache_key, 5, json.dumps(result))
            return Response(result)

        # Layer 3: Compute fresh (expensive aggregates)
        result = self.compute_dashboard_data(request)

        # Warm caches
        cache_service.redis_client.setex(org_cache_key, 30, json.dumps(result))
        cache_service.redis_client.setex(user_cache_key, 5, json.dumps(result))

        return Response(result)

    def compute_dashboard_data(self, request):
        """Original heavy computation - happens only on cache miss"""
        from projects.models import Project, Task
        from comments.models import Comment

        org = request.user.organization
        now = timezone.now()
        last_7_days = now - timedelta(days=7)

        # Aggregation queries (these are expensive)
        projects_by_day = (
            Project.objects.filter(organization=org, created_at__gte=last_7_days)
            .extra({"day": "date(created_at)"})
            .values("day")
            .annotate(count=models.Count("id"))
        )

        total_tasks = Task.objects.filter(project__organization=org).count()
        completed_tasks = Task.objects.filter(
            project__organization=org, status="completed"
        ).count()

        return {
            "project_trends": list(projects_by_day),
            "completion_rate": (
                round((completed_tasks / total_tasks * 100), 2)
                if total_tasks > 0
                else 0
            ),
            "total_projects": Project.objects.filter(organization=org).count(),
            "total_tasks": total_tasks,
            "total_comments": Comment.objects.filter(project__organization=org).count(),
            "_cached_at": now.isoformat(),
            "_cache_ttl": 30,
        }


class CachedDashboardStatsView(APIView):
    """FAANG-level: Pre-warmed dashboard stats"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        org_id = request.user.organization_id

        # Cache warming: Check if cache needs refresh
        cache_key = f"stats:org:{org_id}"
        cache_metadata_key = f"stats:meta:{org_id}"

        # Get metadata (when it was last refreshed)
        metadata = cache_service.redis_client.get(cache_metadata_key)
        if metadata:
            metadata = json.loads(metadata)
            # If cache is older than 5 minutes, trigger background refresh
            if timezone.now().timestamp() - metadata["refreshed_at"] > 300:
                self.trigger_background_refresh.delay(org_id)

        # Return cached or compute
        return cache_service.get_or_set(
            cache_key,
            lambda: self.compute_stats(request),
            ttl=cache_service.CACHE_TTL["dashboard_stats"],
        )

    def compute_stats(self, request):
        from projects.models import Project, Task

        org = request.user.organization
        return {
            "organization_name": org.name,
            "organization_plan": org.plan,
            "total_projects": Project.objects.filter(organization=org).count(),
            "total_tasks": Task.objects.filter(project__organization=org).count(),
            "completed_tasks": Task.objects.filter(
                project__organization=org, status="completed"
            ).count(),
            "pending_tasks": Task.objects.filter(
                project__organization=org, status="pending"
            ).count(),
            "total_users": org.users.count(),
            "_computed_at": timezone.now().isoformat(),
        }

    @staticmethod
    def trigger_background_refresh(org_id):
        """Async cache warming - FAANG pattern"""
        from celery import shared_task

        @shared_task
        def warm_dashboard_cache(org_id):
            from organizations.models import Organization
            from projects.models import Project, Task

            org = Organization.objects.get(id=org_id)
            # Pre-compute and cache
            stats = {
                "total_projects": Project.objects.filter(organization=org).count(),
                "total_tasks": Task.objects.filter(project__organization=org).count(),
            }
            cache_key = f"stats:org:{org_id}"
            cache_service.redis_client.setex(cache_key, 300, json.dumps(stats))

        warm_dashboard_cache.delay(org_id)
