import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path

from notifications.consumers import NotificationConsumer
from tasks.consumers import TaskConsumer
from comments.consumers import CommentConsumer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            URLRouter(
                [
                    path(
                        "ws/notifications/",
                        NotificationConsumer.as_asgi(),
                    ),
                    path(
                        "ws/tasks/<int:project_id>/",
                        TaskConsumer.as_asgi(),
                    ),
                    path(
                        "ws/comments/<int:project_id>/",
                        CommentConsumer.as_asgi(),
                    ),
                ]
            )
        ),
    }
)
