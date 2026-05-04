# reports/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Sum, Q, Avg  # Add Avg here
from datetime import datetime, timedelta
from projects.models import Project, Task
from accounts.models import User
from .excel_export import ExcelReportGenerator


class AdvancedReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = request.user.organization
        now = datetime.now()

        # Fix: Use Avg correctly
        avg_tasks_count = (
            Task.objects.filter(project__organization=org)
            .values("project")
            .annotate(task_count=Count("id"))
            .aggregate(avg_tasks=Avg("task_count"))
        )

        avg_tasks_per_project = avg_tasks_count.get("avg_tasks", 0) or 0

        # User productivity
        user_productivity = []
        for user in User.objects.filter(organization=org):
            task_count = Task.objects.filter(
                created_by=user, project__organization=org
            ).count()
            from comments.models import Comment

            comment_count = Comment.objects.filter(
                user=user, project__organization=org
            ).count()
            user_productivity.append(
                {
                    "user": user.email,
                    "tasks_created": task_count,
                    "comments_made": comment_count,
                    "score": task_count * 10 + comment_count,
                }
            )

        # Monthly trends (last 6 months)
        monthly_data = []
        for i in range(5, -1, -1):
            month_date = now - timedelta(days=30 * i)
            month_start = month_date.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )

            if i == 0:
                month_end = now
            else:
                month_end = (month_start + timedelta(days=32)).replace(
                    day=1
                ) - timedelta(days=1)

            projects_created = Project.objects.filter(
                organization=org, created_at__range=[month_start, month_end]
            ).count()

            tasks_completed = Task.objects.filter(
                project__organization=org,
                status="completed",
                updated_at__range=[month_start, month_end],
            ).count()

            monthly_data.append(
                {
                    "month": month_start.strftime("%B %Y"),
                    "projects": projects_created,
                    "tasks_completed": tasks_completed,
                }
            )

        return Response(
            {
                "project_forecast": {
                    "current_projects": Project.objects.filter(
                        organization=org
                    ).count(),
                    "estimated_completion_rate": round(avg_tasks_per_project, 1),
                    "predicted_completion_date": (
                        now + timedelta(days=avg_tasks_per_project * 3)
                    ).strftime("%Y-%m-%d"),
                },
                "user_productivity": sorted(
                    user_productivity, key=lambda x: x["score"], reverse=True
                )[:10],
                "monthly_trends": monthly_data,
            }
        )


from .excel_export import ExcelReportGenerator


class ComprehensiveReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        generator = ExcelReportGenerator(request.user)
        return generator.generate_comprehensive_report()
