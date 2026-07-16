# analytics/urls.py
from django.urls import path

from .views import MistakeListAPIView

urlpatterns = [
    path("mistakes/", MistakeListAPIView.as_view(), name="mistake_list"),
]
