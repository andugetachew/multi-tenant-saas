# billing/tests/test_admin_approval.py
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from organizations.models import Organization
from accounts.models import User
from billing.models import Plan, Subscription, Invoice


class AdminApproveUpgradeTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Approval Org", plan="trial")
        self.owner = User.objects.create_user(
            email="approval_owner@example.com",
            password="pass123",
            organization=self.org,
            is_email_verified=True,
            is_owner=True,
        )

        self.admin_org = Organization.objects.create(name="Admin Org")
        self.superuser = User.objects.create_user(
            email="approval_admin@example.com",
            password="pass123",
            organization=self.admin_org,
            is_email_verified=True,
            is_superuser=True,
        )

        self.free_plan, _ = Plan.objects.get_or_create(
            slug="free",
            defaults={"name": "Free", "price_monthly": 0, "max_projects": 100, "max_users": 10},
        )
        self.pro_plan, _ = Plan.objects.get_or_create(
            slug="pro",
            defaults={
                "name": "Pro",
                "price_monthly": 29,
                "max_projects": 100,
                "max_users": 50,
                "has_real_time_analytics": True,
                "has_api_access": True,
            },
        )

        self.subscription, _ = Subscription.objects.get_or_create(
            organization=self.org,
            defaults={"plan": self.free_plan, "status": "active"},
        )

        self.invoice = Invoice.objects.create(
            organization=self.org,
            subscription=self.subscription,
            invoice_number="INV-APPROVAL001",
            amount=29,
            status="pending",
            requested_plan=self.pro_plan,
            requested_by=self.owner,
        )

    def auth_as(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_superuser_can_approve_invoice(self):
        self.auth_as(self.superuser)
        response = self.client.post(
            f"/api/billing/admin/approve/{self.invoice.id}/",
            {"action": "approve"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, "approved")
        self.assertEqual(self.invoice.approved_by, self.superuser)

        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.plan.slug, "pro")
        self.assertEqual(self.subscription.status, "active")
        self.assertEqual(self.subscription.max_projects, self.pro_plan.max_projects)
        self.assertEqual(self.subscription.max_users, self.pro_plan.max_users)
        self.assertEqual(self.subscription.has_real_time_analytics, self.pro_plan.has_real_time_analytics)

        self.org.refresh_from_db()
        self.assertEqual(self.org.plan, "pro")
        self.assertEqual(self.org.subscription_status, "active")
    def test_non_superuser_cannot_approve(self):
        self.auth_as(self.owner)
        response = self.client.post(
            f"/api/billing/admin/approve/{self.invoice.id}/",
            {"action": "approve"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_reject_invoice(self):
        self.auth_as(self.superuser)
        response = self.client.post(
            f"/api/billing/admin/approve/{self.invoice.id}/",
            {"action": "reject"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, "rejected")

    def test_invalid_action_returns_400(self):
        self.auth_as(self.superuser)
        response = self.client.post(
            f"/api/billing/admin/approve/{self.invoice.id}/",
            {"action": "bogus"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_approve_nonexistent_invoice_returns_404(self):
        self.auth_as(self.superuser)
        response = self.client.post(
            "/api/billing/admin/approve/99999/",
            {"action": "approve"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)