import streamlit as st
import folium
from streamlit_folium import st_folium
from agent import run_ariadne_agent
import json

st.set_page_config(page_title="Project Ariadne", page_icon="🧶", layout="wide")

# Setting up session state variables
if "clicks" not in st.session_state:
    st.session_state["clicks"] = []
if "route" not in st.session_state:
    st.session_state["route"] = None
# We need to persist the distance so it doesn't get lost on reload
if "route_dist" not in st.session_state:
    st.session_state["route_dist"] = None

# Sidebar: AI controls and statistics
with st.sidebar:
    st.header("🧠 Ariadne AI")

    # Capture the user's request
    user_query = st.text_input("Ask your coach:", placeholder="e.g., '10km loop'")

    # Handle the submit action
    if st.button("Submit Request", type="primary"):
        if not st.session_state["clicks"]:
            st.error("⚠️ Click the map to set a Start Point first.")
        elif not user_query:
            st.warning("Please type a distance.")
        else:
            start_lat = st.session_state["clicks"][-1][0]
            start_lon = st.session_state["clicks"][-1][1]

            with st.spinner("🤖 AI is calculating..."):
                result = run_ariadne_agent(user_query, start_lat, start_lon)

                if result:
                    try:
                        data = json.loads(result)
                        st.session_state["route"] = data["coords"]
                        st.session_state["route_dist"] = data["distance"]  # Save it
                    except:
                        st.error("AI returned invalid data.")
                else:
                    st.warning("AI didn't understand. Try 'Loop 5km'.")

    # Displaying the route statistics
    st.divider()
    if st.session_state["route_dist"]:
        st.metric(
            label="🏃‍♂️ Actual Distance",
            value=f"{st.session_state['route_dist']:.2f} km",
        )

    # Reset button to clear the map
    st.divider()
    if st.button("Reset Map"):
        st.session_state["clicks"] = []
        st.session_state["route"] = None
        st.session_state["route_dist"] = None
        st.rerun()

# Configuring the main map display
st.title("🧶 Project Ariadne")

center = (
    st.session_state["clicks"][-1] if st.session_state["clicks"] else [51.5074, -0.1278]
)
m = folium.Map(location=center, zoom_start=13)

# Visualizing the calculated route
if st.session_state["route"]:
    folium.PolyLine(
        st.session_state["route"], color="#FF4B4B", weight=5, opacity=0.8
    ).add_to(m)

# Marking the starting point
if st.session_state["clicks"]:
    # Create a dynamic popup text
    if st.session_state["route_dist"]:
        popup_txt = f"Loop: {st.session_state['route_dist']:.2f} km"
    else:
        popup_txt = "Start Here"

    folium.Marker(
        st.session_state["clicks"][-1],
        icon=folium.Icon(color="green", icon="play"),
        popup=popup_txt,
        tooltip=popup_txt,
    ).add_to(m)

# Capturing map clicks to set the start point
st_data = st_folium(m, width=1200, height=700)

if st_data["last_clicked"]:
    new_click = [st_data["last_clicked"]["lat"], st_data["last_clicked"]["lng"]]

    # Only update if the click is different from the last one
    if not st.session_state["clicks"] or st.session_state["clicks"][-1] != new_click:
        st.session_state["clicks"] = [new_click]
        # Clear old stats since we have a new start point
        st.session_state["route"] = None
        st.session_state["route_dist"] = None
        st.rerun()
