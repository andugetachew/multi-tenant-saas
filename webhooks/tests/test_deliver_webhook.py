import pytest
from unittest.mock import patch, Mock
from celery.exceptions import Retry

from organizations.models import Organization
from webhooks.models import Webhook, WebhookDelivery
from webhooks.tasks import deliver_webhook


@pytest.fixture
def webhook(db):
    org = Organization.objects.create(name="Test Org")
    return Webhook.objects.create(
        organization=org,
        url="https://example.com/hook",
        events=["project.created"],
        secret="test-secret",
        is_active=True,
    )


@pytest.mark.django_db
class TestDeliverWebhook:

    @patch("webhooks.tasks.requests.post")
    def test_successful_delivery_marks_success_and_returns_delivery_id(
        self, mock_post, webhook
    ):
        mock_post.return_value = Mock(status_code=200, text="OK")

        result = deliver_webhook.apply(
            args=[webhook.id, "project.created", {"project_id": 1}]
        )

        delivery_id = result.get()
        delivery = WebhookDelivery.objects.get(id=delivery_id)

        assert delivery.success is True
        assert delivery.response_status == 200
        assert delivery.response_body == "OK"
        assert delivery.event == "project.created"
        assert delivery.payload == {"project_id": 1}
        assert delivery.completed_at is not None

        # Confirms the secret is sent so receivers can verify authenticity
        _, kwargs = mock_post.call_args
        assert kwargs["headers"]["X-Webhook-Secret"] == "test-secret"
        assert kwargs["json"]["event"] == "project.created"

    @patch("webhooks.tasks.requests.post")
    def test_non_2xx_response_marks_failure_and_retries(self, mock_post, webhook):
        mock_post.return_value = Mock(status_code=500, text="Internal Server Error")

        with pytest.raises(Retry):
            deliver_webhook.apply(
                args=[webhook.id, "task.updated", {"task_id": 5}], throw=True
            )

        delivery = WebhookDelivery.objects.get(webhook=webhook, event="task.updated")
        assert delivery.success is False
        assert delivery.response_status == 500

    @patch("webhooks.tasks.requests.post")
    def test_response_body_truncated_to_500_chars(self, mock_post, webhook):
        long_body = "x" * 1000
        mock_post.return_value = Mock(status_code=200, text=long_body)

        result = deliver_webhook.apply(
            args=[webhook.id, "project.created", {"project_id": 2}]
        )
        delivery = WebhookDelivery.objects.get(id=result.get())

        assert len(delivery.response_body) == 500

    @patch("webhooks.tasks.requests.post")
    def test_creates_delivery_record_before_sending_request(self, mock_post, webhook):
        """Delivery is logged even if the request fails, since attempts=1 is set on create."""
        mock_post.side_effect = Exception("Connection timeout")

        with pytest.raises(Retry):
            deliver_webhook.apply(
                args=[webhook.id, "project.created", {"project_id": 3}], throw=True
            )

        delivery = WebhookDelivery.objects.get(webhook=webhook, event="project.created")
        assert delivery.attempts == 1
        assert delivery.success is False  # never updated since exception happened first