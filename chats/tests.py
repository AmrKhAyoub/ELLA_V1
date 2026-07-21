# chats/tests.py
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from notifications.models import NotificationHistory

from .models import Session

User = get_user_model()


class ChatsAPITests(APITestCase):
    def setUp(self):
        """
        Set up the test environment: create a user, generate token,
        and create an initial chat session.
        """
        self.user = User.objects.create_user(
            username="chat_user",
            email="chat@example.com",
            password="StrongPassword123!",
        )
        self.token = str(RefreshToken.for_user(self.user).access_token)

        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token)

        self.session = Session.objects.create(
            user=self.user, topic="Initial Test Session"
        )

        self.session_list_url = reverse("session_list_create")
        self.session_messages_url = reverse(
            "session_messages", kwargs={"session_id": self.session.id}
        )
        self.send_message_url = reverse(
            "send_message", kwargs={"session_id": self.session.id}
        )

        # 2. ADD THE NEW URL FOR DICTATION
        self.create_dictation_url = reverse("create_dictation_session")

    # ... (Keep your existing tests here: test_create_session_success, test_get_session_list, etc.) ...

    # =========================================================
    # NEW TESTS FOR DICTATION SESSION
    # =========================================================

    @patch("chats.views.generate_ai_response_text")
    def test_create_dictation_session_success(self, mock_generate_text):
        """
        Test that providing a valid notification_id creates a new session
        and initiates a conversation with the AI successfully.
        """
        # Mock the AI's opening response
        mock_generate_text.return_value = (
            "Welcome to the library! Can you explain the word 'book'?"
        )

        # Create a mock notification for the test user
        notification = NotificationHistory.objects.create(
            user=self.user,
            title="Discovery near Library",
            message="You are now near a Library! words: book, quiet, read.",
        )

        # Send request
        response = self.client.post(
            self.create_dictation_url, {"notification_id": notification.id}
        )

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("session", response.data)
        self.assertIn("first_message", response.data)

        # Verify the session was created with the notification title as the topic
        self.assertEqual(response.data["session"]["topic"], "Discovery near Library")

        # Verify the AI message text matches the mock and sender is AI
        self.assertEqual(
            response.data["first_message"]["content_text"],
            "Welcome to the library! Can you explain the word 'book'?",
        )
        self.assertEqual(response.data["first_message"]["sender"], "ai")

        # Verify the AI service was actually called
        mock_generate_text.assert_called_once()

    def test_create_dictation_session_wrong_user(self):
        """
        Test that a user cannot start a dictation session using another user's notification.
        Should return 404 Not Found.
        """
        # Create another user and a notification for them
        other_user = User.objects.create_user(
            username="thief", email="thief@test.com", password="pwd"
        )
        other_notification = NotificationHistory.objects.create(
            user=other_user, title="Private Location", message="Secret words"
        )

        # Attempt to access the other user's notification
        response = self.client.post(
            self.create_dictation_url, {"notification_id": other_notification.id}
        )

        # Should be blocked by get_object_or_404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("chats.views.generate_ai_response_text")
    def test_create_dictation_session_ai_fallback(self, mock_generate_text):
        """
        Test that the system falls back to a default message gracefully
        if the LLM API throws an exception.
        """
        # Force the AI to crash
        mock_generate_text.side_effect = Exception("Groq API Timeout")

        notification = NotificationHistory.objects.create(
            user=self.user, title="Supermarket Visit", message="Words: apple, buy."
        )

        response = self.client.post(
            self.create_dictation_url, {"notification_id": notification.id}
        )

        # It should STILL succeed (201 Created) because we catch the exception
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify it used the fallback default text
        self.assertIn(
            "Hello! I saw you are exploring a new place!",
            response.data["first_message"]["content_text"],
        )
