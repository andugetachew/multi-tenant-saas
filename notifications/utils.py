from .models import Notification


def create_notification(user, title, message, notification_type="info", link=None):
    """Create a notification for a user"""
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link,
        is_read=False,
    )
    return notification
