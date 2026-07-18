from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .constants import ACADEMIC_QUESTIONS
from .models import AssessmentSession

User = get_user_model()


class AssessmentModelTests(APITestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )

    def test_assessment_session_creation(self):
        """Test if the session is created with correct default values."""
        session = AssessmentSession.objects.create(user=self.user)
        self.assertEqual(session.status, "in_progress")
        self.assertEqual(session.current_step, 1)
        self.assertEqual(session.draft_data, {})
        self.assertIsNone(session.final_score)

    def test_is_expired_property_active_session(self):
        """Test that a newly created session is NOT expired."""
        session = AssessmentSession.objects.create(user=self.user)
        self.assertFalse(session.is_expired)

    def test_is_expired_property_expired_session(self):
        """Test that a session older than 7 days IS expired."""
        session = AssessmentSession.objects.create(user=self.user)
        # We use .update() here to bypass the auto_now=True behavior of updated_at
        AssessmentSession.objects.filter(id=session.id).update(
            updated_at=timezone.now() - timedelta(days=8)
        )
        session.refresh_from_db()
        self.assertTrue(session.is_expired)

    def test_is_expired_property_completed_session(self):
        """Test that a completed session NEVER expires, regardless of date."""
        session = AssessmentSession.objects.create(user=self.user, status="completed")
        AssessmentSession.objects.filter(id=session.id).update(
            updated_at=timezone.now() - timedelta(days=10)
        )
        session.refresh_from_db()
        self.assertFalse(session.is_expired)


class AssessmentAPITests(APITestCase):
    def setUp(self):
        # Create and authenticate a test user
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )
        self.client.force_authenticate(user=self.user)

    # ---------------------------------------------------------
    # 1. Tests for AssessmentSessionView (Start / Resume)
    # ---------------------------------------------------------
    def test_start_new_assessment(self):
        """Test that a new user gets a fresh assessment session."""
        response = self.client.get("/api/assessments/session/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Starting a new assessment.")
        self.assertEqual(response.data["session"]["current_step"], 1)
        self.assertEqual(AssessmentSession.objects.count(), 1)

    def test_resume_active_assessment(self):
        """Test that a user with an active session resumes it without creating a new one."""
        AssessmentSession.objects.create(user=self.user, current_step=3)
        response = self.client.get("/api/assessments/session/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Resuming your ongoing assessment.")
        self.assertEqual(response.data["session"]["current_step"], 3)
        self.assertEqual(AssessmentSession.objects.count(), 1)  # Still only 1 session

    def test_restart_expired_assessment(self):
        """Test that if a session is older than 7 days, it gets deleted and restarted."""
        session = AssessmentSession.objects.create(user=self.user, current_step=5)
        AssessmentSession.objects.filter(id=session.id).update(
            updated_at=timezone.now() - timedelta(days=8)
        )

        response = self.client.get("/api/assessments/session/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"],
            "Your previous session expired. Starting a new assessment.",
        )
        self.assertEqual(response.data["session"]["current_step"], 1)  # Reset to 1

    def test_user_already_completed_assessment(self):
        """Test that a user who completed the assessment cannot start it again via this endpoint."""
        self.user.has_taken_initial_assessment = True
        self.user.save()
        response = self.client.get("/api/assessments/session/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["message"], "You have already completed the assessment."
        )

    # ---------------------------------------------------------
    # 2. Tests for SaveStepProgressView
    # ---------------------------------------------------------
    def test_save_step_success(self):
        """Test saving progress for a specific step successfully."""
        AssessmentSession.objects.create(user=self.user)
        payload = {"step_number": 1, "step_data": {"name": "Leo", "age": "18-24"}}
        response = self.client.post(
            "/api/assessments/save-step/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["current_step"], 2)  # Increments to next step

        # Verify DB update
        session = AssessmentSession.objects.get(user=self.user)
        self.assertIn("step_1", session.draft_data)
        self.assertEqual(session.draft_data["step_1"]["name"], "Leo")

    def test_save_step_validation_error(self):
        """Test saving progress with an invalid step number (e.g., out of 1-7 range)."""
        AssessmentSession.objects.create(user=self.user)
        payload = {"step_number": 8, "step_data": {}}  # Invalid step
        response = self.client.post(
            "/api/assessments/save-step/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_save_step_no_active_session(self):
        """Test attempting to save a step when no active session exists."""
        payload = {"step_number": 2, "step_data": {"skills": "good"}}
        response = self.client.post(
            "/api/assessments/save-step/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_save_step_expired_session(self):
        """Test attempting to save a step to an expired session."""
        session = AssessmentSession.objects.create(user=self.user)
        AssessmentSession.objects.filter(id=session.id).update(
            updated_at=timezone.now() - timedelta(days=8)
        )
        payload = {"step_number": 2, "step_data": {"data": "test"}}
        response = self.client.post(
            "/api/assessments/save-step/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"], "Session expired. Please restart the assessment."
        )

    # ---------------------------------------------------------
    # 3. Tests for SubmitAssessmentView (Grading & Finalizing)
    # ---------------------------------------------------------
    def test_submit_assessment_success(self):
        """Test finalizing the assessment, checking score calculation and flag updates."""
        # Create a session with dummy answers mimicking step_6 (academic test)
        # Using string keys to simulate JSON payload
        academic_answers = {
            "1": 2,
            "2": 2,
            "3": 2,
            "4": 2,
            "5": 3,
            "6": 1,
            "7": 2,
            "8": 1,
            "9": 3,
            "10": 2,
        }
        session = AssessmentSession.objects.create(
            user=self.user, draft_data={"step_6": academic_answers}
        )

        response = self.client.post("/api/assessments/submit/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # In our dummy data, all answers match the CORRECT_ANSWERS_MAP perfectly, so score should be 10.
        self.assertEqual(response.data["final_score"], 10)
        self.assertEqual(response.data["level"], "Advanced (CEFR C1)")

        # Verify DB updates
        session.refresh_from_db()
        self.assertEqual(session.status, "completed")
        self.assertEqual(session.final_score, 10)

        # Verify User model flag
        self.user.refresh_from_db()
        self.assertTrue(self.user.has_taken_initial_assessment)

    def test_submit_assessment_low_score(self):
        """Test finalization grading logic for a beginner score."""
        academic_answers = {"1": 2, "2": 1, "3": 1}  # Only 1 correct answer (ID 1)
        session = AssessmentSession.objects.create(
            user=self.user, draft_data={"step_6": academic_answers}
        )

        response = self.client.post("/api/assessments/submit/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["final_score"], 1)
        self.assertEqual(response.data["level"], "Beginner (CEFR A1 - A2)")

    # ---------------------------------------------------------
    # 4. Tests for AcademicQuestionsView (Security Check)
    # ---------------------------------------------------------
    def test_fetch_academic_questions_hides_answers(self):
        """Test that the fetched questions do not expose the 'correct' or 'explanation' fields."""
        response = self.client.get("/api/assessments/questions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        questions = response.data
        self.assertEqual(len(questions), len(ACADEMIC_QUESTIONS))

        # Ensure answers are stripped
        first_question = questions[0]
        self.assertIn("id", first_question)
        self.assertIn("question", first_question)
        self.assertNotIn("correct", first_question)
        self.assertNotIn("explanation", first_question)

    def test_unauthenticated_access_blocked(self):
        """Ensure endpoints are secure and require authentication."""
        self.client.logout()  # Remove authentication

        response1 = self.client.get("/api/assessments/session/")
        response2 = self.client.post("/api/assessments/save-step/", {})
        response3 = self.client.post("/api/assessments/submit/")
        response4 = self.client.get("/api/assessments/questions/")

        self.assertEqual(response1.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response2.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response3.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response4.status_code, status.HTTP_401_UNAUTHORIZED)
