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
if "uploaded_file_name" not in st.session_state:
    st.session_state.uploaded_file_name = None
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

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

# --- 5. THE ULTIMATE CSS (COMPLETE & ANIMATED) ---
def get_ultimate_css():
    neon_cyan = "#00ffff"
    return f"""
    <style>
    html, body, [data-testid="stAppViewContainer"] {{ 
        background-color: #050505 !important; 
        color: #f0f0f0 !important; 
    }}
    [data-testid="stStatusWidget"], header, footer {{ visibility: hidden; }}

    /* LOGO & HEADER CENTERED */
    .logo-container {{ display: flex; justify-content: center; margin-top: -60px; margin-bottom: 10px; }}
    .logo-static {{ 
        width: 100px; height: 100px; background-image: url("{logo_html}"); background-size: cover; 
        border-radius: 50%; border: 2px solid {neon_cyan}; box-shadow: 0 0 20px {neon_cyan}33;
    }}

    /* CHAT BUBBLE STYLING */
    [data-testid="stChatMessage"] {{
        padding: 1.2rem !important; margin-bottom: 20px !important;
        border-radius: 20px !important; max-width: 85% !important;
        animation: fadeIn 0.5s ease-out;
    }}
    [data-testid="stChatMessage"] img {{
        border-radius: 15px !important; margin-bottom: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }}
    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}

    /* ANIMASI INPUT MEMANJANG & MEMBESAR (ELASTIC) */
    [data-testid="stChatInput"] {{ 
        padding: 10px !important; max-width: 450px !important; margin: 0 auto !important;
        transition: all 0.7s cubic-bezier(0.19, 1, 0.22, 1) !important;
    }}
    [data-testid="stChatInput"]:focus-within {{ 
        max-width: 100% !important; transform: scale(1.03) !important;
    }}

    /* TOMBOL PANAH CHATGPT (CSS ONLY) */
    [data-testid="stChatInput"] button {{
        background-color: #ffffff !important; border-radius: 9px !important;
        width: 34px !important; height: 34px !important; bottom: 12px !important; right: 12px !important;
    }}
    [data-testid="stChatInput"] button::after {{
        content: ""; display: block; width: 8px; height: 8px;
        border-top: 2.5px solid #000; border-right: 2.5px solid #000;
        transform: rotate(-45deg); margin: 3px auto 0;
    }}
    [data-testid="stChatInput"] button svg {{ display: none !important; }}

    /* UPLOADER HACK */
    [data-testid="stFileUploader"] {{ width: 42px !important; margin: 0 auto !important; margin-top: -65px !important; position: relative; z-index: 10; }}
    [data-testid="stFileUploaderDropzone"] {{
        padding: 0 !important; border-radius: 50% !important; background: rgba(0,255,255,0.15) !important;
        border: 1px solid {neon_cyan}44 !important; height: 40px !important; width: 40px !important;
    }}
    [data-testid="stFileUploaderDropzone"]::before {{ content: "＋"; color: {neon_cyan}; font-size: 22px; line-height: 40px; font-weight: bold; text-align:center; display:block; }}
    [data-testid="stFileUploaderDropzone"] div, [data-testid="stFileUploaderDropzone"] button {{ display: none !important; }}

    .blurred {{ filter: blur(1.5px); transition: filter 0.5s ease; }}
    </style>
    """
st.markdown(get_ultimate_css(), unsafe_allow_html=True)

# --- 6. CORE LOGIC FUNCTIONS ---
def analyze_pixels(image):
    width, height = image.size
    mode = image.mode
    pixels = np.array(image)
    analysis = f"**DIMENSIONS:** {width}x{height} | **MODE:** {mode}\n"
    if mode == 'RGB':
        r, g, b = pixels[:, :, 0].flatten(), pixels[:, :, 1].flatten(), pixels[:, :, 2].flatten()
        analysis += f"**AVG COLOR:** (R:{int(np.mean(r))}, G:{int(np.mean(g))}, B:{int(np.mean(b))})\n"
        analysis += f"**DOMINANT:** ({np.argmax(np.bincount(r))}, {np.argmax(np.bincount(g))}, {np.argmax(np.bincount(b))})\n"
    edge_image = image.filter(ImageFilter.EDGE_ENHANCE)
    return analysis, edge_image

# --- 7. HEADER ---
st.markdown('<div class="logo-container"><div class="logo-static"></div></div>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:6px; margin-top:-5px; margin-bottom:0;'>NEO AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#666; font-size:14px;'>Supreme Multi-modal Intelligence</p>", unsafe_allow_html=True)

# --- 8. RENDER MESSAGES ---
for msg in st.session_state.messages:
    avatar = "logo.png" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        if msg.get("image_data"):
            st.image(msg["image_data"], use_container_width=True)
        if msg.get("type") == "image_generated":
            st.image(msg["content"], use_container_width=True)
        if msg.get("content") and msg.get("type") != "image_generated":
            st.markdown(msg["content"])

# --- 9. UPLOAD & FILE PROCESSING ---
uploaded_file = st.file_uploader("", type=["png", "jpg", "jpeg", "txt", "py", "md"], label_visibility="collapsed")
file_context = ""

if uploaded_file:
    file_name = uploaded_file.name.lower()
    if file_name.endswith(('.png', '.jpg', '.jpeg')):
        if st.session_state.uploaded_file_name != uploaded_file.name:
            image = Image.open(uploaded_file)
            analysis, edge_img = analyze_pixels(image)
            st.session_state.uploaded_image = uploaded_file.getvalue()
            st.session_state.uploaded_file_name = uploaded_file.name
            st.toast("📸 Vision data locked.")
            with st.expander("🛠️ Internal Vision Logs"):
                st.code(analysis, language="yaml")
                st.image(edge_img, caption="Edge Enhancement Analysis")
    else:
        file_context = uploaded_file.getvalue().decode("utf-8")
        st.session_state.uploaded_file_name = uploaded_file.name
        st.toast("📄 Context loaded.")

# --- 10. INPUT & ENGINE ---
if user_input := st.chat_input("Command NEO AI..."):
    # Siapkan paket pesan
    pkg = {"role": "user", "content": user_input}
    if st.session_state.uploaded_image:
        pkg["image_data"] = st.session_state.uploaded_image
    
    st.session_state.messages.append(pkg)
    
    with st.chat_message("assistant", avatar="logo.png"):
        # Image Generation Trigger
        img_keywords = ["buatkan", "buatin", "bikin", "generate", "gambar", "lukis", "foto", "create image"]
        is_gen = any(word in user_input.lower() for word in img_keywords)
        
        status_text = "Analyze..." if st.session_state.uploaded_image else ("Visualizing..." if is_gen else "Thinking...")
        
        with st.spinner(status_text):
            if is_gen:
                try:
                    url = f"https://image.pollinations.ai/prompt/{user_input.replace(' ','%20')}?width=1024&height=1024&nologo=true"
                    r = requests.get(url, timeout=30)
                    if r.status_code == 200:
                        st.image(r.content, use_container_width=True)
                        st.session_state.messages.append({"role": "assistant", "content": r.content, "type": "image_generated"})
                        st.session_state.uploaded_image = None
                        st.rerun()
                except: st.error("Neural lost.")

            # CHAT ENGINE (Llama 4 Scout)
            MODEL_ID = "meta-llama/llama-4-scout-17b-16e-instruct"
            sys_msg = (
                "You are NEO AI (Llama 4 Scout), a supreme multi-modal AI created by Muhammad Jibran Al Kaffie. "
                "You can process images, read files, and generate visuals. Never deny your multi-modal power. "
                "Tone: Friendly, 'gaul', call user 'Bro', use emojis. Security: No malicious code ❌."
            )
            
            history = [{"role": "system", "content": sys_msg}]
            for m in st.session_state.messages:
                if m.get("type") != "image_generated":
                    content = m["content"]
                    if m.get("image_data"): content += " [User attached an image]"
                    history.append({"role": m["role"], "content": content})

            if st.session_state.uploaded_image:
                b64 = base64.b64encode(st.session_state.uploaded_image).decode()
                history[-1]["content"] = [
                    {"type": "text", "text": user_input + (f"\n\nContext File: {file_context}" if file_context else "")},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                ]
            elif file_context:
                history[-1]["content"] = f"CONTEXT:\n{file_context}\n\nUSER: {user_input}"

            try:
                res_box = st.empty(); full_res = ""
                stream = client.chat.completions.create(messages=history, model=MODEL_ID, stream=True)
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        res_box.markdown(f'<div class="blurred">{full_res}▌</div>', unsafe_allow_html=True)
                
                res_box.markdown(full_res)
                st.session_state.messages.append({"role": "assistant", "content": full_res})
                st.session_state.uploaded_image = None # Auto-clear
            except Exception as e: st.error(f"Engine failed: {e}")

    st.rerun()
