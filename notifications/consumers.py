# notifications/consumers.py
import json

from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Check if the user was authenticated by our JWTAuthMiddleware
        self.user = self.scope.get("user")

        if self.user and self.user.is_authenticated:
            # Use the authenticated user's ID for the group name
            self.group_name = f"user_{self.user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        else:
            # Reject connection if not authenticated
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_notification(self, event):
        title = event["title"]
        message = event["message"]

        await self.send(
            text_data=json.dumps(
                {"title": title, "message": message}, ensure_ascii=False
            )
        )
