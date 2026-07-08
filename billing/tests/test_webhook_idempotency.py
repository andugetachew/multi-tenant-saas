from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APIClient
from organizations.models import Organization
from accounts.models import User
from billing.models import Plan, Subscription, Invoice, Transaction, ProcessedWebhookEvent


class WebhookIdempotencyTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Idempotency Org", plan="trial")
        self.owner = User.objects.create_user(
            email="idempotency_owner@example.com",
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
            defaults={"name": "Basic", "price_monthly": 9, "max_projects": 20, "max_users": 10},
        )
        self.subscription, _ = Subscription.objects.get_or_create(
            organization=self.org,
            defaults={"plan": self.free_plan, "status": "active"},
        )
        self.invoice = Invoice.objects.create(
            organization=self.org,
            subscription=self.subscription,
            invoice_number="INV-IDEMP001",
            amount=9,
            status="pending",
            requested_plan=self.basic_plan,
            requested_by=self.owner,
        )

    def _fake_event(self, event_id, event_type, data_object):
        return {"id": event_id, "type": event_type, "data": {"object": data_object}}

    @patch("billing.views.stripe.Webhook.construct_event")
    def test_duplicate_event_processed_only_once(self, mock_construct_event):
        event = self._fake_event(
            "evt_duplicate_test",
            "checkout.session.completed",
            {
                "metadata": {"organization_id": str(self.org.id), "plan_slug": "basic"},
                "subscription": "sub_dup_test",
                "amount_total": 900,
            },
        )
        mock_construct_event.return_value = event

        response1 = self.client.post(
            "/api/billing/webhook/stripe/", data=b"{}",
            content_type="application/json", HTTP_STRIPE_SIGNATURE="fake_sig",
        )
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(Transaction.objects.filter(organization=self.org).count(), 1)
        self.assertEqual(ProcessedWebhookEvent.objects.filter(event_id="evt_duplicate_test").count(), 1)

        response2 = self.client.post(
            "/api/billing/webhook/stripe/", data=b"{}",
            content_type="application/json", HTTP_STRIPE_SIGNATURE="fake_sig",
        )
        self.assertEqual(response2.status_code, 200)

        self.assertEqual(Transaction.objects.filter(organization=self.org).count(), 1)
        self.assertEqual(ProcessedWebhookEvent.objects.filter(event_id="evt_duplicate_test").count(), 1)