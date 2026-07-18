# tracker/utils.py
import math
import random
import urllib.parse
from datetime import datetime

import pytz
import requests
from timezonefinder import TimezoneFinder

tf = TimezoneFinder()
HEADERS = {"User-Agent": "ELLA-App/1.0"}

# Dictionary containing categories and rich vocabulary words for each type of place
VOCABULARY_DATABASE = {
    "university": [
        "lecture",
        "exam",
        "seminar",
        "professor",
        "campus",
        "assignment",
        "scholarship",
        "thesis",
        "dormitory",
        "graduate",
        "syllabus",
        "faculty",
    ],
    "restaurant": [
        "bill",
        "cashier",
        "menu",
        "waiter",
        "cuisine",
        "appetizer",
        "dessert",
        "reservation",
        "chef",
        "recipe",
        "beverage",
        "gratuity",
    ],
    "hospital": [
        "doctor",
        "nurse",
        "patient",
        "prescription",
        "emergency",
        "ward",
        "surgery",
        "pharmacy",
        "diagnosis",
        "clinic",
        "symptom",
        "treatment",
    ],
    "tourism": [
        "souvenir",
        "monument",
        "landmark",
        "guidebook",
        "sightseeing",
        "itinerary",
        "attraction",
        "museum",
        "excursion",
        "heritage",
        "traveler",
        "destination",
    ],
    "general": [
        "explore",
        "discover",
        "journey",
        "landmark",
        "wander",
        "location",
        "neighborhood",
        "scenery",
        "path",
        "map",
        "direction",
        "adventure",
    ],
}


def get_location_by_ip(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=10)
        data = response.json()
        if data.get("status") == "success":
            return {
                "lat": data.get("lat"),
                "lon": data.get("lon"),
                "city": data.get("city"),
                "region": data.get("regionName"),
                "country": data.get("country"),
            }
    except Exception:
        pass
    return None


def reverse_geocode(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        address = response.json().get("address", {})
        return {
            "city": address.get("city")
            or address.get("town")
            or address.get("village", "Unknown"),
            "region": address.get("state", ""),
            "country": address.get("country", ""),
            "place_name": address.get("amenity")
            or address.get("tourism")
            or address.get("road")
            or address.get("city", "Unknown Location"),
        }
    except Exception:
        return {
            "city": "Unknown",
            "region": "Unknown",
            "country": "Unknown",
            "place_name": "Unknown Location",
        }


def get_local_time_offline(lat, lon):
    try:
        timezone_name = tf.timezone_at(lng=lon, lat=lat)
        if timezone_name:
            tz = pytz.timezone(timezone_name)
            local_dt = datetime.now(tz)
            return {"timezone": timezone_name, "local_time": local_dt.isoformat()}
    except Exception:
        pass
    return {
        "timezone": "UTC (Fallback)",
        "local_time": datetime.now(pytz.utc).isoformat(),
    }


def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def get_places_nearby(lat, lon, radius_m=1000):
    categories = {
        "tourism": '[out:json][timeout:25];(node["tourism"](around:{r},{la},{lo});way["tourism"](around:{r},{la},{lo}););out body 50;',
        "amenities": '[out:json][timeout:25];(node["amenity"](around:{r},{la},{lo});way["amenity"](around:{r},{la},{lo}););out body 50;',
    }

    all_places = []
    for category, query_template in categories.items():
        query = query_template.format(r=radius_m, la=lat, lo=lon)
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://overpass-api.de/api/interpreter?data={encoded_query}"
            resp = requests.get(url, headers=HEADERS, timeout=30)
            if resp.status_code == 200:
                for element in resp.json().get("elements", []):
                    tags = element.get("tags", {})
                    name = tags.get("name")
                    if not name:
                        continue

                    elem_lat = element.get("lat") or element.get("center", {}).get(
                        "lat"
                    )
                    elem_lon = element.get("lon") or element.get("center", {}).get(
                        "lon"
                    )

                    if not elem_lat:
                        continue
                    distance = calculate_distance(lat, lon, elem_lat, elem_lon)

                    # Determine the subcategory from tags for vocabulary mapping
                    amenity_type = tags.get("amenity", "")
                    tourism_type = tags.get("tourism", "")

                    place_type = "general"
                    if tourism_type:
                        place_type = "tourism"
                    elif amenity_type in ["university", "college", "school"]:
                        place_type = "university"
                    elif amenity_type in [
                        "restaurant",
                        "cafe",
                        "fast_food",
                        "food_court",
                    ]:
                        place_type = "restaurant"
                    elif amenity_type in ["hospital", "clinic", "doctors"]:
                        place_type = "hospital"

                    all_places.append(
                        {
                            "name": name,
                            "distance_meters": round(distance, 1),
                            "type": place_type,
                        }
                    )
        except Exception:
            continue

    all_places = sorted(all_places, key=lambda x: x["distance_meters"])
    return all_places[:20]


# tracker/utils.py
# (قم بتحديث الجزء الخاص بدالة create_notification_content فقط)


def create_notification_content(place_name, nearby_places, is_static=False):
    if is_static:
        messages = [
            "Are you still here?",
            "Don't you want to go somewhere else?",
            "You have been in this place for a while!",
        ]
        return random.choice(messages)
    else:
        if nearby_places:
            # Get the closest place to determine the category context
            closest_place = nearby_places[0]
            place_type = closest_place.get("type", "general")
            place_category_name = (
                "interesting place" if place_type == "general" else place_type
            )

            # Select the vocabulary words based on the category
            vocab_pool = VOCABULARY_DATABASE.get(
                place_type, VOCABULARY_DATABASE["general"]
            )
            # Safely sample 2 random words from the pool
            selected_words = random.sample(vocab_pool, min(2, len(vocab_pool)))

            # --- MODIFIED HERE: Removed curly braces {} and used single quotes instead ---
            formatted_words = f"'{selected_words[0]}' and '{selected_words[1]}'"

            # Randomly select a prompt style for educational engagement
            prompts = [
                f"You are now in {place_name}! There is a {place_category_name} near you! Can you explain what is {formatted_words}?",
                f"You are now in {place_name}! There is a {place_category_name} near you! Have you heard of {formatted_words}?",
                f"You are now in {place_name}! While exploring this {place_category_name}, do you know the meaning of {formatted_words}?",
            ]
            return random.choice(prompts)
        else:
            # Fallback when no nearby places are discovered, using general vocabulary
            vocab_pool = VOCABULARY_DATABASE["general"]
            selected_words = random.sample(vocab_pool, 2)

            # --- MODIFIED HERE: Removed curly braces {} and used single quotes instead ---
            formatted_words = f"'{selected_words[0]}' and '{selected_words[1]}'"

            return f"You are now in {place_name}! Let's start an adventure. Do you know the words {formatted_words}?"
