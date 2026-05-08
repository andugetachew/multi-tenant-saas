import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Task


class TaskConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.project_id = self.scope["url_route"]["kwargs"]["project_id"]
        self.room_group_name = f"tasks_{self.project_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data["type"] == "task_update":
            task = await self.update_task(data)

            await self.channel_layer.group_send(
                self.room_group_name, {"type": "task_updated", "task": task}
            )

    async def task_updated(self, event):
        await self.send(
            text_data=json.dumps({"type": "task_updated", "task": event["task"]})
        )

    @database_sync_to_async
    def update_task(self, data):
        task = Task.objects.get(id=data["task_id"])
        task.status = data["status"]
        task.save()
        return {
            "id": task.id,
            "title": task.title,
            "status": task.status,
            "updated_by": self.scope["user"].email,
        }
