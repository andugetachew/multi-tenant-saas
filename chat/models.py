from django.db import models
from projects.models import Project


class ChatMessage(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="messages"
    )
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    message = models.TextField()
    attachments = models.JSONField(default=list)
    is_edited = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.user.email}: {self.message[:50]}"
