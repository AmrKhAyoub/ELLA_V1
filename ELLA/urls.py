# ELLA/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from notifications.views import MarkNotificationsReadAPIView, NotificationListAPIView
from tracker.views import UpdateLocationAPIView

User = get_user_model()


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return Response({"status": "healthy"}, status=200)


urlpatterns = [
    # Admin endpoint
    path("admin/", admin.site.urls),
    # Test Ping endpoint
    path("ping/", health_check, name="health_check"),
    # Authentication endpoints (register, login, refresh)
    path("api/auth/", include("accounts.urls")),
    # Chat API endpoints
    path("api/chats/", include("chats.urls")),
    # Assessments API endpoints
    path("api/assessments/", include("assessments.urls")),
    # Analytics API endpoints
    path("api/analytics/", include("analytics.urls")),
    # API endpoint for updating user location
    path(
        "api/update-location/", UpdateLocationAPIView.as_view(), name="update_location"
    ),
    # Notifications API endpoints
    path(
        "api/notifications/",
        NotificationListAPIView.as_view(),
        name="notification_list",
    ),
    path(
        "api/notifications/mark-read/",
        MarkNotificationsReadAPIView.as_view(),
        name="mark_notifications_read",
    ),
    # API DOCUMENTATION
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

# to serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
