# ELLA/urls.py
from django.contrib import admin
from django.urls import path

from tracker.views import UpdateLocationAPIView

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "api/update-location/", UpdateLocationAPIView.as_view(), name="update_location"
    ),
]
