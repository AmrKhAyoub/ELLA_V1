# chats/urls.py
from django.urls import path

from .views import SendMessageAPIView, SessionListCreateAPIView, SessionMessagesAPIView

urlpatterns = [
    path("sessions/", SessionListCreateAPIView.as_view(), name="session_list_create"),
    path(
        "sessions/<uuid:session_id>/messages/",
        SessionMessagesAPIView.as_view(),
        name="session_messages",
    ),
    path(
        "sessions/<uuid:session_id>/send/",
        SendMessageAPIView.as_view(),
        name="send_message",
    ),
]
