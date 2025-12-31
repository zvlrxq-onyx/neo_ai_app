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

# --- 5. THE ULTIMATE CSS (UPDATED FOR IMAGE BUBBLES) ---
def get_ultimate_css():
    neon_cyan = "#00ffff"
    return f"""
    <style>
    /* --- CORE SETTINGS --- */
    html, body, [data-testid="stAppViewContainer"] {{ 
        background-color: #050505 !important; 
        color: #f0f0f0 !important; 
    }}
    [data-testid="stStatusWidget"], header, footer {{ visibility: hidden; }}

    /* --- CHAT BUBBLE LOGIC --- */
    [data-testid="stChatMessage"] {{
        padding: 1rem !important;
        margin-bottom: 15px !important;
        display: flex !important;
        width: fit-content !important;
        max-width: 85% !important;
        animation: fadeInSlide 0.5s ease forwards;
        border-radius: 20px !important;
    }}

    /* PESAN USER (KANAN) */
    /* Kita mendeteksi user dari absence of avatar image container yang spesifik */
    [data-testid="stChatMessage"][class*="st-emotion-cache-"] {{
         flex-direction: row-reverse !important;
    }}
    /* Hardcode fix untuk user message alignment (workaround CSS Streamlit yang tricky) */
    div[data-testid="stChatMessage"]:nth-child(odd) {{
        margin-left: auto !important;
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.15) 0%, rgba(0, 0, 0, 0.5) 100%) !important;
        border: 1px solid {neon_cyan}44 !important;
        border-radius: 25px 25px 5px 25px !important;
        flex-direction: row-reverse !important;
    }}

    /* PESAN AI (KIRI) */
    div[data-testid="stChatMessage"]:nth-child(even) {{
        margin-right: auto !important;
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 25px 25px 25px 5px !important;
        flex-direction: row !important;
    }}

    @keyframes fadeInSlide {{
        from {{ opacity: 0; transform: translateY(15px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* --- INPUT CHAT --- */
    [data-testid="stChatInput"] {{ 
        padding: 5px !important;
        max-width: 320px !important;
        margin: 0 auto !important;
        transition: transform 1s cubic-bezier(0.68, -0.55, 0.265, 1.55) !important;
    }}
    [data-testid="stChatInput"]:focus-within {{ 
        transform: scaleX(1.1) !important;
        box-shadow: 0 0 25px {neon_cyan}44 !important;
    }}

    /* --- UI ELEMENTS --- */
    .stButton > button, .reset-container button {{
        border-radius: 50% !important;
        width: 45px !important; height: 45px !important;
        background: rgba(0, 255, 255, 0.05) !important;
        border: 1px solid {neon_cyan}33 !important;
        transition: all 0.5s;
    }}
    .stButton > button:hover {{
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
        justify-content: center !important;
        align-items: center !important;
        display: flex !important;
    }}
    [data-testid="stFileUploaderDropzone"] div, [data-testid="stFileUploaderDropzone"] button {{ display: none !important; }}
    [data-testid="stFileUploaderDropzone"]::before {{
        content: "＋"; color: {neon_cyan}; font-size: 26px; font-weight: bold;
    }}

    /* EXPANDER STYLING */
    .streamlit-expanderHeader {{
        font-family: 'Courier New', monospace;
        font-size: 0.9em;
        color: #888;
        background-color: transparent !important;
    }}
    
    .blurred {{ filter: blur(1.5px); transition: filter 0.5s ease; }}
    </style>
    """
st.markdown(get_ultimate_css(), unsafe_allow_html=True)

# --- 6. MAIN UI ---
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
st.markdown(f"<p style='text-align:center; color:#b0b0b0; font-size:18px; margin-top:10px;'>How can I help you today?</p>", unsafe_allow_html=True)

# --- 7. RENDER MESSAGES (LOGIKA BARU: IMAGE + TEXT SATU BUBBLE) ---
for msg in st.session_state.messages:
    if msg.get("type") == "system_memory": continue
    
    # Tentukan Avatar
    avatar = "logo.png" if msg["role"] == "assistant" else None
    
    with st.chat_message(msg["role"], avatar=avatar):
        # 1. Cek jika pesan ini punya gambar attachment (User Image)
        if msg.get("image_data"):
            # Render gambar di dalam bubble user
            st.image(msg["image_data"], use_container_width=True)
        
        # 2. Cek jika ini pesan gambar dari AI (Generated Image)
        if msg.get("type") == "image_generated":
             st.image(msg["content"])
        
        # 3. Render teks biasa (jika ada)
        if msg.get("content") and msg.get("type") != "image_generated":
            st.markdown(msg["content"])

# --- 8. UPLOAD & ANALYSIS LOGIC ---
uploaded_file = st.file_uploader("", type=["txt", "py", "md", "png", "jpg", "jpeg", "gif"], label_visibility="collapsed")
file_context = ""
pixel_analysis = ""
edge_image_data = None

def analyze_pixels(image):
    width, height = image.size
    mode = image.mode
    pixels = np.array(image)
    
    analysis = f"**Dimensi:** {width}x{height} | **Mode:** {mode}\n"
    if mode == 'RGB':
        r, g, b = pixels[:, :, 0].flatten(), pixels[:, :, 1].flatten(), pixels[:, :, 2].flatten()
        analysis += f"**Avg RGB:** ({int(np.mean(r))}, {int(np.mean(g))}, {int(np.mean(b))})\n"
        dominant_r = np.argmax(np.bincount(r))
        dominant_g = np.argmax(np.bincount(g))
        dominant_b = np.argmax(np.bincount(b))
        analysis += f"**Dominant:** ({dominant_r}, {dominant_g}, {dominant_b})\n"
    
    edge_image = image.filter(ImageFilter.EDGE_ENHANCE) 
    return analysis, edge_image

if uploaded_file:
    file_name = uploaded_file.name.lower()
    if file_name.endswith(('.png', '.jpg', '.jpeg', '.gif')):
        # Handle image upload
        if st.session_state.uploaded_file_name != uploaded_file.name:
            image = Image.open(uploaded_file)
            pixel_analysis, edge_img = analyze_pixels(image)
            
            st.session_state.uploaded_image = uploaded_file.getvalue()
            st.session_state.uploaded_file_name = uploaded_file.name
            st.toast(f"✅ {uploaded_file.name} Ready to send!")
            
            # --- PREVIEW AREA (Hanya Log Teknis, Gambar akan masuk chat saat dikirim) ---
            with st.expander("🛠️ Image Analysis Data (Pending Send)"):
                st.code(pixel_analysis, language="yaml")
                st.image(edge_img, caption="Edge View", use_container_width=True)
            # ---------------------------------
    else:
        if st.session_state.uploaded_file_name != uploaded_file.name:
            file_context = uploaded_file.getvalue().decode("utf-8")
            st.toast(f"✅ {uploaded_file.name} Loaded!")
            st.session_state.uploaded_file_name = uploaded_file.name
            file_context = uploaded_file.getvalue().decode("utf-8")

# --- 9. INPUT HANDLING (LOGIKA GABUNG IMAGE + TEXT) ---
if user_input := st.chat_input("Command NEO AI..."):
    
    # Siapkan paket pesan
    message_package = {"role": "user", "content": user_input}
    
    # Cek apakah ada gambar yang sedang "pending" di upload
    if st.session_state.uploaded_image:
        message_package["image_data"] = st.session_state.uploaded_image
        # Kita simpan di message history, tapi JANGAN hapus dulu dari session_state
        # karena engine butuh datanya untuk processing di bawah.
    
    st.session_state.messages.append(message_package)
    st.rerun()

# --- 10. ENGINE (LLAMA 4 SCOUT) ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_msg = st.session_state.messages[-1] # Ambil object full
    last_text = last_msg["content"]
    
    # Cek apakah pesan TERAKHIR ini punya gambar (attached image)
    current_image_bytes = last_msg.get("image_data")
    
    # Jika pesan terakhir punya gambar, kita hapus status upload global
    # agar chat berikutnya tidak 'membawa' gambar yang sama
    if current_image_bytes and st.session_state.uploaded_image:
        st.session_state.uploaded_image = None
        st.session_state.uploaded_file_name = None
    
    with st.chat_message("assistant", avatar="logo.png"):
        if "buatkan" in last_text.lower() or "make" in last_text.lower():
            with st.spinner("Visualizing..."):
                try:
                    img_url = f"https://image.pollinations.ai/prompt/{last_text.replace(' ','%20')}?width=1024&height=1024&nologo=true"
                    r = requests.get(img_url, timeout=30)
                    if r.status_code == 200:
                        st.image(r.content)
                        st.session_state.messages.append({"role": "assistant", "content": r.content, "type": "image_generated"})
                except: st.error("Neural lost.")
        else:
            res_area = st.empty(); full_res = ""
            clean_history = []
            
            # Build history (filter images from text context if needed, or pass desc)
            for m in st.session_state.messages[:-1]: # Exclude current msg temp
                if m.get("type") != "image_generated":
                    content = m["content"]
                    if m.get("image_data"): content += " [User sent an image]"
                    clean_history.append({"role": m["role"], "content": str(content)})
            
            system_prompt = (
                "You are NEO AI (Model: Llama 4 Scout). "
                "Respond confidently. If the user sends an image, analyze it using the provided vision data. "
                "Be helpful, concise, and use emojis like 🚀, 💡, 🔥 to match the vibe."
            )
            messages = [{"role": "system", "content": system_prompt}] + clean_history
            
            # SETUP REQUEST UTAMA
            if current_image_bytes:
                base64_image = base64.b64encode(current_image_bytes).decode('utf-8')
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": last_text},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                })
                active_model = "meta-llama/llama-3.2-11b-vision-preview" # Vision Model
            else:
                messages.append({"role": "user", "content": last_text})
                active_model = "llama-3.3-70b-versatile" # Text Model

            try:
                stream = client.chat.completions.create(messages=messages, model=active_model, stream=True)
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        res_area.markdown(f'<div class="blurred">{full_res}▌</div>', unsafe_allow_html=True)
                
                res_area.markdown(full_res)
                st.session_state.messages.append({"role": "assistant", "content": full_res})
            except Exception as e: 
                st.error(f"Engine failed: {e}")
                
    st.rerun()
