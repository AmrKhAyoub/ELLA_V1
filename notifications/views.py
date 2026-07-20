# notifications/views.py
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import NotificationHistory
from .serializers import NotificationSerializer


class NotificationListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # using the test user with ID 1
        # user, _ = User.objects.get_or_create(id=1, defaults={"username": "test_user_1"})
        user = request.user
        # retrieve all notifications for the user, ordered by creation date (most recent first)
        notifications = NotificationHistory.objects.filter(user=user).order_by(
            "-created_at"
        )
        serializer = NotificationSerializer(notifications, many=True)

        # calculate the count of unread notifications for the frontend (Badge)
        unread_count = notifications.filter(is_read=False).count()

        return Response(
            {"unread_count": unread_count, "notifications": serializer.data},
            status=status.HTTP_200_OK,
        )


class MarkNotificationsReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # using the test user with ID 1
        # user, _ = User.objects.get_or_create(id=1, defaults={"username": "test_user_1"})
        user = request.user

        # update all unread notifications to be read in one operation
        NotificationHistory.objects.filter(user=user, is_read=False).update(
            is_read=True
        )

        return Response(
            {"message": "All notifications have been marked as read."},
            status=status.HTTP_200_OK,
        )
