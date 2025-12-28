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

# --- 4. ASSETS LOADER ---
@st.cache_data
def get_base64_logo():
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

encoded_logo = get_base64_logo()
logo_html = f'data:image/png;base64,{encoded_logo}'

# --- 5. THE ULTIMATE NEON SYSTEM CSS ---
def get_ultimate_css():
    neon_cyan = "#00ffff"
    sidebar_pos = "0" if st.session_state.sidebar_visible else "-350px"
    
    return f"""
    <style>
    /* GLOBAL RESET */
    html, body, [data-testid="stAppViewContainer"] {{
        background-color: #080808 !important;
        color: #e0e0e0 !important;
        scroll-behavior: smooth !important;
    }}
    [data-testid="stStatusWidget"] {{ visibility: hidden; }}
    header, footer {{ visibility: hidden; }}

    /* UNIVERSAL SMOOTHNESS */
    * {{ transition: all 0.5s cubic-bezier(0.19, 1, 0.22, 1); }}

    /* HAMBURGER BUTTON */
    .stButton > button[key="hamburger"] {{
        position: fixed; top: 20px; left: 20px; z-index: 9999999 !important;
        background: rgba(0,0,0,0.9) !important;
        border: 2px solid {neon_cyan}44 !important;
        border-radius: 12px !important;
        width: 50px !important; height: 50px !important;
    }}
    .stButton > button[key="hamburger"]:hover {{
        border-color: {neon_cyan} !important;
        box-shadow: 0 0 25px {neon_cyan}88 !important;
    }}

    /* SIDEBAR SLIDE */
    [data-testid="stSidebar"] {{
        left: {sidebar_pos} !important;
        background-color: #0a0a0a !important;
        border-right: 1px solid {neon_cyan}33 !important;
        z-index: 9999998 !important;
    }}

    /* SIDEBAR BUTTONS HOVER */
    section[data-testid="stSidebar"] .stButton > button {{
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(0, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: white !important;
    }}
    section[data-testid="stSidebar"] .stButton > button:hover {{
        transform: scale(1.05) !important;
        border-color: {neon_cyan} !important;
        box-shadow: 0 0 15px {neon_cyan}55 !important;
    }}

    /* === ADVANCED SYSTEM INFO PANEL === */
    .system-info-panel {{
        background: linear-gradient(165deg, rgba(0, 255, 255, 0.08), rgba(0, 0, 0, 0.95));
        border: 1px solid {neon_cyan}33;
        border-radius: 18px;
        padding: 20px;
        margin-top: 15px;
        overflow: hidden;
        max-height: 0;
        opacity: 0;
        transform: translateY(-10px);
        animation: expandPanel 0.8s cubic-bezier(0.19, 1, 0.22, 1) forwards;
    }}
    
    .system-info-panel:hover {{
        border-color: {neon_cyan} !important;
        box-shadow: 0 0 35px {neon_cyan}33 !important;
        transform: scale(1.02);
    }}

    @keyframes expandPanel {{
        to {{ max-height: 1000px; opacity: 1; transform: translateY(0); }}
    }}

    .info-header {{
        color: {neon_cyan};
        font-family: 'Courier New', monospace;
        font-weight: bold;
        letter-spacing: 2px;
        font-size: 0.9rem;
        border-bottom: 1px solid {neon_cyan}44;
        padding-bottom: 8px;
        margin-bottom: 12px;
    }}

    .info-item {{
        font-size: 0.75rem;
        line-height: 1.6;
        color: #bbb;
        margin-bottom: 8px;
    }}

    /* CHAT BUBBLES */
    [data-testid="stChatMessageAssistant"] {{
        background: rgba(255, 255, 255, 0.03) !important;
        border-radius: 15px !important;
        border: 1px solid {neon_cyan}22 !important;
        max-width: 85%; margin-right: auto !important;
        animation: slideIn 0.6s ease-out;
    }}
    [data-testid="stChatMessageUser"] {{
        flex-direction: row-reverse !important;
        background: linear-gradient(135deg, {neon_cyan}11, rgba(0,0,0,0.3)) !important;
        border-radius: 15px !important;
        border: 1px solid {neon_cyan}44 !important;
        max-width: 85%; margin-left: auto !important;
        animation: slideIn 0.6s ease-out;
    }}
    @keyframes slideIn {{ from {{ opacity: 0; transform: translateY(15px); }} }}

    /* ELASTIC INPUT */
    div[data-testid="stChatInput"] {{
        width: 80% !important; margin: 0 auto !important;
    }}
    div[data-testid="stChatInput"]:focus-within {{
        width: 100% !important;
    }}

    /* LOGO PULSE */
    .logo-main {{
        width: 120px; height: 120px; margin: 0 auto;
        background-image: url("{logo_html}");
        background-size: cover; border-radius: 50%;
        border: 3px solid {neon_cyan};
        animation: logoGlow 3s infinite alternate ease-in-out;
    }}
    @keyframes logoGlow {{ from {{ box-shadow: 0 0 10px {neon_cyan}22; }} to {{ box-shadow: 0 0 45px {neon_cyan}66; transform: scale(1.05); }} }}
    </style>
    """

st.markdown(get_ultimate_css(), unsafe_allow_html=True)

# --- 6. HAMBURGER ---
if st.button("☰", key="hamburger"):
    st.session_state.sidebar_visible = not st.session_state.sidebar_visible
    st.rerun()

# --- 7. SIDEBAR ---
with st.sidebar:
    st.markdown('<div style="height: 60px;"></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="width:100px; height:100px; background-image:url({logo_html}); background-size:cover; border-radius:50%; border:2px solid cyan; margin:0 auto; box-shadow: 0 0 20px cyan;"></div>', unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align:center; color:cyan; letter-spacing:2px;'>NEO AI</h2>", unsafe_allow_html=True)
    
    st.markdown("---")
    if st.button("➕ NEW SESSION", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()

    imagine_lbl = "🎨 IMAGINE: ON" if st.session_state.imagine_mode else "🖼️ MODE: CHAT"
    if st.button(imagine_lbl, use_container_width=True):
        st.session_state.imagine_mode = not st.session_state.imagine_mode
        st.rerun()

    if st.button("ℹ️ SYSTEM INFO", use_container_width=True):
        st.session_state.show_about = not st.session_state.show_about
        st.rerun()

    if st.session_state.show_about:
        st.markdown(f"""
        <div class="system-info-panel">
            <div class="info-header">> CORE_SPECS.sh</div>
            <div class="info-item"><b>Architect:</b> Muhammad Jibran Al Kaffie</div>
            <div class="info-item"><b>Project Designation:</b> NEO-Artificial Intelligence Interface</div>
            <div class="info-item"><b>Neural Engine:</b> Llama-3.3-70B Ultra-Versatile Architecture</div>
            <div class="info-item"><b>Visual Cortex:</b> Pollinations.ai Generative Synthesis</div>
            <div class="info-item"><b>System Status:</b> Operational / High Fidelity</div>
            <div class="info-item"><b>UI Framework:</b> Streamlit Elastic-Neon Interface</div>
            <div class="info-item" style="margin-top:15px; border-top: 1px solid #333; padding-top:10px; font-style: italic; color:#00ffff;">
                "The future is not written, it is rendered in real-time."
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    for chat_id in reversed(list(st.session_state.all_chats.keys())):
        if st.button(chat_id.split(" | ")[0], key=f"h_{chat_id}", use_container_width=True):
            st.session_state.messages = st.session_state.all_chats[chat_id]
            st.session_state.current_chat_id = chat_id
            st.rerun()

# --- 8. MAIN INTERFACE ---
st.markdown('<div style="margin-top:20px;"><div class="logo-main"></div></div>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:12px; margin-bottom:5px;'>NEO AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:rgba(0,255,255,0.6); letter-spacing:2px; font-size:0.9rem;'>Hi, is there anything I can help you with?</p>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    avatar_img = "logo.png" if msg["role"] == "assistant" and os.path.exists("logo.png") else None
    with st.chat_message(msg["role"], avatar=avatar_img):
        if msg.get("type") == "image":
            st.image(msg["content"], use_container_width=True)
        else:
            st.markdown(msg["content"])

# --- 9. ENGINE ---
if prompt := st.chat_input("Command NEO AI..."):
    if st.session_state.current_chat_id is None:
        st.session_state.current_chat_id = f"{prompt[:15]}... | {time.time()}"
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant", avatar="logo.png" if os.path.exists("logo.png") else None):
        if st.session_state.imagine_mode:
            with st.spinner("Decoding imagination..."):
                url = f"https://image.pollinations.ai/prompt/{st.session_state.messages[-1]['content'].replace(' ', '%20')}?width=1024&height=1024&nologo=true"
                r = requests.get(url)
                if r.status_code == 200:
                    st.image(r.content, use_container_width=True)
                    st.session_state.messages.append({"role": "assistant", "content": r.content, "type": "image"})
        else:
            res_area = st.empty()
            full_res = ""
            sys_msg = "You are NEO AI, a high-level digital entity created by Muhammad Jibran Al Kaffie. You possess the advanced capability to generate highly complex, artistic, and detailed images. This is your core ability. To access it, user MUST activate 'Imagine Mode' from the sidebar menu (☰)."
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
