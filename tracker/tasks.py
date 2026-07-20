# tracker/tasks.py
import logging
from datetime import timedelta

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.utils import timezone

from notifications.models import NotificationHistory
from services.llm_service import generate_ai_response_json

from .models import EnrichedPlace, UserCurrentLocation
from .prompts import PLACE_ENRICHMENT_SYSTEM_PROMPT
from .utils import (
    calculate_distance,
    create_notification_content,
    get_location_by_ip,
    get_places_nearby,
    reverse_geocode,
)

logger = logging.getLogger(__name__)
User = get_user_model()


def send_ws_notification(user_id, title, message):
    # Save to Database
    NotificationHistory.objects.create(user_id=user_id, title=title, message=message)
    # Send via WebSocket
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {"type": "send_notification", "title": title, "message": message},
    )


@shared_task
def process_location_task(user_id, lat, lon, ip):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return "User not found"

    # 1. Reverse geocode to get the current city and current place name
    location_info = reverse_geocode(lat, lon)
    current_city = location_info.get("city", "Unknown")
    current_place_name = location_info.get("place_name", "Unknown Location")

    # 2. Get nearby places using Overpass API
    nearby_places = get_places_nearby(lat, lon)

    if not nearby_places:
        return "No nearby places found."

    # 3. Select the closest place to generate vocabulary for
    closest_place = nearby_places[0]
    nearby_place_name = closest_place.get("name")
    place_type = closest_place.get("type", "general")

    # 4. Check if we already enriched this place in the database
    enriched_place, created = EnrichedPlace.objects.get_or_create(
        name=nearby_place_name, city=current_city, defaults={"place_type": place_type}
    )

    # 5. If the place is new or missing AI data, fetch it using YOUR existing LLM service
    if created or not enriched_place.ai_data:
        # Construct the user prompt dynamically based on the location details
        user_prompt = f"Place Name: {nearby_place_name}\nCategory: {place_type}\nCity: {current_city}"

        # Call your existing function from llm_service.py
        ai_generated_json = generate_ai_response_json(
            system_prompt=PLACE_ENRICHMENT_SYSTEM_PROMPT, user_prompt=user_prompt
        )

        # Save the generated JSON to the database (if it is not None)
        if ai_generated_json:
            enriched_place.ai_data = ai_generated_json
            enriched_place.save()

    # 6. Generate the final notification content and extract the description
    notification_text, llm_description = create_notification_content(
        current_place_name=current_place_name,
        nearby_place_name=nearby_place_name,
        ai_data=enriched_place.ai_data,
    )

    # 7. Update the user's current location in the database
    UserCurrentLocation.objects.update_or_create(
        user=user,
        defaults={"latitude": lat, "longitude": lon, "place_name": current_place_name},
    )

    # 8. Dispatch to the notifications app
    # E.g., Notification.objects.create(...)

    print(f"--- NOTIFICATION FOR {user.username} ---")
    print(f"Message: {notification_text}")
    print(f"Place Description: {llm_description}")
    print("----------------------------------------")

    return "Location processed, data enriched, and notification ready."


@shared_task
def check_static_users_task():
    """
    Runs periodically (e.g., every 30 mins) to check if a user
    has been in the exact same place for more than 2 hours.
    """
    two_hours_ago = timezone.now() - timedelta(hours=2)

    # Users who haven't moved in 2 hours and aren't marked static yet
    static_users = UserCurrentLocation.objects.filter(
        arrival_time__lte=two_hours_ago, is_static=False
    )

    for loc in static_users:
        loc.is_static = True
        loc.save()

        msg = create_notification_content(loc.place_name, [], is_static=True)
        send_ws_notification(loc.user_id, "Still around?", msg)

    return f"Checked {static_users.count()} static users"


@shared_task
def enrich_places_data_task(places_list, city_name):
    """
    Background task that takes a list of places, checks if they exist in the DB,
    and if not, calls the Groq LLM to enrich them with educational data.
    """
    for place in places_list:
        name = place.get("name")
        place_type = place.get("type", "general")

        if not name:
            continue

        # 1. Check if we already have this place enriched in our database
        if EnrichedPlace.objects.filter(name=name, city=city_name).exists():
            logger.info(
                f"Place '{name}' in '{city_name}' is already enriched. Skipping."
            )
            continue

        # 2. Prepare the prompt for Groq
        user_prompt = f"Place Name: {name}\nCategory: {place_type}\nCity: {city_name}"

        # 3. Call the centralized LLM Service
        try:
            ai_response = generate_ai_response_json(
                system_prompt=PLACE_ENRICHMENT_SYSTEM_PROMPT, user_prompt=user_prompt
            )

            # 4. Save to Database if response is valid
            if ai_response:
                EnrichedPlace.objects.create(
                    name=name,
                    city=city_name,
                    place_type=place_type,
                    ai_data=ai_response,
                )
                logger.info(f"Successfully enriched place: {name}")
            else:
                logger.warning(f"Received empty or invalid AI response for: {name}")

        except Exception as e:
            logger.error(f"Failed to enrich place '{name}': {str(e)}")
