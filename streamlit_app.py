import streamlit as st
from groq import Groq
import time
import os
import base64

# --- 1. INITIALIZE SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "all_chats" not in st.session_state: st.session_state.all_chats = {}
if "current_chat_id" not in st.session_state: st.session_state.current_chat_id = None
if "show_about" not in st.session_state: st.session_state.show_about = False
if "editing_chat_id" not in st.session_state: st.session_state.editing_chat_id = None

# --- 2. CONFIG API ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except:
    st.error("SYSTEM ERROR: API KEY NOT FOUND")
    st.stop()

# --- 3. PAGE CONFIG ---
st.set_page_config(page_title="NEO AI", page_icon="⚡", layout="centered")

# --- 4. OPTIMIZED LOGO LOADER ---
@st.cache_data
def get_base64_logo():
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

encoded_logo = get_base64_logo()

# --- 5. ULTRA PREMIUM CSS (ANTI-FLASH & SMOOTH EDITION) ---
def get_pro_css():
    neon_cyan = "#00ffff"
    return f"""
    <style>
    /* KUNCI UTAMA ANTI-KEDIP */
    html, body, [data-testid="stAppViewContainer"], .stApp {{
        background-color: #080808 !important;
        color: #e0e0e0 !important;
    }}
    
    /* Hilangkan animasi loading standar Streamlit yang bikin kedip */
    [data-testid="stStatusWidget"] {{ display: none; }}

    /* GLOBAL SMOOTH TRANSITION */
    * {{ transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1); }}

    /* Logo Statis */
    .center-container {{ display: flex; flex-direction: column; align-items: center; justify-content: center; margin-bottom: 20px; }}
    .logo-circle {{
        width: 125px; height: 125px;
        background-image: url("data:image/png;base64,{encoded_logo}");
        background-size: cover; background-position: center;
        border-radius: 50%; border: 2px solid {neon_cyan};
        box-shadow: 0 0 30px {neon_cyan}33;
    }}
    
    .neon-title {{
        text-align: center; color: {neon_cyan}; font-size: 3.5rem; 
        font-weight: 900; letter-spacing: 12px; margin-bottom: 10px;
        text-transform: uppercase; text-shadow: 0 0 20px {neon_cyan}44;
    }}

    /* SIDEBAR & HOVER SMOOTH */
    section[data-testid="stSidebar"] {{ 
        background-color: #050505 !important; 
        border-right: 1px solid {neon_cyan}22; 
    }}

    .stButton > button {{
        background: transparent !important;
        color: #ffffff !important;
        border: 1px solid {neon_cyan}44 !important;
        border-radius: 30px !important;
        padding: 10px 20px !important;
        width: 100% !important;
        transform: scale(1);
    }}

    .stButton > button:hover {{
        transform: scale(1.06) !important;
        border-color: {neon_cyan} !important;
        background: rgba(0, 255, 255, 0.1) !important;
        box-shadow: 0 0 20px {neon_cyan}55 !important;
    }}

    /* CHAT INPUT EXPAND SMOOTH */
    div[data-testid="stChatInput"] {{
        width: 75% !important; 
        margin: 0 auto !important;
        transition: width 0.8s cubic-bezier(0.19, 1, 0.22, 1) !important;
    }}
    div[data-testid="stChatInput"]:focus-within {{ width: 100% !important; }}
    .stChatInput textarea {{ 
        border-radius: 30px !important; 
        background: #111 !important;
        border: 1px solid {neon_cyan}22 !important;
    }}

    /* Fluid Boxes */
    .fluid-box {{
        background: rgba(0, 255, 255, 0.03);
        border: 1px solid {neon_cyan}22;
        border-radius: 20px; padding: 15px; margin-top: 15px;
        animation: fluidIn 0.4s ease-out;
    }}
    @keyframes fluidIn {{ from {{ opacity: 0; transform: scale(0.98); }} to {{ opacity: 1; transform: scale(1); }} }}

    header, footer {{ visibility: hidden; }}
    </style>
    """

st.markdown(get_pro_css(), unsafe_allow_html=True)

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown(f'<div class="center-container"><div class="logo-circle"></div></div>', unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align:center; color:#00ffff; letter-spacing:5px; font-size:2.2rem; text-shadow: 0 0 10px #00ffff; margin-bottom:20px;'>NEO AI</h1>", unsafe_allow_html=True)
    
    if st.button("NEW SESSION", key="btn_new", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()

    st.markdown("---")
    
    for chat_id in reversed(list(st.session_state.all_chats.keys())):
        display_name = chat_id.split(" | ")[0]
        c1, c2 = st.columns([0.8, 0.2])
        with c1:
            if st.button(display_name, key=f"h_{chat_id}", use_container_width=True):
                st.session_state.messages = st.session_state.all_chats[chat_id]
                st.session_state.current_chat_id = chat_id
                st.rerun()
        with c2:
            if st.button("✏️", key=f"e_{chat_id}"):
                st.session_state.editing_chat_id = chat_id
                st.rerun()

    if st.button("ABOUT", key="btn_about", use_container_width=True):
        st.session_state.show_about = not st.session_state.show_about
        st.rerun()

    if st.session_state.show_about:
        st.markdown(f'<div class="fluid-box"><b>Architect:</b> Jibran Al Kaffie<br><b>Engine:</b> Llama-3.3</div>', unsafe_allow_html=True)

# --- 7. MAIN INTERFACE ---
st.markdown(f'<div class="center-container"><div class="logo-circle"></div><h1 class="neon-title">NEO AI</h1></div>', unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 8. CHAT LOGIC ---
if prompt := st.chat_input("COMMAND..."):
    if st.session_state.current_chat_id is None:
        st.session_state.current_chat_id = f"{prompt[:20]}... | {time.time()}"
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()
