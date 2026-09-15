import streamlit as st
import pandas as pd
import math
import streamlit.components.v1 as components

# --- PAGE CONFIGURATION (Mobile Friendly) ---
st.set_page_config(
    page_title="Golf Drive Tracker",
    page_icon="⛳",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM CSS FOR IPHONE / SAFARI PWA ---
st.markdown("""
    <style>
        /* Optimize button sizes for mobile thumbs */
        .stButton button {
            width: 100%;
            padding: 0.75rem;
            font-size: 1.1rem !important;
            border-radius: 10px;
        }
        /* Make select boxes larger and easier to tap */
        .stSelectbox div[data-baseweb="select"] {
            font-size: 1.1rem !important;
        }
        /* Lock down scaling behaviors */
        html, body, [data-testid="stAppViewContainer"] {
            overflow-x: hidden;
        }
    </style>
""", unsafe_allow_html=True)

# --- HAVERSINE DISTANCE FORMULA (Do Not Change) ---
def calculate_haversine(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return 0.0
    R = 6371000 # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    meters = R * c
    yards = meters * 1.09361
    return round(yards, 1)

# --- SESSION STATE INITIALIZATION ---
if "scorecard" not in st.session_state:
    st.session_state.scorecard = pd.DataFrame(columns=["Shot #", "Club Used", "Distance (Yds)"])

if "start_coords" not in st.session_state:
    st.session_state.start_coords = None

# --- CLUB BAG SELECTION (Do Not Change) ---
CLUB_BAG = [
    "Driver", "Mini-Driver", "3-Wood", 
    "4-Iron", "5-Iron", "6-Iron", "7-Iron", "8-Iron", "9-Iron", 
    "Pitching Wedge", "Gap Wedge", "54° Wedge", "60° Wedge"
]

st.title("⛳ Golf Drive Tracker")

# --- LOW-OVERHEAD MOBILE GEOLOCATION BRIDGE ---
# This component acts purely as a click listener. It passes data upstream without triggering 
# window.parent reloads, bypassing Safari's aggressive caching/flashing loop entirely.
def geolocation_button(label, key):
    html_code = f"""
    <button id="geo-btn" style="
        width: 100%; 
        padding: 12px; 
        background-color: #FF4B4B; 
        color: white; 
        border: none; 
        border-radius: 10px; 
        font-size: 16px; 
        font-weight: bold;
        cursor: pointer;">
        {label}
    </button>

    <script>
        const btn = document.getElementById('geo-btn');
        btn.addEventListener('click', () => {{
            if (!navigator.geolocation) {{
                alert('Geolocation is not supported by your browser.');
                return;
            }}
            
            btn.innerText = "Locating...";
            btn.style.backgroundColor = "#FFA0A0";
            
            navigator.geolocation.getCurrentPosition(
                (position) => {{
                    // Send coordinates securely back to Streamlit app window without reloads
                    window.parent.postMessage({{
                        type: 'streamlit:setComponentValue',
                        value: {{
                            lat: position.coords.latitude,
                            lon: position.coords.longitude,
                            timestamp: position.timestamp
                        }}
                    }}, '*');
                    btn.innerText = "{label}";
                    btn.style.backgroundColor = "#FF4B4B";
                }},
                (error) => {{
                    alert('Error getting location: ' + error.message);
                    btn.innerText = "{label}";
                    btn.style.backgroundColor = "#FF4B4B";
                }},
                {{
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                }}
            );
        }});
    </script>
    """
    # Render component inline with a short height to mimic a native button layout
    return components.html(html_code, height=50)

# --- USER INTERFACE ---

selected_club = st.selectbox("Select Club Used:", CLUB_BAG)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Step 1")
    start_click = geolocation_button("📍 Mark Start Ball", key="start_btn")
    # Capture data passed back from the specific iframe component instance
    if start_click:
        st.session_state.start_coords = (start_click['lat'], start_click['lon'])
        st.toast(f"Start location locked!", icon="🎯")

with col2:
    st.subheader("Step 2")
    end_click = geolocation_button("⛳ Mark End Ball", key="end_btn")
    if end_click:
        if st.session_state.start_coords is None:
            st.error("Please mark a Start position first!")
        else:
            lat2, lon2 = end_click['lat'], end_click['lon']
            lat1, lon1 = st.session_state.start_coords
            
            # Calculate final distance
            distance = calculate_haversine(lat1, lon1, lat2, lon2)
            
            # Append shot to rolling history DataFrame
            shot_num = len(st.session_state.scorecard) + 1
            new_shot = pd.DataFrame([{
                "Shot #": int(shot_num), 
                "Club Used": selected_club, 
                "Distance (Yds)": distance
            }])
            st.session_state.scorecard = pd.concat([st.session_state.scorecard, new_shot], ignore_index=True)
            
            # Reset start state for next shot
            st.session_state.start_coords = None
            st.toast(f"Shot tracked: {distance} Yds!", icon="🚀")

# --- DISPLAY CURRENT TARGETING STATE ---
if st.session_state.start_coords:
    st.info("🔄 Ball is live. Walk to your ball and tap **Mark End Ball** to calculate distance.")
else:
    st.success("✅ Ready for next shot. Tap **Mark Start Ball** at your current location.")

# --- PERSISTENT SCORECARD TABLE (Do Not Change) ---
st.subheader("📋 Round History")
if not st.session_state.scorecard.empty:
    # Render table nicely across phone dimensions
    st.dataframe(
        st.session_state.scorecard.set_index("Shot #"), 
        use_container_width=True
    )
    
    if st.button("🗑️ Reset Round"):
        st.session_state.scorecard = pd.DataFrame(columns=["Shot #", "Club Used", "Distance (Yds)"])
        st.session_state.start_coords = None
        st.rerun()
else:
    st.write("_No shots tracked yet for this round._")








