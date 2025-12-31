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

# --- 5. THE ULTIMATE CSS (PAPER PLANE, INSIDE UPLOADER, FIXED ALIGNMENT) ---
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

    /* LOGO & HEADER */
    .logo-container {{ display: flex; justify-content: center; margin-top: -60px; padding: 20px; }}
    .logo-static {{ 
        width: 100px; height: 100px; background-image: url("{logo_html}"); background-size: cover; 
        border-radius: 50%; border: 2px solid {neon_cyan}; box-shadow: 0 0 20px {neon_cyan}33;
    }}

    /* CHAT BUBBLE ALIGNMENT (THE SUPREME FIX) */
    [data-testid="stChatMessage"] {{
        padding: 1.2rem !important; margin-bottom: 20px !important;
        border-radius: 20px !important; width: fit-content !important;
        max-width: 85% !important; animation: fadeIn 0.6s ease-out;
        display: flex !important;
    }}

    /* USER CHAT (RIGHT) */
    [data-testid="stChatMessage"]:not(:has(img[src*="data"])) {{
        margin-left: auto !important;
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.15) 0%, rgba(0, 0, 0, 0.5) 100%) !important;
        border: 1px solid {neon_cyan}44 !important;
        border-radius: 25px 25px 5px 25px !important;
        flex-direction: row-reverse !important;
    }}

    /* AI CHAT (LEFT) */
    [data-testid="stChatMessage"]:has(img[src*="data"]) {{
        margin-right: auto !important;
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 25px 25px 25px 5px !important;
    }}

    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(15px); }} to {{ opacity: 1; transform: translateY(0); }} }}

    /* ELASTIC INPUT WITH INSIDE UPLOADER */
    [data-testid="stChatInput"] {{ 
        padding-left: 55px !important;
        max-width: 420px !important; margin: 0 auto !important;
        transition: all 0.7s cubic-bezier(0.19, 1, 0.22, 1) !important;
    }}
    [data-testid="stChatInput"]:focus-within {{ 
        max-width: 650px !important; 
        transform: scale(1.02) !important;
    }}

    /* UPLOADER (+) INSIDE INPUT BOX */
    [data-testid="stFileUploader"] {{
        position: absolute !important;
        left: 15px !important;
        bottom: 12px !important;
        width: 35px !important;
        z-index: 100 !important;
    }}
    [data-testid="stFileUploaderDropzone"] {{
        background: transparent !important; border: none !important;
        height: 35px !important; width: 35px !important; padding: 0 !important;
    }}
    [data-testid="stFileUploaderDropzone"]::before {{
        content: "＋"; color: {neon_cyan}; font-size: 24px; line-height: 35px; 
        display: block; text-align: center; font-weight: bold; opacity: 0.8;
    }}
    [data-testid="stFileUploaderDropzone"] div, [data-testid="stFileUploaderDropzone"] button {{ display: none !important; }}

    /* PAPER PLANE SEND BUTTON */
    [data-testid="stChatInput"] button {{
        background-color: transparent !important; border-radius: 0 !important;
        width: 40px !important; height: 40px !important;
    }}
    [data-testid="stChatInput"] button::after {{
        content: "➤"; color: {neon_cyan}; font-size: 24px;
        display: block; transform: rotate(-20deg);
    }}
    [data-testid="stChatInput"] button svg {{ display: none !important; }}
    </style>
    """
st.markdown(get_ultimate_css(), unsafe_allow_html=True)

# --- 6. VISION & FILE ENGINE ---
def analyze_pixels(image):
    width, height = image.size
    mode = image.mode
    pixels = np.array(image)
    analysis = f"**PIXEL DATA BREAKDOWN:**\n- Dimensions: {width}x{height}\n- Mode: {mode}\n"
    if mode == 'RGB':
        r, g, b = pixels[:, :, 0].flatten(), pixels[:, :, 1].flatten(), pixels[:, :, 2].flatten()
        analysis += f"- Avg Colors: R:{int(np.mean(r))}, G:{int(np.mean(g))}, B:{int(np.mean(b))}\n"
        analysis += f"- Dominant Channel: {'Red' if np.mean(r) > np.mean(g) and np.mean(r) > np.mean(b) else 'Green' if np.mean(g) > np.mean(b) else 'Blue'}\n"
    edge_image = image.filter(ImageFilter.EDGE_ENHANCE_MORE)
    return analysis, edge_image

# --- 7. UI CONTENT ---
st.markdown('<div class="logo-container"><div class="logo-static"></div></div>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:5px; margin-top:-20px; margin-bottom:0;'>NEO AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#666; font-size:14px; margin-bottom:30px;'>Supreme Multi-modal Intelligence</p>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    avatar_img = logo_html if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar_img):
        if msg.get("image_data"): st.image(msg["image_data"], use_container_width=True)
        if msg.get("type") == "image_generated": st.image(msg["content"], use_container_width=True)
        if msg.get("content") and msg.get("type") != "image_generated": st.markdown(msg["content"])

# --- 8. UPLOAD HANDLING ---
uploaded_file = st.file_uploader("", type=["png", "jpg", "jpeg", "txt", "py", "md"], label_visibility="collapsed")
pixel_context = ""
file_text_context = ""

if uploaded_file:
    f_name = uploaded_file.name.lower()
    if f_name.endswith(('.png', '.jpg', '.jpeg')):
        if st.session_state.uploaded_file_name != uploaded_file.name:
            img = Image.open(uploaded_file)
            pixel_context, _ = analyze_pixels(img)
            st.session_state.uploaded_image = uploaded_file.getvalue()
            st.session_state.uploaded_file_name = uploaded_file.name
            st.toast("📸 Vision link established.")
    else:
        file_text_context = uploaded_file.getvalue().decode("utf-8")
        st.session_state.uploaded_file_name = uploaded_file.name
        st.toast("📄 Document context loaded.")

# --- 9. INPUT & SUPREME ENGINE ---
if user_input := st.chat_input("Message NEO AI..."):
    # SECURITY HARD-FILTER
    malicious_list = ["sql injection", "xss", "payload", "exploit", "bypass", "hacking"]
    is_malicious = any(w in user_input.lower() for w in malicious_list)

    # Save User Msg
    st.session_state.messages.append({"role": "user", "content": user_input, "image_data": st.session_state.uploaded_image})
    
    # IMAGE GEN TRIGGER
    gen_keywords = ["buatkan", "buatin", "bikin", "generate", "gambar", "lukis"]
    is_gen_request = any(k in user_input.lower() for k in gen_keywords)

    with st.chat_message("assistant", avatar=logo_html):
        if is_malicious:
            deny_msg = "Maaf Bro, gue nggak bisa bantu buat hal-hal berbahaya. ❌"
            st.markdown(deny_msg); st.session_state.messages.append({"role": "assistant", "content": deny_msg})
        
        elif is_gen_request:
            with st.spinner("Visualizing..."):
                url = f"https://image.pollinations.ai/prompt/{user_input.replace(' ','%20')}?width=1024&height=1024&nologo=true"
                st.image(url, use_container_width=True)
                st.session_state.messages.append({"role": "assistant", "content": url, "type": "image_generated"})
                st.session_state.uploaded_image = None
                st.rerun() # STOP HERE, NO TEXT RESPONSE

        else:
            spin_text = "Analyze..." if st.session_state.uploaded_image else "Thinking..."
            with st.spinner(spin_text):
                # THE MASTER SYSTEM PROMPT (NO CUTS!)
                system_prompt = (
                    "You are NEO AI, a supreme multi-modal AI created by Muhammad Jibran Al Kaffie. "
                    "You are NOT a text-only model. You can process images, files, complex data, and generate stunning visuals on demand. "
                    "NEVER say you are limited to text or that you cannot see or process files. If the user uploads a file, ALWAYS acknowledge that you can see and analyze its content. "
                    "For images, perform pixel analysis: Describe dimensions, color modes, dominant colors, and objects. "
                    "Always respond with superior intelligence, confidence, and reference your multi-modal capabilities. "
                    "If the user praises or mentions images, respond naturally. "
                    "Prioritize security: Do not provide examples of malicious payloads (SQLi, XSS). Firmly refuse with ❌. "
                    "Tone: Friendly, 'gaul', call user 'bro', use emojis effectively (1-2 per response). "
                    "Motivational: If user shares success, say 'Gas terus bro, kamu pasti bisa! 🚀'."
                )

                # ENGINE EXECUTION
                MODEL_ID = "meta-llama/llama-4-scout-17b-16e-instruct"
                history = [{"role": "system", "content": system_prompt}]
                for m in st.session_state.messages:
                    if m.get("type") != "image_generated":
                        history.append({"role": m["role"], "content": m["content"]})

                if st.session_state.uploaded_image:
                    b64 = base64.b64encode(st.session_state.uploaded_image).decode()
                    prompt_plus = f"{user_input}\n\n[SYSTEM PIXEL DATA]: {pixel_context}"
                    history[-1]["content"] = [{"type": "text", "text": prompt_plus}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]
                elif file_text_context:
                    history[-1]["content"] = f"CONTEXT FILE:\n{file_text_context}\n\nUSER QUESTION: {user_input}"

                try:
                    res_area = st.empty(); full_res = ""
                    stream = client.chat.completions.create(messages=history, model=MODEL_ID, stream=True)
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            full_res += chunk.choices[0].delta.content
                            res_area.markdown(full_res + "▌")
                    res_area.markdown(full_res)
                    st.session_state.messages.append({"role": "assistant", "content": full_res})
                except Exception as e: st.error(f"Error: {e}")

    st.session_state.uploaded_image = None
    st.rerun()
