from django.core.management.base import BaseCommand
from billing.models import Plan


class Command(BaseCommand):
    help = "Create default subscription plans"

    def handle(self, *args, **kwargs):
        plans = [
            {"name": "Free", "slug": "free", "price_monthly": 0, "max_projects": 3},
            {"name": "Pro", "slug": "pro", "price_monthly": 29, "max_projects": 50},
            {
                "name": "Enterprise",
                "slug": "enterprise",
                "price_monthly": 99,
                "max_projects": -1,
            },
        ]

        for plan_data in plans:
            Plan.objects.get_or_create(slug=plan_data["slug"], defaults=plan_data)
            self.stdout.write(f"✅ Created plan: {plan_data['name']}")
