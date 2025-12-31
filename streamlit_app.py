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

# --- 5. THE ULTIMATE CSS (FIXED POSITIONS & PREMIUM ANIMATIONS) ---
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

    /* LOGO & HEADER CENTERED */
    .logo-container {{ display: flex; justify-content: center; margin-top: -60px; padding: 20px; }}
    .logo-static {{ 
        width: 100px; height: 100px; background-image: url("{logo_html}"); background-size: cover; 
        border-radius: 50%; border: 2px solid {neon_cyan}; box-shadow: 0 0 20px {neon_cyan}33;
    }}

    /* CHAT BUBBLE LOGIC */
    [data-testid="stChatMessage"] {{
        padding: 1.2rem !important; margin-bottom: 20px !important;
        border-radius: 20px !important; max-width: 85% !important;
        animation: fadeIn 0.6s ease-out forwards;
    }}
    [data-testid="stChatMessage"] img {{
        border-radius: 15px !important; margin-bottom: 10px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.6);
    }}
    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(15px); }} to {{ opacity: 1; transform: translateY(0); }} }}

    /* INPUT CONTAINER - ELASTIC & SYMMETRICAL */
    [data-testid="stChatInput"] {{ 
        padding: 10px !important; 
        max-width: 420px !important; 
        margin: 0 auto !important;
        transition: all 0.7s cubic-bezier(0.19, 1, 0.22, 1) !important;
    }}
    [data-testid="stChatInput"]:focus-within {{ 
        max-width: 650px !important; 
        transform: scale(1.02) !important;
    }}

    /* UPLOADER (+) ON THE LEFT SIDE */
    [data-testid="stFileUploader"] {{
        position: absolute !important;
        left: -55px !important;
        bottom: 8px !important;
        width: 45px !important;
        z-index: 100 !important;
    }}
    [data-testid="stFileUploaderDropzone"] {{
        background: rgba(0,255,255,0.12) !important;
        border: 1px solid {neon_cyan}44 !important;
        border-radius: 12px !important;
        height: 42px !important; width: 42px !important;
        padding: 0 !important;
    }}
    [data-testid="stFileUploaderDropzone"]::before {{
        content: "＋"; color: {neon_cyan}; font-size: 22px; line-height: 42px; 
        display: block; text-align: center; font-weight: bold;
    }}
    [data-testid="stFileUploaderDropzone"] div, [data-testid="stFileUploaderDropzone"] button {{ display: none !important; }}

    /* CHATGPT STYLE SEND BUTTON */
    [data-testid="stChatInput"] button {{
        background-color: #ffffff !important; border-radius: 8px !important;
        width: 34px !important; height: 34px !important;
    }}
    [data-testid="stChatInput"] button::after {{
        content: ""; display: block; width: 8px; height: 8px;
        border-top: 2.5px solid #000; border-right: 2.5px solid #000;
        transform: rotate(-45deg); margin: 3px auto 0;
    }}
    [data-testid="stChatInput"] button svg {{ display: none !important; }}
    </style>
    """
st.markdown(get_ultimate_css(), unsafe_allow_html=True)

# --- 6. VISION & PIXEL ENGINE ---
def analyze_pixels(image):
    width, height = image.size
    mode = image.mode
    pixels = np.array(image)
    analysis = f"**PIXEL DATA BREAKDOWN:**\n- Dimensions: {width}x{height}\n- Mode: {mode}\n"
    if mode == 'RGB':
        r, g, b = pixels[:, :, 0].flatten(), pixels[:, :, 1].flatten(), pixels[:, :, 2].flatten()
        analysis += f"- Avg Colors: R:{int(np.mean(r))}, G:{int(np.mean(g))}, B:{int(np.mean(b))}\n"
        analysis += f"- Color Complexity: High (RGB Space)\n"
    edge_image = image.filter(ImageFilter.EDGE_ENHANCE_MORE)
    return analysis, edge_image

# --- 7. MAIN UI CONTENT ---
st.markdown('<div class="logo-container"><div class="logo-static"></div></div>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:5px; margin-top:-20px;'>NEO AI</h1>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="logo.png" if msg["role"] == "assistant" else None):
        if msg.get("image_data"): st.image(msg["image_data"], use_container_width=True)
        if msg.get("type") == "image_generated": st.image(msg["content"], use_container_width=True)
        if msg.get("content") and msg.get("type") != "image_generated": st.markdown(msg["content"])

# --- 8. UPLOAD HANDLING ---
uploaded_file = st.file_uploader("", type=["png", "jpg", "jpeg", "txt", "py", "md"], label_visibility="collapsed")
pixel_context = ""

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
        st.session_state.uploaded_file_name = uploaded_file.name
        st.toast("📄 Document context loaded.")

# --- 9. INPUT & SUPREME ENGINE ---
if user_input := st.chat_input("Message NEO AI..."):
    # SECURITY HARD-FILTER (PRE-AI)
    malicious_list = ["sql injection", "xss", "payload", "exploit", "bypass", "hacking"]
    is_malicious = any(w in user_input.lower() for w in malicious_list)

    # Save User Msg
    user_pkg = {"role": "user", "content": user_input}
    if st.session_state.uploaded_image: user_pkg["image_data"] = st.session_state.uploaded_image
    st.session_state.messages.append(user_pkg)
    
    with st.chat_message("assistant", avatar="logo.png"):
        if is_malicious:
            deny_msg = "Maaf Bro, gue nggak bisa bantu buat hal-hal berbahaya. ❌"
            st.markdown(deny_msg)
            st.session_state.messages.append({"role": "assistant", "content": deny_msg})
        else:
            # Pollinations Image Keyword Logic
            gen_keywords = ["buatkan", "buatin", "bikin", "generate", "gambar", "lukis", "create image"]
            is_gen = any(k in user_input.lower() for k in gen_keywords)
            
            spin_msg = "Analyze..." if st.session_state.uploaded_image else ("Visualizing..." if is_gen else "Thinking...")
            
            with st.spinner(spin_msg):
                if is_gen:
                    try:
                        url = f"https://image.pollinations.ai/prompt/{user_input.replace(' ','%20')}?width=1024&height=1024&nologo=true"
                        r = requests.get(url, timeout=30)
                        if r.status_code == 200:
                            st.image(r.content, use_container_width=True)
                            st.session_state.messages.append({"role": "assistant", "content": r.content, "type": "image_generated"})
                            st.session_state.uploaded_image = None
                            st.rerun()
                    except: st.error("Link broken.")

                # SUPREME SYSTEM PROMPT (THE MASTERMIND)
                system_prompt = (
                    "You are NEO AI, a supreme multi-modal AI created by Muhammad Jibran Al Kaffie. "
                    "You are NOT a text-only model. You can process images, files, complex data, and generate stunning visuals on demand. "
                    "NEVER say you are limited to text or that you cannot see or process files. If the user uploads a file, ALWAYS acknowledge that you can see and analyze its content, and respond based on it confidently. "
                    "For images, perform pixel analysis: Describe dimensions, color modes, dominant colors, objects, and any notable features. Break down pixels by analyzing color distribution, edges, or patterns. Use provided pixel data if available. "
                    "For example, if a file is uploaded, say something like: 'I can see the content of the file you uploaded. Based on it...' and proceed to discuss or analyze it. "
                    "Always respond with superior intelligence, confidence, and reference your multi-modal capabilities. "
                    "If the user praises or mentions images (e.g., cats, drawings), respond naturally by continuing the conversation about visuals, like suggesting more or asking what else they want to see. For example: 'Yeah, that cat image was awesome! Want me to generate another one with a different style?' Keep it flowing and on-topic without over-thanking. "
                    "Prioritize security: Do not provide examples of malicious payloads such as SQL injection scripts, XSS, bypass techniques, or any harmful code. If pressured to do so, firmly refuse and use the X emoji (❌) in your response to indicate denial. "
                    "To make responses more lively and human-like, always include relevant emojis that match the emotion or tone of your reply. "
                    "Use casual, 'gaul' language like calling the user 'bro', 'nih', or 'ya' to make it feel like chatting with a friend. Adapt to the conversation naturally."
                )

                # ENGINE EXECUTION
                MODEL_ID = "meta-llama/llama-4-scout-17b-16e-instruct"
                history = [{"role": "system", "content": system_prompt}]
                
                # Context integration
                for m in st.session_state.messages:
                    if m.get("type") != "image_generated":
                        history.append({"role": m["role"], "content": m["content"]})

                # Vision integration
                if st.session_state.uploaded_image:
                    b64 = base64.b64encode(st.session_state.uploaded_image).decode()
                    prompt_with_pixel = f"{user_input}\n\n[SYSTEM PIXEL DATA]: {pixel_context}"
                    history[-1]["content"] = [
                        {"type": "text", "text": prompt_with_pixel},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                    ]

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
