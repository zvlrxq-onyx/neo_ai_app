import streamlit as st
from groq import Groq
import time
import os
from dotenv import load_dotenv
import base64

# --- LOAD ENV ---
load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

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

# --- PAGE CONFIG ---
st.set_page_config(page_title="NEO AI", page_icon="⚡", layout="centered")

# --- BASE64 LOGO ---
# Ganti ini dengan base64 PNG-mu
with open("assets/logo.png", "rb") as f:
    logo_bytes = f.read()
encoded_logo = base64.b64encode(logo_bytes).decode()

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

    css = f"""
    <style>
    /* GLOBAL */
    .stApp {{
        background-color: {main_bg};
        color: {main_text};
        transition: background-color 0.5s, color 0.5s;
    }}

    /* SIDEBAR */
    section[data-testid="stSidebar"] {{
        background-color: {sidebar_bg} !important;
        color: {sidebar_text} !important;
        transition: background-color 0.5s, color 0.5s;
    }}

    section[data-testid="stSidebar"] .stButton button {{
        transition: all 0.4s ease;
    }}
    section[data-testid="stSidebar"] .stButton button:hover {{
        transform: scale(1.05);
    }}

    /* LOGO */
    .big-logo-n {{
        width: 80px;
        height: 80px;
        margin: 10px auto;
        border-radius: 12px;
        background-image: url("data:image/png;base64,{encoded_logo}");
        background-size: cover;
        background-position: center;
        box-shadow: 0 0 10px {neon_cyan}33;
        transition: all 0.5s ease-in-out;
        cursor: pointer;
    }}
    .big-logo-n:hover {{
        box-shadow: 0 0 20px {neon_cyan}66;
        transform: scale(1.1);
    }}

    /* TITLE */
    .neon-title {{
        text-align: center;
        font-size: 3rem;
        font-weight: 900;
        color: {neon_cyan};
        text-shadow: 0 0 10px {neon_cyan}44, 0 0 20px {neon_cyan}22;
        animation: neonPulse 1.5s infinite ease-in-out;
    }}
    @keyframes neonPulse {{
        0%,100%{{text-shadow:0 0 10px {neon_cyan}44,0 0 20px {neon_cyan}22;}}
        50%{{text-shadow:0 0 25px {neon_cyan}88,0 0 40px {neon_cyan}44;}}
    }}

    /* CHAT */
    .stChatMessage p {{ color: {chat_text_color} !important; }}

    /* CHAT INPUT */
    div[data-testid="stChatInput"] {{
        transition: width 0.5s ease, box-shadow 0.5s ease;
        width: 80% !important;
        margin: 0 auto !important;
    }}
    div[data-testid="stChatInput"]:focus-within {{
        width: 100% !important;
        box-shadow: 0 0 25px {neon_cyan}44, 0 5px 15px {neon_cyan}22;
    }}
    .stChatInput textarea {{
        color: {input_text_color} !important;
        border-radius: 30px !important;
        border: 1.5px solid {neon_cyan} !important;
        padding: 12px 20px !important;
        background-color: rgba(20,20,20,0.9) if {str(dark).lower()} else rgba(255,255,255,0.9) !important;
    }}

    /* ABOUT */
    .about-text {{
        font-size:0.85rem;
        line-height:1.5;
        color:#888;
        padding:10px;
        border-top:1px solid {neon_cyan};
        margin-top:10px;
        transition: all 0.5s ease-in-out;
    }}
    </style>
    """
    return css

st.markdown(get_css(), unsafe_allow_html=True)

# --- THEME TOGGLE ---
t1, t2 = st.columns([0.9, 0.1])
with t2:
    label = "🌙" if st.session_state.dark_mode else "☀️"
    if st.button(label, key="theme_toggle"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown('<div class="big-logo-n"></div>', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center;'>NEO AI</h3>", unsafe_allow_html=True)

    if st.button("NEW SESSION", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.session_state.editing_id = None
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # CHAT HISTORY
    if not isinstance(st.session_state.all_chats, dict):
        st.session_state.all_chats = {}
    for chat_id in list(st.session_state.all_chats.keys()):
        c1, c2 = st.columns([0.8, 0.2])
        with c1:
            if st.button(chat_id, key=f"h_{chat_id}", use_container_width=True):
                st.session_state.current_chat_id = chat_id
                st.session_state.messages = st.session_state.all_chats[chat_id]
                st.rerun()
        with c2:
            if st.button("✎", key=f"ed_{chat_id}"):
                st.session_state.editing_id = chat_id

    if st.session_state.editing_id:
        new_name = st.text_input("RENAME TO:", key="rename_input")
        if st.button("SAVE"):
            st.session_state.all_chats[new_name] = st.session_state.all_chats.pop(st.session_state.editing_id)
            st.session_state.editing_id = None
            st.rerun()

    st.markdown("<div style='height:40vh;'></div>", unsafe_allow_html=True)
    if st.button("ABOUT NEO AI", use_container_width=True):
        st.session_state.show_about = not st.session_state.show_about
        st.rerun()
    
    if st.session_state.show_about:
        st.markdown(f"""
        <div class="about-text">
            <b>DEVELOPER</b><br>Muhammad Jibran Al Kaffie<br><br>
            <b>CORE ENGINE</b><br>Neo-Intelligence v4.0<br><br>
            <b>OBJECTIVE</b><br>High-performance AI assistant for advanced technical operations and analysis.
        </div>
        """, unsafe_allow_html=True)

# --- MAIN ---
st.markdown('<div class="big-logo-n"></div>', unsafe_allow_html=True)
st.markdown('<h1 class="neon-title">NEO AI</h1>', unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- CHAT INPUT ---
if prompt := st.chat_input("COMMAND..."):
    st.components.v1.html(
        """<script>parent.document.querySelectorAll('textarea').forEach(el => el.setAttribute('spellcheck', 'false'));</script>""",
        height=0
    )

    if not st.session_state.messages:
        words = prompt.split()[:3]
        temp_id = " ".join(words) + ("..." if len(prompt.split()) > 3 else "")
        st.session_state.current_chat_id = temp_id

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
                    time.sleep(0.01)
            res_area.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            if st.session_state.current_chat_id not in st.session_state.all_chats:
                st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages
        except:
            st.error("SYSTEM OVERLOAD")
    st.rerun()
