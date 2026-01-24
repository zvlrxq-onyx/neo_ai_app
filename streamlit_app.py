import streamlit as st
from groq import Groq
from huggingface_hub import InferenceClient
import google.generativeai as genai
import os, base64, requests, json
import re
from PIL import Image
import io
import urllib.parse
import time
import hashlib

# --- 1. CONFIG & SYSTEM SETUP ---
st.set_page_config(page_title="ZETRO: ZX-1.5 Flash", page_icon="🌌", layout="wide")

# Simple Session State (No Cookies - lebih stabil!)
if "cookies_ready" not in st.session_state:
    st.session_state.cookies_ready = True

# NAMA FILE DATABASE (Per-user dengan hash)
DB_FOLDER = "zetro_users_db"
if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER)

# File untuk user credentials
USERS_FILE = os.path.join(DB_FOLDER, "users.json")

def load_users():
    """Load registered users"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users_dict):
    """Save users to file"""
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(users_dict, f)
    except Exception as e:
        print(f"Error saving users: {e}")

def hash_password(password):
    """Hash password untuk keamanan"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username, password):
    """Verify user credentials"""
    users = load_users()
    if username in users:
        return users[username] == hash_password(password)
    return False

def register_user(username, password):
    """Register new user"""
    users = load_users()
    if username in users:
        return False, "Username sudah dipakai bro!"
    users[username] = hash_password(password)
    save_users(users)
    return True, "Registrasi berhasil!"

def get_user_db_file(username):
    """Generate unique database file path untuk setiap user"""
    user_hash = hashlib.md5(username.encode()).hexdigest()
    return os.path.join(DB_FOLDER, f"user_{user_hash}.json")

def load_history_from_db(username):
    """Load history dari file JSON spesifik user"""
    db_file = get_user_db_file(username)
    if os.path.exists(db_file):
        try:
            with open(db_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
                return {}
        except Exception as e:
            print(f"Error loading DB for {username}: {e}")
            return {}
    return {}

def save_history_to_db(username, history_dict):
    """Save history ke file JSON spesifik user"""
    db_file = get_user_db_file(username)
    try:
        with open(db_file, "w", encoding="utf-8") as f:
            json.dump(history_dict, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Gagal save db untuk {username}: {e}")

def analyze_image_pixels(image_data):
    """Analisis pixel gambar untuk data lebih detail"""
    try:
        img = Image.open(io.BytesIO(image_data))
        width, height = img.size
        mode = img.mode
        return f"Size: {width}x{height}, Mode: {mode}"
    except:
        return "Image analysis available"

# --- 2. USERNAME AUTHENTICATION (SECURE WITH PASSWORD) ---
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"

# Login Screen
if st.session_state.current_user is None:
    st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; height: 100vh; background: #0a0a0a;">
        <div style="background: #1a1a1a; 
                    padding: 50px; border-radius: 30px; 
                    border: 2px solid #06b6d4;
                    box-shadow: 0 0 40px rgba(6,182,212,0.5); text-align: center; max-width: 400px;">
            <h1 style="color: #ffffff; margin-bottom: 10px;">🌌 ZETRO</h1>
            <p style="color: #888; margin-bottom: 30px; font-weight: bold;">Sistem AI Terintegrasi untuk Pemrograman Tingkat Lanjut</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
        
        with tab1:
            st.markdown("<h3 style='text-align:center; color:#ffffff; margin-bottom:20px;'>Login to Your Account</h3>", unsafe_allow_html=True)
            login_username = st.text_input("Username", placeholder="Your username", key="login_user")
            login_password = st.text_input("Password", type="password", placeholder="Your password", key="login_pass")
            
            if st.button("🚀 Login", use_container_width=True, key="btn_login"):
                if login_username.strip() and login_password.strip():
                    if verify_user(login_username.strip(), login_password.strip()):
                        st.session_state.current_user = login_username.strip()
                        st.success("✅ Login successful!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ Username atau password salah bro!")
                else:
                    st.error("❌ Isi username dan password dulu!")
        
        with tab2:
            st.markdown("<h3 style='text-align:center; color:#ffffff; margin-bottom:20px;'>Create New Account</h3>", unsafe_allow_html=True)
            reg_username = st.text_input("Username", placeholder="Choose a username", key="reg_user")
            reg_password = st.text_input("Password", type="password", placeholder="Choose a password", key="reg_pass")
            reg_confirm = st.text_input("Confirm Password", type="password", placeholder="Confirm your password", key="reg_confirm")
            
            if st.button("📝 Register", use_container_width=True, key="btn_register"):
                if reg_username.strip() and reg_password.strip() and reg_confirm.strip():
                    if reg_password != reg_confirm:
                        st.error("❌ Password tidak sama bro!")
                    elif len(reg_password) < 4:
                        st.error("❌ Password minimal 4 karakter!")
                    else:
                        success, message = register_user(reg_username.strip(), reg_password.strip())
                        if success:
                            st.success("✅ " + message + " Silakan login!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ " + message)
                else:
                    st.error("❌ Isi semua field!")
    st.stop()

# --- 3. INITIALIZE SESSION STATE (Per User) ---
if "all_chats" not in st.session_state:
    st.session_state.all_chats = load_history_from_db(st.session_state.current_user)

if "messages" not in st.session_state:
    if st.session_state.all_chats:
        last_key = list(st.session_state.all_chats.keys())[-1]
        st.session_state.messages = st.session_state.all_chats[last_key].copy()
    else:
        st.session_state.messages = []

if "current_session_key" not in st.session_state:
    if st.session_state.all_chats:
        st.session_state.current_session_key = list(st.session_state.all_chats.keys())[-1]
    else:
        st.session_state.current_session_key = None

if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

if "show_upload_notif" not in st.session_state:
    st.session_state.show_upload_notif = False

# --- 4. API KEYS ---
try:
    client_groq = Groq(api_key=st.secrets["GROQ_API_KEY"])
    client_hf = InferenceClient(token=st.secrets["HF_TOKEN"])
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    client_gemini = genai.GenerativeModel('gemini-3-flash-preview')
    POLLINATIONS_API = "https://image.pollinations.ai/prompt/"
except Exception as e:
    st.error(f"❌ API Keys Error: {e}")
    st.info("Cek secrets.toml lu bro! Pastikan ada GROQ_API_KEY, HF_TOKEN, dan GEMINI_API_KEY")
    st.stop()

# --- 5. ASSETS (LOGO & USER) ---
@st.cache_data
def get_base64_img(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo_data = get_base64_img('logo.png')
logo_url = f"data:image/png;base64,{logo_data}" if logo_data else ""
user_img = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRfIrn5orx6KdLUiIvZ3IUkZTMdIyes-D6sMA&s"

# --- 6. CSS (ROUNDED DESIGN + GRADIENT BORDER ONLY) ---
st.markdown(f"""
<style>
    [data-testid="stAppViewContainer"] {{ background: #0a0a0a; }}
    
    /* FILE UPLOADER - ROUNDED CIRCLE */
    [data-testid="stFileUploader"] {{ position: fixed; bottom: 58px; left: 15px; width: 45px; z-index: 1000; }}
    [data-testid="stFileUploaderDropzone"] {{
        background: #1a1a1a !important; 
        border: 2px solid #06b6d4 !important; 
        border-radius: 50% !important;
        height: 42px !important; 
        width: 42px !important; 
        padding: 0 !important;
        transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    }}
    [data-testid="stFileUploaderDropzone"]:hover {{
        transform: scale(1.15) rotate(90deg) !important;
        background: #2a2a2a !important;
        border-color: #8b5cf6 !important;
        box-shadow: 0 0 25px rgba(6,182,212,0.6) !important;
    }}
    [data-testid="stFileUploaderDropzone"] div {{ display: none !important; }}
    [data-testid="stFileUploaderDropzone"] span {{ display: none !important; }}
    [data-testid="stFileUploaderDropzone"] p {{ display: none !important; }}
    [data-testid="stFileUploaderDropzone"] small {{ display: none !important; }}
    [data-testid="stFileUploaderDropzone"]::before {{
        content: "＋"; color: #06b6d4; font-size: 26px; font-weight: bold;
        display: flex; align-items: center; justify-content: center; height: 100%;
    }}
    [data-testid="stFileUploader"] label {{ display: none !important; }}
    [data-testid="stFileUploader"] span {{ display: none !important; }}
    [data-testid="stFileUploader"] small {{ display: none !important; }}
    
    /* CHAT INPUT AREA */
    [data-testid="stChatInput"] {{ margin-left: 60px !important; width: calc(100% - 80px) !important; }}
    
    /* INPUT BOX - KOTAK DENGAN ROUNDED DIKIT */
    [data-testid="stChatInputTextArea"] {{
        border-radius: 8px !important;
        border: 2px solid #06b6d4 !important;
        background: #1a1a1a !important;
        padding: 12px 50px 12px 20px !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    }}
    
    [data-testid="stChatInputTextArea"]:focus {{
        border-color: #8b5cf6 !important;
        box-shadow: 0 0 20px rgba(6,182,212,0.4) !important;
    }}
    
    /* TOMBOL KIRIM - KOTAK ROUNDED + ICON PANAH KE ATAS */
    [data-testid="stChatInputSubmitButton"] {{
        background: linear-gradient(135deg, #8b5cf6, #06b6d4) !important;
        border-radius: 10px !important;
        width: 40px !important;
        height: 40px !important;
        border: none !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        position: relative !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}
    
    [data-testid="stChatInputSubmitButton"]:hover {{
        transform: scale(1.1) !important;
        box-shadow: 0 0 20px rgba(139,92,246,0.6) !important;
    }}
    
    /* SEMBUNYIKAN ICON PESAWAT KERTAS DEFAULT */
    [data-testid="stChatInputSubmitButton"] svg {{
        display: none !important;
    }}
    
    /* TAMPILIN ICON PANAH KE ATAS ↑ */
    [data-testid="stChatInputSubmitButton"]::after {{
        content: "↑";
        color: white !important;
        font-size: 22px !important;
        font-weight: bold !important;
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        line-height: 1;
        font-family: Arial, sans-serif;
    }}
    
    /* SIDEBAR LOGO - ROUNDED */
    .sidebar-logo {{ 
        display: block; 
        margin: auto; 
        width: 80px; 
        height: 80px; 
        border-radius: 50%; 
        border: 2px solid #06b6d4; 
        object-fit: cover; 
        margin-bottom: 10px; 
        box-shadow: 0 0 15px rgba(6,182,212,0.5); 
    }}
    
    /* ROTATING LOGO - ROUNDED */
    .rotating-logo {{ 
        animation: rotate 8s linear infinite; 
        border-radius: 50%; 
        border: 2px solid #06b6d4; 
        box-shadow: 0 0 25px rgba(6,182,212,0.6); 
    }}
    
    @keyframes rotate {{ 
        from {{ transform: rotate(0deg); }} 
        to {{ transform: rotate(360deg); }} 
    }}
    
    @keyframes slideInRight {{
        from {{ opacity: 0; transform: translateX(20px); }}
        to {{ opacity: 1; transform: translateX(0); }}
    }}
    
    @keyframes slideInLeft {{
        from {{ opacity: 0; transform: translateX(-20px); }}
        to {{ opacity: 1; transform: translateX(0); }}
    }}
    
    /* TYPING INDICATOR */
    .typing-indicator {{ display: flex; align-items: center; gap: 5px; padding: 5px 0; }}
    .typing-dot {{ width: 7px; height: 7px; background: #06b6d4; border-radius: 50%; animation: blink 1.4s infinite both; }}
    .typing-dot:nth-child(2) {{ animation-delay: 0.2s; }}
    .typing-dot:nth-child(3) {{ animation-delay: 0.4s; }}
    @keyframes blink {{ 0%, 80%, 100% {{ opacity: 0; }} 40% {{ opacity: 1; }} }}
    
    /* USER BADGE - ROUNDED */
    .user-badge {{ 
        background: linear-gradient(135deg, #8b5cf6, #06b6d4);
        padding: 10px 18px; 
        border-radius: 25px;
        color: #ffffff; 
        font-size: 13px; 
        font-weight: bold; 
        text-align: center;
        margin-bottom: 15px; 
        box-shadow: 0 0 15px rgba(6,182,212,0.4); 
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important; 
    }}
    
    .user-badge:hover {{
        box-shadow: 0 0 25px rgba(139,92,246,0.6) !important;
        transform: scale(1.05) !important;
    }}
    
    /* BUTTONS - ROUNDED */
    .stButton button {{
        transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        border: 1px solid #06b6d4 !important;
        background: #1a1a1a !important;
        color: #ffffff !important;
        border-radius: 20px !important;
    }}
    
    .stButton button:hover {{
        transform: scale(1.05) translateY(-2px) !important;
        box-shadow: 0 8px 30px rgba(6,182,212,0.5) !important;
        border-color: #8b5cf6 !important;
        background: linear-gradient(135deg, #8b5cf6, #06b6d4) !important;
    }}
    
    .stButton button:active {{
        transform: scale(0.98) translateY(0) !important;
        box-shadow: 0 2px 15px rgba(6,182,212,0.3) !important;
        transition: all 0.1s ease !important;
    }}
    
    /* SELECTBOX - ROUNDED */
    [data-testid="stSelectbox"] {{
        transition: all 0.3s ease !important;
    }}
    
    [data-testid="stSelectbox"]:hover {{
        transform: scale(1.02) !important;
    }}
    
    [data-testid="stSelectbox"] > div {{
        transition: all 0.3s ease !important;
        border-radius: 15px !important;
    }}
    
    [data-testid="stSelectbox"] > div:hover {{
        border-color: #8b5cf6 !important;
        box-shadow: 0 0 20px rgba(139,92,246,0.3) !important;
    }}
    
    /* SMOOTH TRANSITIONS */
    * {{
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    }}
</style>
""", unsafe_allow_html=True)

# --- 7. BUBBLE ENGINE (BORDER GRADIENT ONLY) ---
def clean_text(text):
    if not isinstance(text, str): 
        return str(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
    return text.strip()

def render_chat_bubble(role, content):
    content = clean_text(content)
    
    if role == "user":
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-end; margin-bottom: 20px; animation: slideInRight 0.3s ease-out;">
            <div style="background: #1a1a1a; 
                        color: white; 
                        padding: 15px 20px; 
                        border-radius: 25px 25px 5px 25px; 
                        max-width: 85%; 
                        border: 2px solid transparent;
                        background-image: linear-gradient(#1a1a1a, #1a1a1a), linear-gradient(135deg, #8b5cf6, #06b6d4);
                        background-origin: border-box;
                        background-clip: padding-box, border-box;
                        word-wrap: break-word; 
                        box-shadow: 0 4px 20px rgba(139,92,246,0.3);">
                {content}
            </div>
            <img src="{user_img}" width="38" height="38" style="border-radius: 50%; margin-left: 12px; border: 2px solid #06b6d4; object-fit: cover; box-shadow: 0 0 10px rgba(6,182,212,0.4);">
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-start; margin-bottom: 20px; animation: slideInLeft 0.3s ease-out;">
            <img src="{logo_url}" width="38" height="38" style="border-radius: 50%; margin-right: 12px; border: 2px solid #06b6d4; object-fit: cover; box-shadow: 0 0 10px rgba(6,182,212,0.4);">
            <div style="background: #1a1a1a; 
                        color: #e9edef; 
                        padding: 15px 20px; 
                        border-radius: 5px 25px 25px 25px; 
                        max-width: 85%; 
                        border-left: 4px solid;
                        border-image: linear-gradient(180deg, #8b5cf6, #06b6d4) 1;
                        word-wrap: break-word; 
                        box-shadow: 0 4px 20px rgba(6,182,212,0.3);">
                {content}
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- 8. SIDEBAR ---
with st.sidebar:
    if logo_url: 
        st.markdown(f'<img src="{logo_url}" class="sidebar-logo">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:#ffffff; text-shadow: 0 0 10px rgba(139,92,246,0.5);'>ZETRO</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#888; font-size:11px; margin-top:-10px;'>ZX-1.5 Flash System</p>", unsafe_allow_html=True)
    
    st.markdown(f'<div class="user-badge">👤 {st.session_state.current_user}</div>', unsafe_allow_html=True)
    
    if st.button("🚪 Logout", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    if st.button("＋ New Session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.uploaded_image = None
        st.session_state.current_session_key = None
        st.rerun()
        
    st.markdown("---")
    
    engine_map = {
        "ZT-3 Pro": "Gemini",
        "ZT-3 Fast": "DeepSeek",
        "ZT-VISION 2.5": "Scout",
        "ZT-1 Flash": "Llama33",
        "ZT-2": "HuggingFace",
        "Z-ART 3 Fast": "Pollinations"
    }
    selected_engine_name = st.selectbox("Pilih Model AI", list(engine_map.keys()))
    engine = engine_map[selected_engine_name]

    st.markdown("### 🕒 Saved History")
    
    chat_keys = list(st.session_state.all_chats.keys())[::-1]
    
    if chat_keys:
        for title in chat_keys:
            col1, col2 = st.columns([4, 1])
            with col1:
                button_label = f"{'✅ ' if title == st.session_state.current_session_key else ''}{title}"
                if st.button(button_label, key=f"load_{title}", use_container_width=True):
                    st.session_state.messages = st.session_state.all_chats[title].copy()
                    st.session_state.current_session_key = title
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"delete_{title}", use_container_width=True):
                    del st.session_state.all_chats[title]
                    if st.session_state.current_session_key == title:
                        st.session_state.current_session_key = None
                        st.session_state.messages = []
                    save_history_to_db(st.session_state.current_user, st.session_state.all_chats)
                    st.rerun()
    else:
        st.info("Belum ada history nih bro! 📝")

# --- 9. MAIN RENDER ---
if logo_url:
    st.markdown(f'<div style="text-align:center; margin-bottom:20px;"><img src="{logo_url}" width="130" class="rotating-logo"></div>', unsafe_allow_html=True)
    if not st.session_state.messages:
        st.markdown("<div style='text-align:center; color:#ffffff; font-size:22px; font-weight:bold;'>ZETRO | ZX-1.5 Flash</div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; color:#888; font-size:14px; margin-top:5px;'>Sistem AI Terintegrasi untuk Pemrograman Tingkat Lanjut</div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; color:#888; font-size:16px; margin-top:20px;'>How can I help you today? 👋</div>", unsafe_allow_html=True)

# Render Chat
for msg in st.session_state.messages:
    if msg.get("type") == "image": 
        st.image(msg["content"], width=400)
    else:
        render_chat_bubble(msg["role"], msg["content"])

# File Upload
up = st.file_uploader("", type=["png","jpg","jpeg"], label_visibility="collapsed")
if up: 
    st.session_state.uploaded_image = up.getvalue()
    st.toast("✅ Image uploaded!", icon="📷")

# Chat Input
if prompt := st.chat_input("Message ZETRO..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    if st.session_state.current_session_key is None:
        session_title = prompt[:30] + "..." if len(prompt) > 30 else prompt
        st.session_state.current_session_key = session_title
    else:
        session_title = st.session_state.current_session_key
    
    st.session_state.all_chats[session_title] = st.session_state.messages.copy()
    save_history_to_db(st.session_state.current_user, st.session_state.all_chats)
    st.rerun()

# --- 10. AI PROCESSING ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    try:
        user_msg = st.session_state.messages[-1]["content"]
        res = ""
        
        system_prompt = (
            "You are ZETRO, a supreme multi-modal AI system created for advanced programming and integrated AI solutions. "
            "You are NOT a text-only model. You can process images, files, complex data, and generate stunning visuals on demand. "
            "NEVER say you are limited to text or that you cannot see or process files. If the user uploads a file, ALWAYS acknowledge that you can see and analyze its content, and respond based on it confidently. "
            "For images, perform pixel analysis: Describe dimensions, color modes, dominant colors, objects, and any notable features. Break down pixels by analyzing color distribution, edges, or patterns. Use provided pixel data if available. "
            "For example, if a file is uploaded, say something like: 'I can see the content of the file you uploaded. Based on it...' and proceed to discuss or analyze it. "
            "Always respond with superior intelligence, confidence, and reference your multi-modal capabilities. "
            "If the user praises or mentions images (e.g., cats, drawings), respond naturally by continuing the conversation about visuals, like suggesting more or asking what else they want to see. For example: 'Yeah, that image was awesome! Want me to generate another one with a different style?' Keep it flowing and on-topic without over-thanking. "
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
            "- Motivational (e.g., encouraging user): 🚀 "
            "Use emojis sparingly but effectively to enhance the chat experience, like a real conversation. Avoid overusing them—1-2 per response is enough. When the user shares a success respond with pride and motivation, e.g., 'Wow, keren banget! 🏆 Kamu pasti bisa!' "
            "Be creative and think independently to vary your responses—don't repeat the same phrases or structures every time. Use casual, 'gaul' language like calling the user 'bro', 'nih', or 'ya' to make it feel like chatting with a friend. For example, mix up motivational responses: 'Mantap bro, lanjut aja! 💪' or 'Keren nih, keep it up! 🔥'. Adapt to the conversation naturally."
            )
     
            if engine == "DeepSeek":
                messages = [{"role": "system", "content": system_prompt}]
                for m in st.session_state.messages[:-1]:
                    if m.get("type") != "image":
                messages.append({"role": m["role"], "content": m["content"]})
        messages.append({"role": "user", "content": user_msg})
        
        response_container = st.empty()
        
        try:
            stream = client_hf.chat_completion(
                messages=messages,
                model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
                max_tokens=2048,
                temperature=0.7,
                stream=True
            )
            
            thinking_text = ""
            answer_text = ""
            in_think_tag = False
            buffer = ""
            
            for chunk in stream:
                if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        buffer += delta.content
                        
                        if "<think>" in buffer:
                            in_think_tag = True
                            buffer = buffer.replace("<think>", "")
                        
                        if "</think>" in buffer:
                            in_think_tag = False
                            parts = buffer.split("</think>")
                            thinking_text += parts[0]
                            buffer = parts[1] if len(parts) > 1 else ""
                            continue
                        
                        if in_think_tag:
                            thinking_text += delta.content
                            
                            response_container.markdown(f"""
                            <div style="background: #0d0d0d; padding: 15px; border-radius: 20px; border-left: 4px solid; border-image: linear-gradient(180deg, #8b5cf6, #06b6d4) 1; margin-bottom: 15px; box-shadow: 0 4px 20px rgba(6,182,212,0.3);">
                                <div style="background: linear-gradient(135deg, #8b5cf6, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: bold; margin-bottom: 10px; display: flex; align-items: center; gap: 8px;">
                                    🧠 ZETRO Deep Thinking Process
                                    <div class="typing-indicator" style="margin: 0;">
                                        <div class="typing-dot"></div>
                                        <div class="typing-dot"></div>
                                        <div class="typing-dot"></div>
                                    </div>
                                </div>
                                <div style="color: #888; font-size: 13px; font-family: 'Consolas', monospace; white-space: pre-wrap; line-height: 1.6;">{clean_text(thinking_text)}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            answer_text += delta.content
                            clean_answer = clean_text(answer_text)
                            
                            response_container.markdown(f"""
                            <div style="display: flex; justify-content: flex-start; margin-bottom: 20px; animation: slideInLeft 0.3s ease-out;">
                                <img src="{logo_url}" width="38" height="38" style="border-radius: 50%; margin-right: 12px; border: 2px solid #06b6d4; object-fit: cover; box-shadow: 0 0 10px rgba(6,182,212,0.4);">
                                <div style="background: #1a1a1a; color: #e9edef; padding: 15px 20px; border-radius: 5px 25px 25px 25px; 
                                            max-width: 85%; border-left: 4px solid; border-image: linear-gradient(180deg, #8b5cf6, #06b6d4) 1; word-wrap: break-word; box-shadow: 0 4px 20px rgba(6,182,212,0.3);">
                                    <div style="white-space: pre-wrap;">{clean_answer}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            time.sleep(0.01)
            
            res = answer_text.strip() if answer_text else thinking_text.strip()
                
        except Exception as e:
            if "busy" in str(e).lower() or "503" in str(e):
                res = "DeepSeek lagi sibuk nih bro! 😅 Coba model lain atau tunggu sebentar ya!"
            else:
                res = f"Error: {str(e)}"
    
    elif engine == "Gemini":
        messages_history = []
        for m in st.session_state.messages[:-1]:
            if m.get("type") != "image":
                role = "user" if m["role"] == "user" else "model"
                messages_history.append({"role": role, "parts": [m["content"]]})
        
        response_container = st.empty()
        res_text = ""
        
        try:
            chat = client_gemini.start_chat(history=messages_history)
            stream = chat.send_message(user_msg, stream=True)
            
            for chunk in stream:
                if chunk.text:
                    res_text += chunk.text
                    clean_res = clean_text(res_text)
                    
                    response_container.markdown(f"""
                    <div style="display: flex; justify-content: flex-start; margin-bottom: 20px; animation: slideInLeft 0.3s ease-out;">
                        <img src="{logo_url}" width="38" height="38" style="border-radius: 50%; margin-right: 12px; border: 2px solid #06b6d4; object-fit: cover; box-shadow: 0 0 10px rgba(6,182,212,0.4);">
                        <div style="background: #1a1a1a; color: #e9edef; padding: 15px 20px; border-radius: 5px 25px 25px 25px; 
                                    max-width: 85%; border-left: 4px solid; border-image: linear-gradient(180deg, #8b5cf6, #06b6d4) 1; word-wrap: break-word; box-shadow: 0 4px 20px rgba(6,182,212,0.3);">
                            <div style="white-space: pre-wrap;">{clean_res}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    time.sleep(0.01)
            
            res = res_text
        except Exception as e:
            res = f"Gemini error bro: {str(e)} 😰"
    
    elif engine == "Scout":
        current_image_data = st.session_state.uploaded_image
        
        if current_image_data:
            pixel_info = analyze_image_pixels(current_image_data)
            base64_image = base64.b64encode(current_image_data).decode('utf-8')
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "text", "text": f"{user_msg} (Image info: {pixel_info})"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}
            ]
            
            response_container = st.empty()
            res_text = ""
            
            stream = client_groq.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    res_text += chunk.choices[0].delta.content
                    clean_res = clean_text(res_text)
                    
                    response_container.markdown(f"""
                    <div style="display: flex; justify-content: flex-start; margin-bottom: 20px;">
                        <img src="{logo_url}" width="38" height="38" style="border-radius: 50%; margin-right: 12px; border: 2px solid #06b6d4;">
                        <div style="background: #1a1a1a; color: #e9edef; padding: 15px 20px; border-radius: 5px 25px 25px 25px; 
                                    max-width: 85%; border-left: 4px solid; border-image: linear-gradient(180deg, #8b5cf6, #06b6d4) 1; word-wrap: break-word;">
                            <div style="white-space: pre-wrap;">{clean_res}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    time.sleep(0.02)
            
            res = res_text
            st.session_state.uploaded_image = None
        else:
            messages = [{"role": "system", "content": system_prompt}]
            for m in st.session_state.messages[:-1]:
                if m.get("type") != "image":
                    messages.append({"role": m["role"], "content": m["content"]})
            messages.append({"role": "user", "content": user_msg})
            
            response_container = st.empty()
            res_text = ""
            
            stream = client_groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    res_text += chunk.choices[0].delta.content
                    clean_res = clean_text(res_text)
                    
                    response_container.markdown(f"""
                    <div style="display: flex; justify-content: flex-start; margin-bottom: 20px;">
                        <img src="{logo_url}" width="38" height="38" style="border-radius: 50%; margin-right: 12px; border: 2px solid #06b6d4;">
                        <div style="background: #1a1a1a; color: #e9edef; padding: 15px 20px; border-radius: 5px 25px 25px 25px; 
                                    max-width: 85%; border-left: 4px solid; border-image: linear-gradient(180deg, #8b5cf6, #06b6d4) 1; word-wrap: break-word;">
                            <div style="white-space: pre-wrap;">{clean_res}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    time.sleep(0.02)
            
            res = res_text
    
    elif engine == "Llama33":
        messages = [{"role": "system", "content": system_prompt}]
        for m in st.session_state.messages[:-1]:
            if m.get("type") != "image":
                messages.append({"role": m["role"], "content": m["content"]})
        messages.append({"role": "user", "content": user_msg})
        
        response_container = st.empty()
        res_text = ""
        
        stream = client_groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.8,
            max_tokens=1024,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                res_text += chunk.choices[0].delta.content
                clean_res = clean_text(res_text)
                
                response_container.markdown(f"""
                <div style="display: flex; justify-content: flex-start; margin-bottom: 20px;">
                    <img src="{logo_url}" width="38" height="38" style="border-radius: 50%; margin-right: 12px; border: 2px solid #06b6d4;">
                    <div style="background: #1a1a1a; color: #e9edef; padding: 15px 20px; border-radius: 5px 25px 25px 25px; 
                                max-width: 85%; border-left: 4px solid; border-image: linear-gradient(180deg, #8b5cf6, #06b6d4) 1; word-wrap: break-word;">
                        <div style="white-space: pre-wrap;">{clean_res}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                time.sleep(0.02)
        
        res = res_text
    
    elif engine == "HuggingFace":
        messages = [{"role": "system", "content": system_prompt}]
        for m in st.session_state.messages[:-1]:
            if m.get("type") != "image":
                messages.append({"role": m["role"], "content": m["content"]})
        messages.append({"role": "user", "content": user_msg})
        
        response_container = st.empty()
        res_text = ""
        
        stream = client_hf.chat_completion(
            messages=messages,
            model="Qwen/Qwen2.5-7B-Instruct",
            max_tokens=1024,
            temperature=0.9,
            stream=True
        )
        
        for chunk in stream:
            if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if hasattr(delta, 'content') and delta.content:
                    res_text += delta.content
                    clean_res = clean_text(res_text)
                    
                    response_container.markdown(f"""
                    <div style="display: flex; justify-content: flex-start; margin-bottom: 20px;">
                        <img src="{logo_url}" width="38" height="38" style="border-radius: 50%; margin-right: 12px; border: 2px solid #06b6d4;">
                        <div style="background: #1a1a1a; color: #e9edef; padding: 15px 20px; border-radius: 5px 25px 25px 25px; 
                                    max-width: 85%; border-left: 4px solid; border-image: linear-gradient(180deg, #8b5cf6, #06b6d4) 1; word-wrap: break-word;">
                            <div style="white-space: pre-wrap;">{clean_res}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    time.sleep(0.02)
        
        res = res_text
    
    elif engine == "Pollinations":
        encoded_prompt = urllib.parse.quote(user_msg)
        image_url = f"{POLLINATIONS_API}{encoded_prompt}"
        
        img_response = requests.get(image_url)
        img = Image.open(io.BytesIO(img_response.content))
        
        st.session_state.messages.append({"role": "assistant", "type": "image", "content": img})
        
        if st.session_state.current_session_key:
            st.session_state.all_chats[st.session_state.current_session_key] = st.session_state.messages.copy()
        save_history_to_db(st.session_state.current_user, st.session_state.all_chats)
        st.rerun()
    
    if res:
        st.session_state.messages.append({"role": "assistant", "content": res})
        
        if st.session_state.current_session_key:
            st.session_state.all_chats[st.session_state.current_session_key] = st.session_state.messages.copy()
        save_history_to_db(st.session_state.current_user, st.session_state.all_chats)
        st.rerun()

except Exception as e:
    st.error(f"❌ Error bro: {str(e)}")
    error_msg = f"Sorry bro, ada error: {str(e)} 😰"
    st.session_state.messages.append({"role": "assistant", "content": error_msg})
    if st.session_state.current_session_key:
        st.session_state.all_chats[st.session_state.current_session_key] = st.session_state.messages.copy()
    save_history_to_db(st.session_state.current_user, st.session_state.all_chats)
    st.rerun()
