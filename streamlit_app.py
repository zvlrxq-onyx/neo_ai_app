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

# --- 5. THE ULTIMATE SMOOTH, GLOW & SLIDE CSS ---
def get_ultimate_css():
    neon_cyan = "#00ffff"
    sidebar_pos = "0" if st.session_state.sidebar_visible else "-350px"
    
    return f"""
    <style>
    /* ANTI-FLICKER CORE */
    html, body, [data-testid="stAppViewContainer"] {{
        background-color: #080808 !important;
        color: #e0e0e0 !important;
        scroll-behavior: smooth !important;
    }}
    [data-testid="stStatusWidget"] {{ visibility: hidden; }}

    /* GLOBAL TRANSITION */
    * {{ transition: all 0.45s cubic-bezier(0.175, 0.885, 0.32, 1.275); }}

    /* HAMBURGER BUTTON */
    .stButton > button[key="hamburger"] {{
        position: fixed; top: 25px; left: 20px; z-index: 99999;
        background: rgba(0,0,0,0.8) !important;
        border: 1.5px solid {neon_cyan}44 !important;
        border-radius: 12px !important;
        width: 48px !important; height: 48px !important;
    }}
    .stButton > button[key="hamburger"]:hover {{
        border-color: {neon_cyan} !important;
        box-shadow: 0 0 20px {neon_cyan}88 !important;
        transform: scale(1.1);
    }}

    /* SIDEBAR SLIDE */
    [data-testid="stSidebar"] {{
        left: {sidebar_pos} !important;
        transition: all 0.6s cubic-bezier(0.19, 1, 0.22, 1) !important;
        background-color: #0a0a0a !important;
        border-right: 1px solid {neon_cyan}33 !important;
        z-index: 99998 !important;
    }}

    /* SIDEBAR BUTTON HOVER GLOW */
    section[data-testid="stSidebar"] .stButton > button {{
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(0, 255, 255, 0.1) !important;
        color: white !important;
        border-radius: 12px !important;
        margin-bottom: 8px !important;
    }}
    section[data-testid="stSidebar"] .stButton > button:hover {{
        transform: scale(1.06) !important;
        border-color: {neon_cyan} !important;
        box-shadow: 0 0 20px {neon_cyan}66 !important;
        background: rgba(0, 255, 255, 0.08) !important;
    }}

    /* MODERN ABOUT PANEL (VERTICAL SLIDE) */
    .about-panel {{
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.05) 0%, rgba(0, 0, 0, 0.9) 100%);
        border: 1px solid {neon_cyan}55;
        border-radius: 20px;
        padding: 25px;
        margin-top: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.5), inset 0 0 20px {neon_cyan}11;
        overflow: hidden;
        animation: slideDown 0.7s cubic-bezier(0.19, 1, 0.22, 1) forwards;
    }}
    @keyframes slideDown {{
        from {{ opacity: 0; transform: translateY(-30px); max-height: 0; }}
        to {{ opacity: 1; transform: translateY(0); max-height: 1000px; }}
    }}

    /* LOGO PULSING */
    .logo-main {{
        width: 135px; height: 135px; margin: 0 auto;
        background-image: url("{logo_html}");
        background-size: cover; border-radius: 50%;
        border: 3px solid {neon_cyan};
        animation: glowPulse 3s infinite alternate ease-in-out;
    }}
    @keyframes glowPulse {{
        from {{ box-shadow: 0 0 10px {neon_cyan}22; transform: scale(1); }}
        to {{ box-shadow: 0 0 40px {neon_cyan}66; transform: scale(1.05); }}
    }}

    /* ELASTIC INPUT */
    div[data-testid="stChatInput"] {{
        width: 80% !important; margin: 0 auto !important;
    }}
    div[data-testid="stChatInput"]:focus-within {{
        width: 100% !important;
    }}
    div[data-testid="stChatInput"] textarea {{
        border: 2px solid rgba(0, 255, 255, 0.1) !important;
        border-radius: 30px !important;
        background: #111 !important;
    }}
    div[data-testid="stChatInput"] textarea:focus {{
        border-color: {neon_cyan} !important;
        box-shadow: 0 0 25px {neon_cyan}33 !important;
    }}

    header, footer {{ visibility: hidden; }}
    </style>
    """

st.markdown(get_ultimate_css(), unsafe_allow_html=True)

# --- 6. HAMBURGER LOGIC ---
if st.button("☰", key="hamburger"):
    st.session_state.sidebar_visible = not st.session_state.sidebar_visible
    st.rerun()

# --- 7. SIDEBAR ---
with st.sidebar:
    st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)
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

    st.markdown("---")
    st.caption("RECENT HISTORY")
    for chat_id in reversed(list(st.session_state.all_chats.keys())):
        if st.button(chat_id.split(" | ")[0], key=f"h_{chat_id}", use_container_width=True):
            st.session_state.messages = st.session_state.all_chats[chat_id]
            st.session_state.current_chat_id = chat_id
            st.rerun()

# --- 8. MAIN INTERFACE ---
if st.session_state.show_about:
    st.markdown(f"""
    <div class="about-panel">
        <h3 style="color:#00ffff; margin-bottom:15px; letter-spacing:2px;">NEO CORE SYSTEM ARCHITECTURE</h3>
        <p style="color:#fff; font-size:0.95rem; line-height:1.7;">
            <b>Overview:</b><br>
            NEO AI is a sophisticated neural interface designed by <b>Muhammad Jibran Al Kaffie</b>. 
            It represents the pinnacle of neo-futuristic AI design, blending high-speed processing 
            capabilities with a sleek, minimalist aesthetic.
            <br><br>
            <b>Technical Specifications:</b><br>
            • <b>Core Intelligence:</b> Powered by the Llama-3.3-70B model via Groq's LPU technology, ensuring near-instantaneous response times.<br>
            • <b>Visual Engine:</b> Integrated with the Pollinations Neural Network for high-fidelity, complex image generation.<br>
            • <b>UI/UX:</b> Built on a custom-engineered Streamlit framework featuring elastic CSS animations, glassmorphism, and anti-flicker rendering.
            <br><br>
            <b>Philosophy:</b><br>
            The system is built on the principle of <i>"Seamless Intelligence"</i>—where the boundary between human imagination and AI execution is eliminated through a smooth, responsive, and visually immersive experience.
        </p>
        <p style="color:#00ffff; font-size:0.8rem; margin-top:15px; text-align:right; font-style:italic;">
            "Designed for the future, engineered for the present."
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div style="text-align:center; margin-top:20px;"><div class="logo-main"></div></div>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:15px;'>NEO AI</h1>", unsafe_allow_html=True)

# Chat Display
for msg in st.session_state.messages:
    avatar_img = "logo.png" if msg["role"] == "assistant" and os.path.exists("logo.png") else None
    with st.chat_message(msg["role"], avatar=avatar_img):
        if msg.get("type") == "image":
            st.image(msg["content"], use_container_width=True)
        else:
            st.markdown(msg["content"])

# --- 9. ENGINE LOGIC ---
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
            sys_msg = "You are NEO AI, created by Muhammad Jibran Al Kaffie."
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
