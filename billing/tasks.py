# billing/tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from organizations.models import Organization


@shared_task
def check_subscription_expiry():
    """Check and update expired subscriptions"""
    expired_orgs = Organization.objects.filter(
        subscription_status="active", trial_ends_at__lt=timezone.now()
    )

    for org in expired_orgs:
        org.plan = "trial"
        org.subscription_status = "expired"
        org.save()

        # Notify organization owners
        from notifications.utils import create_notification

        for user in org.users.filter(is_owner=True):
            create_notification(
                user=user,
                title="Subscription Expired",
                message=f"Your subscription has expired. Please upgrade to continue using premium features.",
                notification_type="warning",
            )
