from django.test import TransactionTestCase
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async

from core.asgi import application
from rest_framework_simplejwt.tokens import AccessToken

from organizations.models import Organization
from accounts.models import User


class WebSocketTestCase(TransactionTestCase):
    """Test WebSocket auth + real-time notifications (SaaS safe)"""

    def setUp(self):
        self.org = Organization.objects.create(name="Org A")
        self.other_org = Organization.objects.create(name="Org B")

        self.user = User.objects.create_user(
            email="user@example.com",
            password="pass123",
            organization=self.org,
            is_email_verified=True,
        )

        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="pass123",
            organization=self.other_org,
            is_email_verified=True,
        )

        self.token = str(AccessToken.for_user(self.user))



    async def test_websocket_connection_success(self):
        communicator = WebsocketCommunicator(
            application,
            f"/ws/notifications/?token={self.token}"
        )

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.disconnect()

    async def test_websocket_rejects_invalid_token(self):
        communicator = WebsocketCommunicator(
            application,
            "/ws/notifications/?token=invalid"
        )

        connected, _ = await communicator.connect()
        self.assertFalse(connected)



    async def test_websocket_tenant_isolation(self):
        """
        Ensure a user only receives notifications sent to their own group,
        not another org's user's notifications.
        """
        from channels.layers import get_channel_layer

        communicator = WebsocketCommunicator(
            application,
            f"/ws/notifications/?token={self.token}"
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        channel_layer = get_channel_layer()

        # Simulate a notification meant for a DIFFERENT user (other org)
        await channel_layer.group_send(
            f"notifications_{self.other_user.id}",
            {"type": "notification.message", "message": {"title": "Should not arrive"}},
        )

        # This user should NOT receive it
        nothing_received = await communicator.receive_nothing(timeout=1)
        self.assertTrue(nothing_received)

        # Now simulate a notification meant for THIS user — should arrive
        await channel_layer.group_send(
            f"notifications_{self.user.id}",
            {"type": "notification.message", "message": {"title": "Should arrive"}},
        )

        response = await communicator.receive_json_from(timeout=2)
        self.assertEqual(response["title"], "Should arrive")

        await communicator.disconnect()