from django.core.cache import cache
from .models import Subscription


def get_organization_subscription(organization):
    """Get subscription with caching"""
    if not organization:
        return None

    cache_key = f"subscription_{organization.id}"
    subscription = cache.get(cache_key)

    if not subscription:
        try:
            subscription = Subscription.objects.select_related("plan").get(
                organization=organization
            )
            cache.set(cache_key, subscription, 300)
        except Subscription.DoesNotExist:
            subscription = None

    return subscription


def check_org_limit(organization, resource_type):
    """Check if organization has reached its limit"""
    if not organization:
        return True  # Allow if no organization

    subscription = get_organization_subscription(organization)

    if not subscription or subscription.status != "active":
        return True

    from projects.models import Project
    from accounts.models import User

    limit_map = {
        "projects": (
            "max_projects",
            Project.objects.filter(organization=organization).count(),
        ),
        "users": ("max_users", User.objects.filter(organization=organization).count()),
    }

    if resource_type not in limit_map:
        return True

    limit_field, current_count = limit_map[resource_type]
    max_limit = getattr(subscription, limit_field, 100)

    if max_limit == -1:
        return True

    return current_count < max_limit


def get_remaining_limit(organization, resource_type):
    """Get remaining limit for a resource"""
    if not organization:
        return 999

    subscription = get_organization_subscription(organization)

    if not subscription or subscription.status != "active":
        return 0

    limit_map = {
        "projects": ("max_projects", "projects"),
        "users": ("max_users", "users"),
    }

    if resource_type not in limit_map:
        return 0

    limit_field, count_field = limit_map[resource_type]
    max_limit = getattr(subscription, limit_field)

    if max_limit == -1:
        return 999999

    from projects.models import Project
    from accounts.models import User

    if resource_type == "projects":
        current = Project.objects.filter(organization=organization).count()
    elif resource_type == "users":
        current = User.objects.filter(organization=organization).count()
    else:
        current = 0

    return max(0, max_limit - current)
