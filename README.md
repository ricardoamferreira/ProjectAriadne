# 🧶 Project Ariadne (WIP)

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://projectariadne.streamlit.app/)


**Project Ariadne** is an AI-powered running route generator. It uses an LLM agent to interpret natural language requests (e.g., "5km loop north") and generates a running route on a map using OpenRouteService.

> 🚧 **Work In Progress**: This project is under active development. Features and APIs may change.

## Features
- **AI Interface**: Ask for a route in plain English.
- **Dynamic Routing**: Generates loop courses based on distance and direction.
- **Interactive Map**: View your route, starting point, and stats.

## Setup

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install streamlit folium streamlit-folium langchain-openai python-dotenv openrouteservice
    ```
3.  Set up environment variables in a `.env` file:
    ```
    OPENAI_API_KEY=your_openai_key
    ORS_API_KEY=your_openrouteservice_key
    ```

## Usage

Run the Streamlit app:
```bash
streamlit run app.py
```

Click on the map to set a starting point, then ask the AI for a route!
