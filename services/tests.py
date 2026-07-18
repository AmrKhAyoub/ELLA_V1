from unittest.mock import MagicMock, patch

from django.test import TestCase

from services.llm_service import generate_ai_response_json, generate_ai_response_text


class LLMServiceTests(TestCase):
    @patch("services.llm_service.client.chat.completions.create")
    def test_generate_ai_response_json_success(self, mock_create):
        """Test successful JSON parsing from Groq response."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = (
            '{"description": "A nice place", "atmosphere": "Quiet"}'
        )
        mock_create.return_value = mock_response

        response = generate_ai_response_json("System prompt", "User prompt")

        self.assertIsInstance(response, dict)
        self.assertEqual(response["description"], "A nice place")
        self.assertTrue(mock_create.called)

    @patch("services.llm_service.client.chat.completions.create")
    def test_generate_ai_response_json_failure(self, mock_create):
        """Test failure when Groq returns invalid JSON."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "This is not a JSON"
        mock_create.return_value = mock_response

        response = generate_ai_response_json("System prompt", "User prompt")
        self.assertIsNone(response)

    @patch("services.llm_service.client.chat.completions.create")
    def test_generate_ai_response_text_success(self, mock_create):
        """Test successful text response generation."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Hello! I am your AI tutor."
        mock_create.return_value = mock_response

        messages = [{"role": "user", "content": "Hi"}]
        response = generate_ai_response_text("System prompt", messages)

        self.assertEqual(response, "Hello! I am your AI tutor.")
