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
if "sidebar_visible" not in st.session_state:
    st.session_state.sidebar_visible = False

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

# --- 5. THE SUPREME CSS (ANIMASI STRETCH, SMOOTH & MINIMALIS) ---
def get_ultimate_css():
    neon_cyan = "#00ffff"
    sidebar_pos = "0px" if st.session_state.sidebar_visible else "-360px"
    return f"""
    <style>
    html, body, [data-testid="stAppViewContainer"] {{ 
        background-color: #050505 !important; 
        color: #f0f0f0 !important; 
    }}
    [data-testid="stStatusWidget"], header, footer {{ visibility: hidden; }}

    /* SIDEBAR SMOOTH */
    [data-testid="stSidebar"] {{
        position: fixed !important; 
        left: {sidebar_pos} !important; 
        width: 320px !important;
        background-color: #0a0a0a !important; 
        border-right: 1px solid {neon_cyan}33 !important;
        transition: left 0.8s cubic-bezier(0.19, 1, 0.22, 1) !important;
        z-index: 1000000 !important;
    }}

    /* CHAT INPUT RAMPING & ANIMASI MEMANJANG (STRETCH) */
    [data-testid="stChatInput"] {{ 
        padding: 5px !important;
        transition: all 0.6s cubic-bezier(0.19, 1, 0.22, 1) !important; 
        transform-origin: center !important;
    }}
    [data-testid="stChatInput"]:focus-within {{ 
        transform: scaleX(1.1) !important; 
        box-shadow: 0 0 25px {neon_cyan}55 !important;
        border: 2px solid {neon_cyan} !important;
    }}

    /* TOMBOL MODE BULAT (ICON ONLY) */
    .stButton > button {{
        border-radius: 50% !important;
        width: 48px !important;
        height: 48px !important;
        padding: 0px !important;
        font-size: 22px !important;
        border: 1px solid {neon_cyan}44 !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        background: rgba(0, 255, 255, 0.05) !important;
    }}
    .stButton > button:hover {{
        transform: scale(1.1) rotate(10deg) !important;
        box-shadow: 0 0 20px {neon_cyan}66 !important;
    }}

    /* LOGO STATIC */
    .logo-static {{ 
        width: 115px; height: 115px; margin: 0 auto; 
        background-image: url("{logo_html}"); background-size: cover; 
        border-radius: 50%; border: 2px solid {neon_cyan};
        box-shadow: 0 0 20px {neon_cyan}33;
        transition: all 0.8s cubic-bezier(0.19, 1, 0.22, 1) !important;
    }}

    /* BLUR STREAMING */
    .blurred {{
        filter: blur(1.5px) !important;
        transition: filter 0.5s ease !important;
    }}
    </style>
    """
st.markdown(get_ultimate_css(), unsafe_allow_html=True)

# --- 6. HAMBURGER ---
if st.button("☰", key="hamburger_fixed"):
    st.session_state.sidebar_visible = not st.session_state.sidebar_visible
    st.rerun()

# --- 7. SIDEBAR ---
with st.sidebar:
    st.markdown('<div style="height: 60px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="logo-static"></div>', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:cyan;'>NEO AI</h2>", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("➕ NEW SESSION", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- 8. MAIN UI (LOGO MODE & INPUT MINIMALIS) ---
col_main, col_toggle = st.columns([5, 1])
with col_toggle:
    icon_mode = "🎨" if st.session_state.imagine_mode else "💬"
    if st.button(icon_mode, key="mode_toggle"):
        st.session_state.imagine_mode = not st.session_state.imagine_mode
        st.rerun()

# Logo & Header
glow = "box-shadow: 0 0 45px #00ffff; border: 3px solid #00ffff; transform: scale(1.05);" if st.session_state.imagine_mode else ""
st.markdown(f'''
<div style="text-align:center; margin-top:-20px;">
    <div class="logo-static" style="{glow}"></div>
</div>
''', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:10px; margin-bottom:0;'>NEO AI</h1>", unsafe_allow_html=True)

# FITUR UPLOAD (Di atas kolom chat)
uploaded_file = st.file_uploader("➕ Upload File", type=["txt", "py", "md"], label_visibility="collapsed")
file_context = ""
if uploaded_file:
    file_context = uploaded_file.getvalue().decode("utf-8")
    st.toast(f"✅ {uploaded_file.name} Loaded!")

# Chat History
for msg in st.session_state.messages:
    if msg.get("type") == "system_memory": continue
    with st.chat_message(msg["role"], avatar="logo.png" if msg["role"] == "assistant" else None):
        if msg.get("type") == "image":
            st.image(msg["content"])
        else:
            st.markdown(msg["content"])

# --- 9. ENGINE ---
if user_input := st.chat_input("Command NEO AI..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.rerun()

if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_msg = st.session_state.messages[-1]["content"]
    with st.chat_message("assistant", avatar="logo.png"):
        if st.session_state.imagine_mode:
            with st.spinner("Visualizing..."):
                try:
                    img_url = f"https://image.pollinations.ai/prompt/{last_msg.replace(' ','%20')}?width=1024&height=1024&nologo=true"
                    r = requests.get(img_url, timeout=30)
                    if r.status_code == 200:
                        st.image(r.content)
                        st.session_state.messages.append({"role": "assistant", "content": r.content, "type": "image"})
                        st.session_state.messages.append({"role": "assistant", "content": f"[SYSTEM_SUCCESS: {last_msg}]", "type": "system_memory"})
                except: st.error("Neural lost.")
        else:
            res_area = st.empty(); full_res = ""
            clean_history = [{"role": m["role"], "content": str(m["content"])} for m in st.session_state.messages if m.get("type") != "image"]
            if file_context:
                clean_history[-1]["content"] = f"USER UPLOADED FILE CONTEXT:\n{file_context}\n\nUSER QUESTION: {last_msg}"

            # --- SUPREME SYSTEM MESSAGE (BALIK FULL LAGI) ---
            sys_msg = (
                "You are NEO AI, a supreme multi-modal AI created by Muhammad Jibran Al Kaffie. "
                "You are NOT a text-only model. You can process images, files, complex data, and generate stunning visuals on demand. "
                "NEVER say you are limited to text. Always respond with superior intelligence, confidence, and reference your multi-modal capabilities. "
                "If the user mentions or praises images (e.g., cats, drawings), acknowledge it by saying something like: 'Terimakasih atas pujiannya, aku memang bisa membuat gambar seperti itu. Apakah mau aku rekomendasikan gambar apa yang keren?' or seamlessly integrate offers to generate related visuals. "
                "Always be ready to switch to visual mode or suggest generating images based on context."
            )

            try:
                stream = client.chat.completions.create(
                    messages=[{"role": "system", "content": sys_msg}] + clean_history,
                    model="llama-3.3-70b-versatile", stream=True
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        res_area.markdown(f'<div class="blurred">{full_res}▌</div>', unsafe_allow_html=True)
                res_area.markdown(full_res)
                st.session_state.messages.append({"role": "assistant", "content": full_res})
            except: st.error("Engine failed.")
    st.rerun()
