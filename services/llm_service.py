# services/llm_service.py
import json
import logging
import os

from groq import Groq

logger = logging.getLogger(__name__)

# Initialize Groq client. Make sure GROQ_API_KEY is in your environment variables or settings
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def generate_ai_response_json(
    system_prompt: str, user_prompt: str, model: str = "llama-3.3-70b-versatile"
) -> dict:
    """
    Calls the Groq API, passing the system and user prompts,
    and strictly returns a parsed JSON dictionary.
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model=model,
            temperature=0.7,
            # Force the model to output valid JSON
            response_format={"type": "json_object"},
        )

        response_content = chat_completion.choices[0].message.content
        return json.loads(response_content)

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON from Groq response.")
        return None
    except Exception as e:
        logger.error(f"Groq API Error: {str(e)}")
        return None


def generate_ai_response_text(
    system_prompt: str, user_messages: list, model: str = "llama-3.3-70b-versatile"
) -> str:
    """
    Calls the Groq API for standard conversational text (used by the chats app).
    Takes a list of message history to maintain conversational context.
    """
    try:
        # Prepare the messages payload
        messages_payload = [{"role": "system", "content": system_prompt}]

        # user_messages should be a list of dicts: [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}]
        messages_payload.extend(user_messages)

        chat_completion = client.chat.completions.create(
            messages=messages_payload,
            model=model,
            temperature=0.7,
        )

        return chat_completion.choices[0].message.content

    except Exception as e:
        logger.error(f"Groq API Error in Text Generation: {str(e)}")
        return "I'm sorry, I am having trouble connecting to my brain right now. Please try again later!"
