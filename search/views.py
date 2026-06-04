from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from core.rate_limits import SearchGlobalThrottle


class GlobalSearchView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [SearchGlobalThrottle]

    def get(self, request):
        try:
            from projects.models import Project, Task
        except ImportError:
            return Response({"error": "Project models not found"}, status=500)

        query = request.query_params.get("q", "")

        if not query:
            return Response({"error": "Search query required"}, status=400)

        org = request.user.organization

        if not org:
            return Response({"error": "No organization assigned"}, status=400)

        # Search projects
        projects = Project.objects.filter(
            Q(organization=org)
            & (Q(name__icontains=query) | Q(description__icontains=query))
        ).values("id", "name", "description")

        # Search tasks
        tasks = Task.objects.filter(
            Q(project__organization=org)
            & (Q(title__icontains=query) | Q(description__icontains=query))
        ).values("id", "title", "status", "project__name")

        # Search comments - wrap in try/except
        comments = []
        try:
            from comments.models import Comment

            comments = Comment.objects.filter(
                Q(project__organization=org) & Q(content__icontains=query)
            ).values("id", "content", "project__name")
            comments = list(comments)
        except ImportError:
            pass  # Comments app not installed

        return Response(
            {
                "query": query,
                "results": {
                    "projects": list(projects),
                    "tasks": list(tasks),
                    "comments": comments,
                },
            }
        )
