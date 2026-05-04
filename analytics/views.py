from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q
from datetime import timedelta
from django.utils import timezone
from .models import AnalyticsEvent
from projects.models import Project, Task


class DashboardAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = request.user.organization
        now = timezone.now()
        last_30_days = now - timedelta(days=30)

        analytics = {
            "projects": {
                "total": Project.objects.filter(organization=org).count(),
                "created_last_30_days": Project.objects.filter(
                    organization=org, created_at__gte=last_30_days
                ).count(),
            },
            "tasks": {
                "total": Task.objects.filter(project__organization=org).count(),
                "completed": Task.objects.filter(
                    project__organization=org, status="completed"
                ).count(),
                "overdue": Task.objects.filter(
                    project__organization=org,
                    due_date__lt=now,
                    status__in=["pending", "in_progress"],
                ).count(),
            },
            "activity": {
                "total_events": AnalyticsEvent.objects.filter(
                    organization=org, created_at__gte=last_30_days
                ).count(),
                "by_type": dict(
                    AnalyticsEvent.objects.filter(
                        organization=org, created_at__gte=last_30_days
                    )
                    .values_list("event_type")
                    .annotate(count=Count("id"))
                ),
            },
        }
        return Response(analytics)
