from celery import shared_task
import requests
from datetime import datetime
from .models import Webhook, WebhookDelivery


@shared_task(bind=True, max_retries=5)
def deliver_webhook(self, webhook_id, event, payload):
    try:
        webhook = Webhook.objects.get(id=webhook_id)

        delivery = WebhookDelivery.objects.create(
            webhook=webhook, event=event, payload=payload, attempts=1
        )

        response = requests.post(
            webhook.url,
            json={
                "event": event,
                "data": payload,
                "timestamp": datetime.now().isoformat(),
            },
            headers={"X-Webhook-Secret": webhook.secret},
            timeout=10,
        )

        delivery.response_status = response.status_code
        delivery.response_body = response.text[:500]
        delivery.success = 200 <= response.status_code < 300
        delivery.completed_at = datetime.now()
        delivery.save()

        if not delivery.success:
            raise Exception(f"HTTP {response.status_code}")

        return delivery.id

    except Exception as e:
        self.retry(exc=e, countdown=60 * self.request.retries)
