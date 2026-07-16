# accounts/middleware.py
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from jwt import decode as jwt_decode
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken

User = get_user_model()


@database_sync_to_async
def get_user_from_token(token_key):
    """
    Validates the JWT token and returns the corresponding user.
    """
    try:
        # Validate the token
        UntypedToken(token_key)
        # Decode the token payload to get the user ID
        decoded_data = jwt_decode(token_key, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = decoded_data.get("user_id")
        return User.objects.get(id=user_id)
    except (InvalidToken, TokenError, User.DoesNotExist, Exception):
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom Middleware to authenticate WebSocket connections using SimpleJWT.
    It expects the token in the query string: ws://url/?token=<jwt_token>
    """

    async def __call__(self, scope, receive, send):
        # Parse the query string to extract the token
        query_string = scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)

        token = query_params.get("token")

        if token:
            # If token exists, fetch the user asynchronously
            scope["user"] = await get_user_from_token(token[0])
        else:
            # If no token, set user to AnonymousUser
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)
