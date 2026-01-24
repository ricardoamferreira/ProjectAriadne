import json
from typing import TypedDict, Annotated, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from router import generate_loop_coords

load_dotenv()

# LLM Setup
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


class RunningRequest(BaseModel):
    """Details for a running route request."""

    distance_km: float = Field(description="The target distance in kilometers.")
    direction: str = Field(
        description="The general heading: 'north', 'south', 'east', 'west'. Defaults to 'north' if unspecified."
    )


# Export Function


def run_ariadne_agent(user_text, current_lat, current_lon):
    """
    Extracts intent using LLM, then calls router.
    """
    system_msg = f"""
    You are a running coach assistant.
    The user is located at Lat: {current_lat}, Lon: {current_lon}.
    Extract the desired distance and direction from their request.
    If the user doesn't specify a direction, pick a random one or default to 'north'.
    """

    structured_llm = llm.with_structured_output(RunningRequest)

    try:
        # Extract parameters
        request_data = structured_llm.invoke(
            [SystemMessage(content=system_msg), HumanMessage(content=user_text)]
        )

        if not request_data:
            return None

        # Call router
        coords, dist = generate_loop_coords(
            current_lat, current_lon, request_data.distance_km, request_data.direction
        )

        if coords:
            # Return JSON
            return json.dumps({"coords": coords, "distance": dist})
        else:
            return None

    except Exception as e:
        print(f"Agent Error: {e}")
        return None
