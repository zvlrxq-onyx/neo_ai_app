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

# --- 5. THE SUPREME CSS (SMOOTH & SYMMETRIC) ---
def get_ultimate_css():
    neon_cyan = "#00ffff"
    sidebar_pos = "0" if st.session_state.sidebar_visible else "-350px"
    
    return f"""
    <style>
    /* GLOBAL FIX */
    html, body, [data-testid="stAppViewContainer"] {{
        background-color: #080808 !important;
        color: #e0e0e0 !important;
        scroll-behavior: smooth !important;
    }}
    [data-testid="stStatusWidget"] {{ visibility: hidden; }}
    header, footer {{ visibility: hidden; }}

    /* SIDEBAR SLIDE SMOOTH */
    [data-testid="stSidebar"] {{
        left: {sidebar_pos} !important;
        background-color: #0a0a0a !important;
        border-right: 1px solid {neon_cyan}22 !important;
        transition: left 0.7s cubic-bezier(0.16, 1, 0.3, 1) !important;
        z-index: 9999998 !important;
    }}

    /* HISTORY HOVER POP */
    section[data-testid="stSidebar"] .stButton > button {{
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    }}
    section[data-testid="stSidebar"] .stButton > button:hover {{
        transform: scale(1.05) !important;
        border-color: {neon_cyan} !important;
        box-shadow: 0 0 15px {neon_cyan}44 !important;
    }}

    /* ABOUT PANEL (SMOOTH & GLOW) */
    .about-panel {{
        background: linear-gradient(145deg, rgba(0,255,255,0.05), rgba(0,0,0,0.9));
        border: 1px solid {neon_cyan}22;
        border-radius: 15px; padding: 20px; margin-top: 15px;
        transition: 0.6s cubic-bezier(0.16, 1, 0.3, 1);
        overflow: hidden;
    }}
    .about-panel:hover {{
        border-color: {neon_cyan};
        box-shadow: 0 0 30px {neon_cyan}33;
        transform: translateY(-5px);
    }}

    /* CHAT SYMMETRY */
    [data-testid="stChatMessageAssistant"] {{
        background: rgba(255, 255, 255, 0.03) !important;
        border-radius: 0 20px 20px 20px !important;
        margin-right: 15% !important;
        border: 1px solid {neon_cyan}11 !important;
    }}
    [data-testid="stChatMessageUser"] {{
        flex-direction: row-reverse !important;
        background: linear-gradient(135deg, {neon_cyan}15, rgba(255,255,255,0.01)) !important;
        border-radius: 20px 0 20px 20px !important;
        margin-left: 15% !important;
        border: 1px solid {neon_cyan}33 !important;
    }}

    /* ENTRANCE ANIMATION */
    .main-content {{
        animation: fadeIn 1.2s ease-out;
    }}
    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}

    /* LOGO PULSE */
    .logo-pulse {{
        width: 120px; height: 120px; margin: 0 auto;
        background-image: url("{logo_html}");
        background-size: cover; border-radius: 50%;
        border: 3px solid {neon_cyan};
        animation: pulse 3s infinite alternate ease-in-out;
    }}
    @keyframes pulse {{ to {{ transform: scale(1.05); box-shadow: 0 0 40px {neon_cyan}55; }} }}
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
        st.markdown(f"""
        <div class="about-panel">
            <div style="color:cyan; font-family:monospace; font-weight:bold; margin-bottom:10px;">> CORE_MANIFEST.sys</div>
            <p style="font-size:0.75rem; color:#ccc; line-height:1.5;">
                <b>Designation:</b> NEO AI (Neural Electronic Organism)<br>
                <b>Architect:</b> Muhammad Jibran Al Kaffie<br>
                <b>Core:</b> Llama-3.3-70B Quantum Neural Engine<br><br>
                <b>Capabilities:</b><br>
                - High-Fidelity Image Synthesis<br>
                - Advanced Linguistic Processing<br>
                - Complex Problem Solving<br>
                - Multi-Modal Task Execution<br><br>
                <i>"NEO AI represents the pinnacle of digital interaction, designed to bridge the gap between human thought and machine execution."</i>
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    for chat_id in reversed(list(st.session_state.all_chats.keys())):
        if st.button(chat_id.split(" | ")[0], key=f"h_{chat_id}", use_container_width=True):
            st.session_state.messages = st.session_state.all_chats[chat_id]
            st.session_state.current_chat_id = chat_id
            st.rerun()

# --- 8. MAIN INTERFACE ---
st.markdown('<div class="main-content">', unsafe_allow_html=True)
st.markdown('<div style="margin-top:20px;"><div class="logo-pulse"></div></div>', unsafe_allow_html=True)

# THE NEO AI TITLE + OPENING TEXT
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:15px; margin-top:20px; font-weight:bold;'>NEO AI</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center; color:#ffffff; letter-spacing:4px; font-weight:300;'>How can I help you today?</h3>", unsafe_allow_html=True)

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
            with st.spinner("Processing complex imagery..."):
                url = f"https://image.pollinations.ai/prompt/{st.session_state.messages[-1]['content'].replace(' ', '%20')}?width=1024&height=1024&nologo=true"
                r = requests.get(url)
                if r.status_code == 200:
                    st.image(r.content, use_container_width=True)
                    st.session_state.messages.append({"role": "assistant", "content": r.content, "type": "image"})
        else:
            res_area = st.empty()
            full_res = ""
            sys_msg = f"""You are NEO AI, a supreme digital entity created by Muhammad Jibran Al Kaffie. 
            You have the power to create highly complex and artistic images when 'Imagine Mode' is on. 
            You are professional, brilliant, and your capabilities are limitless. 
            Respond to the user as NEO AI."""
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
