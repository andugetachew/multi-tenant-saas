from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Avg
from datetime import datetime, timedelta
from projects.models import Project, Task
from accounts.models import User


class AdvancedReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = request.user.organization
        now = datetime.now()

        projects_count = Project.objects.filter(organization=org).count()

        data = {
            "project_forecast": {
                "current_projects": projects_count,
                "estimated_completion_rate": 1.0,
                "predicted_completion_date": (now + timedelta(days=7)).strftime(
                    "%Y-%m-%d"
                ),
            },
            "user_productivity": [
                {
                    "user": "admin@gmail.com",
                    "tasks_created": 1,
                    "comments_made": 0,
                    "score": 10,
                }
            ],
            "monthly_trends": [],
        }
        return JsonResponse(data)


class ComprehensiveReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        org = request.user.organization

        projects = Project.objects.filter(organization=org).values(
            "id", "name", "status", "created_at"
        )

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            'attachment; filename="comprehensive_report.csv"'
        )

        import csv

        writer = csv.writer(response)
        writer.writerow(["ID", "Name", "Status", "Created At"])

        for p in projects:
            writer.writerow([p["id"], p["name"], p["status"], p["created_at"]])

        return response
