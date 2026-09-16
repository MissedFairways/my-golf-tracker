import streamlit as st
from streamlit_js_eval import streamlit_js_eval
import math
import pandas as pd
import time

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
if 'gps_trigger' not in st.session_state:
    st.session_state.gps_trigger = 0
if 'shot_history' not in st.session_state:
    st.session_state.shot_history = load_persistent_history()
if 'tee_lat' not in st.session_state:
    st.session_state.tee_lat = None
    st.session_state.tee_lon = None
if 'waiting_for_end_gps' not in st.session_state:
    st.session_state.waiting_for_end_gps = False
if 'saved_club' not in st.session_state:
    st.session_state.saved_club = "Driver"
if 'last_calculated_distance' not in st.session_state:
    st.session_state.last_calculated_distance = None

# 3. Continuous Live Streaming GPS Loop (Stream instead of Snapshot)
js_live_stream_script = """
new Promise((resolve) => {
    if (!navigator.geolocation) {
        resolve({ error: "Geolocation not supported" });
        return;
    }
    // watchPosition establishes a continuous stream to keep the GPS chip active and accurate
    const watchId = navigator.geolocation.watchPosition(
        (pos) => {
            navigator.geolocation.clearWatch(watchId);
            resolve({
                coords: {
                    latitude: pos.coords.latitude,
                    longitude: pos.coords.longitude,
                    accuracy: pos.coords.accuracy
                }
            });
        },
        (err) => { 
            navigator.geolocation.clearWatch(watchId);
            resolve({ error: err.message }); 
        },
        { enableHighAccuracy: true, timeout: 8000, maximumAge: 0 }
    );
});
"""

location = streamlit_js_eval(
    js_expressions=js_live_stream_script, 
    key=f"gps_streamer_{st.session_state.gps_trigger}"
)

current_lat = None
current_lon = None
gps_accuracy_yards = None

if location is None:
    st.info("🔄 Streaming live satellite data... Please stand in an open area.")
elif 'error' in location:
    st.warning(f"⚠️ GPS Stream Error: {location['error']}. Check Safari location settings.")
elif 'coords' in location:
    current_lat = location['coords']['latitude']
    current_lon = location['coords']['longitude']
    # Convert accuracy from meters to yards (1 meter ≈ 1.09361 yards)
    gps_accuracy_yards = round(location['coords']['accuracy'] * 1.09361, 1)

    # Process distance tracking logic if the user clicked "At My Ball"
    if st.session_state.waiting_for_end_gps:
        # Step A: Filter out old cached values if the coordinate hasn't budget at all
        if current_lat == st.session_state.tee_lat and current_lon == st.session_state.tee_lon:
            st.toast("🛰️ iPhone returned cached position. Forcing fresh satellite recalculation...", icon="⏳")
            time.sleep(0.5)
            st.session_state.gps_trigger += 1
            st.rerun()

        # Step B: Only accept coordinates once the satellite precision settles under 12 yards
        if gps_accuracy_yards > 12.0:
            st.toast(f"⏳ Waiting for high accuracy... current error margin is {gps_accuracy_yards} yards.", icon="🛰️")
            time.sleep(0.5)
            st.session_state.gps_trigger += 1
            st.rerun()

        # Step C: Precision verification passed, run calculation
        lat1, lon1 = math.radians(st.session_state.tee_lat), math.radians(st.session_state.tee_lon)
        lat2, lon2 = math.radians(current_lat), math.radians(current_lon)
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance_in_yards = round(6967410 * c)
        
        if distance_in_yards > 8:
            st.session_state.last_calculated_distance = distance_in_yards
            shot_number = len(st.session_state.shot_history) + 1
            new_shot = {"Shot #": shot_number, "Club Used": st.session_state.saved_club, "Distance": f"{distance_in_yards} Yards"}
            st.session_state.shot_history.append(new_shot)
            save_persistent_history(st.session_state.shot_history)
            
            st.session_state.tee_lat = None
            st.session_state.tee_lon = None
            st.session_state.waiting_for_end_gps = False
            st.toast(f"🚀 Shot logged: {distance_in_yards} Yards!", icon="🏌️‍♂️")
            st.rerun()
        else:
            st.session_state.gps_trigger += 1
            st.rerun()

# 4. App Main Layout Elements
st.subheader("1. Setup Your Shot")
club_options = ["Driver", "Mini-Driver", "3-Wood", "4-Iron", "5-Iron", "6-Iron", "7-Iron", "8-Iron", "9-Iron", "Pitching Wedge", "Gap Wedge", "54° Wedge", "60° Wedge"]
selected_club = st.selectbox("Which club are you hitting?", options=club_options, index=club_options.index(st.session_state.saved_club) if st.session_state.saved_club in club_options else 0)
st.session_state.saved_club = selected_club

st.divider()
st.subheader("2. Track Your Distance")
col1, col2 = st.columns(2)
with col1:
    if st.button("🔴 Click 1: Just Teed Off", use_container_width=True, disabled=st.session_state.waiting_for_end_gps or current_lat is None):
        st.session_state.tee_lat = current_lat
        st.session_state.tee_lon = current_lon
        st.session_state.gps_trigger += 1  
        st.session_state.last_calculated_distance = None
        st.toast(f"🎯 Tee location saved for your {selected_club}!", icon="📍")
        st.rerun()

with col2:
    if st.button("⚪ Click 2: At My Ball", use_container_width=True, disabled=(st.session_state.tee_lat is None or st.session_state.waiting_for_end_gps or current_lat is None)):
        st.session_state.waiting_for_end_gps = True
        st.session_state.gps_trigger += 1  
        st.toast("🛰️ Analyzing accuracy levels...", icon="🔄")
        st.rerun()

# --- LIVE ACCURACY METER DISPLAY ---
if gps_accuracy_yards is not None:
    if gps_accuracy_yards <= 5.0:
        badge_color, text_color, status_text = "#E8F5E9", "#2E7D32", "🎯 EXCELLENT"
    elif gps_accuracy_yards <= 12.0:
        badge_color, text_color, status_text = "#FFF3E0", "#E65100", "✅ GOOD (Ready)"
    else:
        badge_color, text_color, status_text = "#FFEBEE", "#C62828", "⏳ STABILIZING (Wait)"

    st.markdown(f"""
        <div style="background-color: {badge_color}; border: 2px solid {text_color}; padding: 10px; border-radius: 8px; text-align: center; margin-top: 12px;">
            <span style="color: {text_color}; font-weight: 800; font-size: 16px;">
                🛰️ GPS Signal Strength: {status_text} &nbsp;|&nbsp; Margin of Error: ±{gps_accuracy_yards} Yards
            </span>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <div style="background-color: #F5F5F5; border: 2px dashed #9E9E9E; padding: 10px; border-radius: 8px; text-align: center; margin-top: 12px;">
            <span style="color: #616161; font-weight: 800; font-size: 16px;">🛰️ Checking Signal Quality...</span>
        </div>
    """, unsafe_allow_html=True)

if st.session_state.last_calculated_distance is not None:
    st.markdown(f"""
        <div class="distance-display-box">
            <div class="distance-label">🏌️‍♂️ Last Shot Distance</div>
            <div class="distance-number">{st.session_state.last_calculated_distance} YARDS</div>
        </div>
    """, unsafe_allow_html=True)

if st.session_state.waiting_for_end_gps:
    st.info("🛰️ Processing live satellite coordinates... calculating distance.")
elif st.session_state.tee_lat:
    st.info(f"🔄 Ball is live. Walk to your shot, stand still for a brief second, then tap **Click 2: At My Ball**.")
else:
    st.success("✅ Ready for next shot. Tap **Click 1: Just Teed Off** at your current location.")

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
        st.session_state.waiting_for_end_gps = False
        st.session_state.last_calculated_distance = None
        st.session_state.gps_trigger += 1
        st.rerun()
with col_clear2:
    if st.button("🗑️ Clear Entire Scorecard", use_container_width=True):
        st.session_state.tee_lat, st.session_state.tee_lon = None, None
        st.session_state.waiting_for_end_gps = False
        st.session_state.last_calculated_distance = None
        st.session_state.shot_history = []
        save_persistent_history([])
        st.session_state.gps_trigger += 1
        st.rerun()




























