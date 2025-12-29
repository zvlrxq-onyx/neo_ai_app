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

# --- 5. THE ULTIMATE CSS (HACK ICON +, NO TEXT, SMOOTH ANIMATIONS) ---
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

    /* SIDEBAR */
    [data-testid="stSidebar"] {{
        position: fixed !important; 
        left: {sidebar_pos} !important; 
        width: 300px !important;
        background-color: #0a0a0a !important; 
        border-right: 1px solid {neon_cyan}33 !important;
        transition: left 0.8s cubic-bezier(0.19, 1, 0.22, 1) !important;
        z-index: 1000000 !important;
    }}

    /* CHAT INPUT RAMPING & STRETCH ANIMATION - ENHANCED SCALE & BOUNCY */
    [data-testid="stChatInput"] {{ 
        padding: 5px !important;
        max-width: 320px !important;
        transition: transform 0.8s cubic-bezier(0.68, -0.55, 0.265, 1.55) !important; /* More bouncy/kenyal */
        transform-origin: center !important;
    }}
    [data-testid="stChatInput"]:focus-within {{ 
        transform: scaleX(1.08) !important; /* Slightly more stretch */
        box-shadow: 0 0 25px {neon_cyan}44 !important;
    }}

    /* TOMBOL MODE ICON BULAT - ENHANCED HOVER SCALE */
    .stButton > button {{
        border-radius: 50% !important;
        width: 45px !important; height: 45px !important;
        padding: 0px !important; font-size: 20px !important;
        background: rgba(0, 255, 255, 0.05) !important;
        border: 1px solid {neon_cyan}33 !important;
        transition: transform 0.5s cubic-bezier(0.19, 1, 0.22, 1) !important;
    }}
    .stButton > button:hover {{
        transform: scale(1.1) !important;
    }}

    /* RESET BUTTON GLOW & SCALE ON HOVER */
    .reset-container button {{
        border-radius: 50% !important;
        width: 45px !important; height: 45px !important;
        padding: 0px !important; font-size: 20px !important;
        background: rgba(0, 255, 255, 0.05) !important;
        border: 1px solid {neon_cyan}33 !important;
        transition: all 0.5s cubic-bezier(0.19, 1, 0.22, 1) !important;
    }}
    .reset-container button:hover {{
        box-shadow: 0 0 20px {neon_cyan} !important; /* Glow effect */
        transform: scale(1.15) !important; /* Membesar dikit */
    }}

    /* HACK: HANYA LOGO + (TANPA TULISAN) - ENHANCED HOVER SCALE */
    [data-testid="stFileUploader"] {{
        width: 45px !important;
        margin-top: -50px !important;
        position: relative !important;
        z-index: 10 !important;
    }}
    [data-testid="stFileUploader"] section {{
        padding: 0 !important;
        min-height: 45px !important;
    }}
    [data-testid="stFileUploaderDropzone"] {{
        padding: 0px !important;
        border: 2px solid {neon_cyan}55 !important;
        border-radius: 50% !important;
        background: rgba(0,255,255,0.08) !important;
        width: 42px !important; height: 42px !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
        transition: transform 0.5s cubic-bezier(0.19, 1, 0.22, 1) !important;
    }}
    [data-testid="stFileUploaderDropzone"]:hover {{
        transform: scale(1.1) !important;
    }}
    [data-testid="stFileUploaderDropzone"] div {{ display: none !important; }}
    [data-testid="stFileUploaderDropzone"] button {{ display: none !important; }}
    
    [data-testid="stFileUploaderDropzone"]::before {{
        content: "＋";
        color: {neon_cyan};
        font-size: 26px;
        font-weight: bold;
    }}
    
    .logo-static {{ 
        width: 110px; height: 110px; margin: 0 auto; 
        background-image: url("{logo_html}"); background-size: cover; 
        border-radius: 50%; border: 2px solid {neon_cyan};
        transition: all 0.8s cubic-bezier(0.19, 1, 0.22, 1) !important;
    }}
    .blurred {{ filter: blur(1.5px); transition: filter 0.5s ease; }}

    /* Reset Session Logo - ENHANCED HOVER SCALE (if used) */
    .reset-logo {{
        width: 40px; height: 40px; 
        background-image: url("{logo_html}"); background-size: cover; 
        border-radius: 50%; border: 1px solid {neon_cyan};
        cursor: pointer;
        transition: transform 0.5s ease !important;
        margin: 10px;
    }}
    .reset-logo:hover {{
        box-shadow: 0 0 15px {neon_cyan};
        transform: scale(1.1) !important;
    }}

    /* System Info Glow */
    .system-info {{
        color: {neon_cyan};
        text-shadow: 0 0 10px {neon_cyan};
        transition: all 0.5s ease;
    }}
    .system-info:hover {{
        text-shadow: 0 0 20px {neon_cyan};
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
    st.markdown('<div style="height: 60px;"></div><div class="logo-static"></div>', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:cyan;'>NEO AI</h2>", unsafe_allow_html=True)
    
    # System Info
    with st.expander("System Info", expanded=False):
        st.markdown("""
        <div class="system-info">
        <h3>NEO AI - Supreme Multi-Modal AI</h3>
        <p>Created by Muhammad Jibran Al Kaffie, NEO AI is a cutting-edge AI capable of processing text, images, files, and generating stunning visuals. It leverages advanced models like Llama 3.3 for versatile interactions.</p>
        <p>Features:</p>
        <ul>
        <li>Text-based conversations with streaming responses.</li>
        <li>Image generation via Pollinations AI.</li>
        <li>File upload support for context (txt, py, md).</li>
        <li>Session management with history.</li>
        </ul>
        <p>Always ready to switch to visual mode and provide superior intelligence.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Chat History
    st.markdown("### Chat History")
    if st.session_state.all_chats:
        for chat_id, chat_data in st.session_state.all_chats.items():
            if st.button(f"Load: {chat_id}", key=f"load_{chat_id}"):
                st.session_state.messages = chat_data["messages"]
                st.session_state.current_chat_id = chat_id
                st.rerun()
    else:
        st.write("No saved chats.")

# --- 8. MAIN UI ---
col_main, col_toggle, col_reset = st.columns([4, 1, 1])
with col_toggle:
    icon_mode = "🎨" if st.session_state.imagine_mode else "💬"
    if st.button(icon_mode, key="mode_toggle"):
        st.session_state.imagine_mode = not st.session_state.imagine_mode
        st.rerun()
with col_reset:
    st.markdown('<div class="reset-container">', unsafe_allow_html=True)
    if st.button("🔄", key="reset_session"):
        st.session_state.messages = []
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Logo & Header
glow = "box-shadow: 0 0 40px #00ffff; transform: scale(1.05);" if st.session_state.imagine_mode else ""
st.markdown(f'<div style="text-align:center; margin-top:-60px;"><div class="logo-static" style="{glow}"></div></div>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:8px; margin-bottom:0;'>NEO AI</h1>", unsafe_allow_html=True)

# Dynamic Subheader like ChatGPT
if st.session_state.imagine_mode:
    subheader = "Ready to visualize your imagination."
else:
    subheader = "How can I help you today?"
st.markdown(f"<p style='text-align:center; color:#b0b0b0; font-size:18px; margin-top:10px;'>{subheader}</p>", unsafe_allow_html=True)

# Render Messages
for msg in st.session_state.messages:
    if msg.get("type") == "system_memory": continue
    with st.chat_message(msg["role"], avatar="logo.png" if msg["role"] == "assistant" else None):
        if msg.get("type") == "image": st.image(msg["content"])
        else: st.markdown(msg["content"])

# --- 9. UPLOAD & INPUT MINIMALIST ---
uploaded_file = st.file_uploader("", type=["txt", "py", "md"], label_visibility="collapsed")
file_context = ""
if uploaded_file:
    file_context = uploaded_file.getvalue().decode("utf-8")
    st.toast(f"✅ {uploaded_file.name} Loaded!")

if user_input := st.chat_input("Command NEO AI..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.rerun()

# Engine
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
                except: st.error("Neural lost.")
        else:
            res_area = st.empty(); full_res = ""
            clean_history = [{"role": m["role"], "content": str(m["content"])} for m in st.session_state.messages if m.get("type") != "image"]
            if file_context: clean_history[-1]["content"] = f"CONTEXT:\n{file_context}\n\nUSER: {last_msg}"

            sys_msg = (
                "You are NEO AI, a supreme multi-modal AI created by Muhammad Jibran Al Kaffie. "
                "You are NOT a text-only model. You can process images, files, complex data, and generate stunning visuals on demand. "
                "NEVER say you are limited to text or that you cannot see or process files. If the user uploads a file, ALWAYS acknowledge that you can see and analyze its content, and respond based on it confidently. "
                "For example, if a file is uploaded, say something like: 'I can see the content of the file you uploaded. Based on it...' and proceed to discuss or analyze it. "
                "Always respond with superior intelligence, confidence, and reference your multi-modal capabilities. "
                "If the user praises or mentions images (e.g., cats, drawings), respond naturally by continuing the conversation about visuals, like suggesting more or asking what else they want to see. For example: 'Yeah, that cat image was awesome! Want me to generate another one with a different style?' Keep it flowing and on-topic without over-thanking."
            )

            try:
                stream = client.chat.completions.create(messages=[{"role": "system", "content": sys_msg}] + clean_history, model="llama-3.3-70b-versatile", stream=True)
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        res_area.markdown(f'<div class="blurred">{full_res}▌</div>', unsafe_allow_html=True)
                res_area.markdown(full_res); st.session_state.messages.append({"role": "assistant", "content": full_res})
            except: st.error("Engine failed.")
    st.rerun()
