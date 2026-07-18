# tracker/tests.py
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class TrackerComprehensiveAPITests(APITestCase):
    def setUp(self):
        """
        Set up primary test users, JWT access tokens, and API endpoints.
        """
        self.user = User.objects.create_user(
            username="test_tracker_user",
            email="tracker@ella.com",
            password="SecurePassword123!",
        )
        self.access_token = str(RefreshToken.for_user(self.user).access_token)
        self.url = reverse(
            "update_location"
        )  # Matches path('api/tracker/update-location/', ...)

    @patch("tracker.views.process_location_task.delay")
    def test_update_location_success_with_coordinates(self, mock_task):
        """
        Scenario 1: Authenticated request with complete latitude and longitude.
        Expected: Status 202, Task triggered with parsed coordinates.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        payload = {"latitude": 30.0444, "longitude": 31.2357}
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(
            response.data["message"], "Location received. Processing in background..."
        )

        # Verify that celery task was called with correct arguments
        mock_task.assert_called_once_with(self.user.id, 30.0444, 31.2357, "8.8.8.8")

    @patch("tracker.views.process_location_task.delay")
    def test_update_location_with_empty_strings(self, mock_task):
        """
        Scenario 2: Authenticated request where coordinates are empty strings.
        Expected: Status 202, fields mapped to None so fallback logic triggers successfully.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        payload = {"latitude": "", "longitude": ""}
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mock_task.assert_called_once_with(self.user.id, None, None, "8.8.8.8")

    @patch("tracker.views.process_location_task.delay")
    def test_update_location_with_missing_keys(self, mock_task):
        """
        Scenario 3: Authenticated request with completely missing coordinate keys in the payload.
        Expected: Status 202, missing fields evaluate to None.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mock_task.assert_called_once_with(self.user.id, None, None, "8.8.8.8")

    def test_update_location_unauthenticated(self):
        """
        Scenario 4: Request made without any Authorization headers.
        Expected: Status 401 Unauthorized.
        """
        response = self.client.post(
            self.url, {"latitude": 30.0, "longitude": 31.0}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_location_invalid_token(self):
        """
        Scenario 5: Request made with an expired or manipulated JWT token.
        Expected: Status 401 Unauthorized.
        """
        self.client.credentials(
            HTTP_AUTHORIZATION="Bearer invalid_or_expired_token_signature"
        )
        response = self.client.post(
            self.url, {"latitude": 30.0, "longitude": 31.0}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("tracker.views.process_location_task.delay")
    def test_ip_extraction_from_x_forwarded_for(self, mock_task):
        """
        Scenario 6: Validate IP extraction logic from custom HTTP headers (X-Forwarded-For).
        Expected: Extracted client IP matches the first IP in the forwarded sequence.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        # Simulating a proxy environment forwarding real IP
        response = self.client.post(
            self.url,
            {"latitude": 30.0, "longitude": 31.0},
            HTTP_X_FORWARDED_FOR="198.51.100.42, 127.0.0.1",
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mock_task.assert_called_once_with(self.user.id, 30.0, 31.0, "198.51.100.42")
