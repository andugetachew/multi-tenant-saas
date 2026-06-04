from django.db import models
from django.db.models import Count


def check_org_limit(organization, resource_type):
    """Check if organization has reached its limit for a resource"""
    limits = {
        "trial": {"projects": 5, "tasks": 50, "users": 3},
        "basic": {"projects": 20, "tasks": 200, "users": 10},
        "pro": {"projects": 100, "tasks": 1000, "users": 50},
        "enterprise": {"projects": 999999, "tasks": 999999, "users": 999999},
    }

    # If no plan, use trial limits
    plan = organization.plan if organization.plan else "trial"
    limit = limits.get(plan, limits["trial"]).get(resource_type, 0)

    if resource_type == "projects":
        from projects.models import Project

        current = Project.objects.filter(organization=organization).count()
    elif resource_type == "tasks":
        from projects.models import Task

        current = Task.objects.filter(project__organization=organization).count()
    elif resource_type == "users":
        current = organization.users.count()
    else:
        return True

    return current < limit


def get_remaining_limit(organization, resource_type):
    """Get remaining limit for organization"""
    limits = {
        "trial": {"projects": 5, "tasks": 50, "users": 3},
        "basic": {"projects": 20, "tasks": 200, "users": 10},
        "pro": {"projects": 100, "tasks": 1000, "users": 50},
        "enterprise": {"projects": 999999, "tasks": 999999, "users": 999999},
    }

    plan = organization.plan
    limit = limits.get(plan, limits["trial"]).get(resource_type, 0)

    if resource_type == "projects":
        from projects.models import Project

        current = Project.objects.filter(organization=organization).count()
    elif resource_type == "tasks":
        from projects.models import Task

        current = Task.objects.filter(project__organization=organization).count()
    elif resource_type == "users":
        current = organization.users.count()
    else:
        return 0

    return limit - current
