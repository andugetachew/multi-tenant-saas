from django.db import models
from django.utils import timezone
from datetime import timedelta


class Organization(models.Model):
    name = models.CharField(max_length=100)
    plan = models.CharField(max_length=20, default="free")
    subscription_status = models.CharField(max_length=20, default="active")
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk and not self.trial_ends_at:
            self.trial_ends_at = timezone.now() + timedelta(days=14)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class OrganizationInvitation(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    email = models.EmailField()
    invited_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True
    )
    token = models.CharField(max_length=64, unique=True)
    accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} - {self.organization.name}"