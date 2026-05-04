from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from projects.models import Project, Task
from comments.models import Comment
from audit.models import AuditLog


class ActivityFeedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = request.user.organization
        limit = int(request.query_params.get("limit", 50))

        activities = []

        # Get recent projects
        projects = Project.objects.filter(organization=org).order_by("-created_at")[
            :limit
        ]
        for p in projects:
            activities.append(
                {
                    "type": "project_created",
                    "title": f'Project "{p.name}" was created',
                    "user": p.created_by.email if p.created_by else "System",
                    "timestamp": p.created_at,
                    "project_id": p.id,
                }
            )

        # Get recent tasks
        tasks = Task.objects.filter(project__organization=org).order_by("-created_at")[
            :limit
        ]
        for t in tasks:
            activities.append(
                {
                    "type": "task_created",
                    "title": f'Task "{t.title}" was added to {t.project.name}',
                    "user": t.created_by.email if t.created_by else "System",
                    "timestamp": t.created_at,
                    "task_id": t.id,
                }
            )

        # Get completed tasks
        completed = (
            Task.objects.filter(project__organization=org, status="completed")
            .exclude(completed_at__isnull=True)
            .order_by("-completed_at")[:limit]
        )

        for t in completed:
            activities.append(
                {
                    "type": "task_completed",
                    "title": f'Task "{t.title}" was completed',
                    "user": t.created_by.email if t.created_by else "System",
                    "timestamp": t.completed_at,
                    "task_id": t.id,
                }
            )

        # Get comments
        comments = Comment.objects.filter(project__organization=org).order_by(
            "-created_at"
        )[:limit]
        for c in comments:
            activities.append(
                {
                    "type": "comment_added",
                    "title": f"{c.user.email} commented on {c.project.name}",
                    "content": c.content[:100],
                    "user": c.user.email,
                    "timestamp": c.created_at,
                    "comment_id": c.id,
                }
            )

        # Sort by timestamp and limit
        activities.sort(key=lambda x: x["timestamp"], reverse=True)

        return Response(
            {"total": len(activities[:limit]), "activities": activities[:limit]}
        )
