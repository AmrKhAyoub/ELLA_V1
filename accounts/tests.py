# accounts/tests.py
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

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


class AuthenticationAPITests(APITestCase):
    def setUp(self):
        """
        Set up the initial data for the tests.
        We create one active user to test the login and token endpoints.
        """
        self.login_url = reverse("token_obtain_pair")
        self.register_url = reverse("register")
        self.refresh_url = reverse("token_refresh")

        # Create a valid user for login tests
        self.valid_user_data = {
            "username": "existinguser",
            "email": "existing@example.com",
            "password": "StrongPassword123!",
        }
        self.user = CustomUser.objects.create_user(**self.valid_user_data)

    def test_user_registration_success(self):
        """
        Test that a new user can register successfully using the API.
        """
        new_user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "NewStrongPassword123!",
        }

        response = self.client.post(self.register_url, new_user_data)

        # Check if the response status is 201 CREATED
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check if the user is actually saved in the test database
        self.assertTrue(CustomUser.objects.filter(email="newuser@example.com").exists())

        # Ensure the password was hashed, not saved in plain text
        user = CustomUser.objects.get(email="newuser@example.com")
        self.assertNotEqual(user.password, "NewStrongPassword123!")
        self.assertTrue(user.check_password("NewStrongPassword123!"))

    def test_user_registration_failure_missing_data(self):
        """
        Test that registration fails when required data is missing.
        """
        incomplete_data = {
            "username": "baduser"
            # Missing email and password
        }

        response = self.client.post(self.register_url, incomplete_data)

        # Check if the response status is 400 BAD REQUEST
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login_success(self):
        """
        Test that a valid user can log in and receive JWT tokens.
        """
        login_data = {
            "email": self.valid_user_data["email"],
            "password": self.valid_user_data["password"],
        }

        response = self.client.post(self.login_url, login_data)

        # Check if the response status is 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if both access and refresh tokens are in the response
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_user_login_failure_wrong_password(self):
        """
        Test that login fails and returns 401 Unauthorized for bad credentials.
        """
        bad_login_data = {
            "email": self.valid_user_data["email"],
            "password": "WrongPassword!!!",
        }

        response = self.client.post(self.login_url, bad_login_data)

        # Check if the response status is 401 UNAUTHORIZED
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Check that no tokens are returned
        self.assertNotIn("access", response.data)

    def test_token_refresh_success(self):
        """
        Test that a valid refresh token can be used to get a new access token.
        """
        # 1. First, log in to get a valid refresh token
        login_data = {
            "email": self.valid_user_data["email"],
            "password": self.valid_user_data["password"],
        }
        login_response = self.client.post(self.login_url, login_data)
        refresh_token = login_response.data["refresh"]

        # 2. Now, request a new access token using that refresh token
        refresh_data = {"refresh": refresh_token}
        refresh_response = self.client.post(self.refresh_url, refresh_data)

        # Check if the refresh request is successful
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)

        # Ensure a new access token is provided
        self.assertIn("access", refresh_response.data)
