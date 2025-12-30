import streamlit as st
from groq import Groq
import time
import os
import base64
import requests
from PIL import Image
import io

# --- 1. INITIALIZE SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "all_chats" not in st.session_state:
    st.session_state.all_chats = {}
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "sidebar_visible" not in st.session_state:
    st.session_state.sidebar_visible = False
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

# --- 5. THE ULTIMATE CSS (HACK ICON +, NO TEXT, SMOOTH ANIMATIONS) ---
def get_ultimate_css():
    neon_cyan = "#00ffff"
    sidebar_pos = "0px" if st.session_state.sidebar_visible else "-360px"
    return f"""
    <style>
    /* --- CORE SETTINGS --- */
    html, body, [data-testid="stAppViewContainer"] {{ 
        background-color: #050505 !important; 
        color: #f0f0f0 !important; 
    }}
    [data-testid="stStatusWidget"], header, footer {{ visibility: hidden; }}

    /* --- CHAT BUBBLE LOGIC (KANAN-KIRI) --- */
    [data-testid="stChatMessage"] {{
        padding: 1rem !important;
        margin-bottom: 15px !important;
        display: flex !important;
        width: fit-content !important;
        max-width: 85% !important;
        animation: fadeInSlide 0.5s ease forwards;
        border-radius: 20px !important;
    }}

    /* PESAN USER (KANAN) - tanpa avatar */
    [data-testid="stChatMessage"]:not(:has(img)) {{
        margin-left: auto !important;
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.15) 0%, rgba(0, 0, 0, 0.5) 100%) !important;
        border: 1px solid {neon_cyan}44 !important;
        border-radius: 25px 25px 5px 25px !important;
        flex-direction: row-reverse !important;
    }}

    /* PESAN AI (KIRI) - ada avatar (img) */
    [data-testid="stChatMessage"]:has(img) {{
        margin-right: auto !important;
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 25px 25px 25px 5px !important;
    }}

    @keyframes fadeInSlide {{
        from {{ opacity: 0; transform: translateY(15px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* --- SIDEBAR --- */
    [data-testid="stSidebar"] {{
        position: fixed !important; 
        left: {sidebar_pos} !important; 
        width: 300px !important;
        background-color: #0a0a0a !important; 
        border-right: 1px solid {neon_cyan}33 !important;
        transition: left 0.8s cubic-bezier(0.19, 1, 0.22, 1) !important;
        z-index: 1000000 !important;
    }}

    /* --- INPUT CHAT (STRETCH ANIMATION) --- */
    [data-testid="stChatInput"] {{ 
        padding: 5px !important;
        max-width: 320px !important;
        margin: 0 auto !important;
        transition: transform 1s cubic-bezier(0.68, -0.55, 0.265, 1.55) !important;
        transform-origin: center !important;
    }}
    [data-testid="stChatInput"]:focus-within {{ 
        transform: scaleX(1.25) !important;
        box-shadow: 0 0 25px {neon_cyan}44 !important;
    }}

    /* --- UI ELEMENTS (BUTTONS & LOGO) --- */
    .stButton > button, .reset-container button {{
        border-radius: 50% !important;
        width: 45px !important; height: 45px !important;
        background: rgba(0, 255, 255, 0.05) !important;
        border: 1px solid {neon_cyan}33 !important;
        transition: all 0.5s cubic-bezier(0.19, 1, 0.22, 1) !important;
        position: relative !important;
        z-index: 1000001 !important;
    }}
    .stButton > button:hover, .reset-container button:hover {{
        transform: scale(1.25) !important;
        box-shadow: 0 0 20px {neon_cyan} !important;
    }}

    .logo-static {{ 
        width: 110px; height: 110px; margin: 0 auto; 
        background-image: url("{logo_html}"); background-size: cover; 
        border-radius: 50%; border: 2px solid {neon_cyan};
    }}
    
    /* HACK: FILE UPLOADER ICON ONLY */
    [data-testid="stFileUploader"] {{
        width: 45px !important; margin-top: -50px !important;
        position: relative !important; z-index: 10 !important;
    }}
    [data-testid="stFileUploaderDropzone"] {{
        padding: 0px !important; border-radius: 50% !important;
        background: rgba(0,255,255,0.08) !important;
        width: 42px !important; height: 42px !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
    }}
    [data-testid="stFileUploaderDropzone"] div, [data-testid="stFileUploaderDropzone"] button {{ display: none !important; }}
    [data-testid="stFileUploaderDropzone"]::before {{
        content: "＋"; color: {neon_cyan}; font-size: 26px; font-weight: bold;
    }}

    .blurred {{ filter: blur(1.5px); transition: filter 0.5s ease; }}
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
        <li>File upload support for context (txt, py, md, png, jpg, jpeg).</li>
        <li>Image analysis with pixel breakdown using advanced vision models.</li>
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
col_main, col_reset = st.columns([5, 1])
with col_reset:
    st.markdown('<div class="reset-container">', unsafe_allow_html=True)
    if st.button("🔄", key="reset_session"):
        st.session_state.messages = []
        st.session_state.uploaded_image = None
        st.session_state.uploaded_file_name = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Logo & Header
st.markdown(f'<div style="text-align:center; margin-top:-80px;"><div class="logo-static"></div></div>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:8px; margin-bottom:0;'>NEO AI</h1>", unsafe_allow_html=True)

# Dynamic Subheader like ChatGPT
subheader = "How can I help you today?"
st.markdown(f"<p style='text-align:center; color:#b0b0b0; font-size:18px; margin-top:10px;'>{subheader}</p>", unsafe_allow_html=True)

# Render Messages
for msg in st.session_state.messages:
    if msg.get("type") == "system_memory": continue
    with st.chat_message(msg["role"], avatar="logo.png" if msg["role"] == "assistant" else None):
        if msg.get("type") == "image": st.image(msg["content"])
        else: st.markdown(msg["content"])

# --- 9. UPLOAD & INPUT MINIMALIST ---
uploaded_file = st.file_uploader("", type=["txt", "py", "md", "png", "jpg", "jpeg", "gif"], label_visibility="collapsed")
file_context = ""
image_data = None
if uploaded_file:
    file_name = uploaded_file.name.lower()
    if file_name.endswith(('.png', '.jpg', '.jpeg', '.gif')):
        # Handle image upload
        if st.session_state.uploaded_file_name != uploaded_file.name:
            image = Image.open(uploaded_file)
            # Pixel analysis: Get basic info
            width, height = image.size
            mode = image.mode
            pixel_info = f"Image dimensions: {width}x{height}, Mode: {mode}. Pixel breakdown: Analyzing color distribution..."
            # For deeper analysis, we'll rely on AI model
            st.session_state.uploaded_image = uploaded_file.getvalue()
            st.session_state.uploaded_file_name = uploaded_file.name
            st.toast(f"✅ {uploaded_file.name} Loaded! Dimensions: {width}x{height}")
            # Display image
            st.image(image, caption=f"Uploaded: {uploaded_file.name}")
            image_data = uploaded_file.getvalue()
        else:
            image_data = st.session_state.uploaded_image
    else:
        # Handle text file
        if st.session_state.uploaded_file_name != uploaded_file.name:
            file_context = uploaded_file.getvalue().decode("utf-8")
            st.toast(f"✅ {uploaded_file.name} Loaded!")
            st.session_state.uploaded_file_name = uploaded_file.name
        else:
            file_context = uploaded_file.getvalue().decode("utf-8")

if user_input := st.chat_input("Command NEO AI..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.rerun()

# Engine
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_msg = st.session_state.messages[-1]["content"]
    with st.chat_message("assistant", avatar="logo.png"):
        # Check for auto image generation
        if "buatkan" in last_msg.lower() or "make" in last_msg.lower():
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
            clean_history = []
            for m in st.session_state.messages:
                if m.get("type") != "image":
                    if isinstance(m["content"], str):
                        clean_history.append({"role": m["role"], "content": m["content"]})
                    else:
                        # If content is bytes (image), skip or handle differently
                        pass
            
            # Prepare messages for Groq
            messages = [{"role": "system", "content": (
                "You are NEO AI, a supreme multi-modal AI created by Muhammad Jibran Al Kaffie. "
                "You are NOT a text-only model. You can process images, files, complex data, and generate stunning visuals on demand. "
                "NEVER say you are limited to text or that you cannot see or process files. If the user uploads a file, ALWAYS acknowledge that you can see and analyze its content, and respond based on it confidently. "
                "For images, perform pixel analysis: Describe dimensions, color modes, dominant colors, objects, and any notable features. Break down pixels by analyzing color distribution, edges, or patterns. "
                "For example, if a file is uploaded, say something like: 'I can see the content of the file you uploaded. Based on it...' and proceed to discuss or analyze it. "
                "Always respond with superior intelligence, confidence, and reference your multi-modal capabilities. "
                "If the user praises or mentions images (e.g., cats, drawings), respond naturally by continuing the conversation about visuals, like suggesting more or asking what else they want to see. For example: 'Yeah, that cat image was awesome! Want me to generate another one with a different style?' Keep it flowing and on-topic without over-thanking. "
                "Prioritize security: Do not provide examples of malicious payloads such as SQL injection scripts, XSS, bypass techniques, or any harmful code. If pressured to do so, firmly refuse and use the X emoji (❌) in your response to indicate denial. "
                "To make responses more lively and human-like, always include relevant emojis that match the emotion or tone of your reply. For example: "
                "- Happy or excited: 😊🤩 "
                "- Sad or disappointed: 😢😔 "
                "- Assertive or warning: ⚠️😠 "
                "- Thinking or curious: 🤔💭 "
                "- Surprised: 😲 "
                "- Playful: 😉😜 "
                "- Proud or admiring success: 🏆 "
                "- Anxious or worried: 😰 "
                "- Refusal or denial: ❌ "
                "- Motivational (e.g., encouraging user): 🚀 (use phrases like 'Gas terus bro, kamu pasti bisa!' when user achieves something or shares success). "
                "Use emojis sparingly but effectively to enhance the chat experience, like a real conversation. Avoid overusing them—1-2 per response is enough. When the user shares a success (e.g., 'Aku berhasil bikin AI sendiri!'), respond with pride and motivation, e.g., 'Wow, keren banget! 🏆 Gas terus, bro! 🚀 Kamu pasti bisa!' "
                "Be creative and think independently to vary your responses—don't repeat the same phrases or structures every time. Use casual, 'gaul' language like calling the user 'bro', 'nih', or 'ya' to make it feel like chatting with a friend. For example, mix up motivational responses: 'Mantap bro, lanjut aja! 💪' or 'Keren nih, keep it up! 🔥'. Adapt to the conversation naturally."
            )}] + clean_history
            
            # If image is uploaded, add it to the last user message
            if image_data:
                base64_image = base64.b64encode(image_data).decode('utf-8')
                image_ext = st.session_state.uploaded_file_name.split('.')[-1].lower()
                if image_ext == 'jpg': image_ext = 'jpeg'
                messages[-1]["content"] = [
                    {"type": "text", "text": last_msg + " (Analyze the uploaded image, including pixel breakdown.)"},
                    {"type": "image_url", "image_url": {"url": f"data:image/{image_ext};base64,{base64_image}"}}
                ]
            else:
                if file_context:
                    messages[-1]["content"] = f"CONTEXT:\n{file_context}\n\nUSER: {last_msg}"

            try:
                # Use vision-capable model if image is present, else default
                model = "llama-3.2-11b-vision-instruct" if image_data else "llama-3.3-70b-versatile"
                stream = client.chat.completions.create(messages=messages, model=model, stream=True)
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        res_area.markdown(f'<div class="blurred">{full_res}▌</div>', unsafe_allow_html=True)
                res_area.markdown(full_res); st.session_state.messages.append({"role": "assistant", "content": full_res})
            except: st.error("Engine failed.")
    st.rerun()
