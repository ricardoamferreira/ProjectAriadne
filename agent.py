from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from router import generate_loop_coords
from dotenv import load_dotenv
import json

load_dotenv()


# Adding a 'direction' parameter here so we can guide the route's heading
@tool
def generate_running_loop(
    start_lat: float, start_lon: float, distance_km: float, direction: str = "north"
):
    """
    Generates a running loop.
    args:
        distance_km: The target distance in km.
        direction: The general heading (e.g., 'north', 'south', 'east', 'west').
    """
    coords, dist = generate_loop_coords(start_lat, start_lon, distance_km, direction)
    if coords:
        return json.dumps({"coords": coords, "distance": dist})
    else:
        return "Error: Could not generate route."


llm = ChatOpenAI(model="gpt-4o", temperature=0)
llm_with_tools = llm.bind_tools([generate_running_loop])


def run_ariadne_agent(user_text, current_lat, current_lon):
    # Updating the system prompt to ensure the AI actually looks for a direction
    system_msg = f"""
    You are a running coach. The user is at Lat: {current_lat}, Lon: {current_lon}.
    If the user asks for a run, extract the distance and the direction (North, South, East, West).
    If no direction is given, pick a random one.
    """

    messages = [("system", system_msg), ("user", user_text)]
    ai_msg = llm_with_tools.invoke(messages)

    if ai_msg.tool_calls:
        for tool_call in ai_msg.tool_calls:
            if tool_call["name"] == "generate_running_loop":
                return generate_running_loop.invoke(tool_call["args"])
    return None
