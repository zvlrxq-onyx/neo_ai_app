import streamlit as st
from groq import Groq
import time
import os
import base64
import requests

# --- 1. INITIALIZE SESSION STATE ---
if "messages" not in st.session_state: 
    st.session_state.messages = []
if "all_chats" not in st.session_state: 
    st.session_state.all_chats = {}
if "current_chat_id" not in st.session_state: 
    st.session_state.current_chat_id = None
if "imagine_mode" not in st.session_state: 
    st.session_state.imagine_mode = False
if "show_about" not in st.session_state: 
    st.session_state.show_about = False
if "sidebar_visible" not in st.session_state: 
    st.session_state.sidebar_visible = False

# --- 2. CONFIG API ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except:
    st.error("API Key Groq missing! Please check your secrets.")
    st.stop()

# --- 3. PAGE CONFIG ---
st.set_page_config(
    page_title="NEO AI | Supreme Interface", 
    page_icon="⚡", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 4. ASSETS LOADER ---
@st.cache_data
def get_base64_logo():
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

encoded_logo = get_base64_logo()
logo_html = f'data:image/png;base64,{encoded_logo}'

# --- 5. THE SUPREME CSS (SIDEBAR & ANIMATION FIX) ---
def get_ultimate_css():
    neon_cyan = "#00ffff"
    # Menentukan posisi sidebar secara absolut
    sidebar_pos = "0px" if st.session_state.sidebar_visible else "-360px"
    
    return f"""
    <style>
    /* GLOBAL DARK THEME */
    html, body, [data-testid="stAppViewContainer"] {{
        background-color: #050505 !important;
        color: #f0f0f0 !important;
    }}
    
    [data-testid="stStatusWidget"], header, footer {{ 
        visibility: hidden; 
    }}

    /* SIDEBAR FORCED VISIBILITY & SMOOTH SLIDE */
    [data-testid="stSidebar"] {{
        position: fixed !important;
        left: {sidebar_pos} !important;
        width: 350px !important;
        background-color: #0a0a0a !important;
        border-right: 1px solid {neon_cyan}33 !important;
        transition: left 0.7s cubic-bezier(0.19, 1, 0.22, 1) !important;
        z-index: 9999999 !important; /* Paksa paling depan */
        display: block !important;
        visibility: visible !important;
    }}

    /* OVERLAY FIX (Agar area utama tidak menutupi sidebar) */
    [data-testid="stSidebarContent"] {{
        background-color: #0a0a0a !important;
    }}

    /* HOVER POP ANIMATION FOR HISTORY BUTTONS */
    section[data-testid="stSidebar"] .stButton > button {{
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        background: transparent !important;
        border: 1px solid {neon_cyan}11 !important;
        color: #bbb !important;
        margin-bottom: 8px;
    }}
    section[data-testid="stSidebar"] .stButton > button:hover {{
        transform: scale(1.08) !important; /* EFEK MEMBESAR */
        border-color: {neon_cyan} !important;
        box-shadow: 0 0 20px {neon_cyan}33 !important;
        background: rgba(0, 255, 255, 0.05) !important;
    }}

    /* HAMBURGER BUTTON FIX */
    .stButton > button[key="hamburger"] {{
        position: fixed; top: 20px; left: 20px; z-index: 10000000 !important;
        background: rgba(0,0,0,0.9) !important;
        border: 2px solid {neon_cyan}44 !important;
        border-radius: 50% !important;
        width: 52px !important; height: 52px !important;
        transition: 0.5s cubic-bezier(0.19, 1, 0.22, 1) !important;
    }}
    .stButton > button[key="hamburger"]:hover {{
        transform: rotate(90deg) scale(1.1);
        border-color: {neon_cyan} !important;
    }}

    /* ABOUT PANEL SMOOTH */
    .about-box {{
        max-height: {"1200px" if st.session_state.show_about else "0px"};
        opacity: {"1" if st.session_state.show_about else "0"};
        overflow: hidden;
        transition: all 0.9s cubic-bezier(0.19, 1, 0.22, 1);
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid {neon_cyan}22;
        border-radius: 20px;
        padding: { "25px" if st.session_state.show_about else "0px" };
        margin-top: 15px;
    }}

    /* CHAT SYMMETRY & ENTRANCE */
    [data-testid="stChatMessage"] {{
        animation: slideUp 0.7s cubic-bezier(0.19, 1, 0.22, 1) forwards;
    }}
    @keyframes slideUp {{
        from {{ opacity: 0; transform: translateY(30px); filter: blur(5px); }}
        to {{ opacity: 1; transform: translateY(0); filter: blur(0); }}
    }}

    [data-testid="stChatMessageAssistant"] {{
        background: rgba(255, 255, 255, 0.04) !important;
        margin-right: 15% !important;
        border-radius: 0 25px 25px 25px !important;
    }}
    [data-testid="stChatMessageUser"] {{
        flex-direction: row-reverse !important;
        background: linear-gradient(135deg, {neon_cyan}15, transparent) !important;
        margin-left: 15% !important;
        border-radius: 25px 0 25px 25px !important;
        border: 1px solid {neon_cyan}33 !important;
    }}

    /* ELASTIC INPUT */
    div[data-testid="stChatInput"] {{
        width: 80% !important; 
        margin: 0 auto !important;
        transition: width 0.7s cubic-bezier(0.19, 1, 0.22, 1) !important;
    }}
    div[data-testid="stChatInput"]:focus-within {{
        width: 100% !important;
    }}

    /* STATIC LOGO */
    .logo-container {{
        width: 135px; height: 135px; margin: 0 auto;
        background-image: url("{logo_html}");
        background-size: cover; border-radius: 50%;
        border: 4px solid {neon_cyan};
    }}
    </style>
    """

st.markdown(get_ultimate_css(), unsafe_allow_html=True)

# --- 6. HAMBURGER BUTTON ---
if st.button("☰", key="hamburger"):
    st.session_state.sidebar_visible = not st.session_state.sidebar_visible
    st.rerun()

# --- 7. SIDEBAR ---
with st.sidebar:
    st.markdown('<div style="height: 70px;"></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="width:110px; height:110px; background-image:url({logo_html}); background-size:cover; border-radius:50%; border:2px solid cyan; margin:0 auto;"></div>', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:cyan; letter-spacing:2px;'>NEO AI</h2>", unsafe_allow_html=True)
    
    st.markdown("---")
    if st.button("➕ NEW SESSION", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()

    mode_lbl = "🎨 IMAGINE MODE: ON" if st.session_state.imagine_mode else "🖼️ CHAT MODE: ON"
    if st.button(mode_lbl, use_container_width=True):
        st.session_state.imagine_mode = not st.session_state.imagine_mode
        st.rerun()

    if st.button("ℹ️ SYSTEM INFO", use_container_width=True):
        st.session_state.show_about = not st.session_state.show_about
        st.rerun()

    st.markdown(f"""
    <div class="about-box">
        <p style="font-size:0.8rem; color:#ccc; line-height:1.7;">
            <b>ARCHITECT:</b> Jibran Al Kaffie<br>
            <b>ENTITY:</b> NEO AI Interface<br>
            <b>STABILITY:</b> Quantum Fixed<br><br>
            <i>"The sidebar is now locked to the highest layer for seamless access."</i>
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    for chat_id in reversed(list(st.session_state.all_chats.keys())):
        if st.button(chat_id.split(" | ")[0], key=f"hist_{chat_id}", use_container_width=True):
            st.session_state.messages = st.session_state.all_chats[chat_id]
            st.session_state.current_chat_id = chat_id
            st.rerun()

# --- 8. MAIN INTERFACE ---
st.markdown('<div style="margin-top:25px;"><div class="logo-container"></div></div>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:18px; margin-top:20px; font-weight:900;'>NEO AI</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center; color:#ffffff; font-weight:200; letter-spacing:5px;'>How can I help you today?</h3>", unsafe_allow_html=True)

# Chat Display
for msg in st.session_state.messages:
    av = "logo.png" if msg["role"] == "assistant" and os.path.exists("logo.png") else None
    with st.chat_message(msg["role"], avatar=av):
        if msg.get("type") == "image":
            st.image(msg["content"], use_container_width=True)
        else:
            st.markdown(msg["content"])

# --- 9. ENGINE ---
if prompt := st.chat_input("Command NEO AI..."):
    if st.session_state.current_chat_id is None:
        st.session_state.current_chat_id = f"{prompt[:18]}... | {time.time()}"
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant", avatar="logo.png" if os.path.exists("logo.png") else None):
        if st.session_state.imagine_mode:
            with st.spinner("Decoding Neural Imagination..."):
                query = st.session_state.messages[-1]['content'].replace(' ', '%20')
                url = f"https://image.pollinations.ai/prompt/{query}?width=1024&height=1024&nologo=true"
                response = requests.get(url)
                if response.status_code == 200:
                    st.image(response.content, use_container_width=True)
                    st.session_state.messages.append({"role": "assistant", "content": response.content, "type": "image"})
        else:
            response_container = st.empty()
            accumulated_text = ""
            sys_identity = f"You are NEO AI, a supreme entity created by Muhammad Jibran Al Kaffie."
            
            # Filter image data
            text_only = [m for m in st.session_state.messages if m.get("type") != "image"]
            chat_payload = [{"role": "system", "content": sys_identity}] + text_only
            
            stream = client.chat.completions.create(messages=chat_payload, model="llama-3.3-70b-versatile", stream=True)
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    accumulated_text += chunk.choices[0].delta.content
                    response_container.markdown(accumulated_text + "▌")
                    time.sleep(0.01)
            response_container.markdown(accumulated_text)
            st.session_state.messages.append({"role": "assistant", "content": accumulated_text})
            
    st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages
    st.rerun()
