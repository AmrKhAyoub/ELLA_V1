# chats/models.py
import uuid

from django.conf import settings
from django.db import models


class Session(models.Model):
    # UUID is highly secure for session URLs to prevent guessing
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_sessions"
    )
    topic = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="For example: Past Simple Practice",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session {self.id} - {self.user.username}"


class Message(models.Model):
    class SenderChoices(models.TextChoices):
        USER = "user", "Student"
        AI = "ai", "AI Tutor"

    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.CharField(max_length=10, choices=SenderChoices.choices)
    content_text = models.TextField()
    audio_file = models.FileField(upload_to="chat_audios/", null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Order messages by time to maintain the conversation flow
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.sender} at {self.timestamp}"
