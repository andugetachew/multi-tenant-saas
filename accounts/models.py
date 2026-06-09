from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import secrets
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from organizations.models import Organization
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        if not extra_fields.get('organization'):
            raise ValueError("User must belong to an organization")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_owner", True)
        extra_fields.setdefault("is_email_verified", True)

        if not extra_fields.get("organization"):
            from organizations.models import Organization
            org, _ = Organization.objects.get_or_create(
                name="Default Organization",
                defaults={"plan": "trial"}
            )
            extra_fields["organization"] = org

        return self.create_user(email, password, **extra_fields)
class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    is_owner = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)
    password_reset_token = models.CharField(max_length=100, blank=True, null=True)
    password_reset_token_created_at = models.DateTimeField(null=True, blank=True)

    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("member", "Member"),
        ("viewer", "Viewer"),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="member")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=100, blank=True, null=True)
    objects = CustomUserManager()

    def __str__(self):
        return self.email

    def generate_email_verification_token(self):
        self.email_verification_token = secrets.token_urlsafe(32)
        self.email_verification_sent_at = timezone.now()
        self.save()
        return self.email_verification_token

    def generate_password_reset_token(self):
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_token_created_at = timezone.now()
        self.save()
        return self.password_reset_token

    def is_password_reset_token_valid(self):
        if not self.password_reset_token_created_at:
            return False
        expiry_time = self.password_reset_token_created_at + timezone.timedelta(
            hours=24
        )
        return timezone.now() <= expiry_time

    class Meta:
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["organization", "role"]),
            models.Index(fields=["organization", "is_owner"]),
        ]


@receiver(post_save, sender=User)
def auto_assign_organization(sender, instance, created, **kwargs):
    if instance.is_superuser and not instance.organization:
        from organizations.models import Organization

        org, _ = Organization.objects.get_or_create(
            name=f"{instance.email}'s Company", defaults={"plan": "trial"}
        )
        instance.organization = org
        instance.is_owner = True
        instance.save(update_fields=["organization", "is_owner"])


@receiver(post_migrate)
def create_default_data(sender, **kwargs):
    if sender.name == "accounts":
        from organizations.models import Organization
        from accounts.models import User

        org, created = Organization.objects.get_or_create(
            name="Default Organization",
            defaults={"plan": "trial", "subscription_status": "active"},
        )

        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                email="admin@example.com",
                password="admin123",
                # username="admin",
                organization=org,
                is_owner=True,
                is_email_verified=True,
                is_active=True,
            )
            print("✅ Default superuser created: admin@example.com / admin123")
