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
        .stSelectbox div[data-baseweb="select"] {
            font-size: 1.1rem !important;
        }
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

# --- USER INTERFACE ---
selected_club = st.selectbox("Select Club Used:", CLUB_BAG)

# --- LOW-OVERHEAD MOBILE GEOLOCATION BUTTON COMPONENT ---
def geolocation_button(label, action_type, button_color="#FF4B4B"):
    html_code = f"""
    <button id="geo-btn" style="
        width: 100%; 
        padding: 14px; 
        background-color: {button_color}; 
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
            
            btn.innerText = "🛰️ Locating...";
            btn.style.backgroundColor = "#FFA0A0";
            
            navigator.geolocation.getCurrentPosition(
                (position) => {{
                    // Safely pass data out of the iframe using Streamlit's official API
                    window.parent.postMessage({{
                        type: 'streamlit:setComponentValue',
                        value: {{
                            lat: position.coords.latitude,
                            lon: position.coords.longitude,
                            action: '{action_type}',
                            ts: Date.now()
                        }}
                    }}, '*');
                    btn.innerText = "{label}";
                    btn.style.backgroundColor = "{button_color}";
                }},
                (error) => {{
                    alert('GPS Error: ' + error.message);
                    btn.innerText = "{label}";
                    btn.style.backgroundColor = "{button_color}";
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
    return components.html(html_code, height=60)

# Create layout splits for steps
col1, col2 = st.columns(2)

with col1:
    st.subheader("Step 1")
    # This directly yields data to the variable when tapped
    start_data = geolocation_button("📍 Mark Start Ball", "start", "#2E7D32") 

with col2:
    st.subheader("Step 2")
    end_data = geolocation_button("⛳ Mark End Ball", "end", "#FF4B4B")

# --- STREAMLIT STATE PACKET DISPATCHER ---
# Process data instantly right when the component registers a value click
for data in [start_data, end_data]:
    if data and isinstance(data, dict) and "ts" in data:
        # Check against unique timestamp to prevent reprocessing execution runs
        if "last_processed_ts" not in st.session_state or st.session_state.last_processed_ts != data["ts"]:
            st.session_state.last_processed_ts = data["ts"]
            
            lat, lon, action = data["lat"], data["lon"], data["action"]
            
            if action == "start":
                st.session_state.start_coords = (lat, lon)
                st.toast("Start location locked!", icon="🎯")
                st.rerun()
                
            elif action == "end":
                if st.session_state.start_coords is None:
                    st.error("Please mark a Start position first!")
                else:
                    lat1, lon1 = st.session_state.start_coords
                    distance = calculate_haversine(lat1, lon1, lat, lon)
                    
                    # Append shot to rolling history DataFrame
                    shot_num = len(st.session_state.scorecard) + 1
                    new_shot = pd.DataFrame([{
                        "Shot #": int(shot_num), 
                        "Club Used": selected_club, 
                        "Distance (Yds)": distance
                    }])
                    st.session_state.scorecard = pd.concat([st.session_state.scorecard, new_shot], ignore_index=True)
                    
                    # Reset tracker back to base state
                    st.session_state.start_coords = None
                    st.toast(f"Shot tracked: {distance} Yds!", icon="🚀")
                    st.rerun()

# --- DISPLAY CURRENT TARGETING STATE ---
if st.session_state.start_coords:
    st.info("🔄 Ball is live. Walk to your ball and tap **Mark End Ball** to calculate distance.")
else:
    st.success("✅ Ready for next shot. Tap **Mark Start Ball** at your current location.")

# --- PERSISTENT SCORECARD TABLE (Do Not Change) ---
st.subheader("📋 Round History")
if not st.session_state.scorecard.empty:
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











