from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Project, Task


class ProjectTemplateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Predefined templates
        templates = {
            "software_development": {
                "name": "Software Development Project",
                "description": "Complete software development workflow",
                "tasks": [
                    {"title": "Requirements Gathering", "priority": "high"},
                    {"title": "Design Architecture", "priority": "high"},
                    {"title": "Development Sprint 1", "priority": "medium"},
                    {"title": "Testing & QA", "priority": "medium"},
                    {"title": "Deployment", "priority": "high"},
                    {"title": "Documentation", "priority": "low"},
                ],
            },
            "marketing_campaign": {
                "name": "Marketing Campaign",
                "description": "Launch a marketing campaign",
                "tasks": [
                    {"title": "Market Research", "priority": "high"},
                    {"title": "Content Creation", "priority": "high"},
                    {"title": "Social Media Setup", "priority": "medium"},
                    {"title": "Email Campaign", "priority": "medium"},
                    {"title": "Analytics Setup", "priority": "low"},
                    {"title": "Campaign Launch", "priority": "high"},
                ],
            },
            "event_planning": {
                "name": "Event Planning",
                "description": "Plan and execute an event",
                "tasks": [
                    {"title": "Venue Selection", "priority": "high"},
                    {"title": "Budget Planning", "priority": "high"},
                    {"title": "Vendor Coordination", "priority": "medium"},
                    {"title": "Marketing & Promotion", "priority": "medium"},
                    {"title": "Attendee Management", "priority": "low"},
                    {"title": "Post-Event Followup", "priority": "low"},
                ],
            },
        }
        return Response(templates)

    def post(self, request):
        template_name = request.data.get("template_name")
        project_name = request.data.get("name", f"{template_name} Project")

        templates = {
            "software_development": {...},
            "marketing_campaign": {...},
            "event_planning": {...},
        }

        template = templates.get(template_name)
        if not template:
            return Response({"error": "Template not found"}, status=400)

        # Create project from template
        project = Project.objects.create(
            name=project_name,
            description=template["description"],
            organization=request.user.organization,
            created_by=request.user,
        )

        # Create tasks from template
        for task_data in template["tasks"]:
            Task.objects.create(
                project=project,
                title=task_data["title"],
                priority=task_data["priority"],
                created_by=request.user,
            )

        return Response(
            {
                "id": project.id,
                "name": project.name,
                "tasks_created": len(template["tasks"]),
            }
        )
