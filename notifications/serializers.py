# notifications/serializers.py
from rest_framework import serializers

from .models import NotificationHistory


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationHistory
        fields = ["id", "title", "message", "is_read", "created_at"]
