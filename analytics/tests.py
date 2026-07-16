# analytics/tests.py
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

# Import models from other apps to build the relationships
from chats.models import Message, Session

from .models import Mistake

User = get_user_model()


class AnalyticsAPITests(APITestCase):
    def setUp(self):
        """
        Set up the test environment: create users, tokens, chat sessions,
        messages, and mistake records to test the API thoroughly.
        """
        # 1. Create the primary test user
        self.user1 = User.objects.create_user(
            username="student_1",
            email="student1@example.com",
            password="StrongPassword123!",
        )
        self.token1 = str(RefreshToken.for_user(self.user1).access_token)

        # Create a session and messages for user 1
        self.session1 = Session.objects.create(user=self.user1, topic="Test Session 1")
        self.msg1_user1 = Message.objects.create(
            session=self.session1,
            sender=Message.SenderChoices.USER,
            content_text="He go to school.",
        )
        self.msg2_user1 = Message.objects.create(
            session=self.session1,
            sender=Message.SenderChoices.USER,
            content_text="It is a beautifull day.",
        )

        # Create mistakes for user 1 (Grammar and Spelling)
        self.mistake1 = Mistake.objects.create(
            user=self.user1,
            message=self.msg1_user1,
            wrong_text="He go",
            corrected_text="He goes",
            category=Mistake.CategoryChoices.GRAMMAR,
            explanation="Use 'goes' for third-person singular in Present Simple.",
        )
        self.mistake2 = Mistake.objects.create(
            user=self.user1,
            message=self.msg2_user1,
            wrong_text="beautifull",
            corrected_text="beautiful",
            category=Mistake.CategoryChoices.SPELLING,
            explanation="Beautiful has only one 'l'.",
        )

        # 2. Create a secondary test user to test data isolation
        self.user2 = User.objects.create_user(
            username="student_2",
            email="student2@example.com",
            password="StrongPassword123!",
        )
        self.session2 = Session.objects.create(user=self.user2, topic="Test Session 2")
        self.msg1_user2 = Message.objects.create(
            session=self.session2,
            sender=Message.SenderChoices.USER,
            content_text="I doesn't know.",
        )

        # Create a mistake for user 2
        self.mistake3 = Mistake.objects.create(
            user=self.user2,
            message=self.msg1_user2,
            wrong_text="I doesn't",
            corrected_text="I don't",
            category=Mistake.CategoryChoices.GRAMMAR,
            explanation="Use 'do not' or 'don't' with 'I'.",
        )

        # The URL for the mistake list API
        self.mistake_list_url = reverse(
            "mistake_list"
        )  # Make sure this matches urls.py

    def test_get_mistake_list_authenticated(self):
        """
        Test that an authenticated user can retrieve their own mistakes.
        """
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token1)
        response = self.client.get(self.mistake_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # User 1 has exactly 2 mistakes
        self.assertEqual(
            (
                len(response.data["results"])
                if "results" in response.data
                else len(response.data)
            ),
            2,
        )

    def test_filter_mistakes_by_category(self):
        """
        Test that the API correctly filters mistakes when a category parameter is provided.
        """
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token1)

        # Request only GRAMMAR mistakes
        response = self.client.get(self.mistake_list_url, {"category": "GRAMMAR"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = (
            response.data["results"] if "results" in response.data else response.data
        )

        # User 1 has only 1 GRAMMAR mistake
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["category"], Mistake.CategoryChoices.GRAMMAR)
        self.assertEqual(results[0]["wrong_text"], "He go")

    def test_data_isolation_between_users(self):
        """
        Test that a user cannot see the mistakes of another user.
        """
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token1)
        response = self.client.get(self.mistake_list_url)

        results = (
            response.data["results"] if "results" in response.data else response.data
        )

        # Extract all mistake IDs returned for user 1
        returned_mistake_ids = [mistake["id"] for mistake in results]

        # Ensure User 2's mistake ID is NOT in User 1's response
        self.assertNotIn(self.mistake3.id, returned_mistake_ids)

    def test_unauthenticated_access_denied(self):
        """
        Test that accessing the mistake list without a token returns 401 Unauthorized.
        """
        # No credentials provided
        response = self.client.get(self.mistake_list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
