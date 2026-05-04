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

        # Check for mentions (@username)
        content = self.request.data.get("content", "")
        mentions = self.extract_mentions(content)

        comment = serializer.save(
            user=self.request.user, project=task.project, task=task
        )

        # Create notifications for mentioned users
        from notifications.utils import create_notification

        for mention in mentions:
            create_notification(
                user=mention,
                title=f"Mentioned in task: {task.title}",
                message=f"{self.request.user.email} mentioned you: {content[:100]}",
                link=f"/tasks/{task_id}",
            )

        return comment

    def extract_mentions(self, text):
        import re
        from accounts.models import User

        mentions = re.findall(r"@(\w+)", text)
        return User.objects.filter(username__in=mentions)
