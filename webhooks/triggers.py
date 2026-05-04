import requests
import json
from datetime import datetime
from .models import Webhook


def trigger_webhook(organization, event, data):
    """Trigger webhooks for an event"""
    webhooks = Webhook.objects.filter(
        organization=organization, is_active=True, events__contains=[event]
    )

    for webhook in webhooks:
        try:
            requests.post(
                webhook.url,
                json={"event": event, "data": data, "timestamp": str(datetime.now())},
                headers={"X-Webhook-Secret": webhook.secret},
                timeout=5,
            )
        except Exception as e:
            print(f"Webhook failed for {webhook.url}: {e}")
