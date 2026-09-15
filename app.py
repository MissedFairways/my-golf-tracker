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

# 3. BULLETPROOF NATIVE GPS CAPTURE
st.subheader("2. Track Your Distance")

# Hidden HTML text inputs using standard markdown container targeting
# We use standard HTML input elements inside a clean container to bypass input index conflicts completely.
gps_lat = st.text_input("Latitude", value="", key="lat_holder", label_visibility="collapsed")
gps_lon = st.text_input("Longitude", value="", key="lon_holder", label_visibility="collapsed")

# Native browser HTML5 snippet that securely fetches GPS and injects it into Python via the matching Aria-labels
gps_js_code = """
<script>
function updateGPS() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            // Securely find our targeted input fields inside the webpage frame
            const latInput = window.parent.document.querySelector('input[aria-label="Latitude"]');
            const lonInput = window.parent.document.querySelector('input[aria-label="Longitude"]');
            
            if (latInput && lonInput) {
                latInput.value = position.coords.latitude;
                latInput.dispatchEvent(new Event('input', { bubbles: true }));
                
                lonInput.value = position.coords.longitude;
                lonInput.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }, function(error) {
            console.log("GPS Error: " + error.message);
        }, {enableHighAccuracy: true, timeout: 5000});
    }
}
// Keep location fresh every 3 seconds
setInterval(updateGPS, 3000);
updateGPS();
</script>
"""
st.components.v1.html(gps_js_code, height=0)

# Process tracking ONLY if Safari successfully outputs coordinates into our secure fields
if gps_lat and gps_lon:
    current_lat = float(gps_lat)
    current_lon = float(gps_lon)
    
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
                
                # Save the shot data to our history scorecard memory list
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
    st.info("🔄 Connecting to iPhone GPS satellites... Please tap 'Allow Location' if Safari asks.")

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
        st.shot_history = []
        st.rerun()






