# assessments/views.py
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .constants import ACADEMIC_QUESTIONS, CORRECT_ANSWERS_MAP
from .models import AssessmentSession
from .serializers import AssessmentSessionSerializer, StepUpdateSerializer


class AssessmentSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Starts a new assessment or resumes an existing one.
        Handles the 7-day expiration logic.
        """
        user = request.user

        if user.has_taken_initial_assessment:
            return Response(
                {"message": "You have already completed the assessment."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check for an existing in_progress session
        session = AssessmentSession.objects.filter(
            user=user, status="in_progress"
        ).first()

        if session:
            # Check if it has expired (older than 7 days)
            if session.is_expired:
                session.delete()  # Delete the expired session
                # Create a fresh session
                session = AssessmentSession.objects.create(user=user)
                message = "Your previous session expired. Starting a new assessment."
            else:
                message = "Resuming your ongoing assessment."
        else:
            # No session exists, create a new one
            session = AssessmentSession.objects.create(user=user)
            message = "Starting a new assessment."

        serializer = AssessmentSessionSerializer(session)
        return Response(
            {"message": message, "session": serializer.data}, status=status.HTTP_200_OK
        )


class SaveStepProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Saves the progress of a specific step into the draft_data JSON field.
        """
        serializer = StepUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        step_number = serializer.validated_data["step_number"]
        step_data = serializer.validated_data["step_data"]

        try:
            session = AssessmentSession.objects.get(
                user=request.user, status="in_progress"
            )
        except AssessmentSession.DoesNotExist:
            return Response(
                {"error": "No active assessment session found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if session.is_expired:
            return Response(
                {"error": "Session expired. Please restart the assessment."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update draft_data incrementally
        # Example: draft_data['step_1'] = {"name": "Leo", "age": "18-24"}
        session.draft_data[f"step_{step_number}"] = step_data

        # Move to the next step
        session.current_step = step_number + 1
        session.save()

        return Response(
            {
                "message": f"Step {step_number} saved successfully.",
                "current_step": session.current_step,
            },
            status=status.HTTP_200_OK,
        )


class SubmitAssessmentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Finalizes the assessment (Step 7). Calculates the grade for the academic test
        and updates the User model flag.
        """
        try:
            session = AssessmentSession.objects.get(
                user=request.user, status="in_progress"
            )
        except AssessmentSession.DoesNotExist:
            return Response(
                {"error": "No active assessment session found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Assuming step 6 contains the academic answers: {"1": 2, "2": 2, "3": 3...}
        academic_answers = session.draft_data.get("step_6", {})

        # Calculate Score
        score = 0
        for q_id_str, user_choice in academic_answers.items():
            q_id = int(q_id_str)
            if CORRECT_ANSWERS_MAP.get(q_id) == user_choice:
                score += 1

        # Determine Level (Logic extracted from assesment.py)
        if score <= 3:
            assigned_level = "Beginner (CEFR A1 - A2)"
        elif score <= 7:
            assigned_level = "Intermediate (CEFR B1 - B2)"
        else:
            assigned_level = "Advanced (CEFR C1)"

        # Update Session
        session.final_score = score
        session.assigned_level = assigned_level
        session.status = "completed"
        session.save()

        # Update User Profile flag
        user = request.user
        user.has_taken_initial_assessment = True
        user.save()

        return Response(
            {
                "message": "Assessment completed successfully!",
                "final_score": score,
                "level": assigned_level,
                "roadmap_ready": True,  # Frontend can use this to show the final screen
            },
            status=status.HTTP_200_OK,
        )


class AcademicQuestionsView(APIView):
    """
    Endpoint for the frontend to fetch the 10 academic questions for Step 6.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Remove 'correct' and 'explanation' fields so the frontend can't cheat
        safe_questions = []
        for q in ACADEMIC_QUESTIONS:
            safe_q = {k: v for k, v in q.items() if k not in ["correct", "explanation"]}
            safe_questions.append(safe_q)

        return Response(safe_questions, status=status.HTTP_200_OK)
