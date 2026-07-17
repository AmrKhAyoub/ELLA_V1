# tracker/tasks.py
from datetime import timedelta

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.utils import timezone

from notifications.models import NotificationHistory

from .models import UserCurrentLocation
from .utils import (
    calculate_distance,
    create_notification_content,
    get_location_by_ip,
    get_places_nearby,
    reverse_geocode,
)


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
