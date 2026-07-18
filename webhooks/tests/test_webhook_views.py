import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from organizations.models import Organization
from accounts.models import User
from webhooks.models import Webhook
from webhooks.views import WebhookListCreateView, WebhookDetailView

factory = APIRequestFactory()


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Acme Corp")


@pytest.fixture
def user(org):
    return User.objects.create_user(email="u@acme.com", password="pass123", organization=org)


@pytest.mark.django_db
class TestWebhookListCreateView:
    def test_creates_webhook_with_generated_secret(self, user, org):
        request = factory.post(
            "/api/webhooks/",
            {"url": "https://example.com/hook", "events": ["project.created"]},
            format="json",
        )
        force_authenticate(request, user=user)

        view = WebhookListCreateView.as_view()
        response = view(request)

        assert response.status_code == 201
        webhook = Webhook.objects.get(organization=org)
        assert webhook.secret  # non-empty, auto-generated
        assert len(webhook.secret) > 20

    def test_only_lists_own_organization_webhooks(self, user, org):
        other_org = Organization.objects.create(name="Other")
        Webhook.objects.create(organization=org, url="https://mine.com", secret="s1")
        Webhook.objects.create(organization=other_org, url="https://other.com", secret="s2")

        request = factory.get("/api/webhooks/")
        force_authenticate(request, user=user)

        view = WebhookListCreateView.as_view()
        response = view(request)

        urls = [w["url"] for w in response.data["results"]]
        assert "https://mine.com" in urls
        assert "https://other.com" not in urls


@pytest.mark.django_db
class TestWebhookDetailView:
    def test_retrieves_own_webhook(self, user, org):
        webhook = Webhook.objects.create(organization=org, url="https://example.com", secret="s1")

        request = factory.get(f"/api/webhooks/{webhook.id}/")
        force_authenticate(request, user=user)

        view = WebhookDetailView.as_view()
        response = view(request, pk=webhook.id)

        assert response.status_code == 200
        assert response.data["url"] == "https://example.com"

    def test_cannot_retrieve_other_organization_webhook(self, user):
        other_org = Organization.objects.create(name="Other")
        webhook = Webhook.objects.create(organization=other_org, url="https://other.com", secret="s1")

        request = factory.get(f"/api/webhooks/{webhook.id}/")
        force_authenticate(request, user=user)

        view = WebhookDetailView.as_view()
        response = view(request, pk=webhook.id)

        assert response.status_code == 404