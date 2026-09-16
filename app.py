import streamlit as st
import streamlit.components.v1 as components
import json
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
if 'last_calculated_distance' not in st.session_state:
    st.session_state.last_calculated_distance = None
if 'saved_club' not in st.session_state:
    st.session_state.saved_club = "Driver"

# 3. Main User Interface Layout
st.subheader("1. Setup Your Shot")
club_options = ["Driver", "Mini-Driver", "3-Wood", "4-Iron", "5-Iron", "6-Iron", "7-Iron", "8-Iron", "9-Iron", "Pitching Wedge", "Gap Wedge", "54° Wedge", "60° Wedge"]
selected_club = st.selectbox("Which club are you hitting?", options=club_options, index=club_options.index(st.session_state.saved_club) if st.session_state.saved_club in club_options else 0)
st.session_state.saved_club = selected_club

st.divider()
st.subheader("2. Track Your Distance")

# 4. UNBLOCKED SECURE NATIVE HARDWARE MODULE
# Removed the problematic f-string layout to permanently fix the syntax execution error.
html_interface_bridge = """
<div style="font-family: sans-serif; display: flex; flex-direction: column; gap: 15px; width: 100%;">
    <div style="display: flex; gap: 15px; width: 100%;">
        <button id="btn1" onclick="handleTeeBox()" style="flex: 1; background-color: #2E7D32; color: #000000; font-size: 20px; font-weight: 900; text-transform: uppercase; padding: 18px 10px; border-radius: 12px; border: 3px solid #000000; box-shadow: 4px 4px 0px 0px #000000; cursor: pointer;">
            🔴 Click 1: Just Teed Off
        </button>
        <button id="btn2" onclick="handleLandingBall()" disabled style="flex: 1; background-color: #A5D6A7; color: #555555; font-size: 20px; font-weight: 900; text-transform: uppercase; padding: 18px 10px; border-radius: 12px; border: 3px solid #000000; box-shadow: 4px 4px 0px 0px #000000; cursor: not-allowed; opacity: 0.7;">
            ⚪ Click 2: At My Ball
        </button>
    </div>
    <div id="status_message" style="background-color: #E8F5E9; color: #2E7D32; border: 2px solid #2E7D32; padding: 12px; border-radius: 8px; font-weight: bold; text-align: center; font-size: 16px; margin-top: 5px;">
        ✅ System Armed. Stand on the tee box and tap Click 1.
    </div>
</div>

<script>
    let teeLat = null;
    let teeLon = null;

    function calculateYards(lat1, lon1, lat2, lon2) {
        const p = Math.PI / 180;
        const a = 0.5 - Math.cos((lat2 - lat1) * p)/2 + 
                Math.cos(lat1 * p) * Math.cos(lat2 * p) * 
                (1 - Math.cos((lon2 - lon1) * p))/2;
        return Math.round(2 * 6371000 * Math.asin(Math.sqrt(a)) * 1.09361);
    }

    function handleTeeBox() {
        document.getElementById("status_message").innerHTML = "🛰️ Locking Tee Satellites...";
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    teeLat = position.coords.latitude;
                    teeLon = position.coords.longitude;
                    
                    const b2 = document.getElementById("btn2");
                    b2.disabled = false;
                    b2.style.backgroundColor = "#2E7D32";
                    b2.style.color = "#000000";
                    b2.style.cursor = "pointer";
                    b2.style.opacity = "1";
                    
                    document.getElementById("status_message").style.backgroundColor = "#FFF3E0";
                    document.getElementById("status_message").style.color = "#E65100";
                    document.getElementById("status_message").style.borderColor = "#E65100";
                    document.getElementById("status_message").innerHTML = "🔄 Ball tracking active. Walk to your landing spot, stand still for a second, then hit Click 2.";
                },
                function(error) {
                    document.getElementById("status_message").innerHTML = "❌ GPS Lock Failed. Check Safari location settings.";
                },
                { enableHighAccuracy: true, maximumAge: 0, timeout: 10000 }
            );
        }
    }

    function handleLandingBall() {
        document.getElementById("status_message").innerHTML = "🛰️ Locking Landing Satellites...";
        if (navigator.geolocation && teeLat !== null) {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    const ballLat = position.coords.latitude;
                    const ballLon = position.coords.longitude;
                    
                    const yards = calculateYards(teeLat, teeLon, ballLat, ballLon);
                    
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: yards
                    }, '*');
                },
                function(error) {
                    document.getElementById("status_message").innerHTML = "❌ GPS Lock Failed. Try clicking again.";
                },
                { enableHighAccuracy: true, maximumAge: 0, timeout: 10000 }
            );
        }
    }
</script>
"""

# Render the button array and capture the final calculated integer yardage
returned_yards = components.html(html_interface_bridge, height=130)

# Process data immediately when your iPhone delivers a value
if returned_yards is not None and str(returned_yards).isdigit():
    final_yards = int(returned_yards)
    st.session_state.last_calculated_distance = final_yards
    
    shot_number = len(st.session_state.shot_history) + 1
    new_shot = {
        "Shot #": shot_number, 
        "Club Used": st.session_state.saved_club, 
        "Distance": f"{final_yards} Yards"
    }
    st.session_state.shot_history.append(new_shot)
    save_persistent_history(st.session_state.shot_history)
    st.rerun()

# Scorecard Results Visualization Dashboard
if st.session_state.last_calculated_distance is not None:
    st.markdown(f"""
        <div class="distance-display-box">
            <div class="distance-label">🏌️‍♂️ Last Shot Distance</div>
            <div class="distance-number">{st.session_state.last_calculated_distance} YARDS</div>
        </div>
    """, unsafe_allow_html=True)

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







































