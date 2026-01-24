import openrouteservice
from dotenv import load_dotenv
import os
import math
import random
import streamlit as st

load_dotenv()


def get_ors_client():
    """Initializes and returns the OpenRouteService client."""
    api_key = os.getenv("ORS_API_KEY")
    # Secrets fallback
    if not api_key:
        try:
            api_key = st.secrets["ORS_API_KEY"]
        except Exception:
            pass

    if not api_key:
        print("Error: ORS_API_KEY not found in environment or secrets.")
        return None

    try:
        return openrouteservice.Client(key=api_key)
    except Exception as e:
        print(f"Error initializing OpenRouteService client: {e}")
        return None


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


def geocode_address(address_text):
    """
    Geocodes an address string to (lat, lon).
    Returns (lat, lon) or None if not found/error.
    """
    client = get_ors_client()
    if not client:
        return None

    try:
        # Geocoding
        result = client.pelias_search(text=address_text)
        if result and "features" in result and len(result["features"]) > 0:
            # Extract coordinates
            lon, lat = result["features"][0]["geometry"]["coordinates"]
            return lat, lon
        return None
    except Exception as e:
        print(f"Geocoding error: {e}")
        return None


def generate_loop_coords(start_lat, start_lon, target_km, direction="north"):
    client = get_ors_client()
    if not client:
        return None, 0

    best_route = None
    best_diff = float("inf")

    # Earth radius
    R = 6378.1

    # Initial efficiency
    current_scale = 0.75

    for attempt in range(3):
        # Target perimeter
        drawn_perimeter = target_km * current_scale
        d = drawn_perimeter / 3.0

        # Direction bearing
        base_angle = get_bearing_from_text(direction)

        # Bearing jitter
        base_angle += random.uniform(-15, 15)

        # Triangle vertices
        # Shape variance
        spread = random.uniform(20, 60)

        angle_b = math.radians(base_angle - spread)
        angle_c = math.radians(base_angle + spread)

        # Vertex B
        lat_b = start_lat + (d / R) * (180 / math.pi) * math.cos(angle_b)
        lon_b = start_lon + (d / R) * (180 / math.pi) * math.sin(angle_b) / math.cos(
            start_lat * math.pi / 180
        )

        # Vertex C
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
                coordinates=coords,
                profile="foot-walking",
                format="geojson",
                elevation="true",
            )
            geometry = routes["features"][0]["geometry"]["coordinates"]
            # Extract points
            route_coords = [[lat, lon, alt] for lon, lat, alt in geometry]
            dist_km = routes["features"][0]["properties"]["summary"]["distance"] / 1000

            diff = abs(dist_km - target_km)

            # Best route tracking
            if diff < best_diff:
                best_diff = diff
                best_route = (route_coords, dist_km)

            # Tolerance check
            if diff / target_km <= 0.05:
                print(
                    f"Attempt {attempt+1}: Distance {dist_km:.2f}km is within tolerance of {target_km}km."
                )
                return route_coords, dist_km

            print(
                f"Attempt {attempt+1}: Distance {dist_km:.2f}km too far from {target_km}km. Adjusting..."
            )

            # Scale correction
            # new_scale = current_scale * (target_km / dist_km)

            ratio = target_km / dist_km
            # Dampening
            current_scale = current_scale * ratio

        except Exception as e:
            print(f"API Error on attempt {attempt+1}: {e}")
            # Error handling
            pass

    if best_route:
        print(f"Returning best route found: {best_route[1]:.2f}km")
        return best_route

    return None, 0
