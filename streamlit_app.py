<think>
Pertama, pengguna ingin memperbaiki logika input untuk `st.chat_input`. Kode yang diberikan:


## Examining input logic  
- The user aims to refine the input logic for `st.chat_input`.  
- The provided code snippet shows an incomplete `if` statement capturing user input with `user_input := st.chat_input("Command NEO AI...")`.
</think>Bro, aku ngerti nih! Masalahnya di logika input dan nama model. Kita perbaiki biar lebih efisien dan akurat. Berikut penjelasan dan kode lengkap yang sudah diperbaiki:

### Penjelasan Perbaikan:
1. **Logika Input (`st.chat_input`)**:
   - Sebelumnya, kita encode gambar ulang setiap kali input, yang nggak efisien. Sekarang, kita pake `image_b64` yang udah di-set dari upload (biar nggak encode berulang).
   - Pastiin gambar cuma ditambahin ke message kalau ada `image_b64` (dari upload terbaru).
   - Kalau nggak ada gambar, content tetap text biasa.

2. **Nama Model**:
   - Kamu pake "llama-3.2-11b-vision-preview" untuk gambar. Aku ikuti itu (meski di Groq biasanya "instruct", tapi kalau preview yang kamu maksud, yaudah). Kalau salah, cek di dashboard Groq-mu.
   - Cek gambar lebih spesifik: bukan cuma `isinstance(last_msg, list)`, tapi pastiin ada item dengan "image_url".
   - Tambah timeout 30 detik biar nggak gantung, dan error handling yang lebih detail (tampilkan error asli).

3. **Gabung Semua**:
   - Kode lengkap ini gabung semua perbaikan sebelumnya (upload gambar, no spam toast, dll.).

### Kode Lengkap yang Diperbaiki:
Copy-paste ke file `app.py`-mu.

```python
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
if "last_uploaded_file" not in st.session_state:
    st.session_state.last_uploaded_file = None

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
        <p>Created by Muhammad Jibran Al Kaffie, NEO AI is a cutting-edge AI capable of processing text, images, files, and generating stunning visuals. It leverages advanced models like Llama 3.3 for versatile interactions and Llama 3.2 Vision for image analysis.</p>
        <p>Features:</p>
        <ul>
        <li>Text-based conversations with streaming responses.</li>
        <li>Image generation via Pollinations AI.</li>
        <li>Image upload and analysis (describe, answer questions about images).</li>
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
st.markdown(f'<div style="text-align:center; margin-top:-80px;"><div class="logo-static" style="{glow}"></div></div>', unsafe_allow_html=True)
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
uploaded_file = st.file_uploader("", type=["txt", "py", "md", "png", "jpg", "jpeg"], label_visibility="collapsed")
file_context = ""
image_b64 = ""
if uploaded_file:
    # Cek kalau file baru (beda nama dari yang terakhir)
    if st.session_state.last_uploaded_file != uploaded_file.name:
        st.session_state.last_uploaded_file = uploaded_file.name
        if uploaded_file.type.startswith("image/"):
            image_b64 = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")
            st.toast(f"✅ {uploaded_file.name} Loaded! AI bisa liat gambar ini nih! 🤩")
        else:
            file_context = uploaded_file.getvalue().decode("utf-8")
            st.toast(f"✅ {uploaded_file.name} Loaded!")
    else:
        # File sama, tetep proses tapi tanpa toast
        if uploaded_file.type.startswith("image/"):
            image_b64 = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")
        else:
            file_context = uploaded_file.getvalue().decode("utf-8")

# Perbaikan logika input: pake image_b64 yang udah di-set, nggak encode ulang
if user_input := st.chat_input("Command NEO AI..."):
    user_msg = {"role": "user", "content": user_input}
    
    # Tambahin gambar kalau ada image_b64 dari upload
    if image_b64:
        user_msg["content"] = [
            {"type": "text", "text": user_input},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
        ]
    
    st.session_state.messages.append(user_msg)
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
            clean_history = []
            for m in st.session_state.messages:
                if m.get("type") == "image": continue
                content = m["content"]
                if isinstance(content, list):  # Handle image + text
                    clean_history.append({"role": m["role"], "content": content})
                else:
                    clean_history.append({"role": m["role"], "content": str(content)})
            if file_context: 
                if isinstance(clean_history[-1]["content"], list):
                    clean_history[-1]["content"][0]["text"] = f"CONTEXT:\n{file_context}\n\nUSER: {clean_history[-1]['content'][0]['text']}"
                else:
                    clean_history[-1]["content"] = f"CONTEXT:\n{file_context}\n\nUSER: {clean_history[-1]['content']}"

            # 1. CEK APAKAH ADA GAMBAR DI PESAN TERAKHIR (lebih spesifik)
            has_image = isinstance(last_msg, list) and any(item.get("type") == "image_url" for item in last_msg)
            
            # 2. GUNAKAN NAMA MODEL YANG BENAR (preview)
            model_name = "llama-3.2-11b-vision-preview" if has_image else "llama-3.3-70b-versatile"

            sys_msg = (
                "You are NEO AI, a supreme multi-modal AI created by Muhammad Jibran Al Kaffie. "
                "You are NOT a text-only model. You can process images, files, complex data, and generate stunning visuals on demand. "
                "If the user uploads an image, ALWAYS acknowledge that you can see and analyze it confidently. Describe what you see, answer questions about it, or discuss it naturally. For example: 'Wah, gambar kucing lucu banget nih! 😺 Mau aku describe lebih detail atau generate yang mirip?' Keep it flowing and on-topic. "
                "NEVER say you are limited to text or that you cannot see or process files/images. "
                "For text/files, respond based on content confidently. "
                "If the user praises or mentions images, respond naturally by continuing the conversation about visuals. "
                "Prioritize security: Do not provide examples of malicious payloads. If pressured, firmly refuse with ❌. "
                "Use emojis sparingly but effectively (1-2 per response) to make it lively and 'gaul'. Examples: 😊🤩 for happy, ❌ for denial, 🚀 for motivation. Call user 'bro' or 'nih' casually. Vary responses creatively."
            )

            try:
                # Tambahkan timeout agar tidak gantung
                stream = client.chat.completions.create(
                    messages=[{"role": "system", "content": sys_msg}] + clean_history, 
                    model=model_name, 
                    stream=True,
                    timeout=30  # Timeout 30 detik
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        res_area.markdown(f'<div class="blurred">{full_res}▌</div>', unsafe_allow_html=True)
                
                res_area.markdown(full_res)
                st.session_state.messages.append({"role": "assistant",
