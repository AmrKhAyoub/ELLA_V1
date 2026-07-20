# chats/urls.py
from django.urls import path

from .views import (
    SendMessageAPIView,
    SessionListCreateAPIView,
    SessionMessagesAPIView,
    SessionRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    # GET: List all sessions (?topic=name to filter) | POST: Create a new session
    path("sessions/", SessionListCreateAPIView.as_view(), name="session_list_create"),
    # GET: Retrieve | PUT/PATCH: Update Topic | DELETE: Delete Session and Messages
    path(
        "sessions/<uuid:session_id>/",
        SessionRetrieveUpdateDestroyAPIView.as_view(),
        name="session_detail",
    ),
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
