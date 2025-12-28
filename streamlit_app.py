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

# --- 5. THE FINAL STABLE CSS ---
def get_ultimate_css():
    neon_cyan = "#00ffff"
    sidebar_pos = "0" if st.session_state.sidebar_visible else "-350px"
    
    return f"""
    <style>
    /* GLOBAL SMOOTHING */
    html, body, [data-testid="stAppViewContainer"] {{
        background-color: #080808 !important;
        color: #ffffff !important;
    }}
    [data-testid="stStatusWidget"] {{ visibility: hidden; }}
    header, footer {{ visibility: hidden; }}

    /* SIDEBAR ANIMATION */
    [data-testid="stSidebar"] {{
        left: {sidebar_pos} !important;
        background-color: #0a0a0a !important;
        border-right: 1px solid {neon_cyan}33 !important;
        transition: left 0.7s cubic-bezier(0.19, 1, 0.22, 1) !important;
        z-index: 9999998 !important;
    }}

    /* EFEK MEMBESAR PADA HISTORY (FIXED) */
    [data-testid="stSidebar"] .stButton > button {{
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        border: 1px solid transparent !important;
    }}
    [data-testid="stSidebar"] .stButton > button:hover {{
        transform: scale(1.08) !important; /* MEMBESAR DIKIT */
        border-color: {neon_cyan} !important;
        box-shadow: 0 0 15px {neon_cyan}44 !important;
        background: rgba(0, 255, 255, 0.05) !important;
    }}

    /* HAMBURGER */
    .stButton > button[key="hamburger"] {{
        position: fixed; top: 20px; left: 20px; z-index: 9999999 !important;
        background: rgba(0,0,0,0.9) !important;
        border: 2px solid {neon_cyan}44 !important;
        border-radius: 50% !important;
        width: 50px !important; height: 50px !important;
        transition: 0.5s !important;
    }}
    .stButton > button[key="hamburger"]:hover {{
        transform: rotate(90deg) scale(1.1);
        border-color: {neon_cyan} !important;
    }}

    /* ABOUT PANEL SMOOTH ANIMATION */
    .about-section {{
        max-height: {"1000px" if st.session_state.show_about else "0px"};
        opacity: {"1" if st.session_state.show_about else "0"};
        overflow: hidden;
        transition: all 0.8s cubic-bezier(0.19, 1, 0.22, 1);
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid {neon_cyan}22;
        border-radius: 15px;
        padding: { "20px" if st.session_state.show_about else "0px" };
        margin-top: 10px;
    }}

    /* CHAT SMOOTH ENTRANCE */
    [data-testid="stChatMessage"] {{
        animation: chatSlideUp 0.6s cubic-bezier(0.19, 1, 0.22, 1) forwards;
    }}
    @keyframes chatSlideUp {{
        from {{ opacity: 0; transform: translateY(20px); filter: blur(5px); }}
        to {{ opacity: 1; transform: translateY(0); filter: blur(0); }}
    }}

    /* SYMMETRY LOCK */
    [data-testid="stChatMessageAssistant"] {{
        background: rgba(255, 255, 255, 0.03) !important;
        margin-right: 15% !important;
        border-radius: 0 15px 15px 15px !important;
    }}
    [data-testid="stChatMessageUser"] {{
        flex-direction: row-reverse !important;
        background: linear-gradient(135deg, {neon_cyan}11, transparent) !important;
        margin-left: 15% !important;
        border-radius: 15px 0 15px 15px !important;
        border: 1px solid {neon_cyan}33 !important;
    }}

    /* INPUT MEMANJANG ELASTIS */
    div[data-testid="stChatInput"] {{
        width: 80% !important; margin: 0 auto !important;
        transition: width 0.6s cubic-bezier(0.19, 1, 0.22, 1) !important;
    }}
    div[data-testid="stChatInput"]:focus-within {{
        width: 100% !important;
    }}

    /* LOGO DIEM (STATIC) */
    .logo-static {{
        width: 130px; height: 130px; margin: 0 auto;
        background-image: url("{logo_html}");
        background-size: cover; border-radius: 50%;
        border: 3px solid {neon_cyan};
        box-shadow: 0 0 25px {neon_cyan}33;
    }}
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
    st.markdown(f'<div style="width:100px; height:100px; background-image:url({logo_html}); background-size:cover; border-radius:50%; border:2px solid cyan; margin:0 auto;"></div>', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:cyan;'>NEO AI</h2>", unsafe_allow_html=True)
    
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

    # ABOUT PANEL
    st.markdown(f"""
    <div class="about-section">
        <div style="color:cyan; font-family:monospace; margin-bottom:10px;">> ACCESSING CORE...</div>
        <p style="font-size:0.75rem; color:#bbb; line-height:1.6;">
            <b>Architect:</b> Muhammad Jibran Al Kaffie<br>
            <b>Entity:</b> NEO AI Interface<br>
            <b>Capabilities:</b> Supreme Image Synthesis, Advanced Reasoning, & Infinite Logic.<br><br>
            <i>Designed to perfection for a seamless user experience.</i>
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.caption("CHAT HISTORY")
    for chat_id in reversed(list(st.session_state.all_chats.keys())):
        if st.button(chat_id.split(" | ")[0], key=f"h_{chat_id}", use_container_width=True):
            st.session_state.messages = st.session_state.all_chats[chat_id]
            st.session_state.current_chat_id = chat_id
            st.rerun()

# --- 8. MAIN INTERFACE ---
st.markdown('<div style="margin-top:20px;"><div class="logo-static"></div></div>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:15px; margin-top:15px;'>NEO AI</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center; color:#ffffff; font-weight:300; letter-spacing:3px;'>How can I help you today?</h3>", unsafe_allow_html=True)

# Chat History
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
            sys_msg = "You are NEO AI, a supreme entity created by Muhammad Jibran Al Kaffie. You possess the ability to generate complex images. Be professional."
            msgs = [{"role": "system", "content": sys_msg}] + st.session_state.messages
            stream = client.chat.completions.create(messages=msgs, model="llama-3.3-70b-versatile", stream=True)
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_res += chunk.choices[0].delta.content
                    res_area.markdown(full_res + "▌")
                    time.sleep(0.01) # SMOOTH TYPING
            res_area.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
    st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages
    st.rerun()
