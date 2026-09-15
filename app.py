# 2. Wake up the phone's live GPS coordinates using the correct component parameter
location = get_geolocation(component_key=f"gps_tracker_{st.session_state.gps_trigger}")

if location is None:
    st.info("🔄 Connecting to iPhone GPS satellites... Please allow location access if prompted.")
elif 'coords' not in location:
    st.warning("⚠️ Waiting for location permissions. Please make sure Safari is allowed to use your GPS.")
else:
    current_lat = location['coords']['latitude']
    current_lon = location['coords']['longitude']
    # Pull accuracy radius (in meters) directly from iPhone GPS hardware
    gps_accuracy = location['coords'].get('accuracy', 999)

    # --- MID-RUN CALCULATION INTERCEPTOR ---
    if st.session_state.waiting_for_end_gps:
        # HIGH-ACCURACY GATEKEEPER: If the phone is returning a cached or weak signal (> 25 meters), 
        # force the app to cycle the hardware again until a tight satellite lock is achieved.
        if gps_accuracy > 25:
            st.toast("🛰️ Signal weak or cached. Polling satellites for precise location...", icon="⏳")
            time.sleep(0.5)
            st.session_state.gps_trigger += 1
            st.rerun()

        if current_lat != st.session_state.tee_lat or current_lon != st.session_state.tee_lon:
            lat1, lon1 = math.radians(st.session_state.tee_lat), math.radians(st.session_state.tee_lon)
            lat2, lon2 = math.radians(current_lat), math.radians(current_lon)
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            
            # FIXED MATHEMATICAL CONSTANT: Standard global Earth radius converted strictly to Yards
            distance_in_yards = round(6967410 * c)
            
            # Prevent microscopic GPS drift from logging accidental 0-2 yard phantom shots
            if distance_in_yards > 3:
                st.session_state.last_calculated_distance = distance_in_yards
                
                # Save the shot data to your history memory list
                shot_number = len(st.session_state.shot_history) + 1
                new_shot = {
                    "Shot #": shot_number,
                    "Club Used": st.session_state.saved_club,
                    "Distance": f"{distance_in_yards} Yards"
                }
                st.session_state.shot_history.append(new_shot)
                
                # Lock the new shot into permanent disk memory
                save_persistent_history(st.session_state.shot_history)
            else:
                st.toast("⚠️ Distance too short. Measurement ignored to prevent tracking drift.", icon="🛑")
            
            # Clear targeting state so you can hit your next shot smoothly
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
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="green-action-btn">', unsafe_allow_html=True)
        if st.button("🔴 Click 1: Just Teed Off", use_container_width=True, disabled=st.session_state.waiting_for_end_gps):
            # Only save tee location if the GPS signal is fresh and reasonably accurate
            if gps_accuracy <= 25:
                st.session_state.tee_lat = current_lat
                st.session_state.tee_lon = current_lon
                st.session_state.gps_trigger += 1  
                st.session_state.last_calculated_distance = None
                st.toast(f"🎯 Tee location saved for your {selected_club}!", icon="📍")
                st.rerun()
            else:
                st.toast("🛰️ Waiting for crisp satellite alignment... Try tapping again in a second.", icon="⏳")
                st.session_state.gps_trigger += 1
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="blue-action-btn">', unsafe_allow_html=True)
        if st.button("⚪ Click 2: At My Ball", use_container_width=True, disabled=(st.session_state.tee_lat is None or st.session_state.waiting_for_end_gps)):
            with st.spinner("Locking Satellite Array..."):
                time.sleep(2.0)
            st.session_state.waiting_for_end_gps = True
            st.session_state.gps_trigger += 1  
            st.toast("🛰️ Fetching fresh location...", icon="🔄")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- PERSISTENT MAIN-SCREEN DISTANCE PANEL ---
    if st.session_state.last_calculated_distance is not None:
        st.markdown(f"""
            <div class="distance-display-box">
                <div class="distance-label">🏌️‍♂️ Last Shot Distance</div>
                <div class="distance-number">{st.session_state.last_calculated_distance} YARDS</div>
            </div>
        """, unsafe_allow_html=True)

    # Helper dynamic info status banners with real-time GPS accuracy display
    if st.session_state.waiting_for_end_gps:
        st.info("🛰️ Processing live satellite coordinates... calculating distance.")
    elif st.session_state.tee_lat:
        st.info(f"🔄 Ball is live. Walk to your shot, stand still for a brief second, then tap **Click 2: At My Ball**.")
    else:
        accuracy_text = f" (Signal Accuracy: +/- {round(gps_accuracy)}m)" if gps_accuracy != 999 else ""
        st.success(f"✅ Ready for next shot. Tap **Click 1: Just Teed Off** at your current location.{accuracy_text}")

    st.divider()

    # Display the History Scorecard Table
    st.subheader("📋 Your Shot History Scorecard")
    shot_history_list = st.session_state.shot_history
    
    if shot_history_list:
        df = pd.DataFrame(shot_history_list)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.write("_No shots recorded yet for this round._")

    # --- CLUB AVERAGES TRACKER ---
    st.divider()
    st.subheader("📊 Your Club Averages")

    if not shot_history_list:
        st.markdown("""
            <div style='background-color: #FFFFFF; border: 3px dashed #000000; padding: 15px; border-radius: 12px; text-align: center;'>
                <p style='color: #555555; font-size: 18px; font-weight: 700; margin: 0;'>🏌️‍♂️ Track a few shots above to calculate your personal club averages!</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        try:
            club_data = []
            for shot in shot_history_list:
                raw_dist = str(shot["Distance"]).replace("Yards", "").strip()
                dist_numeric = int(raw_dist)
                club_data.append({"Club": shot["Club Used"], "Distance": dist_numeric})
            
            math_df = pd.DataFrame(club_data)
            avg_df = math_df.groupby("Club")["Distance"].mean().round().astype(int).reset_index()
            avg_df = avg_df.sort_values(by="Distance", ascending=False)
            
            for index, row in avg_df.iterrows():
                st.markdown(f"""
                    <div style='background-color: #FFFFFF; border: 3px solid #000000; border-radius: 12px; padding: 12px 20px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; box-shadow: 4px 4px 0px 0px #000000;'>
                        <span style='font-size: 20px; font-weight: 900; color: #000000;'>{row['Club']}</span>
                        <span style='font-size: 22px; font-weight: 900; color: #2E7D32;'>{row['Distance']} YARDS</span>
                    </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.error("Could not compute club statistics right now.")

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
            save_persistent_history([])
            st.session_state.gps_trigger += 1
            st.rerun()
























