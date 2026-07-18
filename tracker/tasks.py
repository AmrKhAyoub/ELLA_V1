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
    tracking_method = "GPS"

    # If no GPS provided, Fallback to IP
    if lat is None or lon is None:
        ip_info = get_location_by_ip(ip)
        if not ip_info:
            return "Failed to get IP location"
        lat, lon = ip_info["lat"], ip_info["lon"]
        tracking_method = "IP"

    lat, lon = float(lat), float(lon)
    geo_info = reverse_geocode(lat, lon)
    place_name = geo_info.get("place_name", "Unknown Area")

    # Extract city name to pass it to the enrichment task
    city_name = geo_info.get("city", "Unknown")

    # Get User's Current Location Record
    location_record, created = UserCurrentLocation.objects.get_or_create(
        user_id=user_id
    )

    # Check if the user has moved significantly (e.g., > 100 meters)
    has_moved = True
    if not created and location_record.latitude and location_record.longitude:
        dist = calculate_distance(
            lat, lon, location_record.latitude, location_record.longitude
        )
        if dist < 100:  # 100 meters radius
            has_moved = False

    if has_moved:
        # Process heavy Overpass API call ONLY if user moved
        nearby_places = get_places_nearby(lat, lon, radius_m=1000)

        # =========================================================
        # NEW AI ENRICHMENT TRIGGER: Run only if places are found
        # =========================================================
        if nearby_places:
            # Slice the top 3 closest places to save LLM API costs
            top_places = nearby_places[:3]
            # Dispatch the sub-task to Celery in the background
            enrich_places_data_task.delay(top_places, city_name)
        # =========================================================

        # Generate Notification Content
        msg = create_notification_content(place_name, nearby_places, is_static=False)
        send_ws_notification(user_id, "Location Update", msg)

        # Update DB Record
        location_record.latitude = lat
        location_record.longitude = lon
        location_record.place_name = place_name
        location_record.tracking_method = tracking_method
        location_record.arrival_time = timezone.now()
        location_record.is_static = False

    # Always update last_updated timestamp so we know the app is active
    location_record.last_updated = timezone.now()
    location_record.save()

    return "Task completed"


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
