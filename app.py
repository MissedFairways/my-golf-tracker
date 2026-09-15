import streamlit as st
from streamlit_js_eval import get_geolocation
import math
import pandas as pd

# 1. App Styling and Titles
st.set_page_config(page_title="Golf Tracker", page_icon="⛳")
st.title("⛳ My Advanced Golf Drive Tracker")

# 2. Add a hidden component to force a location update when a button is clicked
# We use a standard Streamlit button action to force the app script to rerun and poll the GPS hardware freshly.
location = get_geolocation()

if location is None:
    st.info("🔄 Connecting to iPhone GPS satellites... Please allow location access if prompted.")
elif 'coords' not in location:
    st.warning("⚠️ Waiting for location permissions. Please make sure Safari is allowed to use your GPS.")
else:
    current_lat = location['coords']['latitude']
    current_lon = location['coords']['longitude']

    # 3. Setup Persistent Memory
    if 'tee_lat' not in st.session_state:
        st.session_state.tee_lat = None
        st.session_state.tee_lon = None
    if 'shot_history' not in st.session_state:
        st.session_state.shot_history = []

    # Custom Feature: Club Bag Layout
    st.subheader("1. Setup Your Shot")
    club_options = [
        "Driver", "Mini-Driver", "3-Wood", "4-Iron", "5-Iron", 
        "6-Iron", "7-Iron", "8-Iron", "9-Iron", "Pitching Wedge", 
        "Gap Wedge", "54° Wedge", "60° Wedge"
    ]
    selected_club = st.selectbox("Which club are you hitting?", options=club_options)

    st.divider()

    # 4. Action Buttons
    st.subheader("2. Track Your Distance")
    col1, col2 = st.columns(2)

    with col1:
        # Hitting this button saves the absolute latest fetched latitude/longitude
        if st.button("🔴 Click 1: Just Teed Off", use_container_width=True):
            st.session_state.tee_lat = current_lat
            st.session_state.tee_lon = current_lon
            st.success(f"Tee location saved for your {selected_club}!")
            st.rerun() # Force code block refresh to lock coordinate states securely

    with col2:
        if st.button("⚪ Click 2: At My Ball", use_container_width=True):
            if st.session_state.tee_lat is None:
                st.error("Please click 'Just Teed Off' first!")
            else:
                # Math formula to calculate distance on Earth
                lat1, lon1 = math.radians(st.session_state.tee_lat), math.radians(st.session_state.tee_lon)
                lat2, lon2 = math.radians(current_lat), math.radians(current_lon)
                
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                
                a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                distance_in_yards = round(6967410 * c)
                
                # Show the massive result on screen
                st.metric(label="🏌️‍♂️ Driving Distance", value=f"{distance_in_yards} Yards")
                
                # Save the shot data to our history memory list
                shot_number = len(st.session_state.shot_history) + 1
                new_shot = {
                    "Shot #": shot_number,
                    "Club Used": selected_club,
                    "Distance": f"{distance_in_yards} Yards"
                }
                st.session_state.shot_history.append(new_shot)
                st.success("Shot saved to history scorecard below!")

    # Helper info status tracker
    if st.session_state.tee_lat and not st.session_state.shot_history:
        st.info(f"📍 {selected_club} position locked in. Walk to your ball and hit Click 2!")

    st.divider()

    # Display the History Scorecard Table
    st.subheader("📋 Your Shot History Scorecard")
    if st.session_state.shot_history:
        df = pd.DataFrame(st.session_state.shot_history)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.write("No shots recorded yet for this round.")

    # 5. Reset Options
    st.divider()
    col_clear1, col_clear2 = st.columns(2)
    with col_clear1:
        if st.button("Reset Current Shot", use_container_width=True):
            st.session_state.tee_lat = None
            st.session_state.tee_lon = None
            st.rerun()
    with col_clear2:
        if st.button("🗑️ Clear Entire Scorecard", use_container_width=True):
            st.session_state.tee_lat = None
            st.session_state.tee_lon = None
            st.session_state.shot_history = []
            st.rerun()



