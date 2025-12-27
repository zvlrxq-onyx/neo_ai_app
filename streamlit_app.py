import streamlit as st
from groq import Groq
import time
import os
import base64

# --- SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "all_chats" not in st.session_state: st.session_state.all_chats = {}
if "current_chat_id" not in st.session_state: st.session_state.current_chat_id = None
if "dark_mode" not in st.session_state: st.session_state.dark_mode = True
if "show_about" not in st.session_state: st.session_state.show_about = False

# --- CONFIG API ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except:
    st.error("API KEY MISSING")
    st.stop()

# --- PAGE CONFIG ---
st.set_page_config(page_title="NEO AI", page_icon="⚡", layout="centered")

# --- LOGO LOADER ---
encoded_logo = ""
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as f:
        encoded_logo = base64.b64encode(f.read()).decode()

# --- ULTRA PREMIUM CSS ---
def get_pro_css():
    neon_cyan = "#00ffff"
    return f"""
    <style>
    /* Global Smoothness */
    * {{ transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275); }}
    
    .stApp {{ background: #0a0a0a; }}

    /* Logo Bulat di Tengah */
    .center-logo {{
        display: flex; justify-content: center; margin-bottom: 20px;
    }}
    .logo-circle {{
        width: 120px; height: 120px;
        background-image: url("data:image/png;base64,{encoded_logo}");
        background-size: cover; background-position: center;
        border-radius: 50%;
        border: 2px solid {neon_cyan};
        box-shadow: 0 0 20px {neon_cyan}44;
    }}
    .logo-circle:hover {{
        transform: scale(1.1) rotate(5deg);
        box-shadow: 0 0 40px {neon_cyan};
    }}

    /* Title */
    .neon-title {{
        text-align: center; color: {neon_cyan}; font-size: 3.5rem; 
        font-weight: 900; letter-spacing: 10px; margin-bottom: 50px;
        text-transform: uppercase;
    }}

    /* Chat Input Animasi Memanjang */
    div[data-testid="stChatInput"] {{
        width: 70% !important; margin: 0 auto !important;
        transition: width 0.7s cubic-bezier(0.19, 1, 0.22, 1) !important;
    }}
    div[data-testid="stChatInput"]:focus-within {{
        width: 100% !important;
    }}
    .stChatInput textarea {{
        border-radius: 25px !important;
        border: 1px solid {neon_cyan}44 !important;
        background-color: rgba(20, 20, 20, 0.8) !important;
    }}

    /* About Box Smooth & Professional */
    .about-box {{
        background: rgba(0, 255, 255, 0.03);
        border-left: 3px solid {neon_cyan};
        border-radius: 4px 15px 15px 4px; 
        padding: 25px;
        margin-top: 15px;
        animation: scaleIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }}
    
    @keyframes scaleIn {{
        from {{ transform: scale(0.9); opacity: 0; }}
        to {{ transform: scale(1); opacity: 1; }}
    }}

    .about-title {{
        color: {neon_cyan}; font-size: 1.2rem; font-weight: 800; 
        margin-bottom: 15px; letter-spacing: 2px;
    }}
    .about-content {{
        color: #d1d1d1; font-size: 0.9rem; line-height: 1.6;
    }}

    /* Button Styling */
    .stButton button {{
        background: transparent !important;
        border: 1px solid {neon_cyan}33 !important;
        color: #fff !important;
        border-radius: 8px !important;
        letter-spacing: 1px !important;
    }}
    .stButton button:hover {{
        transform: scale(1.02) !important;
        background: {neon_cyan}11 !important;
        border-color: {neon_cyan} !important;
        box-shadow: 0 0 15px {neon_cyan}33;
    }}

    header {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    </style>
    """

st.markdown(get_pro_css(), unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f'<div class="center-logo"><div class="logo-circle"></div></div>', unsafe_allow_html=True)
    if st.button("NEW SESSION", use_container_width=True):
        st.session_state.messages = []; st.rerun()

    st.markdown("---")
    for chat_id in list(st.session_state.all_chats.keys()):
        if st.button(chat_id, key=f"h_{chat_id}", use_container_width=True):
            st.session_state.messages = st.session_state.all_chats[chat_id]
            st.rerun()

    st.markdown("<div style='height:20vh;'></div>", unsafe_allow_html=True)
    
    if st.button("ABOUT NEO AI", use_container_width=True):
        st.session_state.show_about = not st.session_state.show_about
        st.rerun()

    if st.session_state.show_about:
        st.markdown(f"""
        <div class="about-box">
            <div class="about-title">PROJECT SPECIFICATION</div>
            <div class="about-content">
                <b>NEO AI v4.0</b> is a high-performance artificial intelligence interface developed by 
                <b>Muhammad Jibran Al Kaffie</b>. 
                <br><br>
                This system utilizes <b>Neo-Intelligence Architecture</b> combined with <b>Llama-3.3-70B</b> core 
                to provide advanced technical analysis, creative synthesis, and real-time problem-solving capabilities. 
                Designed for speed and precision, NEO AI represents the intersection of futuristic aesthetics and 
                functional computing.
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- MAIN UI ---
st.markdown(f'<div class="center-logo"><div class="logo-circle"></div></div>', unsafe_allow_html=True)
st.markdown('<h1 class="neon-title">NEO AI</h1>', unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- CHAT INPUT ---
if prompt := st.chat_input("COMMAND..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        res_area = st.empty(); full_res = ""
        msgs = [{"role": "system", "content": "Kamu adalah NEO AI, asisten virtual canggih buatan Muhammad Jibran Al Kaffie. Jawablah dengan nada futuristik dan profesional."}] + st.session_state.messages
        try:
            comp = client.chat.completions.create(messages=msgs, model="llama-3.3-70b-versatile", stream=True)
            for chunk in comp:
                content = chunk.choices[0].delta.content
                if content:
                    full_res += content
                    res_area.markdown(full_res + "▌")
            res_area.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            st.session_state.all_chats[prompt[:20]] = st.session_state.messages
        except: st.error("CONNECTION ERROR: SYSTEM OVERLOAD")
