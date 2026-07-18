# notifications/tests.py
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import NotificationHistory

User = get_user_model()


class NotificationsAPIScenarioTests(APITestCase):
    def setUp(self):
        """
        Set up the isolated database: Create two separate users with active notifications.
        """
        self.user_a = User.objects.create_user(
            username="user_a", email="a@ella.com", password="Password123!"
        )
        self.user_b = User.objects.create_user(
            username="user_b", email="b@ella.com", password="Password123!"
        )

        self.token_a = str(RefreshToken.for_user(self.user_a).access_token)
        self.token_b = str(RefreshToken.for_user(self.user_b).access_token)

        self.list_url = reverse("notification_list")
        self.mark_read_url = reverse("mark_notifications_read")

        # Create unread notifications for User A
        self.notif_a1 = NotificationHistory.objects.create(
            user=self.user_a, title="A1 Title", message="A1 Msg", is_read=False
        )
        self.notif_a2 = NotificationHistory.objects.create(
            user=self.user_a, title="A2 Title", message="A2 Msg", is_read=False
        )

        # Create one read notification for User A
        self.notif_a3 = NotificationHistory.objects.create(
            user=self.user_a, title="A3 Title", message="A3 Msg", is_read=True
        )

        # Create unread notifications for User B
        self.notif_b = NotificationHistory.objects.create(
            user=self.user_b, title="B Title", message="B Msg", is_read=False
        )

    def test_get_notifications_with_correct_counts_and_data_isolation(self):
        """
        Scenario 1: Authenticated User A requests their notifications.
        Expected: Returns only User A's notifications, unread count is exactly 2,
        and no trace of User B's notifications is present in the response.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_a}")
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["unread_count"], 2)

        # Verify only 3 notifications are returned for User A (2 unread + 1 read)
        self.assertEqual(len(response.data["notifications"]), 3)

        # Verify that User B's notification is not present
        titles = [notif["title"] for notif in response.data["notifications"]]
        self.assertNotIn("B Title", titles)

    def test_bulk_mark_as_read_affects_only_request_user(self):
        """
        Scenario 2: Authenticated User A triggers the mark-all-read endpoint.
        Expected: All unread notifications for User A are marked True.
        Importantly, User B's notifications MUST remain unread.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_a}")
        response = self.client.post(self.mark_read_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"], "All notifications have been marked as read."
        )

        # Verify database state for User A
        user_a_unread_exists = NotificationHistory.objects.filter(
            user=self.user_a, is_read=False
        ).exists()
        self.assertFalse(user_a_unread_exists)

        # Verify User B's notifications were NOT modified
        self.notif_b.refresh_from_db()
        self.assertFalse(self.notif_b.is_read)

    def test_notification_endpoints_require_authentication(self):
        """
        Scenario 3: Unauthenticated request to both notification endpoints.
        Expected: Returns 401 Unauthorized for both.
        """
        # Test List URL
        response_list = self.client.get(self.list_url)
        self.assertEqual(response_list.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test Mark Read URL
        response_mark = self.client.post(self.mark_read_url)
        self.assertEqual(response_mark.status_code, status.HTTP_401_UNAUTHORIZED)
