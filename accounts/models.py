# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q

from .utils import generate_avatar_file


class FieldOfStudy(models.Model):
    """A table representing a field of study for users"""

    name = models.CharField(
        max_length=100, unique=True, verbose_name="Field of Study Name"
    )

    def __str__(self):
        return f"{self.name}"


class CustomUser(AbstractUser):
    """A custom user model that extends the default Django AbstractUser model."""

    class LevelChoices(models.TextChoices):
        A1 = "A1", "Beginner (A1)"
        A2 = "A2", "Elementary (A2)"
        B1 = "B1", "Intermediate (B1)"
        B2 = "B2", "Upper Intermediate (B2)"
        C1 = "C1", "Advanced (C1)"
        C2 = "C2", "Proficient (C2)"

    class GenderChoices(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"

    class StudyLevelChoices(models.TextChoices):
        SCHOOL = "SCH", "School Student"
        BACHELOR = "BAC", "Bachelor Degree"
        MASTER = "MAS", "Master Degree"
        PHD = "PHD", "PhD"
        OTHER = "OTH", "Other"

    # User basic info
    email = models.EmailField(unique=True, verbose_name="Email Address")

    # Allow avatar to be null/blank so users don't have to upload one initially
    avatar = models.ImageField(
        upload_to="avatars/", null=True, blank=True, verbose_name="User Avatar"
    )

    # Educational info
    current_level = models.CharField(
        max_length=2, choices=LevelChoices.choices, default=LevelChoices.A1
    )
    target_level = models.CharField(
        max_length=2, choices=LevelChoices.choices, default=LevelChoices.B2
    )
    learning_goal = models.CharField(max_length=100, null=True, blank=True)

    # Personal info
    gender = models.CharField(
        max_length=1, choices=GenderChoices.choices, null=True, blank=True
    )
    birth_date = models.DateField(null=True, blank=True, verbose_name="Birth Date")

    # Study info
    study_level = models.CharField(
        max_length=3, choices=StudyLevelChoices.choices, null=True, blank=True
    )
    study_field = models.ForeignKey(
        FieldOfStudy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
    )
    # Flag to check if the user has completed the initial onboarding assessment
    has_taken_initial_assessment = models.BooleanField(default=False)
    # Django requires this to know which field is used for authentication
    USERNAME_FIELD = "email"
    # Username is required by AbstractUser by default, we keep it in REQUIRED_FIELDS
    REQUIRED_FIELDS = ["username"]

    class Meta:
        # Constraint to ensure target level is always strictly higher than current level at DB layer
        constraints = [
            models.CheckConstraint(
                condition=Q(target_level__gt=F("current_level")),
                name="check_target_level_must_be_higher",
            )
        ]

    def clean(self):
        super().clean()
        # Validation at the application layer
        if self.current_level and self.target_level:
            if self.current_level >= self.target_level:
                raise ValidationError(
                    {"target_level": "Target level must be higher than current level."}
                )

    def save(self, *args, **kwargs):
        # Checking if the user has no avatar to generate a default one
        if not self.avatar:
            # We use username and email to generate the customized avatar file
            self.avatar = generate_avatar_file(self.username, self.email)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.email
