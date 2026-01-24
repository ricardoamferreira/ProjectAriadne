import openrouteservice
from dotenv import load_dotenv
import os
import math
import random
import streamlit as st

load_dotenv()


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
    # Initialize Client safely
    api_key = os.getenv("ORS_API_KEY")
    # Fallback to streamlit secrets if not in env (common in Cloud)
    if not api_key:
        try:
            api_key = st.secrets["ORS_API_KEY"]
        except Exception:
            pass

    if not api_key:
        print("Error: ORS_API_KEY not found in environment or secrets.")
        return None, 0

    try:
        client = openrouteservice.Client(key=api_key)
    except Exception as e:
        print(f"Error initializing OpenRouteService client: {e}")
        return None, 0

    best_route = None
    best_diff = float("inf")

    # Earth's radius in km
    R = 6378.1

    # Initial scale factor (approx. 75% efficiency expected)
    current_scale = 0.75

    for attempt in range(3):
        # Calculate side length for triangle based on current scale
        # The logic is: we want total route ~ target_km.
        # We assume route ~ perimeter * efficiency.
        # So we set perimeter = target_km * current_scale.
        # Wait, original logic was: adjusted_km = target_km * 0.75. d = adjusted_km / 3.0.
        # So essentially perimeter_we_draw = target_km * 0.75.

        drawn_perimeter = target_km * current_scale
        d = drawn_perimeter / 3.0

        # Convert direction to bearing
        base_angle = get_bearing_from_text(direction)

        # Add random jitter to the bearing (+/- 15 degrees)
        # This ensures we don't always go exactly North/South/etc
        base_angle += random.uniform(-15, 15)

        # Calculate points B and C for the loop triangle using the specific bearing
        # Randomize the spread (20-60 degrees) to vary the triangle shape
        spread = random.uniform(20, 60)

        angle_b = math.radians(base_angle - spread)
        angle_c = math.radians(base_angle + spread)

        # Point B coordinates
        lat_b = start_lat + (d / R) * (180 / math.pi) * math.cos(angle_b)
        lon_b = start_lon + (d / R) * (180 / math.pi) * math.sin(angle_b) / math.cos(
            start_lat * math.pi / 180
        )

        # Point C coordinates
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
            # Geometry is [lon, lat, alt]
            route_coords = [[lat, lon, alt] for lon, lat, alt in geometry]
            dist_km = routes["features"][0]["properties"]["summary"]["distance"] / 1000

            diff = abs(dist_km - target_km)

            # Keep track of the best one
            if diff < best_diff:
                best_diff = diff
                best_route = (route_coords, dist_km)

            # If within 5% tolerance, we are good
            if diff / target_km <= 0.05:
                print(
                    f"Attempt {attempt+1}: Distance {dist_km:.2f}km is within tolerance of {target_km}km."
                )
                return route_coords, dist_km

            print(
                f"Attempt {attempt+1}: Distance {dist_km:.2f}km too far from {target_km}km. Adjusting..."
            )

            # Correction:
            # We wanted target_km. We got dist_km.
            # dist_km approx proportional to drawn_perimeter.
            # drawn_perimeter = target_km * current_scale.
            # So dist_km approx k * (target_km * current_scale).
            # We want new_dist_km = target_km.
            # new_scale = current_scale * (target_km / dist_km).

            ratio = target_km / dist_km
            # Dampen the correction slightly to avoid oscillation
            current_scale = current_scale * ratio

        except Exception as e:
            print(f"API Error on attempt {attempt+1}: {e}")
            # If we failed to get a route, maybe try reducing scale if it was too big?
            # Or just continue? For now, just continue/break.
            pass

    if best_route:
        print(f"Returning best route found: {best_route[1]:.2f}km")
        return best_route

    return None, 0
