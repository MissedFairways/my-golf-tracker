import streamlit as st
import math
import pandas as pd

# 1. App Styling and Titles
st.set_page_config(page_title="Golf Tracker", page_icon="⛳")
st.title("⛳ My Advanced Golf Drive Tracker")

# 2. Setup Persistent Memory
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

# 3. BULLETPROOF GPS COMPONENT: Native HTML5 Browser Tracker
# This invisible component forces Safari to pull fresh satellite data instantly when you tap a button.
st.subheader("2. Track Your Distance")

# Injecting raw browser code that talks directly to iOS Location Services
gps_code = """
<script>
function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(showPosition, showError, {enableHighAccuracy: true, timeout: 5000});
    }
}
function showPosition(position) {
    const lat = position.coords.latitude;
    const lon = position.coords.longitude;
    // Pass coordinates directly back to Python seamlessly
    window.parent.postMessage({type: 'streamlit:setComponentValue', value: {lat: lat, lon: lon}}, '*');
}
function showError(error) {
    console.log("GPS Error: " + error.message);
}
// Automatically scan position whenever this block loads
getLocation();
</script>
"""

# Fetch the native coordinates
ctx = st.components.v1.html(gps_code, height=0, srcdoc=True)

# Process the coordinates if Safari successfully hands them over
if ctx is not None:
    current_lat = ctx.get('lat')
    current_lon = ctx.get('lon')
    
    if current_lat and current_lon:
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔴 Click 1: Just Teed Off", use_container_width=True):
                st.session_state.tee_lat = current_lat
                st.session_state.tee_lon = current_lon
                st.success(f"Tee location saved for your {selected_club}!")
                st.rerun()

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
                    
                    # Show the result on screen
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
                    st.rerun()

        # Helper info status tracker
        if st.session_state.tee_lat and not st.session_state.shot_history:
            st.info(f"📍 {selected_club} position locked in. Walk to your ball and hit Click 2!")
    else:
        st.info("🔄 Connecting to iPhone GPS satellites... Please allow location access if prompted.")
else:
    st.info("🔄 Initializing browser location module...")

st.divider()

# Display the History Scorecard Table
st.subheader("📋 Your Shot History Scorecard")
if st.session_state.shot_history:
    df = pd.DataFrame(st.session_state.shot_history)
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.write("No shots recorded yet for this round.")

# 4. Reset Options
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




