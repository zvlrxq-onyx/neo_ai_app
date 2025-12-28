import streamlit as st
from groq import Groq
import time
import os
import base64
import requests
import io
from PIL import Image

# --- 1. INITIALIZE SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "all_chats" not in st.session_state: st.session_state.all_chats = {}
if "current_chat_id" not in st.session_state: st.session_state.current_chat_id = None
if "imagine_mode" not in st.session_state: st.session_state.imagine_mode = False
if "show_about" not in st.session_state: st.session_state.show_about = False

# --- 2. CONFIG API ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except:
    st.error("API Key Groq hilang!")
    st.stop()

# --- 3. PAGE CONFIG ---
st.set_page_config(page_title="NEO AI", page_icon="⚡", layout="centered")

# --- 4. LOGO LOADER ---
@st.cache_data
def get_base64_logo():
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""
encoded_logo = get_base64_logo()

# --- 5. THE ULTIMATE SMOOTH CSS ---
def get_ultimate_css():
    neon_cyan = "#00ffff"
    input_border = neon_cyan if st.session_state.imagine_mode else "rgba(0, 255, 255, 0.2)"
    input_glow = f"0 0 15px {neon_cyan}44" if st.session_state.imagine_mode else "none"
    
    return f"""
    <style>
    /* ANTI-FLICKER & SMOOTH SCROLL */
    html, body, [data-testid="stAppViewContainer"] {{
        background-color: #080808 !important;
        color: #e0e0e0 !important;
        scroll-behavior: smooth !important;
    }}
    
    /* GLOBAL TRANSITION (SMOOTH & ELASTIC) */
    * {{
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    }}

    /* CHAT INPUT AREA (MEMANJANG SMOOTH) */
    div[data-testid="stChatInput"] {{
        padding: 20px 0 !important;
    }}
    div[data-testid="stChatInput"] textarea {{
        border: 2px solid {input_border} !important;
        box-shadow: {input_glow} !important;
        border-radius: 30px !important;
        background: #111 !important;
        padding: 12px 20px !important;
    }}

    /* BUTTONS HOVER & CLICK EFFECT */
    .stButton > button {{
        border-radius: 20px !important;
        border: 1px solid rgba(0, 255, 255, 0.2) !important;
        background: rgba(255, 255, 255, 0.03) !important;
        color: white !important;
        width: 100% !important;
    }}
    .stButton > button:hover {{
        transform: scale(1.05) !important; /* MEMBESAR DIKIT SMOOTH */
        border-color: {neon_cyan} !important;
        box-shadow: 0 0 15px {neon_cyan}33 !important;
    }}
    .stButton > button:active {{
        transform: scale(0.95) !important; /* EFEK PENCET */
    }}

    /* HISTORY CHAT ROUNDED */
    [data-testid="stChatMessage"] {{
        border-radius: 25px !important;
        padding: 15px !important;
        background: rgba(255, 255, 255, 0.03) !important;
        margin-bottom: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
    }}

    /* LOGO & TITLE */
    .logo-circle {{
        width: 100px; height: 100px; margin: 0 auto;
        background-image: url("data:image/png;base64,{encoded_logo}");
        background-size: cover; border-radius: 50%;
        border: 2px solid {neon_cyan};
        box-shadow: 0 0 20px {neon_cyan}44;
    }}

    /* ABOUT BOX PREMIUM */
    .about-box {{
        background: linear-gradient(145deg, rgba(0, 255, 255, 0.1), rgba(0, 0, 0, 0.5));
        border: 1px solid {neon_cyan}33;
        border-radius: 20px;
        padding: 20px;
        margin-top: 20px;
        animation: fadeIn 0.8s ease-out;
    }}
    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}

    /* HIDE STREAMLIT ELEMENTS */
    header, footer, [data-testid="stStatusWidget"] {{ visibility: hidden; }}
    </style>
    """

st.markdown(get_ultimate_css(), unsafe_allow_html=True)

# --- 6. IMAGE GEN (POLLINATIONS) ---
def get_image_ai(prompt):
    url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?width=1024&height=1024&nologo=true"
    res = requests.get(url)
    return res.content if res.status_code == 200 else None

# --- 7. SIDEBAR ---
with st.sidebar:
    st.markdown('<div class="logo-circle"></div>', unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align:center; color:cyan; letter-spacing:3px;'>NEO AI</h2>", unsafe_allow_html=True)
    
    st.markdown("---")
    if st.button("➕ NEW SESSION"):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()

    # IMAGINE MODE BUTTON (HOVER BESAR SMOOTH)
    mode_text = "🎨 IMAGINE: ACTIVE" if st.session_state.imagine_mode else "🖼️ SWITCH IMAGINE"
    if st.button(mode_text):
        st.session_state.imagine_mode = not st.session_state.imagine_mode
        st.rerun()

    st.markdown("---")
    # ABOUT PREMIUM
    if st.button("ℹ️ ABOUT"):
        st.session_state.show_about = not st.session_state.show_about
        st.rerun()
    
    if st.session_state.show_about:
        st.markdown(f"""
        <div class="about-box">
            <p style="color:cyan; font-weight:bold; margin-bottom:5px;">NEO AI v2.0</p>
            <p style="font-size:0.8rem; color:#aaa;">Designed by Jibran. <br> Powered by Llama-3.3 & Pollinations Engine.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    # HISTORY CHAT
    for chat_id in reversed(list(st.session_state.all_chats.keys())):
        if st.button(chat_id.split(" | ")[0], key=f"h_{chat_id}"):
            st.session_state.messages = st.session_state.all_chats[chat_id]
            st.session_state.current_chat_id = chat_id
            st.rerun()

# --- 8. MAIN INTERFACE ---
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:10px;'>NEO AI</h1>", unsafe_allow_html=True)

# Container Chat (Supaya ga kedip pas ngetik)
chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg.get("type") == "image":
                st.image(msg["content"], use_container_width=True)
            else:
                st.markdown(msg["content"])

# --- 9. LOGIC ---
if prompt := st.chat_input("Ask something or draw..."):
    if st.session_state.current_chat_id is None:
        st.session_state.current_chat_id = f"{prompt[:15]}... | {time.time()}"
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun() # Refresh untuk nampilin pesan user tanpa kedip

# Logic setelah rerun (untuk respon AI)
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        if st.session_state.imagine_mode:
            with st.spinner("🎨 Visualizing..."):
                img = get_image_ai(st.session_state.messages[-1]["content"])
                if img:
                    st.image(img, use_container_width=True)
                    st.session_state.messages.append({"role": "assistant", "content": img, "type": "image"})
        else:
            res_area = st.empty()
            full_res = ""
            msgs = [{"role": "system", "content": "You are NEO AI. Be sleek and sharp."}] + st.session_state.messages
            stream = client.chat.completions.create(messages=msgs, model="llama-3.3-70b-versatile", stream=True)
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    full_res += content
                    res_area.markdown(full_res + "▌")
            res_area.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
    
    st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages
    st.rerun()
