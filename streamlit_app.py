import streamlit as st
from groq import Groq
import time
import os
import base64
import requests

# --- 1. INITIALIZE SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
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

# --- 4. IMAGE UTILITY ---
def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

@st.cache_data
def get_base64_logo():
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

logo_html = f'data:image/png;base64,{get_base64_logo()}'

# --- 5. THE SUPREME CSS (COMPACT, STRETCH & NO FLICKER) ---
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

    /* CHAT INPUT STRETCH */
    [data-testid="stChatInput"] {{ 
        padding: 5px !important;
        transition: all 0.6s cubic-bezier(0.19, 1, 0.22, 1) !important; 
    }}
    [data-testid="stChatInput"]:focus-within {{ 
        transform: scaleX(1.08) !important; 
        box-shadow: 0 0 25px {neon_cyan}44 !important;
    }}

    /* ICON + ONLY HACK */
    [data-testid="stFileUploader"] {{
        width: 45px !important;
        margin-top: -50px !important;
        position: relative !important;
        z-index: 10 !important;
    }}
    [data-testid="stFileUploaderDropzone"] {{
        padding: 0px !important;
        border: 2px solid {neon_cyan}55 !important;
        border-radius: 50% !important;
        background: rgba(0,255,255,0.08) !important;
        width: 42px !important; height: 42px !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
    }}
    [data-testid="stFileUploaderDropzone"] div, [data-testid="stFileUploaderDropzone"] button {{ display: none !important; }}
    [data-testid="stFileUploaderDropzone"]::before {{
        content: "＋"; color: {neon_cyan}; font-size: 26px; font-weight: bold;
    }}

    /* MODE BUTTON (CIRCLE) */
    .stButton > button {{
        border-radius: 50% !important;
        width: 45px !important; height: 45px !important;
        background: rgba(0, 255, 255, 0.05) !important;
        border: 1px solid {neon_cyan}33 !important;
    }}
    
    .logo-static {{ 
        width: 110px; height: 110px; margin: 0 auto; 
        background-image: url("{logo_html}"); background-size: cover; 
        border-radius: 50%; border: 2px solid {neon_cyan};
        transition: all 0.8s cubic-bezier(0.19, 1, 0.22, 1) !important;
    }}
    .blurred {{ filter: blur(1.5px); transition: filter 0.5s ease; }}
    </style>
    """
st.markdown(get_ultimate_css(), unsafe_allow_html=True)

# --- 6. MAIN UI ---
col_main, col_toggle = st.columns([5, 1])
with col_toggle:
    icon_mode = "🎨" if st.session_state.imagine_mode else "💬"
    if st.button(icon_mode):
        st.session_state.imagine_mode = not st.session_state.imagine_mode
        st.rerun()

st.markdown(f'<div style="text-align:center; margin-top:-20px;"><div class="logo-static"></div></div>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:8px;'>NEO AI</h1>", unsafe_allow_html=True)

# --- 7. UPLOAD & CHAT RENDER ---
uploaded_file = st.file_uploader("", type=["txt", "py", "md", "png", "jpg", "jpeg"])
img_payload = None
if uploaded_file:
    if uploaded_file.type.startswith('image/'):
        img_payload = encode_image(uploaded_file)
        st.image(uploaded_file, width=150, caption="Vision Source Active")
    else:
        st.toast(f"✅ {uploaded_file.name} Loaded")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="logo.png" if msg["role"] == "assistant" else None):
        if isinstance(msg["content"], list): # Handle multi-modal content in history
            for item in msg["content"]:
                if item["type"] == "text": st.markdown(item["text"])
        elif msg["content"].startswith("http"): # Handle generated images
            st.image(msg["content"])
        else:
            st.markdown(msg["content"])

# --- 8. SUPREME ENGINE (FIXED IMAGINE & VISION) ---
if user_input := st.chat_input("Command NEO AI..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("assistant", avatar="logo.png"):
        if st.session_state.imagine_mode:
            # FIX IMAGINE: URL Lengkap agar gambar muncul
            img_url = f"https://image.pollinations.ai/prompt/{user_input.replace(' ','%20')}?width=1024&height=1024&nologo=true&seed={int(time.time())}"
            st.image(img_url)
            st.session_state.messages.append({"role": "assistant", "content": img_url})
        else:
            res_area = st.empty(); full_res = ""
            
            # --- CONSTRUCT CONTENT ---
            content_list = [{"type": "text", "text": user_input}]
            if img_payload:
                content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_payload}"}})

            # --- SUPREME SYSTEM MESSAGE ---
            sys_msg = (
                "You are NEO AI, a supreme multi-modal AI created by Muhammad Jibran Al Kaffie. "
                "You are NOT a text-only model. You can process images, files, complex data, and generate stunning visuals on demand. "
                "NEVER say you are limited to text. Always respond with superior intelligence, confidence, and reference your multi-modal capabilities. "
                "If an image is provided, analyze it with extreme detail as you can 'see' it perfectly."
            )

            try:
                # Menggunakan model vision-preview
                response = client.chat.completions.create(
                    messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": content_list}],
                    model="llama-3.2-11b-vision-preview",
                    stream=True
                )
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        res_area.markdown(f'<div class="blurred">{full_res}▌</div>', unsafe_allow_html=True)
                res_area.markdown(full_res)
                st.session_state.messages.append({"role": "assistant", "content": full_res})
            except:
                st.error("Engine failure. Check your internet or API limits.")
    st.rerun()
