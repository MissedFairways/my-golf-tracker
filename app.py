import streamlit as st
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

# 3. UNBLOCKED DIRECT HARDWARE BRIDGE
# This invisible script runs locally on your iPhone 15 Pro, forcing Safari to pull fresh satellite data.
st.markdown("""
<script>
    function triggerHardwareGPS(actionType) {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    
                    // Locate the native Streamlit text field input boxes safely
                    const inputs = window.parent.document.querySelectorAll('input[type="text"]');
                    if (inputs.length > 0) {
                        // Inject the raw telemetry string directly into the text field element
                        inputs[0].value = actionType + ":" + lat + "," + lon;
                        inputs[0].dispatchEvent(new Event('input', { bubbles: true }));
                        inputs[0].dispatchEvent(new Event('change', { bubbles: true }));
                    }
                },
                function(error) {
                    console.log("GPS Error: " + error.code);
                },
                { enableHighAccuracy: true, maximumAge: 0, timeout: 10000 }
            );
        }
    }
</script>
""", unsafe_allow_html=True)

# This standard text box is hidden from the UI but acts as our unblocked security bridge
gps_mailbox = st.text_input("GPS Secure Bridge Data Link", key="gps_mailbox_bridge", label_visibility="collapsed")

# Process incoming data instantly when the mailbox receives an injection
if gps_mailbox and (":" in str(gps_mailbox)):
    payload = str(gps_mailbox)
    
    if payload.startswith("TEE:"):
        try:
            coords = payload.replace("TEE:", "").split(",")
            st.session_state.tee_lat = float(coords[0])
            st.session_state.tee_lon = float(coords[1])
            st.session_state.last_calculated_distance = None
            st.toast("🎯 Tee box coordinates locked into memory!", icon="📍")
        except:
            pass
            
    elif payload.startswith("BALL:"):
        try:
            coords = payload.replace("BALL:", "").split(",")
            ball_lat = float(coords[0])
            ball_lon = float(coords[1])
            
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
                
                st.session_state.tee_lat = None
                st.session_state.tee_lon = None
                st.toast(f"🚀 Shot logged: {distance_in_yards} Yards!", icon="🏌️‍♂️")
                st.rerun()
        except:
            pass

# 4. Main User Interface Layout
st.subheader("1. Setup Your Shot")
club_options = ["Driver", "Mini-Driver", "3-Wood", "4-Iron", "5-Iron", "6-Iron", "7-Iron", "8-Iron", "9-Iron", "Pitching Wedge", "Gap Wedge", "54° Wedge", "60° Wedge"]
selected_club = st.selectbox("Which club are you hitting?", options=club_options, index=club_options.index(st.session_state.saved_club) if st.session_state.saved_club in club_options else 0)
st.session_state.saved_club = selected_club

st.divider()
st.subheader("2. Track Your Distance")
col1, col2 = st.columns(2)

with col1:
    # Native button that executes local iPhone browser code instantly, avoiding the sandbox block
    if st.button("🔴 Click 1: Just Teed Off", use_container_width=True):
        st.components.v1.html("<script>window.parent.triggerHardwareGPS('TEE');</script>", height=0, width=0)

with col2:
    is_click2_disabled = (st.session_state.tee_lat is None)
    if st.button("⚪ Click 2: At My Ball", use_container_width=True, disabled=is_click2_disabled):
        st.components.v1.html("<script>window.parent.triggerHardwareGPS('BALL');</script>", height=0, width=0)

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





































