# chats/serializers.py
from rest_framework import serializers

from .models import Message, Session


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "sender", "content_text", "audio_file", "timestamp"]


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ["id", "topic", "created_at"]
