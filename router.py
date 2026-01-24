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

        # Calculate points B and C for the loop triangle using the specific bearing
        angle_b = math.radians(base_angle - 30)
        angle_c = math.radians(base_angle + 30)

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
                coordinates=coords, profile="foot-walking", format="geojson"
            )
            geometry = routes["features"][0]["geometry"]["coordinates"]
            route_coords = [[lat, lon] for lon, lat in geometry]
            dist_km = routes["features"][0]["properties"]["summary"]["distance"] / 1000

            diff = abs(dist_km - target_km)

            # Keep track of the best one
            if diff < best_diff:
                best_diff = diff
                best_route = (route_coords, dist_km)

            # If within 10% tolerance, we are good
            if diff / target_km <= 0.1:
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
