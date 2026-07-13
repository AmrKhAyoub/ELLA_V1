# tracker/utils.py
import math
import urllib.parse
from datetime import datetime

import pytz
import requests
from timezonefinder import TimezoneFinder

tf = TimezoneFinder()
HEADERS = {"User-Agent": "ELLA-App/1.0"}


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
    }  # Kept short for brevity, but you can add your other categories here

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

                    all_places.append(
                        {
                            "name": name,
                            "distance_meters": round(distance, 1),
                        }
                    )
        except Exception:
            continue

    all_places = sorted(all_places, key=lambda x: x["distance_meters"])
    return all_places[:20]


def create_notification_content(place_name, nearby_places, is_static=False):
    import random

    if is_static:
        messages = [
            "Are you still here?",
            "Don't you want to go somewhere else?",
            "You have been in this place for a while!",
        ]
        return random.choice(messages)
    else:
        if nearby_places:
            places_names = [p["name"] for p in nearby_places[:3]]
            places_str = ", ".join(places_names)
            return f"You are now in {place_name}! The nearest places are: {places_str}."
        else:
            return f"You are now in {place_name}!"
