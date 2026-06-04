# from django.apps import AppConfig
# from django.db.models.signals import post_migrate


# def create_default_organization(sender, **kwargs):
#     """Auto-create default organization if none exists"""
#     from organizations.models import Organization

#     if not Organization.objects.exists():
#         org = Organization.objects.create(
#             name="Default Organization", plan="trial", subscription_status="active"
#         )
#         print(f"✅ Created default organization: {org.name}")


# def create_superuser_if_none(sender, **kwargs):
#     """Auto-create superuser if none exists"""
#     from accounts.models import User
#     from organizations.models import Organization

#     if not User.objects.filter(is_superuser=True).exists():
#         org = Organization.objects.first()
#         if not org:
#             org = Organization.objects.create(
#                 name="Default Organization", plan="trial", subscription_status="active"
#             )

#         User.objects.create_superuser(
#             email="admin@example.com",
#             password="admin123",
#             username="admin",
#             organization=org,
#             is_owner=True,
#             is_email_verified=True,
#             is_active=True,
#         )
#         print("✅ Created default superuser: admin@example.com / admin123")


# class CoreConfig(AppConfig):
#     default_auto_field = "django.db.models.BigAutoField"
#     name = "core"

#     def ready(self):
#         # Run after migrations
#         post_migrate.connect(create_default_organization, sender=self)
#         post_migrate.connect(create_superuser_if_none, sender=self)
