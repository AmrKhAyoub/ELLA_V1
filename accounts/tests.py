# accounts/tests.py
from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import CustomUser, FieldOfStudy


class AccountsModelTests(TestCase):
    def setUp(self):
        """
        This method runs before EVERY single test.
        We use it to set up any objects we might need multiple times.
        """
        self.study_field = FieldOfStudy.objects.create(name="Computer Science")

    def test_field_of_study_str(self):
        """
        Test that the string representation of FieldOfStudy model returns its name.
        """
        self.assertEqual(str(self.study_field), "Computer Science")

    def test_user_creation_and_avatar_generation(self):
        """
        Test if creating a CustomUser without explicitly providing an avatar
        triggers the save method to automatically generate one.
        """
        user = CustomUser.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
            current_level=CustomUser.LevelChoices.A1,
            target_level=CustomUser.LevelChoices.B2,
        )

        # 1. Test string representation returns email
        self.assertEqual(str(user), "test@example.com")

        # 2. Test that an avatar file was created
        self.assertTrue(user.avatar)

        # 3. Test that the avatar filename contains 'avatar_test' (based on email 'test@')
        self.assertIn("avatar_test", user.avatar.name)

    def test_user_level_validation_success(self):
        """
        Test that the clean() method passes successfully when target_level
        is strictly higher than current_level.
        """
        user = CustomUser(
            username="validuser",
            email="valid@example.com",
            password="testpassword123",
            current_level=CustomUser.LevelChoices.A2,
            target_level=CustomUser.LevelChoices.C1,
        )

        # If this raises any exception, the test will fail.
        # Since A2 < C1, it should pass silently.
        user.clean()

    def test_user_level_validation_fail(self):
        """
        Test that the clean() method raises a ValidationError when target_level
        is lower than or equal to current_level.
        """
        user = CustomUser(
            username="invaliduser",
            email="invalid@example.com",
            password="testpassword123",
            current_level=CustomUser.LevelChoices.C1,
            target_level=CustomUser.LevelChoices.B1,  # B1 is lower than C1!
        )

        # We explicitly tell the test to expect a ValidationError
        with self.assertRaises(ValidationError):
            user.clean()

    def test_user_level_validation_equal_fail(self):
        """
        Test that the clean() method raises a ValidationError when target_level
        is exactly equal to current_level.
        """
        user = CustomUser(
            username="equaluser",
            email="equal@example.com",
            password="testpassword123",
            current_level=CustomUser.LevelChoices.B2,
            target_level=CustomUser.LevelChoices.B2,  # They are equal!
        )

        # We explicitly tell the test to expect a ValidationError
        with self.assertRaises(ValidationError):
            user.clean()
