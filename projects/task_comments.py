# projects/task_comments.py
from rest_framework import generics, permissions
from .models import Task
from comments.models import Comment
from comments.serializers import CommentSerializer


class TaskCommentView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        task_id = self.kwargs["task_id"]
        return Comment.objects.filter(
            task_id=task_id, project__organization=self.request.user.organization
        )

    def perform_create(self, serializer):
        task_id = self.kwargs["task_id"]
        task = Task.objects.get(id=task_id)
        serializer.save(user=self.request.user, project=task.project, task=task)
