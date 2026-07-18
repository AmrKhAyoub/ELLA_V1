# chats/tests.py
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Message, Session

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

        # Authenticate the test client
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token)

        # Create an initial session
        self.session = Session.objects.create(
            user=self.user, topic="Initial Test Session"
        )

        # URLs
        self.session_list_url = reverse("session_list_create")
        self.session_messages_url = reverse(
            "session_messages", kwargs={"session_id": self.session.id}
        )
        self.send_message_url = reverse(
            "send_message", kwargs={"session_id": self.session.id}
        )

    def test_create_session_success(self):
        """
        Test that an authenticated user can create a new chat session.
        """
        data = {"topic": "Grammar Practice"}
        response = self.client.post(self.session_list_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Session.objects.count(), 2)
        self.assertEqual(response.data["topic"], "Grammar Practice")

    def test_get_session_list(self):
        """
        Test that a user can retrieve only their own sessions.
        """
        # Create a session for another user to ensure isolation
        other_user = User.objects.create_user(
            username="other", email="other@test.com", password="pwd"
        )
        Session.objects.create(user=other_user, topic="Other User Session")

        response = self.client.get(self.session_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return 1 session (the one created in setUp)
        self.assertEqual(
            (
                len(response.data["results"])
                if "results" in response.data
                else len(response.data)
            ),
            1,
        )

    # ---------------------------------------------------------
    # UPDATED PATCH: We now intercept 'generate_ai_response_text'
    # from the centralized LLM service.
    # ---------------------------------------------------------
    @patch("chats.views.generate_ai_response_text")
    def test_send_message_success(self, mock_generate_text):
        """
        Test that sending a message saves the user message, calls the NEW AI service,
        and saves the AI response correctly.
        """
        # Configure the fake AI to return this string
        mock_generate_text.return_value = (
            "Hello! I am the mock AI tutor. How can I help?"
        )

        data = {"content_text": "Hi AI, can you teach me English?"}
        response = self.client.post(self.send_message_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify the database has exactly 2 messages (1 user + 1 AI)
        self.assertEqual(Message.objects.filter(session=self.session).count(), 2)

        # Verify the response structure
        self.assertIn("user_message", response.data)
        self.assertIn("ai_message", response.data)

        # Verify the AI message text matches our mock
        self.assertEqual(
            response.data["ai_message"]["content_text"],
            "Hello! I am the mock AI tutor. How can I help?",
        )

        # Verify that our centralized service function was actually called
        mock_generate_text.assert_called_once()

    def test_send_message_missing_content(self):
        """
        Test that sending a blank message returns a 400 error.
        """
        data = {"content_text": ""}
        response = self.client.post(self.send_message_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Message.objects.filter(session=self.session).count(), 0)

    @patch("chats.views.generate_ai_response_text")
    def test_send_message_ai_failure(self, mock_generate_text):
        """
        Test how the system behaves if the Groq API crashes or goes offline.
        """
        # Force the fake AI to raise an exception
        mock_generate_text.side_effect = Exception("Groq API is down!")

        data = {"content_text": "Hi"}
        response = self.client.post(self.send_message_url, data)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn("AI service failed", response.data["error"])
