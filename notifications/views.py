# notifications/views.py
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import NotificationHistory
from .serializers import NotificationSerializer


class TenPerPagePagination(PageNumberPagination):
    page_size = 10


class NotificationListAPIView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    pagination_class = TenPerPagePagination

    def get_queryset(self):
        # user current notifiactions
        return NotificationHistory.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # total of unread notifications
        unread_count = queryset.filter(is_read=False).count()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data["unread_count"] = unread_count
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {"unread_count": unread_count, "notifications": serializer.data}
        )


class MarkNotificationsReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # using the test user with ID 1
        user = request.user

        # update all unread notifications to be read in one operation
        NotificationHistory.objects.filter(user=user, is_read=False).update(
            is_read=True
        )

        return Response(
            {"message": "All notifications have been marked as read."},
            status=status.HTTP_200_OK,
        )
