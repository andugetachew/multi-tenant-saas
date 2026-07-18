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
from celery import shared_task
from core.circuit_breaker import redis_circuit_breaker, redis_fallback

class CachedRealTimeDashboardView(APIView):
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = request.user.id
        org_id = request.user.organization_id

        user_cache_key = f"dashboard:user:{user_id}"
        user_cached = redis_circuit_breaker.call(
            cache_service.redis_client.get, redis_fallback, user_cache_key
        )
        if user_cached:
            return Response(json.loads(user_cached))

        org_cache_key = f"dashboard:org:{org_id}"
        org_cached = redis_circuit_breaker.call(
            cache_service.redis_client.get, redis_fallback, org_cache_key
        )
        if org_cached:
            result = json.loads(org_cached)
            cache_service.redis_client.setex(user_cache_key, 5, json.dumps(result))
            return Response(result)

        result = self.compute_dashboard_data(request)
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

        cache_key = f"stats:org:{org_id}"
        cache_metadata_key = f"stats:meta:{org_id}"

        metadata = cache_service.redis_client.get(cache_metadata_key)
        if metadata:
            metadata = json.loads(metadata)
            if timezone.now().timestamp() - metadata["refreshed_at"] > 300:
                self.trigger_background_refresh.delay(org_id)

        result = cache_service.get_or_set(
            cache_key,
            lambda: self.compute_stats(request),
            ttl=cache_service.CACHE_TTL["dashboard_stats"],
        )
        return Response(result)
        

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
    @shared_task
    def trigger_background_refresh(org_id):
        """Async cache warming - FAANG pattern"""
        from organizations.models import Organization
        from projects.models import Project, Task

        org = Organization.objects.get(id=org_id)
        stats = {
            "total_projects": Project.objects.filter(organization=org).count(),
            "total_tasks": Task.objects.filter(project__organization=org).count(),
        }
        cache_key = f"stats:org:{org_id}"
        cache_service.redis_client.setex(cache_key, 300, json.dumps(stats))
