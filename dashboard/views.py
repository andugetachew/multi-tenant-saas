# dashboard/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count
from datetime import timedelta
from django.utils import timezone
from projects.models import Project, Task
from comments.models import Comment


class RealTimeDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            org = request.user.organization
            now = timezone.now()
            last_30_days = now - timedelta(days=30)

            # Basic stats
            total_projects = Project.objects.filter(organization=org).count()
            total_tasks = Task.objects.filter(project__organization=org).count()
            completed_tasks = Task.objects.filter(
                project__organization=org, status="completed"
            ).count()
            total_comments = Comment.objects.filter(project__organization=org).count()

            # Calculate completion rate
            completion_rate = (
                (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            )

            # Simple project trends (last 7 days)
            projects_by_day = []
            for i in range(7):
                day = now - timedelta(days=i)
                day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
                count = Project.objects.filter(
                    organization=org, created_at__range=[day_start, day_end]
                ).count()
                projects_by_day.append(
                    {"date": day.strftime("%Y-%m-%d"), "count": count}
                )

            return Response(
                {
                    "project_trends": projects_by_day,
                    "completion_rate": round(completion_rate, 2),
                    "active_users": 1,  # Simplified for now
                    "total_projects": total_projects,
                    "total_tasks": total_tasks,
                    "total_comments": total_comments,
                }
            )
        except Exception as e:
            return Response({"error": str(e)}, status=500)
