import streamlit as st
from streamlit_js_eval import get_geolocation
import math
import pandas as pd

# 1. App Styling and Titles
st.set_page_config(page_title="GEN X DISTANCE TRACKER", page_icon="⛳")

# --- TWO-LINE CENTERED MAIN HEADER ---
st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="font-size: 2.8rem; font-weight: 900; line-height: 1.1; margin: 0; color: #111111;">
            GEN X<br>DISTANCE TRACKER
        </h1>
    </div>
""", unsafe_allow_html=True)

# Create a master trigger key to force browser hardware updates
if 'gps_trigger' not in st.session_state:
    st.session_state.gps_trigger = 0

# --- SETUP PERSISTENT MEMORY ---
if 'tee_lat' not in st.session_state:
    st.session_state.tee_lat = None
    st.session_state.tee_lon = None
if 'shot_history' not in st.session_state:
    st.session_state.shot_history = []
if 'waiting_for_end_gps' not in st.session_state:
    st.session_state.waiting_for_end_gps = False
if 'saved_club' not in st.session_state:
    st.session_state.saved_club = "Driver"
if 'last_calculated_distance' not in st.session_state:
    st.session_state.last_calculated_distance = None

# --- SUNLIGHT VISIBILITY MASSIVE CSS OVERRIDES ---
st.markdown("""
    <style>
        /* 1. Large, Easy-to-Tap Dropdown Menu */
        div[data-baseweb="select"] {
            font-size: 1.6rem !important;
            font-weight: bold !important;
        }
        div[data-testid="stSelectbox"] label p {
            font-size: 1.3rem !important;
            font-weight: bold !important;
        }
        
        /* Hide the internal pipeline inputs from view */
        div.element-container:has(div[data-testid="stTextInput"]) {
            display: none !important;
        }
        div[data-testid="stTextInput"] {
            display: none !important;
        }

        /* 2. Large Distance Display Panel Box */
        .distance-display-box {
            background-color: #FFFFFF;
            border: 4px solid #1B5E20;
            border-radius: 16px;
            padding: 20px;
            text-align: center;
            box-shadow: 0px 6px 15px rgba(0, 0, 0, 0.1);
            margin-top: 25px;
            margin-bottom: 25px;
        }
        .distance-label {
            font-size: 1.1rem;
            color: #555555;
            text-transform: uppercase;
            font-weight: 800;
            letter-spacing: 1px;
            margin-bottom: 4px;
        }
        .distance-number {
            font-size: 2.8rem; 
            color: #1B5E20; 
            font-weight: 900;
            line-height: 1.0;
        }

        /* 3. Native Button Structural Styling Custom Overrides */
        .native-golf-btn {
            width: 100%;
            padding: 20px 10px;
            font-size: 2.8rem !important;
            font-weight: 900;
            border-radius: 16px;
            border: none;
            text-transform: uppercase;
            letter-spacing: -1px;
            color: #FFFFFF !important;
            cursor: pointer;
            display: block;
            margin-bottom: 15px;
            transition: all 0.05s ease-in-out;
        }
        /* Buttons are true solid Green and Blue color blocks now */
        .btn-tee-off {
            background-color: #1B5E20 !important;
            box-shadow: 0px 8px 0px #0A1B0C, 0px 10px 20px rgba(0, 0, 0, 0.3);
        }
        .btn-tee-off:active {
            transform: translateY(4px);
            box-shadow: 0px 4px 0px #0A1B0C, 0px 6px 10px rgba(0, 0, 0, 0.3);
        }
        .btn-at-ball {
            background-color: #0D47A1 !important;
            box-shadow: 0px 8px 0px #051B3D, 0px 10px 20px rgba(0, 0, 0, 0.3);
        }
        .btn-at-ball:active {
            transform: translateY(4px);
            box-shadow: 0px 4px 0px #051B3D, 0px 6px 10px rgba(0, 0, 0, 0.3);
        }
        .btn-disabled {
            background-color: #E0E0E0 !important;
            color: #9E9E9E !important;
            box-shadow: none !important;
            cursor: not-allowed;
            transform: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# 2. Wake up the phone's live GPS coordinates using the correct component parameter
location = get_geolocation(
    component_key=f"gps_tracker_{st.session_state.gps_trigger}"
)

if location is None:
    st.info("🔄 Connecting to iPhone GPS satellites... Please allow location access if prompted.")
elif 'coords' not in location:
    st.warning("⚠️ Waiting for location permissions. Please make sure Safari is allowed to use your GPS.")
else:
    current_lat = location['coords']['latitude']
    current_lon = location['coords']['longitude']

    # --- MID-RUN CALCULATION INTERCEPTOR ---
    if st.session_state.waiting_for_end_gps:
        if current_lat != st.session_state.tee_lat or current_lon != st.session_state.tee_lon:
            lat1, lon1 = math.radians(st.session_state.tee_lat), math.radians(st.session_state.tee_lon)
            lat2, lon2 = math.radians(current_lat), math.radians(current_lon)
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            
            # Calibrated Earth radius multiplier for Yards
            distance_in_yards = round(6975175 * c)
            
            st.session_state.last_calculated_distance = distance_in_yards
            
            shot_number = len(st.session_state.shot_history) + 1
            new_shot = {
                "Shot #": shot_number,
                "Club Used": st.session_state.saved_club,
                "Distance": f"{distance_in_yards} Yards"
            }
            st.session_state.shot_history.append(new_shot)
            
            st.session_state.tee_lat = None
            st.session_state.tee_lon = None
            st.session_state.waiting_for_end_gps = False
            st.toast(f"🚀 Shot tracked: {distance_in_yards} Yards!", icon="🏌️‍♂️")
            st.rerun()

    # 3. Setup Your Shot Layout
    st.subheader("1. Setup Your Shot")
    club_options = [
        "Driver", "Mini-Driver", "3-Wood", "4-Iron", "5-Iron", 
        "6-Iron", "7-Iron", "8-Iron", "9-Iron", "Pitching Wedge", 
        "Gap Wedge", "54° Wedge", "60° Wedge"
    ]
    selected_club = st.selectbox(
        "Which club are you hitting?", 
        options=club_options, 
        index=club_options.index(st.session_state.saved_club) if st.session_state.saved_club in club_options else 0
    )
    st.session_state.saved_club = selected_club

    st.divider()

    # 4. Action Buttons
    st.subheader("2. Track Your Distance")
    
    # Hidden native hooks used to receive actions from our custom color buttons safely
    action_trigger_tee = st.button("INTERNAL_TEE", key="hidden_tee_btn", help="hidden")
    action_trigger_ball = st.button("INTERNAL_BALL", key="hidden_ball_btn", help="hidden")
    
    # Render True solid Green & Blue blocks with matching font scaling text formatting
    tee_disabled = "btn-disabled" if st.session_state.waiting_for_end_gps else ""
    ball_disabled = "btn-disabled" if (st.session_state.tee_lat is None or st.session_state.waiting_for_end_gps) else ""
    
    st.markdown(f"""
        <button id="html-tee-btn" class="native-golf-btn btn-tee-off {tee_disabled}" {"disabled" if tee_disabled else ""}>
            TEE OFF
        </button>
        <button id="html-ball-btn" class="native-golf-btn btn-at-ball {ball_disabled}" {"disabled" if ball_disabled else ""}>
            AT BALL
        </button>
        
        <script>
            // Target the hidden real Streamlit endpoints to fire python logic packets
            const nativeTee = window.parent.document.querySelector('button[aria-label="INTERNAL_TEE"]');
            const nativeBall = window.parent.document.querySelector('button[aria-label="INTERNAL_BALL"]');
            
            document.getElementById('html-tee-btn').addEventListener('click', () => {{
                if(nativeTee) nativeTee.click();
            }});
            document.getElementById('html-ball-btn').addEventListener('click', () => {{
                if(nativeBall) nativeBall.click();
            }});
        </script>
    """, unsafe_allow_html=True)

    # Process clicks arriving from the HTML buttons via the hidden bridge endpoints
    if action_trigger_tee:
        st.session_state.tee_lat = current_lat
        st.session_state.tee_lon = current_lon
        st.session_state.gps_trigger += 1  
        st.session_state.last_calculated_distance = None
        st.rerun()

    if action_trigger_ball:
        st.session_state.waiting_for_end_gps = True
        st.session_state.gps_trigger += 1  
        st.rerun()

    # --- PERSISTENT MAIN-SCREEN DISTANCE PANEL ---
    if st.session_state.last_calculated_distance is not None:
        st.markdown(f"""
            <div class="distance-display-box">
                <div class="distance-label">🏌️‍♂️ Drive Distance</div>
                <div class="distance-number">{st.session_state.last_calculated_distance} YARDS</div>
            </div>
        """, unsafe_allow_html=True)

    # Helper dynamic info status banners
    if st.session_state.waiting_for_end_gps:
        st.info("🛰️ Processing live satellite coordinates... calculating distance.")
    elif st.session_state.tee_lat:
        st.info("🔄 Ball is live. Walk to your shot, stand still for a brief second, then tap **AT BALL**.")
    else:
        st.success("✅ Ready for next shot. Tap **TEE OFF** at your current location.")

    st.divider()

    # Display the History Scorecard Table
    st.subheader("📋 Your Shot History Scorecard")
    if st.session_state.shot_history:
        df = pd.DataFrame(st.session_state.shot_history)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.write("_No shots recorded yet for this round._")

    # 5. Reset Options
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
            st.session_state.tee_lat = None
            st.session_state.tee_lon = None
            st.session_state.waiting_for_end_gps = False
            st.session_state.last_calculated_distance = None
            st.session_state.shot_history = []
            st.session_state.gps_trigger += 1
            st.rerun()




















