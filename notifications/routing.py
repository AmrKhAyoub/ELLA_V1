# notifications/routing.py
from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    # Remove the user_id from the URL pattern, it is extracted from the JWT token
    re_path(r"ws/notifications/$", consumers.NotificationConsumer.as_asgi()),
]
