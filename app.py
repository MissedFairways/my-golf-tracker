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

# 3. COMPASS-GRADE HIGH ACCURACY WATCHER WITH WAKE-LOCK
# This forces Safari to match native app performance and keep the GPS hardware "warm".
gps_watcher_html = """
<div style="display:none;">
    <input type="text" id="gps_data" value="">
</div>
<script>
    let wakeLock = null;

    // Force Safari to stay fully awake while the app is active
    async function requestWakeLock() {
        try {
            if ('wakeLock' in navigator) {
                wakeLock = await navigator.wakeLock.request('screen');
            }
        } catch (err) {
            console.log("Wake Lock clear: " + err.message);
        }
    }

    function sendToStreamlit(lat, lon, acc) {
        const inputEl = document.getElementById("gps_data");
        const dataString = lat + "," + lon + "," + acc;
        inputEl.value = dataString;
        
        const event = new Event('change', { bubbles: true });
        inputEl.dispatchEvent(event);
        
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: dataString
        }, '*');
    }

    if (navigator.geolocation) {
        requestWakeLock();
        
        navigator.geolocation.watchPosition(
            function(position) {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                const accuracy = position.coords.accuracy; // Metric error bound
                
                // Emulate the Compass app: block coarse/cellular network coordinates
                if (accuracy <= 15) {
                    sendToStreamlit(lat, lon, accuracy);
                }
            },
            function(error) {
                console.error("GPS Error: " + error.code);
            },
            {
                enableHighAccuracy: true,
                maximumAge: 0,
                timeout: 10000
            }
        );
    }
</script>
"""

# Render the invisible connection module
gps_stream = components.html(gps_watcher_html, height=0, width=0)

# Extract raw values from the continuous hardware stream
current_lat, current_lon, current_accuracy = None, None, None
if gps_stream and ("," in str(gps_stream)):
    try:
        parts = str(gps_stream).split(",")
        current_lat = float(parts[0])
        current_lon = float(parts[1])
        current_accuracy = float(parts[2])
    except:
        pass

# 4. Main App Layout and Mechanics
if current_lat is None:
    st.info("🛰️ Waking up iPhone GPS satellites... Please step out into an open area away from patio roofs.")
else:
    # Convert accuracy from meters to yards for visual golf validation
    acc_yards = round(current_accuracy * 1.09361)
    
    st.subheader("1. Setup Your Shot")
    club_options = ["Driver", "Mini-Driver", "3-Wood", "4-Iron", "5-Iron", "6-Iron", "7-Iron", "8-Iron", "9-Iron", "Pitching Wedge", "Gap Wedge", "54° Wedge", "60° Wedge"]
    selected_club = st.selectbox("Which club are you hitting?", options=club_options, index=club_options.index(st.session_state.saved_club) if st.session_state.saved_club in club_options else 0)
    st.session_state.saved_club = selected_club

    st.divider()
    st.subheader("2. Track Your Distance")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔴 Click 1: Just Teed Off", use_container_width=True):
            st.session_state.tee_lat = current_lat
            st.session_state.tee_lon = current_lon
            st.session_state.last_calculated_distance = None
            st.toast(f"🎯 Tee location locked! (GPS Margin: ±{acc_yards} yds)", icon="📍")
            st.rerun()

    with col2:
        is_click2_disabled = (st.session_state.tee_lat is None)
        if st.button("⚪ Click 2: At My Ball", use_container_width=True, disabled=is_click2_disabled):
            # Calculate distance using precise Haversine formulas instantly
            lat1, lon1 = math.radians(st.session_state.tee_lat), math.radians(st.session_state.tee_lon)
            lat2, lon2 = math.radians(current_lat), math.radians(current_lon)
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
            
            # Reset the current shot tracking so it's clean for the next hole
            st.session_state.tee_lat = None
            st.session_state.tee_lon = None
            st.toast(f"🚀 Shot logged: {distance_in_yards} Yards!", icon="🏌️‍♂️")
            st.rerun()

    # Scorecard Result Board Display
    if st.session_state.last_calculated_distance is not None:
        st.markdown(f"""
            <div class="distance-display-box">
                <div class="distance-label">🏌️‍♂️ Last Shot Distance</div>
                <div class="distance-number">{st.session_state.last_calculated_distance} YARDS</div>
            </div>
        """, unsafe_allow_html=True)

    # Dynamic status helper banner
    if st.session_state.tee_lat:
        st.info(f"🔄 Ball is live. Walk to your shot. (Current Live Signal Accuracy: ±{acc_yards} Yards).")
    else:
        st.success(f"✅ Satellites locked (Signal Accuracy: ±{acc_yards} Yards). Tap Click 1 to track.")

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
































