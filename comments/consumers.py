import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Comment


class CommentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.project_id = self.scope["url_route"]["kwargs"]["project_id"]
        self.room_group_name = f"comments_{self.project_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        comment = await self.save_comment(data)

        await self.channel_layer.group_send(
            self.room_group_name, {"type": "comment_message", "comment": comment}
        )

    async def comment_message(self, event):
        await self.send(
            text_data=json.dumps({"type": "new_comment", "comment": event["comment"]})
        )

    @database_sync_to_async
    def save_comment(self, data):
        user = self.scope["user"]
        return {
            "id": 0,
            "content": data["content"],
            "user_email": user.email,
            "created_at": "Just now",
        }
