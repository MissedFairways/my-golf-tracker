import streamlit as st

def inject_sunlight_styles():
    st.markdown("""
        <style>
            html, body, [data-testid="stAppViewContainer"] {
                background-color: #FFFFFF !important;
                color: #000000 !important;
            }
            div[data-testid="stSelectbox"] label p {
                font-size: 22px !important;
                font-weight: 800 !important;
                color: #111111 !important;
            }
            div[data-testid="stSelectbox"] div[data-baseweb="select"] {
                border: 3px solid #000000 !important;
                border-radius: 8px !important;
                background-color: #FFFFFF !important;
            }
            div[data-testid="stSelectbox"] span {
                font-size: 22px !important;
                font-weight: 700 !important;
                color: #000000 !important;
            }
            button {
                background-color: #2E7D32 !important;
                color: #000000 !important;            
                font-size: 22px !important;
                font-weight: 900 !important;
                letter-spacing: 0.5px !important;
                text-transform: uppercase !important;
                padding: 18px 10px !important;
                border-radius: 12px !important;
                border: 3px solid #000000 !important;
                box-shadow: 6px 6px 0px 0px #000000 !important;
                transition: transform 0.05s ease !important;
            }
            button:disabled {
                background-color: #A5D6A7 !important;
                color: #555555 !important;
                opacity: 0.8 !important;
                cursor: not-allowed !important;
            }
            button:active {
                transform: translate(3px, 3px) !important;
                box-shadow: 3px 3px 0px 0px #000000 !important;
            }
            .distance-display-box {
                background-color: #FFFFFF;
                border: 4px solid #000000;
                border-radius: 16px;
                padding: 20px;
                text-align: center;
                box-shadow: 6px 6px 0px 0px #2E7D32;
                margin-top: 20px;
                margin-bottom: 20px;
            }
            .distance-label {
                font-size: 1.2rem;
                color: #111111;
                text-transform: uppercase;
                font-weight: 900;
                margin-bottom: 4px;
            }
            .distance-number {
                font-size: 3.5rem;
                color: #2E7D32;
                font-weight: 900;
                line-height: 1.0;
            }
        </style>
    """, unsafe_allow_html=True)
