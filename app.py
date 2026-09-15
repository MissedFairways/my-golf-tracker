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

# --- ENHANCED MOBILE UI CUSTOM CSS ---
st.markdown("""
    <style>
        /* 1. Large, Easy-to-Tap Dropdown Menu */
        div[data-baseweb="select"] {
            font-size: 1.3rem !important;
            font-weight: bold !important;
        }
        div[data-testid="stSelectbox"] label p {
            font-size: 1.1rem !important;
            font-weight: bold !important;
        }

        /* 2. Global Button Sizing Overrides */
        div[data-testid="stButton"] button {
            width: 100% !important;
            padding: 18px 10px !important; /* Extra height padding for thumb taps */
            font-size: 1.25rem !important; /* Significantly larger text */
            font-weight: 800 !important;   /* Ultra-bold typography */
            border-radius: 12px !important;
            border: none !important;
            transition: all 0.1s ease-in-out !important;
        }

        /* 3. Button Depth, Shadows, and Color Coding */
        /* Click 1 Button (Green) */
        div[data-testid="column"]:nth-of-type(1) div[data-testid="stButton"] button {
            background-color: #1B5E20 !important; /* Forest Green */
            color: white !important;
            box-shadow: 0px 5px 0px #0D260D, 0px 8px 15px rgba(0, 0, 0, 0.2) !important;
        }
        div[data-testid="column"]:nth-of-type(1) div[data-testid="stButton"] button:active {
            transform: translateY(3px) !important;
            box-shadow: 0px 2px 0px #0D260D, 0px 4px 8px rgba(0, 0, 0, 0.2) !important;
        }

        /* Click 2 Button (Blue) */
        div[data-testid="column"]:nth-of-type(2) div[data-testid="stButton"] button {
            background-color: #0D47A1 !important; /* Rich Golf Blue */
            color: white !important;
            box-shadow: 0px 5px 0px #0A2244, 0px 8px 15px rgba(0, 0, 0, 0.2) !important;
        }
        div[data-testid="column"]:nth-of-type(2) div[data-testid="stButton"] button:active {
            transform: translateY(3px) !important;
            box-shadow: 0px 2px 0px #0A2244, 0px 4px 8px rgba(0, 0, 0, 0.2) !important;
        }
        
        /* Safe styling for disabled states when calculations are processing */
        div[data-testid="stButton"] button:disabled {
            background-color: #E0E0E0 !important;
            color: #9E9E9E !important;
            box-shadow: none !important;
            transform: none !important;
        }

        /* 4. Large Green Distance Display Panel */
        .distance-display-box {
            background-color: #FFFFFF;
            border: 3px solid #1B5E20;
            border-radius: 14px;
            padding: 20px;
            text-align: center;
            box-shadow: 0px 6px 12px rgba(0, 0, 0, 0.08);
            margin-top: 25px;
            margin-bottom: 25px;
        }
        .distance-label {
            font-size: 1.0rem;
            color: #555555;
            text-transform: uppercase;
            font-weight: 800;
            letter-spacing: 1px;
            margin-bottom: 4px;
        }
        .distance-number {
            font-size: 2.8rem; /* Expanded for quick glance scanning */
            color: #1B5E20; 
            font-weight: 900;
            line-height: 1.0;
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
        if st.button("🟢 Teed Off", use_container_width=True, disabled=st.session_state.waiting_for_end_gps):
            st.session_state.tee_lat = current_lat
            st.session_state.tee_lon = current_lon
            st.session_state.gps_trigger += 1  
            st.session_state.last_calculated_distance = None
            st.toast(f"🎯 Tee location saved for your {selected_club}!", icon="📍")
            st.rerun()

    with col2:
        if st.button("🔵 At My Ball", use_container_width=True, disabled=(st.session_state.tee_lat is None or st.session_state.waiting_for_end_gps)):
            st.session_state.waiting_for_end_gps = True
            st.session_state.gps_trigger += 1  
            st.toast("🛰️ Fetching new location...", icon="🔄")
            st.rerun()

    # --- PERSISTENT MAIN-SCREEN DISTANCE PANEL ---
    if st.session_state.last_calculated_distance is not None:
        st.markdown(f"""
            <div class="distance-display-box">
                <div class="distance-label">🏌️‍♂️ Drive Distance</div>
                <div class="distance-number">{st.session_state.last_calculated_distance} YARDS</div>
            </div>
        """, unsafe_allow_html=True)

    # Helper dynamic info status banners
    if st.session_state.waiting_for_end_gps:
        st.info("🛰️ Processing live satellite coordinates... calculating distance.")
    elif st.session_state.tee_lat:
        st.info(f"🔄 Ball is live. Walk to your shot, stand still for a brief second, then tap **🔵 At My Ball**.")
    else:
        st.success("✅ Ready for next shot. Tap **🟢 Teed Off** at your current location.")

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


















