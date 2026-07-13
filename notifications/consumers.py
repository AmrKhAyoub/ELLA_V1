# notifications/consumers.py
import json

from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # We will use user_id passed in URL parameters (e.g., ws://.../ws/1/)
        self.user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.group_name = f"user_{self.user_id}"

        # Join user-specific group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Receive message from room group (Triggered by Celery)
    async def send_notification(self, event):
        title = event["title"]
        message = event["message"]

        # Send message to WebSocket
        await self.send(text_data=json.dumps({"title": title, "message": message}))
