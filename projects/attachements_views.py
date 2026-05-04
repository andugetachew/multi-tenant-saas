from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.files.base import ContentFile
from .models import Task, TaskAttachment


class TaskAttachmentUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        task = Task.objects.get(
            id=task_id, project__organization=request.user.organization
        )
        file = request.FILES.get("file")

        if not file:
            return Response({"error": "No file provided"}, status=400)

        attachment = TaskAttachment.objects.create(
            task=task,
            file=file,
            filename=file.name,
            file_size=file.size,
            uploaded_by=request.user,
        )

        return Response(
            {
                "id": attachment.id,
                "filename": attachment.filename,
                "file_size": attachment.file_size,
                "url": attachment.file.url,
            }
        )


class TaskAttachmentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        task = Task.objects.get(
            id=task_id, project__organization=request.user.organization
        )
        attachments = task.attachments.all()
        return Response(
            [
                {
                    "id": a.id,
                    "filename": a.filename,
                    "file_size": a.file_size,
                    "uploaded_by": a.uploaded_by.email,
                    "created_at": a.created_at,
                }
                for a in attachments
            ]
        )
