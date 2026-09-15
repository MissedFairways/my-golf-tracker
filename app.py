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

# --- GEOLOCATION CONTROLLER VIA URL QUERY PARAMS ---
# Read location parameters if they were injected into the URL by our buttons
params = st.query_params

if "lat" in params and "lon" in params and "action" in params:
    lat = float(params["lat"])
    lon = float(params["lon"])
    action = params["action"]
    
    # Process actions cleanly on backend script execution pass
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
                "Club Used": params.get("club", "Driver"), 
                "Distance (Yds)": distance
            }])
            st.session_state.scorecard = pd.concat([st.session_state.scorecard, new_shot], ignore_index=True)
            st.session_state.start_coords = None
            st.toast(f"Shot tracked: {distance} Yds!", icon="🚀")
            
    # Instantly wipe query params to prevent reprocessing the same coordinates on user orientation changes
    st.query_params.clear()
    st.rerun()

# --- LOW-OVERHEAD MOBILE GEOLOCATION BUTTON ---
def geolocation_button(label, action_type, club_name=""):
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
                    // Update URL params silently without browser context resets
                    const u = new URL(window.top.location.href);
                    u.searchParams.set('lat', position.coords.latitude);
                    u.searchParams.set('lon', position.coords.longitude);
                    u.searchParams.set('action', '{action_type}');
                    u.searchParams.set('club', '{club_name}');
                    
                    // Replace state tells Streamlit window to look at new params quietly
                    window.top.history.replaceState(null, null, u.toString());
                    window.top.location.reload();
                }},
                (error) => {{
                    alert('Location Error: ' + error.message);
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
    return components.html(html_code, height=55)

# --- USER INTERFACE ---
selected_club = st.selectbox("Select Club Used:", CLUB_BAG)

col1, col2 = st.columns(2)
with col1:
    st.subheader("Step 1")
    geolocation_button("📍 Mark Start Ball", "start", selected_club)

with col2:
    st.subheader("Step 2")
    geolocation_button("⛳ Mark End Ball", "end", selected_club)

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
        st.query_params.clear()
        st.rerun()
else:
    st.write("_No shots tracked yet for this round._")









