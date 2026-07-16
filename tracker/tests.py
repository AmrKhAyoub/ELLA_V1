# tracker/tests.py
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class TrackerAPITests(APITestCase):
    def setUp(self):
        """
        Set up the test environment: create a valid user, generate a JWT token,
        and define the endpoint URL.
        """
        self.user = User.objects.create_user(
            username="tracker_user",
            email="tracker@example.com",
            password="StrongPassword123!",
        )
        # Generate JWT Token for the user
        self.token = str(RefreshToken.for_user(self.user).access_token)
        self.url = reverse(
            "update_location"
        )  # Make sure this name matches the one in ELLA/urls.py

    def test_update_location_with_valid_token(self):
        """
        Test that an authenticated user with a valid JWT token can update their location.
        """
        # Inject the token into the request headers
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token)

        data = {"latitude": 40.7128, "longitude": -74.0060}
        response = self.client.post(self.url, data)

        # We expect a 202 ACCEPTED status since Celery processes it in the background
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(
            response.data["message"], "Location received. Processing in background..."
        )

    def test_update_location_without_token(self):
        """
        Test that the API rejects requests that do not include an authorization token.
        """
        data = {"latitude": 40.7128, "longitude": -74.0060}
        # No credentials added here
        response = self.client.post(self.url, data)

        # We expect a 401 UNAUTHORIZED status
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_location_with_missing_coordinates(self):
        """
        Test that the API still accepts the request if coordinates are missing,
        meaning it will rely on the IP address.
        """
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token)

        # Empty payload
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
