import streamlit as st
import folium
from streamlit_folium import st_folium
from agent import run_ariadne_agent
import json

st.set_page_config(page_title="Project Ariadne", page_icon="🧶", layout="wide")

# Custom CSS
st.markdown(
    """
<style>
    /* Remove default top padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #f9f9f9;
        border-right: 1px solid #e0e0e0;
    }
    
    /* Metric styling */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #e0e0e0;
    }
    
    /* Input field styling */
    .stTextInput > div > div > input {
        border-radius: 8px;
    }
    
    /* Button Styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        width: 100%;
        border: none;
        transition: all 0.2s ease;
    }
    
    /* Primary button enhancements */
    .stButton > button[kind="primary"] {
        box-shadow: 0 4px 14px 0 rgba(0,0,0,0.1);
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
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
    st.header("🧠 Ariadne AI")

    # User input
    user_query = st.text_input("Ask your coach:", placeholder="e.g., '10km loop'")

    # Submit action
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
                        st.session_state["route_dist"] = data["distance"]
                    except:
                        st.error("AI returned invalid data.")
                else:
                    st.warning("AI didn't understand. Try 'Loop 5km'.")

    # Route statistics
    st.divider()
    if st.session_state["route_dist"]:
        st.metric(
            label="🏃‍♂️ Actual Distance",
            value=f"{st.session_state['route_dist']:.2f} km",
        )

    # Reset button
    st.divider()
    if st.button("Reset Map"):
        st.session_state["clicks"] = []
        st.session_state["route"] = None
        st.session_state["route_dist"] = None
        st.rerun()

# Main map configuration
st.title("🧶 Project Ariadne")

center = (
    st.session_state["clicks"][-1] if st.session_state["clicks"] else [51.5074, -0.1278]
)
m = folium.Map(location=center, zoom_start=13, tiles="CartoDB positron")

# Route visualization
if st.session_state["route"]:
    folium.PolyLine(
        st.session_state["route"], color="#FF4B4B", weight=5, opacity=0.8
    ).add_to(m)

# Start point marker
if st.session_state["clicks"]:
    # Dynamic popup text
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

# Map click handling
st_data = st_folium(m, width=1200, height=700)

if st_data["last_clicked"]:
    new_click = [st_data["last_clicked"]["lat"], st_data["last_clicked"]["lng"]]

    # Update on new click
    if not st.session_state["clicks"] or st.session_state["clicks"][-1] != new_click:
        st.session_state["clicks"] = [new_click]
        # Reset stats
        st.session_state["route"] = None
        st.session_state["route_dist"] = None
        st.rerun()
