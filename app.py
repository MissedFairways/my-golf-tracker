import streamlit as st
import streamlit.components.v1 as components
import math
import pandas as pd

# Import configurations from our custom helper files
from styles import inject_sunlight_styles
from storage import load_persistent_history, save_persistent_history, render_club_averages

# 1. UI Initialization
st.set_page_config(page_title="GEN X GOLF", page_icon="⛳", layout="centered")
st.markdown("""
    <h1 style='text-align: center; font-size: 2.8rem; font-weight: 900; color: #000000; line-height: 1.2; margin-bottom: 25px;'>
        GEN X GOLF<br><span style='font-size: 2.2rem; font-weight: 800; color: #2E7D32;'>DISTANCE TRACKER</span>
    </h1>
""", unsafe_allow_html=True)
inject_sunlight_styles()

# 2. Session Memory Synchronization
if 'shot_history' not in st.session_state:
    st.session_state.shot_history = load_persistent_history()
if 'tee_lat' not in st.session_state:
    st.session_state.tee_lat = None
    st.session_state.tee_lon = None
if 'saved_club' not in st.session_state:
    st.session_state.saved_club = "Driver"
if 'last_calculated_distance' not in st.session_state:
    st.session_state.last_calculated_distance = None

# 3. THE INSTANT SATELLITE BRIDGE COMPONENT
gps_bridge_html = """
<script>
    function captureHardwareGPS(actionType) {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    const accuracy = position.coords.accuracy;
                    
                    // Pipe the fresh, live numbers directly back to Python instantly
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: actionType + ":" + lat + "," + lon + "," + accuracy
                    }, '*');
                },
                function(error) {
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: "ERROR:" + error.code
                    }, '*');
                },
                {
                    enableHighAccuracy: true,
                    maximumAge: 0,
                    timeout: 10000
                }
            );
        }
    }

    // Read instructions sent from Python buttons
    window.addEventListener('message', function(e) {
        if (e.data.type === 'trigger_click1') {
            captureHardwareGPS('TEE');
        } else if (e.data.type === 'trigger_click2') {
            captureHardwareGPS('BALL');
        }
    });
</script>
"""

# Establish the secure communications array channel
gps_response = components.html(gps_bridge_html, height=0, width=0)

# Process incoming hardware payloads immediately when a button is touched
if gps_response and (":" in str(gps_response)):
    payload = str(gps_response)
    
    if payload.startswith("TEE:"):
        try:
            coords = payload.replace("TEE:", "").split(",")
            # FIXED: Grabbing the items by index out of the list explicitly
            st.session_state.tee_lat = float(coords[0])
            st.session_state.tee_lon = float(coords[1])
            st.session_state.last_calculated_distance = None
            st.toast("🎯 Tee box coordinates locked into memory!", icon="📍")
        except:
            st.toast("⚠️ GPS data corrupt. Please try clicking again.", icon="❌")
            
    elif payload.startswith("BALL:"):
        try:
            coords = payload.replace("BALL:", "").split(",")
            # FIXED: Grabbing the items by index out of the list explicitly
            ball_lat = float(coords[0])
            ball_lon = float(coords[1])
            
            # Run the Haversine formula calculation instantly using the fresh data
            if st.session_state.tee_lat is not None:
                lat1, lon1 = math.radians(st.session_state.tee_lat), math.radians(st.session_state.tee_lon)
                lat2, lon2 = math.radians(ball_lat), math.radians(ball_lon)
                dlat, dlon = lat2 - lat1, lon2 - lon1
                
                a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                distance_in_yards = round(6967410 * c)
                
                st.session_state.last_calculated_distance = distance_in_yards
                shot_number = len(st.session_state.shot_history) + 1
                
                new_shot = {
                    "Shot #": shot_number, 
                    "Club Used": st.session_state.saved_club, 
                    "Distance": f"{distance_in_yards} Yards"
                }
                st.session_state.shot_history.append(new_shot)
                save_persistent_history(st.session_state.shot_history)
                
                # Instantly clear variables so the application stands ready for the next shot
                st.session_state.tee_lat = None
                st.session_state.tee_lon = None
                st.toast(f"🚀 Shot logged: {distance_in_yards} Yards!", icon="🏌️‍♂️")
                st.rerun()
        except:
            st.toast("⚠️ Distance math failed. Please retry Click 2.", icon="❌")

# 4. Main User Interface Layout
st.subheader("1. Setup Your Shot")
club_options = ["Driver", "Mini-Driver", "3-Wood", "4-Iron", "5-Iron", "6-Iron", "7-Iron", "8-Iron", "9-Iron", "Pitching Wedge", "Gap Wedge", "54° Wedge", "60° Wedge"]
selected_club = st.selectbox("Which club are you hitting?", options=club_options, index=club_options.index(st.session_state.saved_club) if st.session_state.saved_club in club_options else 0)
st.session_state.saved_club = selected_club

st.divider()
st.subheader("2. Track Your Distance")
col1, col2 = st.columns(2)

with col1:
    # Click 1 Component Execution
    if st.button("🔴 Click 1: Just Teed Off", use_container_width=True):
        st.markdown("""
            <script>
                window.parent.postMessage({type: 'trigger_click1'}, '*');
            </script>
        """, unsafe_allow_html=True)

with col2:
    # Click 2 Component Execution (Disabled until Click 1 sets a starting baseline)
    is_click2_disabled = (st.session_state.tee_lat is None)
    if st.button("⚪ Click 2: At My Ball", use_container_width=True, disabled=is_click2_disabled):
        st.markdown("""
            <script>
                window.parent.postMessage({type: 'trigger_click2'}, '*');
            </script>
        """, unsafe_allow_html=True)

# Scorecard Results Visualization Dashboard
if st.session_state.last_calculated_distance is not None:
    st.markdown(f"""
        <div class="distance-display-box">
            <div class="distance-label">🏌️‍♂️ Last Shot Distance</div>
            <div class="distance-number">{st.session_state.last_calculated_distance} YARDS</div>
        </div>
    """, unsafe_allow_html=True)

# Dynamic status helper banner
if st.session_state.tee_lat:
    st.info("🔄 Ball tracking active. Walk out to your landing spot, stand still for a second, then hit Click 2.")
else:
    st.success("✅ System Armored. Stand on the tee box and tap Click 1 to begin.")

st.divider()
st.subheader("📋 Your Shot History Scorecard")
shot_history_list = st.session_state.shot_history
if shot_history_list:
    df = pd.DataFrame(shot_history_list)
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.write("_No shots recorded yet for this round._")

st.divider()
st.subheader("📊 Your Club Averages")
render_club_averages(shot_history_list)

st.divider()
col_clear1, col_clear2 = st.columns(2)
with col_clear1:
    if st.button("Reset Current Shot", use_container_width=True):
        st.session_state.tee_lat = None
        st.session_state.tee_lon = None
        st.session_state.last_calculated_distance = None
        st.rerun()
with col_clear2:
    if st.button("🗑️ Clear Entire Scorecard", use_container_width=True):
        st.session_state.tee_lat, st.session_state.tee_lon = None, None
        st.session_state.last_calculated_distance = None
        st.session_state.shot_history = []
        save_persistent_history([])
        st.rerun()



































