import pytest
from django.utils import timezone
from datetime import timedelta

from organizations.models import Organization
from accounts.models import User
from notifications.models import Notification
from billing.tasks import check_subscription_expiry


@pytest.mark.django_db
class TestCheckSubscriptionExpiry:

    def test_expired_active_subscription_is_marked_expired(self):
        org = Organization.objects.create(
            name="Acme Corp", plan="pro", subscription_status="active"
        )
        org.trial_ends_at = timezone.now() - timedelta(days=1)
        org.save()

        check_subscription_expiry()
        org.refresh_from_db()

        assert org.subscription_status == "expired"
        assert org.plan == "trial"

    def test_owner_receives_notification_on_expiry(self):
        org = Organization.objects.create(
            name="Acme Corp", plan="pro", subscription_status="active"
        )
        org.trial_ends_at = timezone.now() - timedelta(days=1)
        org.save()

        owner = User.objects.create_user(
            email="owner@acme.com", password="pass123",
            organization=org, is_owner=True,
        )
        non_owner = User.objects.create_user(
            email="member@acme.com", password="pass123",
            organization=org, is_owner=False,
        )

        check_subscription_expiry()

        assert Notification.objects.filter(user=owner, notification_type="warning").exists()
        assert not Notification.objects.filter(user=non_owner).exists()

    def test_non_expired_subscription_is_untouched(self):
        org = Organization.objects.create(
            name="Acme Corp", plan="pro", subscription_status="active"
        )
        org.trial_ends_at = timezone.now() + timedelta(days=5)
        org.save()

        check_subscription_expiry()
        org.refresh_from_db()

        assert org.subscription_status == "active"
        assert org.plan == "pro"

    def test_already_expired_subscription_not_reprocessed(self):
        """Task filters on subscription_status='active', so already-expired orgs are skipped."""
        org = Organization.objects.create(
            name="Old Corp", plan="trial", subscription_status="expired"
        )
        org.trial_ends_at = timezone.now() - timedelta(days=30)
        org.save()

        owner = User.objects.create_user(
            email="old@corp.com", password="pass123",
            organization=org, is_owner=True,
        )

        check_subscription_expiry()

        # No new notification since org was already expired, not newly transitioned
        assert not Notification.objects.filter(user=owner).exists()

    def test_org_with_no_trial_end_date_is_unaffected(self):
        org = Organization.objects.create(
            name="No Trial Corp", plan="enterprise", subscription_status="active"
        )
        org.trial_ends_at = None
        org.save()

        check_subscription_expiry()
        org.refresh_from_db()

        assert org.subscription_status == "active"