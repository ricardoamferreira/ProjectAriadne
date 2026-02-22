import streamlit as st
import folium
import re
import math
import altair as alt
import time
import os
import json
import pandas as pd

from streamlit_folium import st_folium
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from agent import run_ariadne_agent
from router import geocode_address, generate_loop_coords, generate_gpx

st.set_page_config(page_title="Project Ariadne", page_icon="🧶", layout="wide")

# Startup Checks
if not os.getenv("ORS_API_KEY") and "ORS_API_KEY" not in st.secrets:
    st.error(
        "🚨 Critical Error: ORS_API_KEY is missing. Please check your .env file or secrets."
    )
    st.stop()

# Styling
st.markdown(
    """
<style>
    /* Remove default top padding */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    /* Clean interface */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Chat styling */
    .stChatMessage {
        padding: 0.5rem;
    }
</style>
""",
    unsafe_allow_html=True,
)

# State initialization
if "clicks" not in st.session_state:
    st.session_state["clicks"] = []
if "route" not in st.session_state:
    st.session_state["route"] = None
if "route_dist" not in st.session_state:
    st.session_state["route_dist"] = None
if "map_center" not in st.session_state:
    st.session_state["map_center"] = [51.5074, -0.1278]  # Default: London
if "map_zoom" not in st.session_state:
    st.session_state["map_zoom"] = 13
if "force_map_update" not in st.session_state:
    st.session_state["force_map_update"] = False

# Handle Map State (Clicks only — center/zoom not tracked to avoid rerun on every pan)
if "main_map" in st.session_state:
    # Check if we should ignore the map state (after a programmatic update)
    if st.session_state.get("force_map_update", False):
        st.session_state["force_map_update"] = False
    else:
        # Handle Clicks
        if st.session_state["main_map"].get("last_clicked"):
            new_click = [
                st.session_state["main_map"]["last_clicked"]["lat"],
                st.session_state["main_map"]["last_clicked"]["lng"],
            ]
            # Update only if different
            if (
                not st.session_state["clicks"]
                or st.session_state["clicks"][-1] != new_click
            ):
                st.session_state["clicks"] = [new_click]
                st.session_state["map_center"] = new_click
                st.session_state["route"] = None
                st.session_state["route_dist"] = None

# Chat History
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        AIMessage(
            content="Hi! I'm Ariadne, your AI running coach. 🏃‍♂️\n\nTell me where you want to run and how far (e.g. '5km loop north of here')."
        )
    ]


# Sidebar layout
with st.sidebar:
    st.markdown("### 🏃‍♂️ Plan your next run")

    # Location search
    with st.expander("📍 Location Settings", expanded=not st.session_state["clicks"]):
        with st.form("search_form"):
            search_query = st.text_input(
                "Set Start Location:",
                placeholder="e.g. Hyde Park, London",
            )
            search_submitted = st.form_submit_button("Find Place")

        if search_submitted and search_query:
            with st.spinner("Searching..."):
                coords = geocode_address(search_query)
                if coords:
                    st.session_state["clicks"] = [[coords[0], coords[1]]]
                    # Update map view
                    st.session_state["map_center"] = [coords[0], coords[1]]
                    st.session_state["map_zoom"] = 15
                    st.session_state["force_map_update"] = True
                    # Clear route when location changes
                    st.session_state["route"] = None
                    st.session_state["route_dist"] = None
                    st.success(f"Found: {search_query}")
                    st.rerun()
                else:
                    st.error("Location not found.")

    st.divider()

    # Chat Interface
    chat_container = st.container(height=500)

    with chat_container:
        for msg in st.session_state["messages"]:
            if isinstance(msg, HumanMessage):
                st.chat_message("user").write(msg.content)
            elif isinstance(msg, AIMessage):
                if msg.content:
                    st.chat_message("assistant").write(msg.content)
            elif isinstance(msg, ToolMessage):
                with st.chat_message("assistant"):
                    st.info(f"🗺️ {msg.content}")

    # Helper to execute tool calls
    def handle_tool_call(tool_call, start_lat, start_lon):
        if tool_call["name"] == "generate_route":
            args = tool_call["args"]
            dist_km = args.get("distance_km")
            direction = args.get("direction", "north")

            with st.status(
                f"Generating {dist_km}km run {direction}...", expanded=True
            ) as status:
                coords, dist = generate_loop_coords(
                    start_lat, start_lon, dist_km, direction
                )
                if coords:
                    st.session_state["route"] = coords
                    st.session_state["route_dist"] = dist
                    status.update(label="Route Found!", state="complete")
                    return f"Plotting a {dist:.2f}km route."
                else:
                    status.update(label="Failed to generate route", state="error")
                    return "Failed to start route generation."
        return "Unknown tool."

    # Chat Input
    if prompt := st.chat_input("Ask your coach..."):
        # Guardrail: Input Validation
        if not re.match(r"^[a-zA-Z0-9\s,.\-?!'\"éèà%()]+$", prompt):
            st.error(
                "⚠️ Invalid characters detected. Please use letters, numbers, and basic punctuation."
            )
        elif not st.session_state["clicks"]:
            st.error("Please set a start location above first!")
        else:
            # 1. Add user message
            st.session_state["messages"].append(HumanMessage(content=prompt))
            with chat_container:
                st.chat_message("user").write(prompt)

            # 2. Call Agent
            current_lat = st.session_state["clicks"][-1][0]
            current_lon = st.session_state["clicks"][-1][1]

            with st.spinner("Thinking..."):
                response = run_ariadne_agent(
                    st.session_state["messages"], current_lat, current_lon
                )

            # 3. Handle Response
            st.session_state["messages"].append(response)

            # 4. Check for tool calls
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    # Execute tool logic
                    tool_result_text = handle_tool_call(
                        tool_call, current_lat, current_lon
                    )

                    # Create Tool Message
                    tool_msg = ToolMessage(
                        content=tool_result_text, tool_call_id=tool_call["id"]
                    )
                    st.session_state["messages"].append(tool_msg)

                # Rerun once after all tool calls are processed to update map
                st.rerun()

            elif response.content:
                with chat_container:
                    st.chat_message("assistant").write(response.content)

    # GPX Download Button
    if st.session_state["route"]:
        gpx_data = generate_gpx(st.session_state["route"])
        st.download_button(
            label="Download GPX",
            data=gpx_data,
            file_name="ariadne_run.gpx",
            mime="application/gpx+xml",
        )


# Dashboard

# HUD
# HUD
hud_col1, hud_col2 = st.columns([1, 1])
with hud_col1:
    if st.session_state["route_dist"]:
        dist_km = st.session_state["route_dist"]
        dist_mi = dist_km * 0.621371
        st.metric(label="DISTANCE", value=f"{dist_km:.2f} km / {dist_mi:.2f} mi")
    else:
        st.metric(label="DISTANCE", value="0.00 km")

with hud_col2:
    if st.session_state["route"]:
        # Calculate total elevation gain
        total_gain = 0
        route = st.session_state["route"]
        for i in range(1, len(route)):
            diff = route[i][2] - route[i - 1][2]
            if diff > 0:
                total_gain += diff

        gain_ft = total_gain * 3.28084
        st.metric(
            label="ELEVATION GAIN", value=f"{int(total_gain)} m / {int(gain_ft)} ft"
        )
    else:
        st.metric(label="ELEVATION GAIN", value="0 m")

# Map
m = folium.Map(
    location=st.session_state["map_center"],
    zoom_start=st.session_state["map_zoom"],
    tiles="CartoDB voyager",  # Colorful, modern tiles
)
fg = folium.FeatureGroup(name="Dynamic Markers")

# Route plotting
if st.session_state["route"]:
    # Data preparation
    map_path = [[pt[0], pt[1]] for pt in st.session_state["route"]]

    # Green styled path
    folium.PolyLine(map_path, color="#10B981", weight=4, opacity=0.9).add_to(fg)

    # Distance calculation
    def haversine(coord1, coord2):
        R = 6371  # Earth radius in km
        lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
        lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    elevations = [pt[2] for pt in st.session_state["route"]]
    distances = [0]
    total_dist = 0
    for i in range(1, len(st.session_state["route"])):
        dist = haversine(st.session_state["route"][i - 1], st.session_state["route"][i])
        total_dist += dist
        distances.append(total_dist)

    chart_data = pd.DataFrame({"Distance (km)": distances, "Elevation (m)": elevations})

# Start marker
if st.session_state["clicks"]:
    # Popup text
    if st.session_state["route_dist"]:
        popup_txt = f"Loop: {st.session_state['route_dist']:.2f} km"
    else:
        popup_txt = "Start Here"

    folium.Marker(
        st.session_state["clicks"][-1],
        icon=folium.Icon(color="green", icon="play"),
        popup=popup_txt,
        tooltip=popup_txt,
    ).add_to(fg)

# Map interaction
st_folium(
    m,
    feature_group_to_add=fg,
    height=1000,
    width="stretch",
    returned_objects=["last_clicked"],
    key="main_map",
)

# Elevation chart
if st.session_state["route"] and "chart_data" in locals():
    # Chart configuration
    chart = (
        alt.Chart(chart_data)
        .mark_area(color="#10B981", opacity=0.6, line={"color": "#10B981"})
        .encode(
            x=alt.X(
                "Distance (km)",
                axis=alt.Axis(grid=False, labelColor="#9CA3AF", titleColor="#9CA3AF"),
                scale=alt.Scale(domain=[0, distances[-1]]),
            ),
            y=alt.Y(
                "Elevation (m)",
                axis=alt.Axis(grid=False, labelColor="#9CA3AF", titleColor="#9CA3AF"),
            ),
        )
        .configure_view(strokeWidth=0)
        .configure(background="transparent")  # Fix white background
        .properties(height=200)  # Fixed height
    )

    st.altair_chart(chart, width="stretch")
