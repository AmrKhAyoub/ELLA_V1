# assessments/urls.py
from django.urls import path

from .views import (
    AcademicQuestionsView,
    AssessmentSessionView,
    SaveStepProgressView,
    SubmitAssessmentView,
)

urlpatterns = [
    path("session/", AssessmentSessionView.as_view(), name="assessment_session"),
    path("save-step/", SaveStepProgressView.as_view(), name="save_step_progress"),
    path("submit/", SubmitAssessmentView.as_view(), name="submit_assessment"),
    path("questions/", AcademicQuestionsView.as_view(), name="academic_questions"),
]
