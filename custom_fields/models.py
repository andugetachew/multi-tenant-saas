from django.db import models
from organizations.models import Organization
from projects.models import Project


class CustomField(models.Model):
    FIELD_TYPES = [
        ("text", "Text"),
        ("number", "Number"),
        ("date", "Date"),
        ("checkbox", "Checkbox"),
        ("select", "Select"),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    options = models.JSONField(default=list, blank=True)  # For select fields
    is_required = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class CustomFieldValue(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="custom_fields"
    )
    field = models.ForeignKey(CustomField, on_delete=models.CASCADE)
    value = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
