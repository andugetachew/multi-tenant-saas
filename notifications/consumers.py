import json
from urllib.parse import parse_qs
from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        from channels.db import database_sync_to_async
        from rest_framework_simplejwt.tokens import AccessToken
        from accounts.models import User

        query = parse_qs(self.scope["query_string"].decode())
        token = query.get("token", [None])[0]

        if token:
            try:
                access_token = AccessToken(token)
                self.user_id = access_token["user_id"]
                self.room_group_name = f"notifications_{self.user_id}"

                await self.channel_layer.group_add(
                    self.room_group_name, self.channel_name
                )
                await self.accept()
            except Exception as e:
                print(f"Token error: {e}")
                await self.close()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    async def receive(self, text_data):
        pass

    async def notification_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))
