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

# --- 5. ULTRA PREMIUM CSS (ANTI-FLASH & SMOOTH) ---
def get_pro_css():
    neon_cyan = "#00ffff"
    return f"""
    <style>
    html, body, [data-testid="stAppViewContainer"], .stApp {{
        background-color: #080808 !important;
        color: #e0e0e0 !important;
    }}
    [data-testid="stStatusWidget"] {{ display: none; }}
    * {{ transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275); }}

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
        font-weight: 900; letter-spacing: 12px; margin-bottom: 5px;
        text-transform: uppercase; text-shadow: 0 0 20px {neon_cyan}44;
    }}

    section[data-testid="stSidebar"] {{ background-color: #050505 !important; border-right: 1px solid {neon_cyan}22; }}
    .stButton > button {{
        background: transparent !important; color: #ffffff !important;
        border: 1px solid {neon_cyan}44 !important; border-radius: 30px !important; width: 100% !important;
    }}
    .stButton > button:hover {{
        transform: scale(1.08) !important; border-color: {neon_cyan} !important;
        background: rgba(0, 255, 255, 0.12) !important; box-shadow: 0 0 25px {neon_cyan}66 !important;
    }}

    div[data-testid="stChatInput"] {{
        width: 75% !important; margin: 0 auto !important;
        transition: width 0.9s cubic-bezier(0.23, 1, 0.32, 1) !important;
    }}
    div[data-testid="stChatInput"]:focus-within {{ width: 100% !important; }}
    .stChatInput textarea {{ border-radius: 30px !important; background: #111 !important; border: 1px solid {neon_cyan}22 !important; }}

    .fluid-box {{
        background: linear-gradient(145deg, rgba(0, 255, 255, 0.05), rgba(0, 0, 0, 0.2));
        border: 1px solid {neon_cyan}33; border-left: 5px solid {neon_cyan};
        border-radius: 20px; padding: 20px; margin-top: 20px;
        animation: fluidSlide 0.7s cubic-bezier(0.23, 1, 0.32, 1);
        backdrop-filter: blur(10px);
    }}
    @keyframes fluidSlide {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}

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
    
    # Render History & Rename
    for chat_id in reversed(list(st.session_state.all_chats.keys())):
        display_name = chat_id.split(" | ")[0]
        col_m, col_e = st.columns([0.8, 0.2])
        with col_m:
            if st.button(display_name, key=f"h_{chat_id}", use_container_width=True):
                st.session_state.messages = st.session_state.all_chats[chat_id]
                st.session_state.current_chat_id = chat_id
                st.rerun()
        with col_e:
            if st.button("✏️", key=f"e_{chat_id}"):
                st.session_state.editing_chat_id = chat_id
                st.rerun()

    if st.session_state.editing_chat_id:
        st.markdown('<div class="fluid-box">', unsafe_allow_html=True)
        new_name = st.text_input("RENAME:", value=st.session_state.editing_chat_id.split(" | ")[0])
        c1, c2 = st.columns(2)
        with c1:
            if st.button("SAVE"):
                suffix = st.session_state.editing_chat_id.split(" | ")[1]
                new_full_id = f"{new_name} | {suffix}"
                st.session_state.all_chats[new_full_id] = st.session_state.all_chats.pop(st.session_state.editing_chat_id)
                st.session_state.editing_chat_id = None
                st.rerun()
        with c2:
            if st.button("BACK"):
                st.session_state.editing_chat_id = None
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:10vh;'></div>", unsafe_allow_html=True)
    if st.button("ABOUT NEO", use_container_width=True):
        st.session_state.show_about = not st.session_state.show_about
        st.rerun()

    if st.session_state.show_about:
        st.markdown(f'<div class="fluid-box"><b>Architect:</b> Jibran Al Kaffie<br><b>Engine:</b> Llama-3.3</div>', unsafe_allow_html=True)

# --- 7. MAIN INTERFACE ---
st.markdown(f"""
    <div class="center-container">
        <div class="logo-circle"></div>
        <h1 class="neon-title">NEO AI</h1>
        <p style="text-align:center; opacity:0.8; font-size:1.3rem; margin-top: 10px;">
            Hi, is there anything I can help you with?
        </p>
    </div>
""", unsafe_allow_html=True)

# Tampilkan chat yang sudah ada
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 8. CHAT LOGIC (FIXED) ---
if prompt := st.chat_input("ENTER COMMAND..."):
    # Buat ID Chat baru jika belum ada
    if st.session_state.current_chat_id is None:
        st.session_state.current_chat_id = f"{prompt[:20]}... | {time.time()}"
    
    # Tambah chat user ke memori
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Tampilkan chat user langsung
    with st.chat_message("user"):
        st.markdown(prompt)

    # Proses jawaban AI
    with st.chat_message("assistant"):
        res_area = st.empty()
        full_res = ""
        msgs = [{"role": "system", "content": "You are NEO AI by Jibran."}] + st.session_state.messages
        
        try:
            # Streaming dari Groq
            completion = client.chat.completions.create(messages=msgs, model="llama-3.3-70b-versatile", stream=True)
            for chunk in completion:
                content = chunk.choices[0].delta.content
                if content:
                    full_res += content
                    res_area.markdown(full_res + "▌")
            res_area.markdown(full_res)
            
            # Simpan jawaban AI ke memori
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages
        except Exception as e:
            st.error(f"ERROR: {e}")

    # Rerun hanya setelah semua data tersimpan
    st.rerun()
