from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification


def create_notification(user, title, message, notification_type="info", link=None):
    """Create notification and send real-time update"""
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link,
    )

    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"notifications_{user.id}",
            {
                "type": "notification_message",
                "message": {
                    "id": notification.id,
                    "title": title,
                    "message": message,
                    "type": notification_type,
                    "created_at": str(notification.created_at),
                },
            },
        )
    except Exception as e:
        print(f"WebSocket error: {e}")

    return notification
