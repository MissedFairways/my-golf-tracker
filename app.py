import streamlit as st
from streamlit_js_eval import get_geolocation
import math

# 1. App Styling and Titles
st.set_page_config(page_title="Golf Tracker", page_icon="⛳")
st.title("⛳ Golf Drive Tracker")
st.write("Click 'Teed Off' at the tee box, then 'At My Ball' when you find your shot.")

# 2. Wake up and grab the phone's live GPS coordinates
location = get_geolocation()

# Safety Check: If the iPhone browser hasn't handed over the location data yet
if location is None:
    st.info("🔄 Connecting to iPhone GPS satellites... Please allow location access if prompted.")
elif 'coords' not in location:
    st.warning("⚠️ Waiting for location permissions. Please make sure Safari is allowed to use your GPS.")
else:
    # Safely extract the current latitude and longitude
    current_lat = location['coords']['latitude']
    current_lon = location['coords']['longitude']

    # 3. Create a clean space in the app's memory to store your clicks
    if 'tee_lat' not in st.session_state:
        st.session_state.tee_lat = None
        st.session_state.tee_lon = None

    # 4. Button 1: TEE BOX
    if st.button("🔴 Click 1: Just Teed Off", use_container_width=True):
        st.session_state.tee_lat = current_lat
        st.session_state.tee_lon = current_lon
        st.success("Tee box location saved!")

    # Show the user if a tee location is currently locked in
    if st.session_state.tee_lat:
        st.info("Tee position locked in. Walk to your ball!")

    # 5. Button 2: AT THE BALL
    if st.button("⚪ Click 2: At My Ball", use_container_width=True):
        if st.session_state.tee_lat is None:
            st.error("Please click 'Just Teed Off' first!")
        else:
            # Mathematical formula (Haversine) to calculate distance on Earth
            lat1, lon1 = math.radians(st.session_state.tee_lat), math.radians(st.session_state.tee_lon)
            lat2, lon2 = math.radians(current_lat), math.radians(current_lon)
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            
            # Earth's radius in yards is roughly 6,967,410
            distance_in_yards = 6967410 * c
            
            # Display the final big result
            st.metric(label="🏌️‍♂️ Driving Distance", value=f"{round(distance_in_yards)} Yards")

    # 6. Reset Button to start a new hole
    if st.button("Clear / Next Hole"):
        st.session_state.tee_lat = None
        st.session_state.tee_lon = None
        st.rerun()
