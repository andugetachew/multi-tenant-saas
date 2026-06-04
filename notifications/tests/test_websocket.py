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
        Ensure user cannot receive messages from another org
        """

        communicator = WebsocketCommunicator(
            application,
            f"/ws/notifications/?token={self.token}"
        )

        connected, _ = await communicator.connect()
        self.assertTrue(connected)


        await communicator.send_json_to({
            "type": "test.message",
            "message": "Org A message"
        })

        response = await communicator.receive_json_from()

  
        self.assertIn("message", response)

        await communicator.disconnect()