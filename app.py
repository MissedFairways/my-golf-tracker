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
        .stButton button {
            width: 100%;
            padding: 0.75rem;
            font-size: 1.1rem !important;
            border-radius: 10px;
        }
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

# --- BULLETPROOF SAFARI GEOLOCATION CONTROLLER ---
# This passes data through the official Streamlit postMessage API instead of trying to force-refresh the parent window.
def native_geo_bridge():
    html_code = """
    <script>
    // System setup to establish safe Streamlit pipeline communications
    function sendToStreamlit(data) {
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: data
        }, '*');
    }

    // Event listener looking for instructions coming out of the rendering loop
    window.addEventListener("message", function(event) {
        if (event.data.type === "streamlit:render") {
            const args = event.data.args;
            if (args.trigger && args.trigger !== window.lastTrigger) {
                window.lastTrigger = args.trigger;
                
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        sendToStreamlit({
                            lat: position.coords.latitude,
                            lon: position.coords.longitude,
                            action: args.action,
                            ts: Date.now()
                        });
                    },
                    (error) => {
                        sendToStreamlit({ error: error.message, ts: Date.now() });
                    },
                    { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
                );
            }
        }
    });
    </script>
    """
    # Hidden engine component that runs smoothly in the background 
    return components.html(html_code, height=0, width=0)

# Render hidden background engine
geo_data = native_geo_bridge()

# --- BACKEND LOGIC DISPATCHER ---
if geo_data and isinstance(geo_data, dict) and "ts" in geo_data:
    # Ensure we are handling a brand new data packet to prevent processing loops
    if "last_processed_ts" not in st.session_state or st.session_state.last_processed_ts != geo_data["ts"]:
        st.session_state.last_processed_ts = geo_data["ts"]
        
        if "error" in geo_data:
            st.error(f"GPS Error: {geo_data['error']}")
        else:
            lat, lon, action = geo_data["lat"], geo_data["lon"], geo_data["action"]
            
            if action == "start":
                st.session_state.start_coords = (lat, lon)
                st.toast("Start location locked!", icon="🎯")
            elif action == "end":
                if st.session_state.start_coords is None:
                    st.error("Please mark a Start position first!")
                else:
                    lat1, lon1 = st.session_state.start_coords
                    distance = calculate_haversine(lat1, lon1, lat, lon)
                    
                    shot_num = len(st.session_state.scorecard) + 1
                    new_shot = pd.DataFrame([{
                        "Shot #": int(shot_num), 
                        "Club Used": st.session_state.get("selected_club_state", "Driver"), 
                        "Distance (Yds)": distance
                    }])
                    st.session_state.scorecard = pd.concat([st.session_state.scorecard, new_shot], ignore_index=True)
                    st.session_state.start_coords = None
                    st.toast(f"Shot tracked: {distance} Yds!", icon="🚀")
        st.rerun()

# --- USER INTERFACE ---
selected_club = st.selectbox("Select Club Used:", CLUB_BAG, key="selected_club_state")

col1, col2 = st.columns(2)
with col1:
    # Native button increments a click counter, telling our hidden engine to fetch GPS
    if st.button("📍 Mark Start Ball"):
        components.html(f"""
            <script>
            window.parent.postMessage({{
                type: 'streamlit:render',
                args: {{ trigger: {Date.now() if 'Date' in locals() else 1}, action: 'start' }}
            }}, '*');
            </script>
        """, height=0, width=0)
        st.toast("Locating start position...", icon="🛰️")

with col2:
    if st.button("⛳ Mark End Ball"):
        components.html(f"""
            <script>
            window.parent.postMessage({{
                type: 'streamlit:render',
                args: {{ trigger: {Date.now() if 'Date' in locals() else 2}, action: 'end' }}
            }}, '*');
            </script>
        """, height=0, width=0)
        st.toast("Locating end position...", icon="🛰️")

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










