from django.db import models
from organizations.models import Organization


class AnalyticsEvent(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    event_type = models.CharField(
        max_length=100
    )  # 'project_view', 'task_complete', etc.
    user_id = models.IntegerField()
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["organization", "event_type"]),
            models.Index(fields=["created_at"]),
        ]
