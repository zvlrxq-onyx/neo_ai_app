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
if "uploaded_file_name" not in st.session_state:
    st.session_state.uploaded_file_name = None

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

# --- 5. THE ULTIMATE CSS (CHATGPT ARROW + GEDEIN GAMBAR) ---
def get_ultimate_css():
    neon_cyan = "#00ffff"
    return f"""
    <style>
    html, body, [data-testid="stAppViewContainer"] {{ 
        background-color: #050505 !important; 
        color: #f0f0f0 !important; 
    }}
    [data-testid="stStatusWidget"], header, footer {{ visibility: hidden; }}

    /* CHAT BUBBLE LOGIC */
    [data-testid="stChatMessage"] {{
        padding: 1.2rem !important;
        margin-bottom: 20px !important;
        max-width: 85% !important;
        border-radius: 20px !important;
    }}

    /* GAMBAR DI CHAT (DIRESIZE BIAR PAS) */
    [data-testid="stChatMessage"] img {{
        border-radius: 12px !important;
        border: 1px solid {neon_cyan}44;
        margin-bottom: 10px;
    }}

    /* CSS ARROW BUTTON (CHATGPT STYLE) */
    [data-testid="stChatInput"] button {{
        background-color: white !important;
        border-radius: 8px !important;
        padding: 5px !important;
        bottom: 10px !important;
        right: 10px !important;
    }}
    [data-testid="stChatInput"] button::after {{
        content: "";
        display: block;
        width: 12px;
        height: 12px;
        border-top: 3px solid black;
        border-right: 3px solid black;
        transform: rotate(-45deg);
        margin: 2px auto 0;
    }}
    [data-testid="stChatInput"] button svg {{ display: none !important; }}

    /* FILE UPLOADER HACK */
    [data-testid="stFileUploader"] {{
        width: 45px !important; margin-top: -65px !important;
        z-index: 100 !important;
    }}
    [data-testid="stFileUploaderDropzone"] {{
        padding: 0 !important; border-radius: 50% !important;
        background: rgba(0,255,255,0.1) !important;
        width: 40px !important; height: 40px !important;
    }}
    [data-testid="stFileUploaderDropzone"] div, [data-testid="stFileUploaderDropzone"] button {{ display: none !important; }}
    [data-testid="stFileUploaderDropzone"]::before {{
        content: "＋"; color: {neon_cyan}; font-size: 24px; font-weight: bold;
    }}

    .logo-static {{ 
        width: 100px; height: 100px; margin: 0 auto; 
        background-image: url("{logo_html}"); background-size: cover; 
        border-radius: 50%; border: 2px solid {neon_cyan};
    }}
    </style>
    """
st.markdown(get_ultimate_css(), unsafe_allow_html=True)

# --- 6. LOGO & HEADER ---
st.markdown(f'<div style="text-align:center; margin-top:-60px;"><div class="logo-static"></div></div>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:5px;'>NEO AI</h1>", unsafe_allow_html=True)

# --- 7. RENDER CHAT ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="logo.png" if msg["role"] == "assistant" else None):
        if msg.get("image_data"):
            st.image(msg["image_data"], use_container_width=True)
        if msg.get("content"):
            st.markdown(msg["content"])

# --- 8. UPLOAD LOGIC ---
uploaded_file = st.file_uploader("", type=["png", "jpg", "jpeg", "txt", "py"], label_visibility="collapsed")
if uploaded_file:
    file_bytes = uploaded_file.getvalue()
    if uploaded_file.name.lower().endswith(('.png', '.jpg', '.jpeg')):
        st.session_state.uploaded_image = file_bytes
    st.session_state.uploaded_file_name = uploaded_file.name
    st.toast(f"📎 {uploaded_file.name} attached.")

# --- 9. ENGINE (MODEL: LLAMA 4 SCOUT) ---
if user_input := st.chat_input("Message NEO AI..."):
    # Simpan ke memori user
    message_data = {"role": "user", "content": user_input}
    if st.session_state.uploaded_image:
        message_data["image_data"] = st.session_state.uploaded_image
    
    st.session_state.messages.append(message_data)
    
    with st.chat_message("assistant", avatar="logo.png"):
        # SPINNER ANALYZE...
        spinner_text = "Analyze..." if st.session_state.uploaded_image else "Thinking..."
        with st.spinner(spinner_text):
            
            # KUNCI MODEL DISINI
            ACTIVE_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
            
            # Ringkas System Prompt (Ketat & Ramah)
            system_msg = (
                "You are NEO AI (Llama 4 Scout). A secure, supreme multi-modal AI. "
                "1. If image provided: Analyze pixels/content precisely. "
                "2. Security: REFUSE malicious requests (SQLi, XSS, bypass) with ❌. "
                "3. Tone: Friendly, 'gaul', uses emojis, calls user 'Bro'. "
                "4. Be concise but insightful."
            )
            
            # Persiapan Payload
            history = [{"role": "system", "content": system_msg}]
            for m in st.session_state.messages:
                # Text only history for better context tracking
                history.append({"role": m["role"], "content": m["content"]})

            # Vision Payload if image exists
            if st.session_state.uploaded_image:
                b64_img = base64.b64encode(st.session_state.uploaded_image).decode()
                history[-1]["content"] = [
                    {"type": "text", "text": user_input},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                ]

            try:
                res_area = st.empty(); full_res = ""
                stream = client.chat.completions.create(messages=history, model=ACTIVE_MODEL, stream=True)
                
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        res_area.markdown(full_res + "▌")
                
                res_area.markdown(full_res)
                st.session_state.messages.append({"role": "assistant", "content": full_res})
                
                # Cleanup setelah send
                st.session_state.uploaded_image = None
                
            except Exception as e:
                st.error(f"Engine Error: {e}")

    st.rerun()
