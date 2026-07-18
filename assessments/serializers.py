# assessments/serializers.py
from rest_framework import serializers

from .models import AssessmentSession


class AssessmentSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentSession
        fields = [
            "id",
            "status",
            "current_step",
            "draft_data",
            "final_score",
            "assigned_level",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "final_score",
            "assigned_level",
            "updated_at",
        ]


class StepUpdateSerializer(serializers.Serializer):
    step_number = serializers.IntegerField(min_value=1, max_value=7)
    step_data = serializers.JSONField()
