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
    st.error("API KEY MISSING IN SECRETS")
    st.stop()

# --- PAGE CONFIG ---
st.set_page_config(page_title="NEO AI", page_icon="⚡", layout="centered")

# --- LOGO LOADER (Fix Path ke Halaman Depan) ---
encoded_logo = ""
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as f:
        encoded_logo = base64.b64encode(f.read()).decode()

# --- ULTRA SMOOTH CSS ---
def get_smooth_css():
    dark = st.session_state.dark_mode
    main_bg = "#0a0a0a" if dark else "#f5f5f7"
    neon_cyan = "#00ffff"
    
    return f"""
    <style>
    /* Global Smooth Transition */
    * {{ transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); }}
    
    .stApp {{ background: {main_bg}; }}

    /* Animation About Box */
    .about-box {{
        background: rgba(0, 255, 255, 0.05);
        border: 1px solid {neon_cyan};
        border-radius: 15px;
        padding: 20px;
        margin-top: 15px;
        animation: expand 0.5s ease-out;
        overflow: hidden;
    }}
    
    @keyframes expand {{
        from {{ transform: scale(0.8); opacity: 0; }}
        to {{ transform: scale(1); opacity: 1; }}
    }}

    /* Logo Hover Effect */
    .big-logo-n {{
        width: 100px; height: 100px; margin: 0 auto;
        background-image: url("data:image/png;base64,{encoded_logo}");
        background-size: contain; background-repeat: no-repeat; background-position: center;
        filter: drop-shadow(0 0 5px {neon_cyan}44);
    }}
    .big-logo-n:hover {{
        transform: rotate(5deg) scale(1.1);
        filter: drop-shadow(0 0 15px {neon_cyan}aa);
    }}

    /* Button Styling Sidebar */
    .stButton button {{
        background: transparent !important;
        border: 1px solid {neon_cyan}44 !important;
        color: {neon_cyan} !important;
        border-radius: 10px !important;
    }}
    .stButton button:hover {{
        background: {neon_cyan}22 !important;
        border: 1px solid {neon_cyan} !important;
        box-shadow: 0 0 10px {neon_cyan}44;
    }}

    /* Title Animation */
    .neon-title {{
        text-align: center; color: {neon_cyan}; font-weight: 900;
        letter-spacing: 5px; text-shadow: 0 0 10px {neon_cyan}55;
    }}

    /* Hide Header Streamlit */
    header {{visibility: hidden;}}
    </style>
    """

st.markdown(get_smooth_css(), unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown('<div class="big-logo-n"></div>', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:#00ffff;'>SYSTEM MENU</h2>", unsafe_allow_html=True)
    
    if st.button("➕ NEW SESSION", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()

    st.markdown("---")
    # History
    for chat_id in list(st.session_state.all_chats.keys()):
        if st.button(f"💬 {chat_id}", key=f"h_{chat_id}", use_container_width=True):
            st.session_state.messages = st.session_state.all_chats[chat_id]
            st.session_state.current_chat_id = chat_id
            st.rerun()

    st.markdown("<div style='height:30vh;'></div>", unsafe_allow_html=True)
    
    if st.button("ℹ️ ABOUT NEO AI", use_container_width=True):
        st.session_state.show_about = not st.session_state.show_about
        st.rerun()

    if st.session_state.show_about:
        st.markdown(f"""
        <div class="about-box">
            <p style='color:cyan; font-weight:bold; margin-bottom:5px;'>NEO INTELLIGENCE v4.0</p>
            <p style='font-size:0.8rem; color:#aaa;'>
                <b>DEVELOPER:</b> Muhammad Jibran Al Kaffie<br>
                <b>STATUS:</b> Operational<br>
                <b>CORE:</b> Llama-3-70B
            </p>
        </div>
        """, unsafe_allow_html=True)

# --- MAIN UI ---
st.markdown('<h1 class="neon-title">NEO AI</h1>', unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- CHAT INPUT ---
if prompt := st.chat_input("COMMAND..."):
    if not st.session_state.messages:
        st.session_state.current_chat_id = prompt[:20]

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        res_area = st.empty()
        full_res = ""
        msgs = [{"role": "system", "content": "Kamu adalah NEO AI, asisten futuristik buatan Muhammad Jibran Al Kaffie."}] + st.session_state.messages
        
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
        except Exception as e:
            st.error(f"SYSTEM OVERLOAD: {e}")
