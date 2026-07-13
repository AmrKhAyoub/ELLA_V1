# tracker/models.py
from django.contrib.auth.models import User
from django.db import models


class UserCurrentLocation(models.Model):
    # Since there is only one user for now, we link it to Django's built-in User
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="current_location"
    )
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    place_name = models.CharField(max_length=255, null=True, blank=True)

    arrival_time = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    tracking_method = models.CharField(max_length=50, default="GPS")
    is_static = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.place_name}"
