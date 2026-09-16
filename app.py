import streamlit as st
import math
import pandas as pd
from streamlit.components.v1 import html

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
if 'saved_club' not in st.session_state:
    st.session_state.saved_club = "Driver"
if 'last_calculated_distance' not in st.session_state:
    st.session_state.last_calculated_distance = None

# 3. Process Inbound Local GPS Data
query_params = st.query_params
if "calculated_yards" in query_params and "club" in query_params:
    try:
        distance_in_yards = int(float(query_params["calculated_yards"]))
        club_used = query_params["club"]
        
        shot_number = len(st.session_state.shot_history) + 1
        new_shot = {"Shot #": shot_number, "Club Used": club_used, "Distance": f"{distance_in_yards} Yards"}
        st.session_state.shot_history.append(new_shot)
        save_persistent_history(st.session_state.shot_history)
        st.session_state.last_calculated_distance = distance_in_yards
        
        st.query_params.clear()
        st.toast(f"🚀 Shot logged: {distance_in_yards} Yards!", icon="🏌️‍♂️")
        st.rerun()
    except Exception as e:
        pass

# 4. App Main Layout Elements
st.subheader("1. Setup Your Shot")
club_options = ["Driver", "Mini-Driver", "3-Wood", "4-Iron", "5-Iron", "6-Iron", "7-Iron", "8-Iron", "9-Iron", "Pitching Wedge", "Gap Wedge", "54° Wedge", "60° Wedge"]
selected_club = st.selectbox("Which club are you hitting?", options=club_options)
st.session_state.saved_club = selected_club

st.divider()
st.subheader("2. Track Your Distance")

# LOCAL COMPONENT: Styled exactly to match your styles.py look
gps_hardware_bridge = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; padding: 0;">
    <div style="display: flex; gap: 1rem; width: 100%; box-sizing: border-box; margin-bottom: 12px;">
        <button id="btn1" onclick="teeOff()" style="flex: 1; background-color: #2E7D32; color: #000000; font-size: 22px; font-weight: 900; letter-spacing: 0.5px; text-transform: uppercase; padding: 18px 10px; border-radius: 12px; border: 3px solid #000000; box-shadow: 6px 6px 0px 0px #000000; cursor: pointer;">🔴 Click 1: Just Teed Off</button>
        <button id="btn2" onclick="atBall()" disabled style="flex: 1; background-color: #A5D6A7; color: #555555; opacity: 0.8; font-size: 22px; font-weight: 900; letter-spacing: 0.5px; text-transform: uppercase; padding: 18px 10px; border-radius: 12px; border: 3px solid #000000; box-shadow: 6px 6px 0px 0px #000000; cursor: not-allowed;">⚪ Click 2: At My Ball</button>
    </div>
    
    <div id="accuracy-meter" style="background-color: #F5F5F5; border: 2px dashed #9E9E9E; padding: 10px; border-radius: 8px; text-align: center; color: #616161; font-weight: 800; font-size: 15px;">
        🛰️ Stabilizing mobile satellite stream...
    </div>
</div>

<script>
    let teeLat = null;
    let teeLon = null;
    let currentLat = null;
    let currentLon = null;
    let currentAccuracy = null;
    const selectedClub = "{selected_club}";

    if (navigator.geolocation) {{
        navigator.geolocation.watchPosition(
            (pos) => {{
                currentLat = pos.coords.latitude;
                currentLon = pos.coords.longitude;
                currentAccuracy = pos.coords.accuracy * 1.09361;
                updateMeter();
            }},
            (err) => {{
                document.getElementById('accuracy-meter').innerText = "⚠️ GPS Error: " + err.message;
            }},
            {{ enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }}
        );
    }}

    function updateMeter() {{
        const meter = document.getElementById('accuracy-meter');
        let status = "❌ POOR";
        let bg = "#FFEBEE";
        let text = "#C62828";
        
        if (currentAccuracy <= 5.0) {{ status = "🎯 LASER ACCURATE"; bg = "#E8F5E9"; text = "#2E7D32"; }}
        else if (currentAccuracy <= 10.0) {{ status = "✅ HIGH QUALITY"; bg = "#E8F5E9"; text = "#1B5E20"; }}
        else if (currentAccuracy <= 18.0) {{ status = "⚠️ MODERATE"; bg = "#FFF3E0"; text = "#E65100"; }}
        
        meter.style.backgroundColor = bg;
        meter.style.border = `2px solid ${{text}}`;
        meter.style.color = text;
        meter.innerHTML = `🛰️ <b>GPS Status:</b> ${{status}} &nbsp;|&nbsp; <b>Margin of Error:</b> ±${{currentAccuracy.toFixed(1)}} Yards`;
    }}

    function teeOff() {{
        if (!currentLat) return;
        teeLat = currentLat;
        teeLon = currentLon;
        
        const btn2 = document.getElementById('btn2');
        btn2.disabled = false;
        btn2.style.backgroundColor = "#2E7D32";
        btn2.style.color = "#000000";
        btn2.style.cursor = "pointer";
        btn2.style.opacity = "1";
        
        alert("🎯 Tee location saved locally!");
    }}

    function atBall() {{
        if (!teeLat || !currentLat) return;
        
        const lat1 = teeLat * Math.PI / 180;
        const lon1 = teeLon * Math.PI / 180;
        const lat2 = currentLat * Math.PI / 180;
        const lon2 = currentLon * Math.PI / 180;
        
        const dlat = lat2 - lat1;
        const dlon = lon2 - lon1;
        const a = Math.sin(dlat/2)**2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dlon/2)**2;
        const c = 2 * Math.atan2(Math.sqrt(a), math.sqrt(1-a));
        const yards = Math.round(6967410 * c);
        
        window.parent.location.search = `?calculated_yards=${{yards}}&club=${{encodeURIComponent(selectedClub)}}`;
    }}
</script>
"""
# Renders the corrected container seamlessly matching your styles
html(gps_hardware_bridge, height=135)

if st.session_state.last_calculated_distance is not None:
    st.markdown(f"""
        <div class="distance-display-box">
            <div class="distance-label">🏌️‍♂️ Last Shot Distance</div>
            <div class="distance-number">{st.session_state.last_calculated_distance} YARDS</div>
        </div>
    """, unsafe_allow_html=True)

st.info(f"🔄 Ball is live. Walk to your shot. Notice how your accuracy error drops the closer you get to your ball!")

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
        st.session_state.last_calculated_distance = None
        st.rerun()
with col_clear2:
    if st.button("🗑️ Clear Entire Scorecard", use_container_width=True):
        st.session_state.last_calculated_distance = None
        st.session_state.shot_history = []
        save_persistent_history([])
        st.rerun()































