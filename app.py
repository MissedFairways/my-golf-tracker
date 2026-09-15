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

# --- CUSTOM CSS & NATIVE INJECTION ENGINE ---
# This hides our hidden bridge data inputs from view, keeping the clean look 
# while making sure the buttons are full size for thumb taps.
st.markdown("""
    <style>
        /* Hide the internal coordinate pipeline inputs from the user interface */
        div[data-testid="stTextInput"] {
            display: none !important;
        }
        /* Mobile thumb friendly club selection sizing */
        .stSelectbox div[data-baseweb="select"] {
            font-size: 1.1rem !important;
        }
        html, body, [data-testid="stAppViewContainer"] {
            overflow-x: hidden;
        }
        
        /* Consistent, reliable styling for both golf tracking buttons */
        .golf-btn {
            width: 100%;
            padding: 14px;
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            margin-top: 10px;
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

# --- HIDDEN DATA BRIDGE PIPELINES ---
# These are the safe entry points that JavaScript uses to inject live coordinates
geo_bridge = st.text_input("Internal GPS Bridge", key="gps_bridge_data")

# --- PROCESS INBOUND GEOLOCATION PACKETS ---
if geo_bridge:
    try:
        # Parse data out of string payload: "action,latitude,longitude,timestamp"
        action, lat_s, lon_s, _ = geo_bridge.split(",")
        lat, lon = float(lat_s), float(lon_s)
        
        if action == "start":
            st.session_state.start_coords = (lat, lon)
            st.toast("Start location locked!", icon="🎯")
            
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
                
                # Reset tracking back to base state
                st.session_state.start_coords = None
                st.toast(f"Shot tracked: {distance} Yds!", icon="🚀")
    except Exception as e:
        pass

# --- INLINE INTERACTIVE GOLF BUTTONS ---
# HTML/JS that directly targets the standard DOM input element. 
# This bypasses the iframe sandboxing restrictions on iOS completely.
components.html(f"""
    <div style="display: flex; gap: 15px;">
        <button id="start-btn" class="golf-btn" style="background-color: #2E7D32; width: 50%; padding: 14px; color: white; border: none; border-radius: 10px; font-size: 16px; font-weight: bold;">
            📍 Mark Start Ball
        </button>
        <button id="end-btn" class="golf-btn" style="background-color: #FF4B4B; width: 50%; padding: 14px; color: white; border: none; border-radius: 10px; font-size: 16px; font-weight: bold;">
            ⛳ Mark End Ball
        </button>
    </div>

    <script>
        function captureLocation(actionType) {{
            const btn = actionType === 'start' ? document.getElementById('start-btn') : document.getElementById('end-btn');
            const originalText = btn.innerText;
            btn.innerText = "🛰️ Locating...";
            
            navigator.geolocation.getCurrentPosition(
                (position) => {{
                    // Locate Streamlit's native input element in the page frame hierarchy
                    const inputs = window.parent.document.querySelectorAll('input[type="text"]');
                    if (inputs.length > 0) {{
                        const targetInput = inputs[0];
                        
                        // Construct value string payload
                        const valueStr = actionType + "," + position.coords.latitude + "," + position.coords.longitude + "," + Date.now();
                        
                        // Force update Streamlit's state cleanly
                        targetInput.value = valueStr;
                        targetInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        targetInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    }}
                    btn.innerText = originalText;
                }},
                (error) => {{
                    alert("GPS Error: " + error.message);
                    btn.innerText = originalText;
                }},
                {{ enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }}
            );
        }}

        document.getElementById('start-btn').addEventListener('click', () => captureLocation('start'));
        document.getElementById('end-btn').addEventListener('click', () => captureLocation('end'));
    </script>
""", height=70)

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












