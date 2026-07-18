import json
import pytest
from channels.testing import WebsocketCommunicator

from core.asgi import application


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestCommentConsumer:
    async def test_connect_and_receive_broadcast(self):
        communicator = WebsocketCommunicator(application, "/ws/comments/1/")
        connected, _ = await communicator.connect()
        assert connected is True

        await communicator.send_to(text_data=json.dumps({"content": "hello"}))
        response = await communicator.receive_from()
        data = json.loads(response)

        assert data["type"] == "new_comment"
        assert data["comment"]["content"] == "hello"

        await communicator.disconnect()