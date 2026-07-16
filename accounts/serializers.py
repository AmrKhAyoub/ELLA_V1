# accounts/serializers.py
from rest_framework import serializers

from .models import CustomUser


class UserRegistrationSerializer(serializers.ModelSerializer):
    # Ensure the password is write-only and required
    password = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )

    class Meta:
        model = CustomUser
        fields = ("id", "username", "email", "password")

    def create(self, validated_data):
        # hashing the password before saving the user
        user = CustomUser.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        return user


class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer for displaying user details."""

    class Meta:
        model = CustomUser
        fields = ("id", "username", "email", "avatar", "current_level", "target_level")
