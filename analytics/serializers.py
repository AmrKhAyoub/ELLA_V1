# analytics/serializers.py
from rest_framework import serializers

from .models import Mistake


class MistakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mistake
        fields = [
            "id",
            "wrong_text",
            "corrected_text",
            "category",
            "explanation",
            "created_at",
        ]
