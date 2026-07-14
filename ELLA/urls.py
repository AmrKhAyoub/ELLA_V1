# ELLA/urls.py
from django.contrib import admin
from django.urls import path

from tracker.views import HelloWorldView, UpdateLocationAPIView

urlpatterns = [
    path("hello/", HelloWorldView.as_view()),
    path("admin/", admin.site.urls),
    path(
        "api/update-location/", UpdateLocationAPIView.as_view(), name="update_location"
    ),
]
