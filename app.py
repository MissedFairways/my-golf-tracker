import streamlit as st
from streamlit_js_eval import get_geolocation
import math
import pandas as pd

# 1. App Styling and Titles
st.set_page_config(page_title="Golf Tracker", page_icon="⛳")
st.title("⛳ My Advanced Golf Drive Tracker")

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

# --- CUSTOM CSS FOR THE DISTANCE DISPLAY BOX ---
st.markdown("""
    <style>
        .distance-display-box {
            background-color: #FFFFFF;
            border: 2px solid #E0E0E0;
            border-radius: 12px;
            padding: 15px;
            text-align: center;
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.05);
            margin-top: 15px;
            margin-bottom: 15px;
        }
        .distance-label {
            font-size: 0.9rem;
            color: #666666;
            text-transform: uppercase;
            font-weight: bold;
            margin-bottom: 2px;
        }
        .distance-number {
            font-size: 2.2rem;
            color: #2E7D32; /* Large Green Numbers */
            font-weight: 800;
            line-height: 1.1;
        }
    </style>
""", unsafe_allow_html=True)

# 2. Wake up the phone's live GPS coordinates using the correct component parameter
location = get_geolocation(
    component_key=f"gps_tracker_{st.session_state.gps_trigger}"
)

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
        if st.button("🔴 Click 1: Just Teed Off", use_container_width=True, disabled=st.session_state.waiting_for_end_gps):
            st.session_state.tee_lat = current_lat
            st.session_state.tee_lon = current_lon
            st.session_state.gps_trigger += 1  
            # Clear out old display value once a fresh tracking run begins
            st.session_state.last_calculated_distance = None
            st.toast(f"🎯 Tee location saved for your {selected_club}!", icon="📍")
            st.rerun()

    with col2:
        if st.button("⚪ Click 2: At My Ball", use_container_width=True, disabled=(st.session_state.tee_lat is None or st.session_state.waiting_for_end_gps)):
            st.session_state.waiting_for_end_gps = True
            st.session_state.gps_trigger += 1  
            st.toast("🛰️ Fetching new location...", icon="🔄")
            st.rerun()

    # --- PERSISTENT MAIN-SCREEN DISTANCE PANEL ---
    # Renders perfectly centered right below your tracking choices
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
    if st.session_state.shot_history:
        df = pd.DataFrame(st.session_state.shot_history)
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
















