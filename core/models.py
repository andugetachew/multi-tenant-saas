from django.db import models
from django.contrib.auth.models import AbstractUser
from organizations.models import Organization


class User(AbstractUser):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    is_owner = models.BooleanField(default=False)

    def __str__(self):
        return self.email
