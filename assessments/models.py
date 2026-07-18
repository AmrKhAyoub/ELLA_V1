# assessments/models.py
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class AssessmentSession(models.Model):
    STATUS_CHOICES = (
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assessment_sessions",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="in_progress"
    )
    current_step = models.IntegerField(
        default=1
    )  # Tracks which step the user is on (1 to 7)

    # JSONField stores all the answers dynamically (Icebreakers, Interests, Test answers)
    draft_data = models.JSONField(default=dict, blank=True)

    # For grading results
    final_score = models.IntegerField(null=True, blank=True)
    assigned_level = models.CharField(
        max_length=50, null=True, blank=True
    )  # e.g., "Beginner (A1-A2)"

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.status} - Step: {self.current_step}"

    @property
    def is_expired(self):
        """
        Checks if the draft is older than 7 days from its last update.
        Completed assessments never expire.
        """
        if self.status == "completed":
            return False
        expiration_date = self.updated_at + timedelta(days=7)
        return timezone.now() > expiration_date
