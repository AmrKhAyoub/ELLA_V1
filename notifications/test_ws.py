# notifications/tests_ws.py
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from rest_framework_simplejwt.tokens import RefreshToken

from ELLA.asgi import application  # Import your ASGI application

User = get_user_model()


class WebSocketAuthenticationTests(TransactionTestCase):
    def setUp(self):
        """
        Set up a user and generate a valid JWT token for WebSocket testing.
        """
        self.user = User.objects.create_user(
            username="ws_user", email="ws@example.com", password="StrongPassword123!"
        )
        self.valid_token = str(RefreshToken.for_user(self.user).access_token)

    async def test_websocket_connection_with_valid_token(self):
        """
        Test that the custom JWTAuthMiddleware accepts the connection
        when a valid token is provided in the query string.
        """
        # Pass the token in the URL just like the React frontend would do
        ws_url = f"/ws/notifications/?token={self.valid_token}"

        communicator = WebsocketCommunicator(application, ws_url)
        connected, subprotocol = await communicator.connect()

        # The connection should be accepted (True)
        self.assertTrue(connected)

        # Clean up by disconnecting
        await communicator.disconnect()

    async def test_websocket_connection_without_token(self):
        """
        Test that the connection is rejected if no token is provided.
        """
        ws_url = "/ws/notifications/"

        communicator = WebsocketCommunicator(application, ws_url)
        connected, subprotocol = await communicator.connect()

        # The connection should be rejected and closed (False)
        self.assertFalse(connected)

    async def test_websocket_connection_with_invalid_token(self):
        """
        Test that the connection is rejected if a fake or expired token is provided.
        """
        ws_url = "/ws/notifications/?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.fake_payload.fake_signature"

        communicator = WebsocketCommunicator(application, ws_url)
        connected, subprotocol = await communicator.connect()

        # The connection should be rejected (False)
        self.assertFalse(connected)
