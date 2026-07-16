# ELLA/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from notifications.views import MarkNotificationsReadAPIView, NotificationListAPIView
from tracker.views import HelloWorldView, UpdateLocationAPIView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Hello World endpoint
    path("hello/", HelloWorldView.as_view()),
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
]

# to serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
