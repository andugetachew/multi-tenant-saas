import json
from channels.generic.websocket import AsyncWebsocketConsumer


class TaskConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.project_id = self.scope["url_route"]["kwargs"]["project_id"]
        self.room_group_name = f"tasks_{self.project_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # 👇 receives message from frontend
    async def receive(self, text_data):
        data = json.loads(text_data)

        await self.channel_layer.group_send(
            self.room_group_name, {"type": "task_update_event", "task": data}
        )

    # 👇 sends message to frontend
    async def task_update_event(self, event):
        await self.send(
            text_data=json.dumps({"type": "task_updated", "task": event["task"]})
        )
