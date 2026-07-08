# billing/tests/test_checkout.py
from unittest.mock import patch, MagicMock
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from organizations.models import Organization
from accounts.models import User
from billing.models import Plan, Subscription, Invoice, Transaction


class CreateCheckoutSessionTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Checkout Org", plan="trial")
        self.owner = User.objects.create_user(
            email="checkout_owner@example.com",
            password="pass123",
            organization=self.org,
            is_email_verified=True,
            is_owner=True,
        )
        self.non_owner = User.objects.create_user(
            email="checkout_member@example.com",
            password="pass123",
            organization=self.org,
            is_email_verified=True,
            is_owner=False,
        )

        self.free_plan, _ = Plan.objects.get_or_create(
            slug="free",
            defaults={"name": "Free", "price_monthly": 0, "max_projects": 100, "max_users": 10},
        )
        self.basic_plan, _ = Plan.objects.get_or_create(
            slug="basic",
            defaults={
                "name": "Basic",
                "price_monthly": 9,
                "max_projects": 20,
                "max_users": 10,
                "stripe_price_id": "price_test_basic",
            },
        )

        self.subscription, _ = Subscription.objects.get_or_create(
            organization=self.org,
            defaults={"plan": self.free_plan, "status": "active"},
        )

    def auth_as(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    @patch("billing.views.stripe.checkout.Session.create")
    @patch("billing.views.stripe.Customer.create")
    def test_owner_can_create_checkout_session(self, mock_customer_create, mock_session_create):
        mock_customer_create.return_value = MagicMock(id="cus_test123")
        mock_session_create.return_value = MagicMock(url="https://checkout.stripe.com/test-session")

        self.auth_as(self.owner)
        response = self.client.post(
            "/api/billing/checkout/", {"plan_slug": "basic"}, format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["checkout_url"], "https://checkout.stripe.com/test-session")

        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.plan.slug, "basic")
        self.assertEqual(self.subscription.stripe_customer_id, "cus_test123")

        invoice = Invoice.objects.filter(organization=self.org).latest("issue_date")
        self.assertEqual(invoice.status, "pending")

    def test_non_owner_cannot_create_checkout_session(self):
        self.auth_as(self.non_owner)
        response = self.client.post(
            "/api/billing/checkout/", {"plan_slug": "basic"}, format="json"
        )
        self.assertEqual(response.status_code, 403)

    def test_rejects_plan_without_stripe_price_id(self):
        self.auth_as(self.owner)
        response = self.client.post(
            "/api/billing/checkout/", {"plan_slug": "free"}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_rejects_invalid_plan_slug(self):
        self.auth_as(self.owner)
        response = self.client.post(
            "/api/billing/checkout/", {"plan_slug": "nonexistent"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        
    @patch("billing.views.stripe.checkout.Session.create")
    @patch("billing.views.stripe.Customer.create")
    def test_downgrade_from_pro_to_basic(self, mock_customer_create, mock_session_create):
        pro_plan, _ = Plan.objects.get_or_create(
            slug="pro",
            defaults={"name": "Pro", "price_monthly": 29, "max_projects": 100, "max_users": 50},
        )
        self.subscription.plan = pro_plan
        self.subscription.status = "active"
        self.subscription.stripe_customer_id = "cus_existing_pro"
        self.subscription.save()

        mock_session_create.return_value = MagicMock(url="https://checkout.stripe.com/downgrade-session")

        self.auth_as(self.owner)
        response = self.client.post(
            "/api/billing/checkout/", {"plan_slug": "basic"}, format="json"
        )

        self.assertEqual(response.status_code, 200)
        mock_customer_create.assert_not_called()  # reuses existing customer

        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.plan.slug, "basic")
        self.assertEqual(self.subscription.status, "pending")  # pending until webhook confirms payment


class StripeWebhookTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Webhook Org", plan="trial")
        self.owner = User.objects.create_user(
            email="webhook_owner@example.com",
            password="pass123",
            organization=self.org,
            is_email_verified=True,
            is_owner=True,
        )
        self.free_plan, _ = Plan.objects.get_or_create(
            slug="free",
            defaults={"name": "Free", "price_monthly": 0, "max_projects": 100, "max_users": 10},
        )
        self.basic_plan, _ = Plan.objects.get_or_create(
            slug="basic",
            defaults={
                "name": "Basic",
                "price_monthly": 9,
                "max_projects": 20,
                "max_users": 10,
                "stripe_price_id": "price_test_basic",
            },
        )
        self.subscription, _ = Subscription.objects.get_or_create(
            organization=self.org,
            defaults={"plan": self.free_plan, "status": "active"},
        )
        self.invoice = Invoice.objects.create(
            organization=self.org,
            subscription=self.subscription,
            invoice_number="INV-WEBHOOK001",
            amount=9,
            status="pending",
            requested_plan=self.basic_plan,
            requested_by=self.owner,
        )

    def _fake_event(self, event_type, data_object):
        return {"type": event_type, "data": {"object": data_object}}

    @patch("billing.views.stripe.Webhook.construct_event")
    def test_checkout_completed_activates_subscription(self, mock_construct_event):
        mock_construct_event.return_value = self._fake_event(
            "checkout.session.completed",
            {
                "metadata": {"organization_id": str(self.org.id), "plan_slug": "basic"},
                "subscription": "sub_test123",
                "amount_total": 900,
            },
        )

        response = self.client.post(
            "/api/billing/webhook/stripe/", data=b"{}",
            content_type="application/json", HTTP_STRIPE_SIGNATURE="fake_sig",
        )

        self.assertEqual(response.status_code, 200)

        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.plan.slug, "basic")
        self.assertEqual(self.subscription.status, "active")

        self.org.refresh_from_db()
        self.assertEqual(self.org.plan, "basic")

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, "paid")

        txn = Transaction.objects.get(organization=self.org)
        self.assertEqual(txn.amount, 9)

    @patch("billing.views.stripe.Webhook.construct_event")
    def test_invalid_signature_returns_400(self, mock_construct_event):
        from stripe import error as stripe_error
        mock_construct_event.side_effect = stripe_error.SignatureVerificationError("bad sig", "sig_header")

        response = self.client.post(
            "/api/billing/webhook/stripe/", data=b"{}",
            content_type="application/json", HTTP_STRIPE_SIGNATURE="bad_sig",
        )
        self.assertEqual(response.status_code, 400)

    @patch("billing.views.stripe.Webhook.construct_event")
    def test_subscription_deleted_marks_canceled(self, mock_construct_event):
        self.subscription.stripe_subscription_id = "sub_test123"
        self.subscription.status = "active"
        self.subscription.save()

        mock_construct_event.return_value = self._fake_event(
            "customer.subscription.deleted", {"id": "sub_test123"}
        )

        response = self.client.post(
            "/api/billing/webhook/stripe/", data=b"{}",
            content_type="application/json", HTTP_STRIPE_SIGNATURE="fake_sig",
        )

        self.assertEqual(response.status_code, 200)
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, "canceled")