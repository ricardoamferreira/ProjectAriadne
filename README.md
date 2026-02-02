# 🧶 Project Ariadne

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://projectariadne.streamlit.app/)

**Project Ariadne** is an intelligent running route generator powered by AI. It uses an LLM agent to interpret natural language requests (e.g., "5km loop north") and generates a running route on a map using OpenRouteService.

> 🚧 **Work In Progress**: This project is under active development. Features and APIs may change.

## Features

- **🏃‍♂️ AI Coach Interface**: Chat with Ariadne to request routes in plain English.
- **🔄 Dynamic Loop Generation**: Automatically creates loop courses based on your desired distance and direction.
- **🗺️ Interactive Map**:
    - **Smart Recentering**: The map automatically focuses on your searched location.
    - **Elevation Profile**: Visualize the elevation gain of your route.
    - **Modern UI**: Clean interface with custom map tiles (CartoDB voyager).
- **📂 GPX Export**: Download your generated routes as GPX files for use with Strava, Garmin, or other fitness apps.
- **🛡️ Secure**: Input sanitization and environment variable management for API keys.

## Setup

### Prerequisites

- Python 3.8+
- [OpenAI API Key](https://platform.openai.com/)
- [OpenRouteService API Key](https://openrouteservice.org/)

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/ricardoamferreira/ProjectAriadne.git
    cd ProjectAriadne
    ```

2.  Create a virtual environment (optional but recommended):
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Mac/Linux
    source .venv/bin/activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4.  Set up environment variables:
    Create a `.env` file in the root directory:
    ```ini
    OPENAI_API_KEY=your_openai_key_here
    ORS_API_KEY=your_openrouteservice_key_here
    ```

## Usage

1.  Run the Streamlit app:
    ```bash
    streamlit run app.py
    ```

2.  Open your browser to the local URL (usually `http://localhost:8501`).

3.  **How to use**:
    - **Set Location**: Use the sidebar to search for a starting location (e.g., "Central Park, NY").
    - **Ask for a Route**: In the chat interface, type your request.
        - *"I want a 5km run."*
        - *"Give me a 10km loop to the east."*
    - **Download**: Once a route is generated, click "Download GPX" to save it.

## Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io/)
- **Map Visualization**: [Folium](https://python-visualization.github.io/folium/) & [Streamlit-Folium](https://github.com/randyzwitch/streamlit-folium)
- **AI/LLM**: [LangChain](https://www.langchain.com/) & [OpenAI](https://openai.com/)
- **Routing**: [OpenRouteService](https://openrouteservice.org/)
- **Data Viz**: [Altair](https://altair-viz.github.io/)

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
