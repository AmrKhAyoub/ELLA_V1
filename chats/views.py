# chats/views.py
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from notifications.models import NotificationHistory

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


class CreateDictationSessionAPIView(APIView):
    """
    POST: Creates a new dictation chat session triggered by a notification.
    Expects 'notification_id' in the request body.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        notification_id = request.data.get("notification_id")

        if not notification_id:
            return Response(
                {"error": "notification_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 1. Fetch the notification and ensure it belongs to the current user
        notification = get_object_or_404(
            NotificationHistory, id=notification_id, user=request.user
        )

        # 2. Extract context from the notification
        # The notification message already contains the place and the 5 words.
        notification_message = notification.message

        # We will use the notification title as the session topic
        session_topic = notification.title

        # 3. Create a new Session
        session = Session.objects.create(user=request.user, topic=session_topic)

        # 4. Construct the exact Dictation Prompt
        # We instruct the AI to initiate the conversation based on the notification context.
        system_prompt = (
            "You are an engaging, friendly English language tutor. "
            "Your student has just arrived at a specific location and received this notification: "
            f"'{notification_message}'.\n"
            "Your goal is to start a 'dictation and explanation' session. "
            "You must initiate the conversation by welcoming them to the place, mentioning "
            "that you noticed they are near this location, and asking them to explain or define "
            "the vocabulary words mentioned in the notification in English. "
            "Keep your opening message encouraging and no longer than 3 sentences."
        )

        # Since this is the first message, the history is just the system prompt
        # We pass an empty list for user_messages because the AI is starting the chat.
        try:
            ai_opening_text = generate_ai_response_text(
                system_prompt=system_prompt, user_messages=[]
            )
        except Exception as e:
            # If AI fails, we still created the session, but we fallback to a default message
            ai_opening_text = (
                "Hello! I saw you are exploring a new place! "
                "Can you try to explain the words you just received in English?"
            )

        # 5. Save the AI's opening message to the database
        ai_message = Message.objects.create(
            session=session,
            sender=Message.SenderChoices.AI,
            content_text=ai_opening_text,
        )

        # 6. Return the session and the first message to the frontend
        return Response(
            {
                "session": SessionSerializer(session).data,
                "first_message": MessageSerializer(ai_message).data,
            },
            status=status.HTTP_201_CREATED,
        )
