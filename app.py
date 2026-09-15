import streamlit as st
from streamlit_js_eval import get_geolocation
import math
import pandas as pd
import time

# 1. App Styling and Titles
st.set_page_config(page_title="GEN X GOLF", page_icon="⛳", layout="centered")

# --- CENTERED TWO-LINE HIGH-CONTRAST TITLE ---
st.markdown("""
    <h1 style='text-align: center; font-size: 2.8rem; font-weight: 900; color: #000000; line-height: 1.2; margin-bottom: 25px;'>
        GEN X GOLF<br>
        <span style='font-size: 2.2rem; font-weight: 800; color: #2E7D32;'>DISTANCE TRACKER</span>
    </h1>
""", unsafe_allow_html=True)

# Create a master trigger key to force browser hardware updates
if 'gps_trigger' not in st.session_state:
    st.session_state.gps_trigger = 0

# --- SETUP PERSISTENT MEMORY ---
if 'tee_lat' not in st.session_state:
    st.session_state.tee_lat = None
    st.session_state.tee_lon = None
if 'shot_history' not in st.session_state:
    st.session_state.shot_history = []
if 'waiting_for_end_gps' not in st.session_state:
    st.session_state.waiting_for_end_gps = False
if 'saved_club' not in st.session_state:
    st.session_state.saved_club = "Driver"
if 'last_calculated_distance' not in st.session_state:
    st.session_state.last_calculated_distance = None

# --- SUNLIGHT HIGH-CONTRAST UI & DISTANCE DISPLAY CONFIGURATION ---
# --- SUNLIGHT HIGH-CONTRAST UI & DISTANCE DISPLAY CONFIGURATION ---
st.markdown("""
    <style>
        /* Global Canvas Overrides for Direct Sunlight Viewability */
        html, body, [data-testid="stAppViewContainer"] {
            background-color: #FFFFFF !important;
            color: #000000 !important;
        }

        /* Club Selector Box Sunlight Enhancements */
        div[data-testid="stSelectbox"] label p {
            font-size: 22px !important;
            font-weight: 800 !important;
            color: #111111 !important;
        }
        div[data-testid="stSelectbox"] div[data-baseweb="select"] {
            border: 3px solid #000000 !important;
            border-radius: 8px !important;
            background-color: #FFFFFF !important;
        }
        div[data-testid="stSelectbox"] span {
            font-size: 22px !important;
            font-weight: 700 !important;
            color: #000000 !important;
        }

        /* NUKES ALL STREAMLIT DEFAULTS: Forces every single button to be green with black text */
        button {
            background-color: #2E7D32 !important; /* Premium Medium Golf Course Green */
            color: #000000 !important;            /* Solid crisp black font */
            font-size: 22px !important;
            font-weight: 900 !important;
            letter-spacing: 0.5px !important;
            text-transform: uppercase !important;
            padding: 18px 10px !important;
            border-radius: 12px !important;
            border: 3px solid #000000 !important;
            box-shadow: 6px 6px 0px 0px #000000 !important;
            transition: transform 0.05s ease !important;
        }

        /* Ensure disabled buttons keep their structure but soften contrast */
        button:disabled {
            background-color: #A5D6A7 !important; /* Lighter muted green when locked */
            color: #555555 !important;
            opacity: 0.8 !important;
            cursor: not-allowed !important;
        }
        
        /* Interactive iOS Safari Tap Action Feedback */
        button:active {
            transform: translate(3px, 3px) !important;
            box-shadow: 3px 3px 0px 0px #000000 !important;
        }

        /* Centered Performance Panel Display */
        .distance-display-box {
            background-color: #FFFFFF;
            border: 4px solid #000000;
            border-radius: 16px;
            padding: 20px;
            text-align: center;
            box-shadow: 6px 6px 0px 0px #2E7D32;
            margin-top: 20px;
            margin-bottom: 20px;
        }
        .distance-label {
            font-size: 1.2rem;
            color: #111111;
            text-transform: uppercase;
            font-weight: 900;
            margin-bottom: 4px;
        }
        .distance-number {
            font-size: 3.5rem;
            color: #2E7D32;
            font-weight: 900;
            line-height: 1.0;
        }
    </style>
""", unsafe_allow_html=True)

# 2. Wake up the phone's live GPS coordinates using the correct component parameter
location = get_geolocation(
    component_key=f"gps_tracker_{st.session_state.gps_trigger}")
# Continues directly from the location check block
if location is None:
    st.info("🔄 Connecting to iPhone GPS satellites... Please allow location access if prompted.")
elif 'coords' not in location:
    st.warning("⚠️ Waiting for location permissions. Please make sure Safari is allowed to use your GPS.")
else:
    current_lat = location['coords']['latitude']
    current_lon = location['coords']['longitude']

    # --- MID-RUN CALCULATION INTERCEPTOR ---
    if st.session_state.waiting_for_end_gps:
        if current_lat != st.session_state.tee_lat or current_lon != st.session_state.tee_lon:
            lat1, lon1 = math.radians(st.session_state.tee_lat), math.radians(st.session_state.tee_lon)
            lat2, lon2 = math.radians(current_lat), math.radians(current_lon)
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            
            # Calibrated Earth radius multiplier for Yards
            distance_in_yards = round(6975175 * c)
            
            # Track it in persistent state so the main interface can render it safely
            st.session_state.last_calculated_distance = distance_in_yards
            
            # Save the shot data to your history memory list
            shot_number = len(st.session_state.shot_history) + 1
            new_shot = {
                "Shot #": shot_number,
                "Club Used": st.session_state.saved_club,
                "Distance": f"{distance_in_yards} Yards"
            }
            st.session_state.shot_history.append(new_shot)
            
            # Clear targeting state so you can hit your next shot smoothly
            st.session_state.tee_lat = None
            st.session_state.tee_lon = None
            st.session_state.waiting_for_end_gps = False
            st.toast(f"🚀 Shot tracked: {distance_in_yards} Yards!", icon="🏌️‍♂️")
            st.rerun()

    # 3. Setup Your Shot Layout
    st.subheader("1. Setup Your Shot")
    club_options = [
        "Driver", "Mini-Driver", "3-Wood", "4-Iron", "5-Iron", 
        "6-Iron", "7-Iron", "8-Iron", "9-Iron", "Pitching Wedge", 
        "Gap Wedge", "54° Wedge", "60° Wedge"
    ]
    selected_club = st.selectbox(
        "Which club are you hitting?", 
        options=club_options, 
        index=club_options.index(st.session_state.saved_club) if st.session_state.saved_club in club_options else 0
    )
    st.session_state.saved_club = selected_club

    st.divider()

    # 4. Action Buttons
    st.subheader("2. Track Your Distance")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="green-action-btn">', unsafe_allow_html=True)
        if st.button("🔴 Click 1: Just Teed Off", use_container_width=True, disabled=st.session_state.waiting_for_end_gps):
            st.session_state.tee_lat = current_lat
            st.session_state.tee_lon = current_lon
            st.session_state.gps_trigger += 1  
            # Clear out old display value once a fresh tracking run begins
            st.session_state.last_calculated_distance = None
            st.toast(f"🎯 Tee location saved for your {selected_club}!", icon="📍")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="blue-action-btn">', unsafe_allow_html=True)
        if st.button("⚪ Click 2: At My Ball", use_container_width=True, disabled=(st.session_state.tee_lat is None or st.session_state.waiting_for_end_gps)):
            # Force structural delay pass allowing PWA to cycle and secure accurate satellite lock
            with st.spinner("Locking Satellite Array..."):
                time.sleep(2.0)
            st.session_state.waiting_for_end_gps = True
            st.session_state.gps_trigger += 1  
            st.toast("🛰️ Fetching new location...", icon="🔄")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- PERSISTENT MAIN-SCREEN DISTANCE PANEL ---
    if st.session_state.last_calculated_distance is not None:
        st.markdown(f"""
            <div class="distance-display-box">
                <div class="distance-label">🏌️‍♂️ Last Shot Distance</div>
                <div class="distance-number">{st.session_state.last_calculated_distance} YARDS</div>
            </div>
        """, unsafe_allow_html=True)

    # Helper dynamic info status banners
    if st.session_state.waiting_for_end_gps:
        st.info("🛰️ Processing live satellite coordinates... calculating distance.")
    elif st.session_state.tee_lat:
        st.info(f"🔄 Ball is live. Walk to your shot, stand still for a brief second, then tap **Click 2: At My Ball**.")
    else:
        st.success("✅ Ready for next shot. Tap **Click 1: Just Teed Off** at your current location.")

    st.divider()

    # Display the History Scorecard Table
    st.subheader("📋 Your Shot History Scorecard")
    
    # CORRECTED ASSIGNMENT: Assigning to a simple variable name first
    shot_history_list = st.session_state.shot_history
    
    if shot_history_list:
        df = pd.DataFrame(shot_history_list)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.write("_No shots recorded yet for this round._")

    # 5. Reset Options
    st.divider()
    col_clear1, col_clear2 = st.columns(2)
    with col_clear1:
        if st.button("Reset Current Shot", use_container_width=True):
            st.session_state.tee_lat = None
            st.session_state.tee_lon = None
            st.session_state.waiting_for_end_gps = False
            st.session_state.last_calculated_distance = None
            st.session_state.gps_trigger += 1
            st.rerun()
    with col_clear2:
        if st.button("🗑️ Clear Entire Scorecard", use_container_width=True):
            st.session_state.tee_lat = None
            st.session_state.tee_lon = None
            st.session_state.waiting_for_end_gps = False
            st.session_state.last_calculated_distance = None
            st.session_state.shot_history = []
            st.session_state.gps_trigger += 1
            st.rerun()





















