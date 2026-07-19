# ELLA/asgi.py
import os

from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402

import notifications.routing  # noqa: E402
from accounts.middleware import JWTAuthMiddleware  # noqa: E402

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ELLA.settings")

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTAuthMiddleware(
            URLRouter(notifications.routing.websocket_urlpatterns)
        ),
    }
)
