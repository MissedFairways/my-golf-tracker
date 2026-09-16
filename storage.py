import json
import os
import pandas as pd
import streamlit as st

DATA_FILE = "golf_shot_history.json"

def load_persistent_history():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_persistent_history(history_list):
    with open(DATA_FILE, "w") as f:
        json.dump(history_list, f)

def render_club_averages(shot_history_list):
    if not shot_history_list:
        st.markdown("<div style='background-color: #FFFFFF; border: 3px dashed #000000; padding: 15px; border-radius: 12px; text-align: center;'><p style='color: #555555; font-size: 18px; font-weight: 700; margin: 0;'>🏌️‍♂️ Track shots to calculate your averages!</p></div>", unsafe_allow_html=True)
        return
    try:
        club_data = []
        for shot in shot_history_list:
            raw_dist = str(shot["Distance"]).replace("Yards", "").strip()
            club_data.append({"Club": shot["Club Used"], "Distance": int(raw_dist)})
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
        st.error("Could not compute statistics.")
