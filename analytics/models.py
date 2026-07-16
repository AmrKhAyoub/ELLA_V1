# analytics/models.py
from django.conf import settings
from django.db import models

from chats.models import Message


class Mistake(models.Model):
    """
    A model to store educational mistakes made by the user during chat sessions,
    categorized for later review and analytics.
    """

    class CategoryChoices(models.TextChoices):
        GRAMMAR = "GRAMMAR", "Grammar"
        SPELLING = "SPELLING", "Spelling"
        VOCABULARY = "VOCABULARY", "Vocabulary"
        PUNCTUATION = "PUNCTUATION", "Punctuation"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mistakes"
    )
    # Linking the mistake directly to the specific user message
    message = models.OneToOneField(
        Message, on_delete=models.CASCADE, related_name="mistake_details"
    )

    wrong_text = models.TextField(help_text="The text that contains the mistake")
    corrected_text = models.TextField(help_text="The corrected text")
    category = models.CharField(max_length=20, choices=CategoryChoices.choices)
    explanation = models.TextField(
        null=True, blank=True, help_text="The educational explanation from the AI tutor"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mistake by {self.user.username} - {self.category}"
