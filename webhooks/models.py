from django.db import models
from organizations.models import Organization


class Webhook(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="webhooks"
    )
    url = models.URLField()
    events = models.JSONField(default=list)  # ['project.created', 'task.updated', etc.]
    secret = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.organization.name} - {self.url}"


class WebhookDelivery(models.Model):
    webhook = models.ForeignKey(
        Webhook, on_delete=models.CASCADE, related_name="deliveries"
    )
    event = models.CharField(max_length=100)
    payload = models.JSONField()
    response_status = models.IntegerField(null=True)
    response_body = models.TextField(blank=True)
    attempts = models.IntegerField(default=0)
    success = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
