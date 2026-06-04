from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from organizations.models import Organization
from accounts.models import User
from billing.models import Plan


class SubscriptionTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Test Org", plan="trial")
        self.user = User.objects.create_user(
            email="billing_user@example.com",
            password="pass123",
            organization=self.org,
            is_email_verified=True,
            is_owner=True,  # ✅ required by RequestUpgradeView
        )
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

        self.plan = Plan.objects.get_or_create(
            slug="basic",
            defaults={
                "name": "Basic",
                "price_monthly": 9.99,
                "is_active": True,
                "max_projects": 20,
                "max_users": 10,
            },
        )[0]

    def test_get_subscription_status(self):
        """Test getting subscription status"""
        response = self.client.get("/api/billing/subscription/")
        self.assertEqual(response.status_code, 200)

        self.assertIn("plan", response.data)
        self.assertIn("features", response.data)

    def test_upgrade_plan(self):
        """Test requesting a plan upgrade"""

        response = self.client.post(
            "/api/billing/upgrade/request/",
            {
                "plan_slug": "basic",
                "billing_email": "billing@example.com",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 202)
        self.assertIn("invoice_id", response.data)
        self.assertIn("invoice_number", response.data)
        self.assertEqual(response.data["status"], "pending")
