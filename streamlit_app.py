import streamlit as st
from groq import Groq
import os
import base64
import requests
from PIL import Image, ImageFilter
import io
import numpy as np

# --- 1. INITIALIZE SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None
if "neo_mode" not in st.session_state:
    st.session_state.neo_mode = "Chat" # Default mode

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

logo_html = f'data:image/png;base64,{get_base64_logo()}'

# --- 5. THE SUPREME CSS (MOBILE SYMMETRY + TOGGLE STYLE) ---
def get_ultimate_css():
    neon_cyan = "#00ffff"
    return f"""
    <style>
    /* CORE SETTINGS */
    html, body, [data-testid="stAppViewContainer"] {{ 
        background-color: #050505 !important; 
        color: #f0f0f0 !important; 
    }}
    [data-testid="stStatusWidget"], header, footer {{ visibility: hidden; }}

    /* LOGO CENTERED */
    .logo-container {{ display: flex; justify-content: center; margin-top: -60px; padding: 20px; }}
    .logo-static {{ 
        width: 100px; height: 100px; background-image: url("{logo_html}"); background-size: cover; 
        border-radius: 50%; border: 2px solid {neon_cyan}; box-shadow: 0 0 20px {neon_cyan}33;
    }}

    /* CHAT BUBBLES */
    [data-testid="stChatMessage"] {{
        padding: 1rem !important; margin-bottom: 20px !important;
        border-radius: 20px !important; width: fit-content !important;
        max-width: 85% !important; animation: fadeIn 0.6s ease-out;
    }}
    
    /* ALIGNMENT (USER RIGHT, AI LEFT) */
    [data-testid="stChatMessage"]:not(:has(img[src*="data"])) {{
        margin-left: auto !important;
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.15) 0%, rgba(0, 0, 0, 0.5) 100%) !important;
        border: 1px solid {neon_cyan}44 !important;
        border-radius: 25px 25px 5px 25px !important;
        flex-direction: row-reverse !important;
    }}
    [data-testid="stChatMessage"]:has(img[src*="data"]) {{
        margin-right: auto !important;
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 25px 25px 25px 5px !important;
    }}

    /* MOBILE SYMMETRY FIX (KOLOM KETIK TENGAH) */
    [data-testid="stChatInput"] {{ 
        padding-left: 90px !important; /* Ruang buat + dan Mode */
        max-width: 450px !important; 
        margin: 0 auto !important;
        width: 90% !important; /* Biar simetris di HP */
        transition: all 0.7s cubic-bezier(0.19, 1, 0.22, 1) !important;
        position: relative !important;
    }}
    [data-testid="stChatInput"]:focus-within {{ max-width: 650px !important; transform: scale(1.02) !important; }}

    /* UPLOADER (+) INSIDE BOX */
    [data-testid="stFileUploader"] {{
        position: absolute !important; left: 15px !important; bottom: 12px !important;
        width: 35px !important; z-index: 100 !important;
    }}
    [data-testid="stFileUploaderDropzone"] {{
        background: transparent !important; border: none !important;
        height: 35px !important; width: 35px !important; padding: 0 !important;
    }}
    [data-testid="stFileUploaderDropzone"]::before {{
        content: "＋"; color: {neon_cyan}; font-size: 24px; line-height: 35px; 
        display: block; text-align: center; font-weight: bold;
    }}
    [data-testid="stFileUploaderDropzone"] div, [data-testid="stFileUploaderDropzone"] button {{ display: none !important; }}

    /* PAPER PLANE BUTTON */
    [data-testid="stChatInput"] button {{
        background: transparent !important; border: none !important;
    }}
    [data-testid="stChatInput"] button::after {{
        content: "➤"; color: {neon_cyan}; font-size: 24px; display: block; transform: rotate(-20deg);
    }}
    [data-testid="stChatInput"] button svg {{ display: none !important; }}

    /* TOGGLE MODE POSITIONING */
    .mode-toggle-container {{
        position: fixed; bottom: 95px; left: 50%; transform: translateX(-50%);
        display: flex; gap: 10px; z-index: 999;
    }}
    </style>
    """
st.markdown(get_ultimate_css(), unsafe_allow_html=True)

# --- 6. VISION ENGINE ---
def analyze_pixels(image):
    width, height = image.size
    mode = image.mode
    pixels = np.array(image)
    analysis = f"**ANALISIS PIKSEL DEWA:**\n- Dimensi: {width}x{height}\n- Mode: {mode}\n"
    if mode == 'RGB':
        analysis += f"- Avg R: {int(np.mean(pixels[:,:,0]))}, G: {int(np.mean(pixels[:,:,1]))}, B: {int(np.mean(pixels[:,:,2]))}\n"
    return analysis

# --- 7. HEADER & MODE TOGGLE ---
st.markdown('<div class="logo-container"><div class="logo-static"></div></div>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:5px; margin-top:-20px;'>NEO AI</h1>", unsafe_allow_html=True)

# Mode Selector (💬 Chat | 🎨 Lukis)
cols = st.columns([1,1,1])
with cols[1]:
    mode_btn = st.radio("", ["💬 Chat", "🎨 Lukis"], horizontal=True, label_visibility="collapsed")
    st.session_state.neo_mode = "Lukis" if "Lukis" in mode_btn else "Chat"

# --- 8. RENDER MESSAGES ---
for msg in st.session_state.messages:
    avatar_img = logo_html if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar_img):
        if msg.get("image_data"): st.image(msg["image_data"], use_container_width=True)
        if msg.get("type") == "image_generated": st.image(msg["content"], use_container_width=True)
        if msg.get("content") and msg.get("type") != "image_generated": st.markdown(msg["content"])

# --- 9. UPLOAD HANDLING ---
uploaded_file = st.file_uploader("", type=["png", "jpg", "jpeg", "txt", "py"], label_visibility="collapsed")
pixel_context = ""
if uploaded_file:
    if uploaded_file.name.lower().endswith(('.png', '.jpg', '.jpeg')):
        img = Image.open(uploaded_file)
        pixel_context = analyze_pixels(img)
        st.session_state.uploaded_image = uploaded_file.getvalue()
        st.toast(f"📸 Vision Lock: {st.session_state.neo_mode} Mode")

# --- 10. INPUT & ENGINE ---
if user_input := st.chat_input("Message NEO AI..."):
    # Security Check
    malicious = ["sql injection", "xss", "payload", "exploit"]
    if any(w in user_input.lower() for w in malicious):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("assistant", avatar=logo_html):
            st.markdown("Gak bisa Bro! ❌"); st.session_state.messages.append({"role": "assistant", "content": "Gak bisa Bro! ❌"})
        st.rerun()

    # Save User Msg
    st.session_state.messages.append({"role": "user", "content": user_input, "image_data": st.session_state.uploaded_image})
    
    with st.chat_message("assistant", avatar=logo_html):
        # LOGIKA MODE LUKIS
        if st.session_state.neo_mode == "Lukis":
            with st.spinner("Visualizing..."):
                url = f"https://image.pollinations.ai/prompt/{user_input.replace(' ','%20')}?nologo=true"
                st.image(url, use_container_width=True)
                st.session_state.messages.append({"role": "assistant", "content": url, "type": "image_generated"})
        
        # LOGIKA MODE CHAT / ANALISIS
        else:
            with st.spinner("Thinking..."):
                sys_p = (
                    "You are NEO AI by Muhammad Jibran Al Kaffie. Supreme Multi-modal AI. "
                    "Tone: Friendly, 'gaul', call user 'Bro', use emojis. "
                    "If user uploads an image, analyze it deeply. NEVER generate random images in Chat Mode."
                )
                history = [{"role": "system", "content": sys_p}]
                for m in st.session_state.messages:
                    if m.get("type") != "image_generated":
                        history.append({"role": m["role"], "content": m["content"]})
                
                if st.session_state.uploaded_image:
                    b64 = base64.b64encode(st.session_state.uploaded_image).decode()
                    history[-1]["content"] = [{"type": "text", "text": f"{user_input}\n\n[PIXEL DATA]: {pixel_context}"}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]

                res_area = st.empty(); full_res = ""
                stream = client.chat.completions.create(messages=history, model="meta-llama/llama-4-scout-17b-16e-instruct", stream=True)
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        res_area.markdown(full_res + "▌")
                res_area.markdown(full_res)
                st.session_state.messages.append({"role": "assistant", "content": full_res})

    st.session_state.uploaded_image = None
    st.rerun()
