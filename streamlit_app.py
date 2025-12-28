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

# --- 5. THE NEO-SMOOTH TYPING & CHAT CSS ---
def get_ultimate_css():
    neon_cyan = "#00ffff"
    sidebar_pos = "0" if st.session_state.sidebar_visible else "-350px"
    
    return f"""
    <style>
    /* BASE SETTINGS */
    html, body, [data-testid="stAppViewContainer"] {{
        background-color: #080808 !important;
        color: #e0e0e0 !important;
        scroll-behavior: smooth !important;
    }}
    [data-testid="stStatusWidget"] {{ visibility: hidden; }}

    /* GLOBAL TRANSITION */
    * {{ transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); }}

    /* HAMBURGER BUTTON */
    .stButton > button[key="hamburger"] {{
        position: fixed; top: 25px; left: 20px; z-index: 99999;
        background: rgba(0,0,0,0.8) !important;
        border: 1.5px solid {neon_cyan}44 !important;
        border-radius: 12px !important;
        width: 48px !important; height: 48px !important;
    }}

    /* SIDEBAR SLIDE */
    [data-testid="stSidebar"] {{
        left: {sidebar_pos} !important;
        transition: all 0.6s cubic-bezier(0.19, 1, 0.22, 1) !important;
        background-color: #0a0a0a !important;
        border-right: 1px solid {neon_cyan}33 !important;
    }}

    /* === ANIMASI CHAT HALUS === */
    [data-testid="stChatMessage"] {{
        animation: slideInUp 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.2) forwards;
        background: rgba(255, 255, 255, 0.02) !important;
        border-radius: 20px !important;
        border: 1px solid rgba(0, 255, 255, 0.05) !important;
        margin-bottom: 10px !important;
    }}

    @keyframes slideInUp {{
        from {{ opacity: 0; transform: translateY(30px) scale(0.98); }}
        to {{ opacity: 1; transform: translateY(0) scale(1); }}
    }}

    /* TYPING FLOW ANIMATION (EFEK TEKS MENGALIR) */
    .typing-text {{
        animation: typingReveal 0.3s ease-out forwards;
    }}

    @keyframes typingReveal {{
        from {{ opacity: 0; filter: blur(5px); transform: translateX(-5px); }}
        to {{ opacity: 1; filter: blur(0); transform: translateX(0); }}
    }}

    /* LOGO GLOW */
    .logo-main {{
        width: 130px; height: 130px; margin: 0 auto;
        background-image: url("{logo_html}");
        background-size: cover; border-radius: 50%;
        border: 2px solid {neon_cyan};
        animation: logoGlow 3s infinite alternate ease-in-out;
    }}
    @keyframes logoGlow {{
        from {{ box-shadow: 0 0 15px {neon_cyan}22; }}
        to {{ box-shadow: 0 0 45px {neon_cyan}55; transform: scale(1.02); }}
    }}

    /* ELASTIC INPUT */
    div[data-testid="stChatInput"] {{
        width: 80% !important; margin: 0 auto !important;
    }}
    div[data-testid="stChatInput"]:focus-within {{
        width: 100% !important;
    }}

    /* SIDEBAR ABOUT PANEL */
    .about-sidebar-panel {{
        background: rgba(0, 255, 255, 0.05);
        border: 1px solid {neon_cyan}33;
        border-radius: 15px; padding: 15px; margin-top: 10px;
        animation: slideDown 0.5s ease-out;
    }}
    @keyframes slideDown {{
        from {{ opacity: 0; max-height: 0; }}
        to {{ opacity: 1; max-height: 500px; }}
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
    st.markdown(f'<div style="width:90px; height:90px; background-image:url({logo_html}); background-size:cover; border-radius:50%; border:2px solid cyan; margin:0 auto; box-shadow: 0 0 15px cyan;"></div>', unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align:center; color:cyan; letter-spacing:2px;'>NEO AI</h2>", unsafe_allow_html=True)
    
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
        <div class="about-sidebar-panel">
            <h4 style="color:cyan; font-size:0.9rem; margin:0;">NEO CORE ARCHITECTURE</h4>
            <p style="color:#bbb; font-size:0.75rem; line-height:1.5; margin-top:10px;">
                <b>Architect:</b> Muhammad Jibran Al Kaffie<br><br>
                NEO AI utilizes Llama-3.3-70B for logic and Pollinations for 
                generative imagery. Designed with elastic CSS for a seamless interface.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.caption("CHATS")
    for chat_id in reversed(list(st.session_state.all_chats.keys())):
        if st.button(chat_id.split(" | ")[0], key=f"h_{chat_id}", use_container_width=True):
            st.session_state.messages = st.session_state.all_chats[chat_id]
            st.session_state.current_chat_id = chat_id
            st.rerun()

# --- 8. MAIN INTERFACE ---
st.markdown('<div style="margin-top:20px;"><div class="logo-main"></div></div>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:15px;'>NEO AI</h1>", unsafe_allow_html=True)

# Chat Display
for msg in st.session_state.messages:
    avatar_img = "logo.png" if msg["role"] == "assistant" and os.path.exists("logo.png") else None
    with st.chat_message(msg["role"], avatar=avatar_img):
        if msg.get("type") == "image":
            st.image(msg["content"], use_container_width=True)
        else:
            # Menggunakan div typing-text agar pesan lama tetap smooth
            st.markdown(f'<div class="typing-text">{msg["content"]}</div>', unsafe_allow_html=True)

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
            sys_msg = (
                "You are NEO AI, created by Muhammad Jibran Al Kaffie. "
                "You are a professional AI that can generate complex images. "
                "If a user asks for an image, strictly tell them to turn on 'Imagine Mode' in the sidebar first."
            )
            msgs = [{"role": "system", "content": sys_msg}] + st.session_state.messages
            stream = client.chat.completions.create(messages=msgs, model="llama-3.3-70b-versatile", stream=True)
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_res += chunk.choices[0].delta.content
                    # Bungkus dalam div typing-text agar setiap chunk muncul halus
                    res_area.markdown(f'<div class="typing-text">{full_res}▌</div>', unsafe_allow_html=True)
            res_area.markdown(f'<div class="typing-text">{full_res}</div>', unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
    st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages
    st.rerun()
