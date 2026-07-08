# billing/tests/test_cancellation.py
from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from organizations.models import Organization
from accounts.models import User
from billing.models import Plan, Subscription


class CancelSubscriptionTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Cancel Org", plan="trial")
        self.owner = User.objects.create_user(
            email="cancel_owner@example.com",
            password="pass123",
            organization=self.org,
            is_email_verified=True,
            is_owner=True,
        )
        self.non_owner = User.objects.create_user(
            email="cancel_member@example.com",
            password="pass123",
            organization=self.org,
            is_email_verified=True,
            is_owner=False,
        )

        self.pro_plan, _ = Plan.objects.get_or_create(
            slug="pro",
            defaults={"name": "Pro", "price_monthly": 29, "max_projects": 100, "max_users": 50},
        )

        self.subscription, _ = Subscription.objects.get_or_create(
            organization=self.org,
            defaults={
                "plan": self.pro_plan,
                "status": "active",
                "stripe_subscription_id": "sub_test_cancel123",
            },
        )

    def auth_as(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    @patch("billing.views.stripe.Subscription.modify")
    def test_owner_can_cancel_at_period_end(self, mock_modify):
        self.auth_as(self.owner)
        response = self.client.post("/api/billing/cancel/", format="json")

        self.assertEqual(response.status_code, 200)
        mock_modify.assert_called_once_with(
            "sub_test_cancel123", cancel_at_period_end=True
        )

        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, "active")

    def test_non_owner_cannot_cancel(self):
        self.auth_as(self.non_owner)
        response = self.client.post("/api/billing/cancel/", format="json")
        self.assertEqual(response.status_code, 403)

    def test_cannot_cancel_without_stripe_subscription(self):
        self.subscription.stripe_subscription_id = None
        self.subscription.save()

        self.auth_as(self.owner)
        response = self.client.post("/api/billing/cancel/", format="json")
        self.assertEqual(response.status_code, 400)

    def test_cannot_cancel_already_canceled_subscription(self):
        self.subscription.status = "canceled"
        self.subscription.save()

        self.auth_as(self.owner)
        response = self.client.post("/api/billing/cancel/", format="json")
        self.assertEqual(response.status_code, 400)

    @patch("billing.views.stripe.Subscription.modify")
    def test_stripe_error_returns_400(self, mock_modify):
        import stripe as stripe_module
        mock_modify.side_effect = stripe_module.error.InvalidRequestError(
            "No such subscription", "subscription"
        )

        self.auth_as(self.owner)
        response = self.client.post("/api/billing/cancel/", format="json")
        self.assertEqual(response.status_code, 400)