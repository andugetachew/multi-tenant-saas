import json

from channels.generic.websocket import AsyncWebsocketConsumer


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

        await self.channel_layer.group_send(
            self.room_group_name, {"type": "comment_message", "comment": data}
        )

    async def comment_message(self, event):

        await self.send(
            text_data=json.dumps({"type": "new_comment", "comment": event["comment"]})
        )
