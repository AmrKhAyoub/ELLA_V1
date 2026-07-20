# chats/views.py
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

# IMPORT THE NEW CENTRALIZED SERVICE
from services.llm_service import generate_ai_response_text

# Ensure you import your models and serializers properly
from .models import Message, Session
from .serializers import MessageSerializer, SessionSerializer


class SessionListCreateAPIView(generics.ListCreateAPIView):
    """
    GET: List all chat sessions for the authenticated user, ordered by newest first.
         Can be filtered by topic (e.g., ?topic=English).
    POST: Create a new chat session.
    """

    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Order by created_at descending (newest to oldest)
        queryset = Session.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )

        # Filter by topic if provided in query parameters
        topic = self.request.query_params.get("topic", None)
        if topic is not None:
            queryset = queryset.filter(topic__icontains=topic)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SessionRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a specific session details.
    PUT/PATCH: Update the session topic.
    DELETE: Delete the session (cascades to delete all related messages).
    """

    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "session_id"  # Matches the URL parameter

    def get_queryset(self):
        # Ensure the user can only access, update, or delete their own sessions
        return Session.objects.filter(user=self.request.user)


class SessionMessagesAPIView(generics.ListAPIView):
    """
    GET: Retrieve all messages for a specific session.
    """

    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        session_id = self.kwargs.get("session_id")
        return Message.objects.filter(
            session__id=session_id, session__user=self.request.user
        ).order_by("timestamp")


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
            session = Session.objects.get(id=session_id, user=request.user)
        except Session.DoesNotExist:
            return Response(
                {"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND
            )

        user_message = Message.objects.create(
            session=session, sender=Message.SenderChoices.USER, content_text=user_text
        )

        recent_messages = Message.objects.filter(session=session).order_by(
            "-timestamp"
        )[:10]

        history = []
        for msg in reversed(recent_messages):
            role = "user" if msg.sender == Message.SenderChoices.USER else "assistant"
            history.append({"role": role, "content": msg.content_text})

        topic_name = getattr(session, "topic", "General English Practice")
        system_prompt = f"You are a helpful and friendly English AI tutor. The current topic is '{topic_name}'. Correct any grammar mistakes gently, keep the conversation engaging, and provide concise answers."

        try:
            ai_text = generate_ai_response_text(
                system_prompt=system_prompt, user_messages=history
            )
        except Exception as e:
            return Response(
                {"error": f"AI service failed: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        ai_message = Message.objects.create(
            session=session, sender=Message.SenderChoices.AI, content_text=ai_text
        )

        return Response(
            {
                "user_message": MessageSerializer(user_message).data,
                "ai_message": MessageSerializer(ai_message).data,
            },
            status=status.HTTP_201_CREATED,
        )
