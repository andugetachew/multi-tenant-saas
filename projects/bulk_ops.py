from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Project, Task
from .serializers import ProjectSerializer, TaskSerializer


class BulkProjectDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        project_ids = request.data.get("project_ids", [])
        if not project_ids:
            return Response({"error": "No project IDs provided"}, status=400)

        deleted = Project.objects.filter(
            id__in=project_ids, organization=request.user.organization
        ).delete()

        return Response({"deleted_count": deleted[0]})


class BulkTaskUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        task_ids = request.data.get("task_ids", [])
        updates = request.data.get("updates", {})

        updated = Task.objects.filter(
            id__in=task_ids, project__organization=request.user.organization
        ).update(**updates)

        return Response({"updated_count": updated})


class BulkProjectArchiveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        project_ids = request.data.get("project_ids", [])

        updated = Project.objects.filter(
            id__in=project_ids, organization=request.user.organization
        ).update(status="archived")

        return Response({"archived_count": updated})
