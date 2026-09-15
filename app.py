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

# 2. Wake up the phone's live GPS coordinates using your dynamic key
location = get_geolocation(key=f"gps_tracker_{st.session_state.gps_trigger}")

if location is None:
    st.info("🔄 Connecting to iPhone GPS satellites... Please allow location access if prompted.")
elif 'coords' not in location:
    st.warning("⚠️ Waiting for location permissions. Please make sure Safari is allowed to use your GPS.")
else:
    current_lat = location['coords']['latitude']
    current_lon = location['coords']['longitude']

    # --- MID-RUN CALCULATION INTERCEPTOR ---
    # This fires automatically ONLY after "Click 2" forces a fresh GPS satellite pull
    if st.session_state.waiting_for_end_gps:
        # Prevent math on identical coordinate caches
        if current_lat != st.session_state.tee_lat or current_lon != st.session_state.tee_lon:
            lat1, lon1 = math.radians(st.session_state.tee_lat), math.radians(st.session_state.tee_lon)
            lat2, lon2 = math.radians(current_lat), math.radians(current_lon)
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            
            # Earth radius conversion to precise Yards
            distance_in_yards = round(6967410 * c)
            
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
    # Retain selected club in memory across state transitions
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
        # Disable button if we are currently waiting for the second click calculation pass
        if st.button("🔴 Click 1: Just Teed Off", use_container_width=True, disabled=st.session_state.waiting_for_end_gps):
            st.session_state.tee_lat = current_lat
            st.session_state.tee_lon = current_lon
            st.session_state.gps_trigger += 1  # Force clear old cached location data
            st.toast(f"🎯 Tee location saved for your {selected_club}!", icon="📍")
            st.rerun()

    with col2:
        # Disable button if you haven't locked in a start point yet
        if st.button("⚪ Click 2: At My Ball", use_container_width=True, disabled=(st.session_state.tee_lat is None or st.session_state.waiting_for_end_gps)):
            # Set the flag saying: "We're walking. Next time coordinates update, do the math!"
            st.session_state.waiting_for_end_gps = True
            st.session_state.gps_trigger += 1  # Tell Safari to wake up hardware and pull new position
            st.toast("🛰️ Fetching new location...", icon="🔄")
            st.rerun()

    # Helper dynamic info status banners
    if st.session_state.waiting_for_end_gps:
        st.info("🛰️ Processing live satellite coordinates... calculating distance.")
    elif st.session_state.tee_lat:
        st.info(f"🔄 Ball is live. Walk to your shot and tap **Click 2: At My Ball**.")
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
            st.session_state.gps_trigger += 1
            st.rerun()
    with col_clear2:
        if st.button("🗑️ Clear Entire Scorecard", use_container_width=True):
            st.session_state.tee_lat = None
            st.session_state.tee_lon = None
            st.session_state.waiting_for_end_gps = False
            st.session_state.shot_history = []
            st.session_state.gps_trigger += 1
            st.rerun()













