from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Plan, Subscription
from organizations.models import Organization


@receiver(post_migrate)
def create_default_plans(sender, **kwargs):
    if sender.name == "billing":
        # Create default plans
        plans_data = [
            {
                "name": "Free",
                "slug": "free",
                "price_monthly": 0,
                "max_projects": 100,
                "max_users": 10,
            },
            {
                "name": "Pro",
                "slug": "pro",
                "price_monthly": 29,
                "max_projects": 1000,
                "max_users": 100,
            },
            {
                "name": "Enterprise",
                "slug": "enterprise",
                "price_monthly": 99,
                "max_projects": -1,
                "max_users": -1,
            },
        ]

        for plan_data in plans_data:
            Plan.objects.get_or_create(slug=plan_data["slug"], defaults=plan_data)

        # Create default subscription for existing organizations
        free_plan = Plan.objects.filter(slug="free").first()
        if free_plan:
            for org in Organization.objects.all():
                Subscription.objects.get_or_create(
                    organization=org,
                    defaults={
                        "plan": free_plan,
                        "status": "active",
                        "max_projects": free_plan.max_projects,
                        "max_users": free_plan.max_users,
                    },
                )
        print("✅ Default plans and subscriptions created")
