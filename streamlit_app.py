import streamlit as st
from groq import Groq
import time
import os
import base64
import requests

# --- 1. INITIALIZE SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "all_chats" not in st.session_state: st.session_state.all_chats = {}
if "current_chat_id" not in st.session_state: st.session_state.current_chat_id = None
if "imagine_mode" not in st.session_state: st.session_state.imagine_mode = False
if "show_about" not in st.session_state: st.session_state.show_about = False
if "sidebar_visible" not in st.session_state: st.session_state.sidebar_visible = False

# --- 2. CONFIG API ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except:
    st.error("API Key Groq missing!")
    st.stop()

# --- 3. PAGE CONFIG ---
st.set_page_config(page_title="NEO AI", page_icon="⚡", layout="centered")

# --- 4. CACHED ASSETS (Penting agar tidak reload gambar tiap detik) ---
@st.cache_data
def get_base64_logo():
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

encoded_logo = get_base64_logo()
logo_html = f'data:image/png;base64,{encoded_logo}'

# --- 5. THE ANTI-FLICKER & ULTRA SMOOTH CSS ---
def get_ultimate_css():
    neon_cyan = "#00ffff"
    sidebar_pos = "0" if st.session_state.sidebar_visible else "-350px"
    
    return f"""
    <style>
    /* MENGUNCI BACKGROUND AGAR TIDAK FLICKER SAAT RERUN */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        background-color: #080808 !important;
        color: #e0e0e0 !important;
    }}

    /* MENGHILANGKAN LOADING SPINNER BAWAAN YANG BIKIN KEDIP */
    [data-testid="stStatusWidget"] {{
        visibility: hidden;
        display: none !important;
    }}

    /* TRANSISI HALUS UNTUK SELURUH ELEMEN */
    * {{
        transition: background-color 0s, opacity 0.3s ease-in-out;
    }}

    /* CUSTOM SIDEBAR DENGAN TRANSFORM (SMOOTH) */
    [data-testid="stSidebar"] {{
        left: {sidebar_pos} !important;
        transition: transform 0.5s cubic-bezier(0.19, 1, 0.22, 1) !important;
        background-color: #0a0a0a !important;
        border-right: 1px solid {neon_cyan}33 !important;
        z-index: 1000000 !important;
    }}

    /* HAMBURGER BUTTON FIX POSITION */
    .stButton > button[key="hamburger"] {{
        position: fixed;
        top: 20px;
        left: 20px;
        z-index: 1000001;
        background: rgba(0,0,0,0.7) !important;
        border: 1.5px solid {neon_cyan}55 !important;
        border-radius: 12px !important;
        width: 45px !important;
        height: 45px !important;
    }}

    .ham-line {{
        width: 20px; height: 2px; background: {neon_cyan};
        margin: 3px 0; border-radius: 2px; display: block;
    }}

    /* AVATAR & IMAGE STYLING */
    [data-testid="stChatMessage"] div[data-testid="stChatAvatar"] img {{
        border-radius: 50% !important;
        border: 1.5px solid {neon_cyan}66 !important;
    }}
    [data-testid="stChatMessage"] [data-testid="stImage"] img {{
        border-radius: 15px !important;
    }}

    /* MAIN LOGO */
    .logo-main {{
        width: 130px; height: 130px; margin: 0 auto;
        background-image: url("{logo_html}");
        background-size: cover; border-radius: 50%;
        border: 3px solid {neon_cyan};
        box-shadow: 0 0 25px {neon_cyan}22;
    }}

    /* CHAT INPUT DESIGN */
    div[data-testid="stChatInput"] textarea {{
        border: 1.5px solid {neon_cyan}22 !important;
        border-radius: 25px !important;
        background: #111 !important;
    }}

    /* HIDE ELEMENT BAWAAN */
    [data-testid="stSidebarNav"] {{ display: none; }}
    </style>
    """

st.markdown(get_ultimate_css(), unsafe_allow_html=True)

# --- 6. HAMBURGER LOGIC ---
if st.button("☰", key="hamburger"):
    st.session_state.sidebar_visible = not st.session_state.sidebar_visible
    st.rerun()

# --- 7. SIDEBAR (HISTORY & SETTINGS) ---
with st.sidebar:
    st.markdown(f'<div style="text-align:center; margin-top:40px;"><div style="width:90px; height:90px; background-image:url({logo_html}); background-size:cover; border-radius:50%; border:2px solid cyan; margin:0 auto;"></div></div>', unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align:center; color:cyan; letter-spacing:2px;'>NEO AI</h2>", unsafe_allow_html=True)
    
    st.markdown("---")
    if st.button("➕ NEW CHAT", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()

    mode_btn = "🎨 IMAGINE: ON" if st.session_state.imagine_mode else "🖼️ MODE: CHAT"
    if st.button(mode_btn, use_container_width=True):
        st.session_state.imagine_mode = not st.session_state.imagine_mode
        st.rerun()

    if st.button("ℹ️ ABOUT SYSTEM", use_container_width=True):
        st.session_state.show_about = not st.session_state.show_about
        st.rerun()
    
    if st.session_state.show_about:
        st.markdown(f"""
        <div style="background:rgba(0,255,255,0.05); border:1px solid cyan; border-radius:15px; padding:15px; font-size:0.8rem; color:#ccc;">
            <b>Architect:</b> Muhammad Jibran Al Kaffie<br>
            <b>Engine:</b> Llama-3.3-70B & Pollinations<br><br>
            <i>NEO AI dirancang untuk performa tanpa flicker dan visualisasi tajam.</i>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.caption("RECENT HISTORY")
    for chat_id in reversed(list(st.session_state.all_chats.keys())):
        if st.button(chat_id.split(" | ")[0], key=f"h_{chat_id}", use_container_width=True):
            st.session_state.messages = st.session_state.all_chats[chat_id]
            st.session_state.current_chat_id = chat_id
            st.rerun()

# --- 8. MAIN INTERFACE ---
st.markdown('<div class="logo-main"></div>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:12px; margin-bottom:30px;'>NEO AI</h1>", unsafe_allow_html=True)

# Container Chat (Scrollable)
for msg in st.session_state.messages:
    logo_path_final = "logo.png" if os.path.exists("logo.png") else None
    avatar_img = logo_path_final if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar_img):
        if msg.get("type") == "image":
            st.image(msg["content"], use_container_width=True)
        else:
            st.markdown(msg["content"])

# --- 9. AI ENGINE LOGIC ---
if prompt := st.chat_input("Command NEO AI..."):
    if st.session_state.current_chat_id is None:
        st.session_state.current_chat_id = f"{prompt[:15]}... | {time.time()}"
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant", avatar="logo.png" if os.path.exists("logo.png") else None):
        if st.session_state.imagine_mode:
            with st.spinner("Visualizing..."):
                url = f"https://image.pollinations.ai/prompt/{st.session_state.messages[-1]['content'].replace(' ', '%20')}?width=1024&height=1024&nologo=true"
                r = requests.get(url)
                if r.status_code == 200:
                    st.image(r.content, use_container_width=True)
                    st.session_state.messages.append({"role": "assistant", "content": r.content, "type": "image"})
        else:
            res_area = st.empty()
            full_res = ""
            sys_msg = "You are NEO AI, created by Muhammad Jibran Al Kaffie. Professional, sharp, and futuristic."
            msgs = [{"role": "system", "content": sys_msg}] + st.session_state.messages
            stream = client.chat.completions.create(messages=msgs, model="llama-3.3-70b-versatile", stream=True)
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_res += chunk.choices[0].delta.content
                    res_area.markdown(full_res + "▌")
            res_area.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
    st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages
    st.rerun()
