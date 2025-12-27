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

# --- 5. ULTRA PREMIUM CSS (ELASTIC & SMOOTH EDITION) ---
def get_pro_css():
    neon_cyan = "#00ffff"
    return f"""
    <style>
    /* ANTI-FLASH: Kunci warna background agar tidak kedip */
    html, body, [data-testid="stAppViewContainer"], .stApp {{
        background-color: #080808 !important;
        color: #e0e0e0 !important;
    }}
    
    [data-testid="stStatusWidget"] {{ display: none; }}

    /* GLOBAL TRANSITION: Efek kenyal (elastic) */
    * {{ transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275); }}

    /* Logo & Title */
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

    /* SIDEBAR BUTTONS HOVER */
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
    }}

    .stButton > button:hover {{
        transform: scale(1.08) !important;
        border-color: {neon_cyan} !important;
        background: rgba(0, 255, 255, 0.12) !important;
        box-shadow: 0 0 25px {neon_cyan}66 !important;
        color: {neon_cyan} !important;
    }}

    /* CHAT INPUT EXPAND SMOOTH */
    div[data-testid="stChatInput"] {{
        width: 75% !important; 
        margin: 0 auto !important;
        transition: width 0.9s cubic-bezier(0.23, 1, 0.32, 1) !important;
    }}
    div[data-testid="stChatInput"]:focus-within {{ width: 100% !important; }}
    .stChatInput textarea {{ border-radius: 30px !important; background: #111 !important; border: 1px solid {neon_cyan}22 !important; }}

    /* ABOUT BOX - SUPER SMOOTH & DETAILED */
    .about-box {{
        background: linear-gradient(145deg, rgba(0, 255, 255, 0.05), rgba(0, 0, 0, 0.2));
        border: 1px solid {neon_cyan}33;
        border-left: 5px solid {neon_cyan};
        border-radius: 20px;
        padding: 20px;
        margin-top: 20px;
        animation: aboutSlide 0.7s cubic-bezier(0.23, 1, 0.32, 1);
        backdrop-filter: blur(10px);
    }}
    
    @keyframes aboutSlide {{
        from {{ opacity: 0; transform: translateY(30px) scale(0.9); filter: blur(10px); }}
        to {{ opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }}
    }}

    .about-title {{ color: {neon_cyan}; font-weight: 800; font-size: 1.1rem; letter-spacing: 2px; margin-bottom: 10px; }}
    .about-content {{ color: #ccc; font-size: 0.85rem; line-height: 1.6; }}
    .about-tag {{ display: inline-block; background: {neon_cyan}22; color: {neon_cyan}; padding: 2px 8px; border-radius: 5px; font-size: 0.7rem; margin-top: 10px; font-weight: bold; }}

    header, footer {{ visibility: hidden; }}
    </style>
    """

st.markdown(get_pro_css(), unsafe_allow_html=True)

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown(f'<div class="center-container"><div class="logo-circle"></div></div>', unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align:center; color:#00ffff; letter-spacing:5px; font-size:2.2rem; text-shadow: 0 0 10px #00ffff; margin-bottom:20px;'>NEO AI</h1>", unsafe_allow_html=True)
    
    if st.button("NEW SESSION", key="new_sess", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()

    st.markdown("---")
    
    # History List
    for chat_id in reversed(list(st.session_state.all_chats.keys())):
        display_name = chat_id.split(" | ")[0]
        if st.button(display_name, key=f"h_{chat_id}", use_container_width=True):
            st.session_state.messages = st.session_state.all_chats[chat_id]
            st.session_state.current_chat_id = chat_id
            st.rerun()

    st.markdown("<div style='height:10vh;'></div>", unsafe_allow_html=True)
    
    if st.button("ABOUT NEO", key="about_btn", use_container_width=True):
        st.session_state.show_about = not st.session_state.show_about
        st.rerun()

    # DETAILED ABOUT WITH SMOOTH ANIMATION
    if st.session_state.show_about:
        st.markdown(f"""
        <div class="about-box">
            <div class="about-title">SYSTEM ARCHITECTURE</div>
            <div class="about-content">
                NEO AI is a custom-built neural interface developed by <b>Muhammad Jibran Al Kaffie</b>. 
                Utilizing the <b>Llama-3.3-70B</b> engine, it delivers high-performance reasoning, 
                computational analysis, and creative synthesis.
                <br><br>
                Designed for speed, the interface features a <b>Fluid-UI</b> system that ensures 
                seamless transitions and an immersive dark-core experience.
            </div>
            <div class="about-tag">V 2.0 - STABLE</div>
            <div class="about-tag">NEURAL-LINK: ACTIVE</div>
        </div>
        """, unsafe_allow_html=True)

# --- 7. MAIN INTERFACE ---
st.markdown(f'<div class="center-container"><div class="logo-circle"></div><h1 class="neon-title">NEO AI</h1><p style="text-align:center; opacity:0.7; font-size:1.2rem;">Hi, is there anything I can help you with?</p></div>', unsafe_allow_html=True)

# Container for Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 8. CHAT LOGIC ---
if prompt := st.chat_input("ENTER COMMAND..."):
    if st.session_state.current_chat_id is None:
        st.session_state.current_chat_id = f"{prompt[:20]}... | {time.time()}"
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        res_area = st.empty()
        full_res = ""
        msgs = [{"role": "system", "content": "You are NEO AI, a high-level assistant created by Muhammad Jibran Al Kaffie. Be concise, sharp, and helpful."}] + st.session_state.messages
        
        try:
            comp = client.chat.completions.create(messages=msgs, model="llama-3.3-70b-versatile", stream=True)
            for chunk in comp:
                content = chunk.choices[0].delta.content
                if content:
                    full_res += content
                    res_area.markdown(full_res + "▌")
            res_area.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages
        except:
            st.error("CONNECTION INTERRUPTED")
            
    st.rerun()
