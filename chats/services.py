# chats/services.py
from django.conf import settings
from groq import Groq

from .models import Message


def get_ai_tutor_response(session, user_message_text):
    """
    This service function initializes the Groq client, fetches the previous
    conversation history from the database to maintain context, sends the new
    message to Groq, and returns the AI's reply.
    """
    # Initialize the Groq client
    client = Groq(api_key=settings.GROQ_API_KEY)

    # 1. System Prompt: Define the AI's persona
    messages_payload = [
        {
            "role": "system",
            # "content": "You are a friendly and helpful English language tutor. Correct mistakes gently.",
            "content": "You are a smart coding assistant.",
        }
    ]

    # 2. History: Fetch previous messages from this session to keep context
    # We only take the last 10 messages to save tokens and prevent large payloads
    previous_messages = session.messages.all().order_by("-timestamp")[:10]

    # We must reverse them because we ordered them descending above,
    # but Groq expects chronological order
    for msg in reversed(previous_messages):
        role = "user" if msg.sender == Message.SenderChoices.USER else "assistant"
        messages_payload.append({"role": role, "content": msg.content_text})

    # 3. Add the current user message
    messages_payload.append({"role": "user", "content": user_message_text})

    # 4. Call Groq API (using LLaMA 3 for example)
    chat_completion = client.chat.completions.create(
        messages=messages_payload,
        model="llama-3.3-70b-versatile",  # requiers VPN
        temperature=0.7,
    )

    # Extract the AI's response text
    ai_response_text = chat_completion.choices[0].message.content
    return ai_response_text
