# accounts/serializers.py
from rest_framework import serializers

from .models import CustomUser


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )

    class Meta:
        model = CustomUser
        fields = ("id", "username", "email", "password")

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        return user


class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer for displaying and updating user details."""

    class Meta:
        model = CustomUser
        # Included all the fields that the user can view/update
        fields = (
            "id",
            "username",
            "email",
            "avatar",
            "current_level",
            "target_level",
            "learning_goal",
            "gender",
            "birth_date",
            "study_level",
            "study_field",
            "has_taken_initial_assessment",
        )
        # Prevent users from changing their and assessment status,
        read_only_fields = ("id", "email", "has_taken_initial_assessment")


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change endpoint."""

    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct.")
        return value
