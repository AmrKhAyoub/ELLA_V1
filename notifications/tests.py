# notifications/tests.py
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import NotificationHistory

User = get_user_model()


class NotificationsAPITests(APITestCase):
    def setUp(self):
        """
        Set up the test environment: create a user, generate token,
        and create some dummy notifications in the database.
        """
        self.user = User.objects.create_user(
            username="notif_user",
            email="notif@example.com",
            password="StrongPassword123!",
        )
        self.token = str(RefreshToken.for_user(self.user).access_token)

        self.list_url = reverse("notification_list")
        self.mark_read_url = reverse("mark_notifications_read")

        # Create two unread notifications for this user
        NotificationHistory.objects.create(
            user=self.user, title="Alert 1", message="Message 1", is_read=False
        )
        NotificationHistory.objects.create(
            user=self.user, title="Alert 2", message="Message 2", is_read=False
        )

    def test_get_notifications_authenticated(self):
        """
        Test that an authenticated user can fetch their notifications and unread count.
        """
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # We expect the unread count to be 2
        self.assertEqual(response.data["unread_count"], 2)
        # We expect 2 notifications in the list
        self.assertEqual(len(response.data["notifications"]), 2)

    def test_get_notifications_unauthenticated(self):
        """
        Test that unauthenticated users are blocked from viewing notifications.
        """
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_mark_notifications_as_read(self):
        """
        Test that calling the mark-read endpoint successfully updates the database.
        """
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token)
        response = self.client.post(self.mark_read_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify in the database that no unread notifications exist for this user
        unread_exists = NotificationHistory.objects.filter(
            user=self.user, is_read=False
        ).exists()
        self.assertFalse(unread_exists)
