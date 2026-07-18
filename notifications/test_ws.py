# notifications/tests_ws.py
import json

from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase, override_settings
from rest_framework_simplejwt.tokens import RefreshToken

from ELLA.asgi import application

User = get_user_model()

# Force the test runner to use an In-Memory channel layer instead of Redis
# This guarantees that tests won't hang if Redis is down or misconfigured.
TEST_CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}


@override_settings(CHANNEL_LAYERS=TEST_CHANNEL_LAYERS)
class WebSocketAuthenticationAndMessagingTests(TransactionTestCase):
    # This attribute ensures that the database connections are handled cleanly across threads
    serialized_rollback = True

    def setUp(self):
        """
        Set up a real test user and generate a valid JWT token.
        """
        self.user = User.objects.create_user(
            username="ws_test_user",
            email="ws_test@ella.com",
            password="SecurePassword123!",
        )
        self.valid_token = str(RefreshToken.for_user(self.user).access_token)

    async def test_successful_websocket_handshake_with_token(self):
        """
        Scenario 1: Connect to WebSocket passing a valid JWT token in the query parameters.
        Expected: Handshake is successful, connection is accepted.
        """
        ws_url = f"/ws/notifications/?token={self.valid_token}"
        communicator = WebsocketCommunicator(application, ws_url)

        # We increase the timeout to 10 seconds to allow Windows environments
        # ample time to warm up the ASGI context.
        connected, _ = await communicator.connect(timeout=10)
        self.assertTrue(connected)

        await communicator.disconnect()

    async def test_rejected_websocket_handshake_missing_token(self):
        """
        Scenario 2: Try to establish a connection with no token in the URL query parameters.
        Expected: Connection is rejected immediately.
        """
        ws_url = "/ws/notifications/"
        communicator = WebsocketCommunicator(application, ws_url)

        connected, _ = await communicator.connect(timeout=10)
        self.assertFalse(connected)

    async def test_rejected_websocket_handshake_invalid_token(self):
        """
        Scenario 3: Try to connect passing a tampered or expired JWT token.
        Expected: Connection is rejected.
        """
        ws_url = "/ws/notifications/?token=invalid.token.string"
        communicator = WebsocketCommunicator(application, ws_url)

        connected, _ = await communicator.connect(timeout=10)
        self.assertFalse(connected)

    async def test_live_notification_reception_over_websocket(self):
        """
        Scenario 4: Establish a valid connection, then simulate pushing a notification
        payload directly to the user's specific Channel Group.
        Expected: The WebSocket client receives the exact JSON structure.
        """
        ws_url = f"/ws/notifications/?token={self.valid_token}"
        communicator = WebsocketCommunicator(application, ws_url)

        connected, _ = await communicator.connect(timeout=10)
        self.assertTrue(connected)

        # Trigger a direct push through the channel layer
        channel_layer = get_channel_layer()
        user_group_name = f"user_{self.user.id}"

        payload = {
            "type": "send_notification",
            "title": "Celery Alert",
            "message": "Your background task has finished successfully!",
        }

        await channel_layer.group_send(user_group_name, payload)

        # Check if the communicator client received the payload
        response_text = await communicator.receive_from(timeout=10)
        response_data = json.loads(response_text)

        self.assertEqual(response_data["title"], "Celery Alert")
        self.assertEqual(
            response_data["message"], "Your background task has finished successfully!"
        )

        await communicator.disconnect()
