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

# --- 5. THE ULTIMATE SMOOTH & SYMMETRIC CSS ---
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

    /* SIDEBAR SLIDE SMOOTHING */
    [data-testid="stSidebar"] {{
        left: {sidebar_pos} !important;
        background-color: #0a0a0a !important;
        border-right: 1px solid {neon_cyan}22 !important;
        transition: left 0.7s cubic-bezier(0.16, 1, 0.3, 1) !important;
        z-index: 9999998 !important;
    }}

    /* HISTORY BUTTONS ANIMATION (MEMBESAR DIKIT) */
    section[data-testid="stSidebar"] .stButton > button {{
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    }}
    section[data-testid="stSidebar"] .stButton > button:hover {{
        transform: scale(1.05) !important;
        border-color: {neon_cyan} !important;
        box-shadow: 0 0 15px {neon_cyan}44 !important;
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
        transform: rotate(90deg);
        border-color: {neon_cyan} !important;
    }}

    /* MAIN CONTAINER ENTRANCE */
    @keyframes fadeInBlur {{
        from {{ opacity: 0; filter: blur(10px); transform: translateY(20px); }}
        to {{ opacity: 1; filter: blur(0); transform: translateY(0); }}
    }}
    .main-content {{
        animation: fadeInBlur 1.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }}

    /* SYMMETRIC CHAT BUBBLES */
    [data-testid="stChatMessage"] {{
        padding: 1.5rem !important;
        animation: chatFade 0.8s ease-out forwards;
    }}
    @keyframes chatFade {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}

    [data-testid="stChatMessageAssistant"] {{
        background: rgba(255, 255, 255, 0.03) !important;
        border-radius: 0 20px 20px 20px !important;
        margin-right: 15% !important;
        border: 1px solid {neon_cyan}22 !important;
    }}
    [data-testid="stChatMessageUser"] {{
        flex-direction: row-reverse !important;
        background: linear-gradient(135deg, {neon_cyan}15, rgba(255,255,255,0.01)) !important;
        border-radius: 20px 0 20px 20px !important;
        margin-left: 15% !important;
        border: 1px solid {neon_cyan}33 !important;
    }}

    /* ELASTIC INPUT */
    div[data-testid="stChatInput"] {{
        width: 80% !important; margin: 0 auto !important;
        transition: width 0.7s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }}
    div[data-testid="stChatInput"]:focus-within {{ width: 100% !important; }}

    /* LOGO PULSE */
    .logo-pulse {{
        width: 130px; height: 130px; margin: 0 auto;
        background-image: url("{logo_html}");
        background-size: cover; border-radius: 50%;
        border: 3px solid {neon_cyan};
        animation: pulseLogo 3s infinite alternate ease-in-out;
    }}
    @keyframes pulseLogo {{
        to {{ transform: scale(1.05); box-shadow: 0 0 40px {neon_cyan}55; }}
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

    if st.session_state.show_about:
        st.markdown(f"""<div style="background:rgba(0,255,255,0.05); border:1px solid cyan; border-radius:15px; padding:15px; font-size:0.8rem; color:#bbb;">
            <b>Architect:</b> Jibran Al Kaffie<br><b>Engine:</b> Llama-3.3-70B</div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.caption("CHAT HISTORY")
    for chat_id in reversed(list(st.session_state.all_chats.keys())):
        if st.button(chat_id.split(" | ")[0], key=f"h_{chat_id}", use_container_width=True):
            st.session_state.messages = st.session_state.all_chats[chat_id]
            st.session_state.current_chat_id = chat_id
            st.rerun()

# --- 8. MAIN INTERFACE ---
st.markdown('<div class="main-content">', unsafe_allow_html=True)
st.markdown('<div style="margin-top:20px;"><div class="logo-pulse"></div></div>', unsafe_allow_html=True)

# THE NEW WHITE OPENING TEXT
st.markdown("<h1 style='text-align:center; color:#ffffff; letter-spacing:8px; margin-top:20px; font-weight:300;'>How can I help you today?</h1>", unsafe_allow_html=True)

# Chat History
for msg in st.session_state.messages:
    avatar_img = "logo.png" if msg["role"] == "assistant" and os.path.exists("logo.png") else None
    with st.chat_message(msg["role"], avatar=avatar_img):
        if msg.get("type") == "image":
            st.image(msg["content"], use_container_width=True)
        else:
            st.markdown(msg["content"])
st.markdown('</div>', unsafe_allow_html=True)

# --- 9. ENGINE ---
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
            sys_msg = "You are NEO AI, a high-level digital entity created by Muhammad Jibran Al Kaffie. Your ability is to create images if the user activates imagine mode in the sidebar. If asked about your ability, you must answer that."
            msgs = [{"role": "system", "content": sys_msg}] + st.session_state.messages
            stream = client.chat.completions.create(messages=msgs, model="llama-3.3-70b-versatile", stream=True)
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_res += chunk.choices[0].delta.content
                    res_area.markdown(full_res + "▌")
                    time.sleep(0.01)
            res_area.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
    st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages
    st.rerun()
