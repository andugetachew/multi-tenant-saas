from django.core.management.base import BaseCommand
from accounts.models import User
from organizations.models import Organization


class Command(BaseCommand):
    help = "Assign organization to existing users without one"

    def handle(self, *args, **kwargs):
        org, _ = Organization.objects.get_or_create(name="Default Org", plan="trial")
        users = User.objects.filter(organization__isnull=True)
        count = users.update(organization=org)
        self.stdout.write(f"✅ Assigned {count} users to organization")
