import streamlit as st
from groq import Groq
import time
import os
import base64

# --- SESSION STATE ---
if "all_chats" not in st.session_state:
    st.session_state.all_chats = {}
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "editing_id" not in st.session_state:
    st.session_state.editing_id = None
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
if "show_about" not in st.session_state:
    st.session_state.show_about = False

# --- CONFIG API (Gunakan st.secrets agar aman di Cloud) ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except Exception:
    st.error("API Key belum diset di Secrets!")
    st.stop()

# --- PAGE CONFIG ---
st.set_page_config(page_title="NEO AI", page_icon="⚡", layout="centered")

# --- BASE64 LOGO (Anti-Error) ---
encoded_logo = ""
# Kode ini akan mengecek apakah folder assets dan logo ada
if os.path.exists("assets/logo.png"):
    with open("assets/logo.png", "rb") as f:
        encoded_logo = base64.b64encode(f.read()).decode()

# --- CSS ---
def get_css():
    dark = st.session_state.dark_mode
    main_bg = "#0a0a0a" if dark else "#ffffff"
    main_text = "#e0e0e0" if dark else "#1a1a1a"
    neon_cyan = "#00ffff" if dark else "#008b8b"
    sidebar_bg = "#111111"
    sidebar_text = "#d1d1d1"
    chat_text_color = "#ffffff" if dark else "#000000"
    input_text_color = "#ffffff" if dark else "#000000"
    # Perbaikan logika background input
    input_bg = "rgba(20,20,20,0.9)" if dark else "rgba(245,245,245,0.9)"

    css = f"""
    <style>
    .stApp {{ background-color: {main_bg}; color: {main_text}; transition: all 0.5s; }}
    section[data-testid="stSidebar"] {{ background-color: {sidebar_bg} !important; color: {sidebar_text} !important; }}
    
    .big-logo-n {{
        width: 80px; height: 80px; margin: 10px auto; border-radius: 12px;
        background-image: url("data:image/png;base64,{encoded_logo}");
        background-size: contain; background-repeat: no-repeat; background-position: center;
        box-shadow: 0 0 10px {neon_cyan}33; transition: all 0.5s;
    }}

    .neon-title {{
        text-align: center; font-size: 3rem; font-weight: 900; color: {neon_cyan};
        text-shadow: 0 0 10px {neon_cyan}44; animation: neonPulse 1.5s infinite;
    }}
    @keyframes neonPulse {{ 0%,100%{{text-shadow:0 0 10px {neon_cyan}44;}} 50%{{text-shadow:0 0 25px {neon_cyan}88;}} }}

    .stChatMessage p {{ color: {chat_text_color} !important; }}
    
    div[data-testid="stChatInput"] {{ width: 80% !important; margin: 0 auto !important; }}
    .stChatInput textarea {{
        color: {input_text_color} !important; background-color: {input_bg} !important;
        border-radius: 30px !important; border: 1.5px solid {neon_cyan} !important;
    }}
    </style>
    """
    return css

st.markdown(get_css(), unsafe_allow_html=True)

# --- THEME TOGGLE ---
_, t2 = st.columns([0.9, 0.1])
with t2:
    if st.button("🌙" if st.session_state.dark_mode else "☀️"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown('<div class="big-logo-n"></div>', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center;'>NEO AI</h3>", unsafe_allow_html=True)
    if st.button("NEW SESSION", use_container_width=True):
        st.session_state.messages = []; st.session_state.current_chat_id = None; st.rerun()

    st.markdown("---")
    # Chat History logic
    for chat_id in list(st.session_state.all_chats.keys()):
        if st.button(chat_id, key=f"h_{chat_id}", use_container_width=True):
            st.session_state.current_chat_id = chat_id
            st.session_state.messages = st.session_state.all_chats[chat_id]
            st.rerun()

    if st.button("ABOUT NEO AI", use_container_width=True):
        st.session_state.show_about = not st.session_state.show_about
        st.rerun()
    if st.session_state.show_about:
        st.info("DEVELOPER: Muhammad Jibran Al Kaffie\n\nCORE: Neo-Intelligence v4.0")

# --- MAIN INTERFACE ---
st.markdown('<div class="big-logo-n"></div>', unsafe_allow_html=True)
st.markdown('<h1 class="neon-title">NEO AI</h1>', unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- CHAT INPUT ---
if prompt := st.chat_input("COMMAND..."):
    if not st.session_state.messages:
        st.session_state.current_chat_id = prompt[:20] + "..."

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        res_area = st.empty()
        full_res = ""
        msgs = [{"role": "system", "content": "Kamu adalah NEO AI buatan Muhammad Jibran Al Kaffie."}] + st.session_state.messages
        
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
            st.error(f"Error: {e}")
