import openrouteservice
from dotenv import load_dotenv
import os
import math
import random

load_dotenv()
client = openrouteservice.Client(key=os.getenv("ORS_API_KEY"))


def get_bearing_from_text(direction_text):
    """Converts a text direction like 'North' into a numerical bearing."""
    if not direction_text:
        return random.choice([0, 90, 180, 270])

    d = direction_text.lower()
    if "north" in d and "east" in d:
        return 45
    if "north" in d and "west" in d:
        return 315
    if "south" in d and "east" in d:
        return 135
    if "south" in d and "west" in d:
        return 225
    if "north" in d:
        return 0
    if "east" in d:
        return 90
    if "south" in d:
        return 180
    if "west" in d:
        return 270
    return 0  # Default North


def generate_loop_coords(start_lat, start_lon, target_km, direction="north"):
    # Real roads aren't straight lines. To hit our target distance,
    # we aim for a smaller geometric shape, shrinking it by about 25%.
    adjusted_km = target_km * 0.75

    # Earth's radius in km
    R = 6378.1
    # Calculate the side length for our conceptual triangle
    d = adjusted_km / 3.0

    # Convert the user's direction text into a bearing
    base_angle = get_bearing_from_text(direction)

    # Determining the other two points of our triangle relative to the start
    # We want a loop that goes roughly in the 'direction'.
    # A simple triangle: Start -> Point B (base_angle - 30 deg) -> Point C (base_angle + 30 deg) -> Start
    angle_b = math.radians(base_angle - 30)
    angle_c = math.radians(base_angle + 30)

    # Calculating Point B coordinates
    lat_b = start_lat + (d / R) * (180 / math.pi) * math.cos(angle_b)
    lon_b = start_lon + (d / R) * (180 / math.pi) * math.sin(angle_b) / math.cos(
        start_lat * math.pi / 180
    )

    # Calculating Point C coordinates
    lat_c = start_lat + (d / R) * (180 / math.pi) * math.cos(angle_c)
    lon_c = start_lon + (d / R) * (180 / math.pi) * math.sin(angle_c) / math.cos(
        start_lat * math.pi / 180
    )

    coords = [
        (start_lon, start_lat),
        (lon_b, lat_b),
        (lon_c, lat_c),
        (start_lon, start_lat),
    ]

    try:
        routes = client.directions(
            coordinates=coords, profile="foot-walking", format="geojson"
        )
        geometry = routes["features"][0]["geometry"]["coordinates"]
        route_coords = [[lat, lon] for lon, lat in geometry]
        dist_km = routes["features"][0]["properties"]["summary"]["distance"] / 1000

        return route_coords, dist_km

    except Exception as e:
        print(f"API Error: {e}")
        return None, 0
