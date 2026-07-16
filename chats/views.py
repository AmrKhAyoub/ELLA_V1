# chats/views.py
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Message, Session
from .serializers import MessageSerializer, SessionSerializer
from .services import get_ai_tutor_response


class SessionListCreateAPIView(generics.ListCreateAPIView):
    """
    GET: List all chat sessions for the logged-in user.
    POST: Create a new chat session.
    """

    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Session.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        # Automatically assign the logged-in user to the new session
        serializer.save(user=self.request.user)


class SessionMessagesAPIView(generics.ListAPIView):
    """
    GET: Retrieve all messages for a specific session.
    """

    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        session_id = self.kwargs["session_id"]
        return Message.objects.filter(
            session__id=session_id, session__user=self.request.user
        )


class SendMessageAPIView(APIView):
    """
    POST: Receive user message, save it, get AI response, and save the AI response.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        user_text = request.data.get("content_text")

        if not user_text:
            return Response(
                {"error": "Content text is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Ensure the session belongs to the user
            session = Session.objects.get(id=session_id, user=request.user)
        except Session.DoesNotExist:
            return Response(
                {"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # 1. Save User Message
        user_message = Message.objects.create(
            session=session, sender=Message.SenderChoices.USER, content_text=user_text
        )

        # 2. Get AI Response via the service layer
        try:
            ai_text = get_ai_tutor_response(session, user_text)
        except Exception as e:
            return Response(
                {"error": f"AI service failed: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # 3. Save AI Message
        ai_message = Message.objects.create(
            session=session, sender=Message.SenderChoices.AI, content_text=ai_text
        )

        # Return both messages to the frontend so it can update the UI immediately
        return Response(
            {
                "user_message": MessageSerializer(user_message).data,
                "ai_message": MessageSerializer(ai_message).data,
            },
            status=status.HTTP_201_CREATED,
        )
