import streamlit as st
import folium
from streamlit_folium import st_folium
from agent import run_ariadne_agent
import json
import altair as alt

st.set_page_config(page_title="Project Ariadne", page_icon="🧶", layout="wide")

# Custom CSS
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
    
    /* Global Dark Theme overrides if needed */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #262730;
        border-right: 1px solid #464B5C;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #FAFAFA !important;
    }
    
    /* Metric styling for HUD */
    [data-testid="stMetric"] {
        background-color: #1F2937; /* Dark gray/blue */
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #374151;
        color: #FF4B4B; /* Red text */
    }
    [data-testid="stMetricLabel"] {
        color: #9CA3AF;
        font-weight: 600;
    }
    [data-testid="stMetricValue"] {
        color: #FF4B4B;
    }
    
    /* Input field styling */
    .stTextInput > div > div > input {
        border-radius: 8px;
        background-color: #374151;
        color: white;
        border: 1px solid #4B5563;
    }
    .stTextInput > div > div > input::placeholder {
        color: #9CA3AF !important;
        opacity: 1;
    }
    
    /* Button Styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        width: 100%;
        border: none;
        transition: all 0.2s ease;
        background-color: #374151;
        color: white;
    }
    
    /* Primary button enhancements */
    .stButton > button[kind="primary"] {
        background-color: #FF4B4B;
        color: #FFFFFF;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.4);
        background-color: #FF2B2B; 
        color: #FFFFFF;
    }
    
    /* Hide default menu and footer for cleaner app feel */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)

# Initialize session state
if "clicks" not in st.session_state:
    st.session_state["clicks"] = []
if "route" not in st.session_state:
    st.session_state["route"] = None
# Persist distance for reload
if "route_dist" not in st.session_state:
    st.session_state["route_dist"] = None

# Sidebar
with st.sidebar:
    st.markdown("### 🏃‍♂️ Plan your next run")

    # User input
    with st.form("input_form"):
        user_query = st.text_input("Ask your coach:", placeholder="e.g., '10km loop'")
        submitted = st.form_submit_button("Submit Request", type="primary")

    # Submit action
    if submitted:
        if not st.session_state["clicks"]:
            st.error("⚠️ Click the map to set a Start Point first.")
        elif not user_query:
            st.warning("Please type a distance.")
        else:
            start_lat = st.session_state["clicks"][-1][0]
            start_lon = st.session_state["clicks"][-1][1]

            with st.spinner("Calculating route..."):
                result = run_ariadne_agent(user_query, start_lat, start_lon)

                if result:
                    try:
                        data = json.loads(result)
                        st.session_state["route"] = data["coords"]
                        st.session_state["route_dist"] = data["distance"]
                    except:
                        st.error("AI returned invalid data.")
                else:
                    st.warning("AI didn't understand. Try 'Loop 5km'.")

    # Reset button
    st.divider()
    if st.button("Reset Map"):
        st.session_state["clicks"] = []
        st.session_state["route"] = None
        st.session_state["route_dist"] = None
        st.rerun()

# --- Main Dashboard Area ---

# 1. HUD Row (Distance Metric)
hud_col1, hud_col2, hud_col3 = st.columns([1, 1, 2])
with hud_col1:
    if st.session_state["route_dist"]:
        dist_km = st.session_state["route_dist"]
        dist_mi = dist_km * 0.621371
        st.metric(label="DISTANCE", value=f"{dist_km:.2f} km / {dist_mi:.2f} mi")
    else:
        st.metric(label="DISTANCE", value="0.00 km")

# 2. Main Map
# Center logic
center = (
    st.session_state["clicks"][-1] if st.session_state["clicks"] else [51.5074, -0.1278]
)

m = folium.Map(
    location=center,
    zoom_start=13,
    tiles="CartoDB dark_matter",  # Dark mode tiles
)

# Route visualization
if st.session_state["route"]:
    # Split data for Map (lat, lon) and Elevation (dist, alt)
    map_path = [[pt[0], pt[1]] for pt in st.session_state["route"]]

    # Red styled path
    folium.PolyLine(map_path, color="#FF4B4B", weight=4, opacity=0.9).add_to(m)

    # Calculate cumulative distance for elevation plot
    import math

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

    import pandas as pd

    chart_data = pd.DataFrame({"Distance (km)": distances, "Elevation (m)": elevations})

# Start point marker
if st.session_state["clicks"]:
    # Dynamic popup text
    if st.session_state["route_dist"]:
        popup_txt = f"Loop: {st.session_state['route_dist']:.2f} km"
    else:
        popup_txt = "Start Here"

    folium.Marker(
        st.session_state["clicks"][-1],
        icon=folium.Icon(color="red", icon="play"),
        popup=popup_txt,
        tooltip=popup_txt,
    ).add_to(m)

# Map click handling - Full Screen Dark
# Use returned_objects to preventing reloading on zoom/pan
# use_container_width=True fills the available space
st_data = st_folium(
    m, height=750, use_container_width=True, returned_objects=["last_clicked"]
)

# Render Elevation Chart below map (Red Style)
if st.session_state["route"] and "chart_data" in locals():
    # Create Altair chart to control background and interactivity
    chart = (
        alt.Chart(chart_data)
        .mark_area(color="#FF4B4B", opacity=0.8, line={"color": "#FF4B4B"})
        .encode(
            x=alt.X(
                "Distance (km)",
                axis=alt.Axis(grid=False, labelColor="#9CA3AF", titleColor="#9CA3AF"),
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

if st_data["last_clicked"]:
    new_click = [st_data["last_clicked"]["lat"], st_data["last_clicked"]["lng"]]

    # Update on new click
    if not st.session_state["clicks"] or st.session_state["clicks"][-1] != new_click:
        st.session_state["clicks"] = [new_click]
        # Reset stats
        st.session_state["route"] = None
        st.session_state["route_dist"] = None
        st.rerun()
