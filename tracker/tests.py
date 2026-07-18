# tracker/tests.py
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

# Import the new models and tasks
from .models import EnrichedPlace
from .tasks import enrich_places_data_task

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


class TrackerTasksTests(APITestCase):
    def setUp(self):
        """
        Set up initial data for testing background tasks.
        """
        # Create a place that is already enriched to test the skipping logic
        EnrichedPlace.objects.create(
            name="Existing Cafe",
            city="Cairo",
            place_type="restaurant",
            ai_data={"description": "A very old and famous cafe."},
        )

    @patch("tracker.tasks.generate_ai_response_json")
    def test_enrich_places_data_task_new_place(self, mock_generate_json):
        """
        Test that a new place correctly calls the AI service and saves the returned JSON to the DB.
        """
        # Setup mock to return a valid dictionary
        mock_generate_json.return_value = {
            "description": "A quiet place for studying.",
            "atmosphere": "Academic",
            "contextual_vocabulary": ["book", "study", "exam", "focus", "read"],
            "language_opportunity": "Try reading a paragraph here.",
            "mini_challenge": "Read one page of an English book.",
        }

        places_list = [{"name": "New University Library", "type": "university"}]
        enrich_places_data_task(places_list, "Cairo")

        # Verify DB insertion
        self.assertTrue(
            EnrichedPlace.objects.filter(
                name="New University Library", city="Cairo"
            ).exists()
        )
        self.assertTrue(mock_generate_json.called)

    @patch("tracker.tasks.generate_ai_response_json")
    def test_enrich_places_data_task_existing_place(self, mock_generate_json):
        """
        Test that an existing place is correctly skipped to prevent redundant API calls.
        """
        places_list = [{"name": "Existing Cafe", "type": "restaurant"}]
        enrich_places_data_task(places_list, "Cairo")

        # Service should NOT be called because it is already in the database
        self.assertFalse(mock_generate_json.called)

    @patch("tracker.tasks.generate_ai_response_json")
    def test_enrich_places_data_task_api_failure(self, mock_generate_json):
        """
        Test that the task handles an empty/None response gracefully without creating a DB entry.
        """
        # Simulate an API failure returning None
        mock_generate_json.return_value = None

        places_list = [{"name": "Failing Museum", "type": "tourism"}]
        enrich_places_data_task(places_list, "Alexandria")

        # Verify it wasn't saved to the DB
        self.assertFalse(EnrichedPlace.objects.filter(name="Failing Museum").exists())
        self.assertTrue(mock_generate_json.called)
