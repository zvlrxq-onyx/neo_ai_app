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
st.set_page_config(page_title="NEO AI", page_icon="🤖", layout="wide")

# Simple Session State
if "cookies_ready" not in st.session_state:
    st.session_state.cookies_ready = True

# Stop generation flag
if "stop_generation" not in st.session_state:
    st.session_state.stop_generation = False

# DATABASE FOLDER
DB_FOLDER = "neo_users_db"
if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER)

USERS_FILE = os.path.join(DB_FOLDER, "users.json")

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users_dict):
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(users_dict, f)
    except Exception as e:
        print(f"Error saving users: {e}")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username, password):
    users = load_users()
    if username in users:
        return users[username] == hash_password(password)
    return False

def register_user(username, password):
    users = load_users()
    if username in users:
        return False, "Username sudah dipakai bro!"
    users[username] = hash_password(password)
    save_users(users)
    return True, "Registrasi berhasil!"

def get_user_db_file(username):
    user_hash = hashlib.md5(username.encode()).hexdigest()
    return os.path.join(DB_FOLDER, f"user_{user_hash}.json")

def load_history_from_db(username):
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
    db_file = get_user_db_file(username)
    try:
        with open(db_file, "w", encoding="utf-8") as f:
            json.dump(history_dict, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Gagal save db untuk {username}: {e}")

def analyze_image_pixels(image_data):
    try:
        img = Image.open(io.BytesIO(image_data))
        width, height = img.size
        mode = img.mode
        return f"Size: {width}x{height}, Mode: {mode}"
    except:
        return "Image analysis available"

# --- 2. AUTHENTICATION ---
if "current_user" not in st.session_state:
    st.session_state.current_user = None

if st.session_state.current_user is None:
    st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; height: 100vh; background: #0a0a0a;">
        <div style="background: #1a1a1a; 
                    padding: 50px; border-radius: 30px; 
                    border: 2px solid #06b6d4;
                    box-shadow: 0 0 40px rgba(6,182,212,0.5); text-align: center; max-width: 400px;">
            <h1 style="color: #ffffff; margin-bottom: 10px;">🤖 NEO AI</h1>
            <p style="color: #888; margin-bottom: 30px; font-weight: bold;">Advanced Multi-Modal AI System</p>
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

# --- 3. INITIALIZE SESSION STATE ---
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

if "model_popup_open" not in st.session_state:
    st.session_state.model_popup_open = False

if "is_generating" not in st.session_state:
    st.session_state.is_generating = False

# --- 4. API KEYS ---
try:
    client_groq = Groq(api_key=st.secrets["GROQ_API_KEY"])
    client_hf = InferenceClient(token=st.secrets["HF_TOKEN"])
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    client_gemini = genai.GenerativeModel('gemini-3-flash-preview')
    POLLINATIONS_API = "https://image.pollinations.ai/prompt/"
except Exception as e:
    st.error(f"❌ API Keys Error: {e}")
    st.stop()

# --- 5. ASSETS ---
@st.cache_data
def get_base64_img(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo_data = get_base64_img('logo.png')
logo_url = f"data:image/png;base64,{logo_data}" if logo_data else ""
user_img = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRfIrn5orx6KdLUiIvZ3IUkZTMdIyes-D6sMA&s"

# --- 6. CSS ---
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background: #0a0a0a; }
    
    /* FILE UPLOADER FIX */
    [data-testid="stFileUploader"] { 
        position: fixed; 
        bottom: 58px; 
        left: 15px; 
        width: 45px; 
        z-index: 1000; 
    }
    [data-testid="stFileUploaderDropzone"] {
        background: #1a1a1a !important; 
        border: 2px solid #06b6d4 !important; 
        border-radius: 50% !important;
        height: 42px !important; 
        width: 42px !important; 
        padding: 0 !important;
        transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        overflow: hidden !important;
        position: relative !important;
    }
    [data-testid="stFileUploaderDropzone"]:hover {
        transform: scale(1.15) rotate(90deg) !important;
        background: #2a2a2a !important;
        border-color: #8b5cf6 !important;
        box-shadow: 0 0 25px rgba(6,182,212,0.6) !important;
    }
    [data-testid="stFileUploaderDropzone"] * { 
        display: none !important; 
    }
    [data-testid="stFileUploaderDropzone"]::before {
        content: "＋" !important;
        color: #06b6d4 !important;
        font-size: 26px !important;
        font-weight: bold !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        height: 100% !important;
        width: 100% !important;
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        z-index: 10 !important;
    }
    [data-testid="stFileUploader"] label { display: none !important; }
    [data-testid="stFileUploader"] small { display: none !important; }
    [data-testid="stFileUploader"] button { display: none !important; }
    [data-testid="stFileUploader"] span { display: none !important; }
    [data-testid="stFileUploader"] section { font-size: 0 !important; }
    
    /* CHAT INPUT - ROUNDED RECTANGLE */
    [data-testid="stChatInput"] { 
        margin-left: 60px !important; 
        width: calc(100% - 80px) !important; 
    }
    
    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] > div > div {
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
    }
    
    [data-testid="stChatInputTextArea"] {
        border-radius: 12px !important;
        border: 2px solid #06b6d4 !important;
        background: #1a1a1a !important;
        padding: 12px 50px 12px 20px !important;
        font-size: 14px !important;
        min-height: 44px !important;
        max-height: 200px !important;
        transition: all 0.3s ease !important;
        box-sizing: border-box !important;
        outline: none !important;
    }
    
    [data-testid="stChatInputTextArea"]:focus {
        border: 2px solid #8b5cf6 !important;
        box-shadow: 0 0 15px rgba(139,92,246,0.4) !important;
    }
    
    [data-testid="stChatInputSubmitButton"] {
        background: linear-gradient(135deg, #8b5cf6, #06b6d4) !important;
        border-radius: 50% !important;
        width: 40px !important;
        height: 40px !important;
        border: none !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    }
    [data-testid="stChatInputSubmitButton"]:hover {
        transform: scale(1.1) !important;
        box-shadow: 0 0 20px rgba(139,92,246,0.6) !important;
    }
    [data-testid="stChatInputSubmitButton"] svg {
        color: white !important;
        transform: rotate(0deg) !important;
    }
    
    /* DEEPSEEK ADVANCED THINKING ANIMATIONS */
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    @keyframes shimmer {
        0% { background-position: -200% center; }
        100% { background-position: 200% center; }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .thinking-container {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 10px 18px;
        background: linear-gradient(90deg, #1a1a1a 0%, #2a2a2a 50%, #1a1a1a 100%);
        background-size: 200% auto;
        border-radius: 20px;
        border: 1px solid #06b6d4;
        animation: shimmer 3s linear infinite;
        box-shadow: 0 0 15px rgba(6,182,212,0.3);
        will-change: transform, opacity;
        backface-visibility: hidden;
        transform: translateZ(0);
    }
    
    .thinking-spinner {
        width: 16px;
        height: 16px;
        border: 2px solid #06b6d4;
        border-top-color: transparent;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    .thinking-text {
        color: #06b6d4;
        font-size: 13px;
        font-weight: 600;
        animation: fadeIn 0.5s ease-in;
    }
    
    .thinking-dots {
        display: flex;
        gap: 3px;
    }
    
    .thinking-dot {
        width: 5px;
        height: 5px;
        border-radius: 50%;
        background: #06b6d4;
        animation: pulse 1.5s ease-in-out infinite;
        will-change: transform, opacity;
        backface-visibility: hidden;
        transform: translateZ(0);
    }
    
    .thinking-dot:nth-child(1) { animation-delay: 0s; }
    .thinking-dot:nth-child(2) { animation-delay: 0.3s; }
    .thinking-dot:nth-child(3) { animation-delay: 0.6s; }
    
    .final-thought {
        color: #8b5cf6;
        font-weight: bold;
        animation: fadeIn 0.5s ease-in;
    }
    
    /* ANIMATIONS */
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    /* SMOOTH TRANSITIONS FOR STREAMING */
    [data-testid="stMarkdownContainer"] {
        transition: all 0.1s ease-out !important;
    }
    
    /* USER BADGE */
    .user-badge { 
        background: linear-gradient(135deg, #8b5cf6, #06b6d4);
        padding: 10px 18px; 
        border-radius: 25px;
        color: #ffffff; 
        font-size: 13px; 
        font-weight: bold; 
        text-align: center;
        margin-bottom: 15px; 
        box-shadow: 0 0 15px rgba(6,182,212,0.4); 
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); 
    }
    .user-badge:hover {
        box-shadow: 0 0 25px rgba(139,92,246,0.6);
        transform: scale(1.05);
    }
    
    /* BUTTONS */
    .stButton button {
        transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        border: 1px solid #06b6d4 !important;
        background: #1a1a1a !important;
        color: #ffffff !important;
        border-radius: 20px !important;
    }
    .stButton button:hover {
        transform: scale(1.05) translateY(-2px) !important;
        box-shadow: 0 8px 30px rgba(6,182,212,0.5) !important;
        border-color: #8b5cf6 !important;
        background: linear-gradient(135deg, #8b5cf6, #06b6d4) !important;
    }
    
    /* EXPANDER CUSTOM STYLE */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #1a1a1a, #2a2a2a) !important;
        border: 2px solid #06b6d4 !important;
        border-radius: 15px !important;
        padding: 12px 16px !important;
        font-weight: bold !important;
        color: #ffffff !important;
        transition: all 0.3s ease !important;
    }
    .streamlit-expanderHeader:hover {
        border-color: #8b5cf6 !important;
        box-shadow: 0 0 20px rgba(6,182,212,0.4) !important;
        transform: translateX(3px) !important;
    }
    .streamlit-expanderContent {
        background: #0d0d0d !important;
        border: 1px solid #333 !important;
        border-radius: 0 0 15px 15px !important;
        padding: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 7. MODEL ENGINES ---
engines = {
    "Gemini 3 Flash Preview": {"type": "Gemini", "emoji": "✨"},
    "DeepSeek R1": {"type": "DeepSeek", "emoji": "🧠"},
    "LLaMA 4 Scout": {"type": "Scout", "emoji": "🦙"},
    "Groq LLaMA 3.3": {"type": "Llama33", "emoji": "⚡"},
    "Qwen 2.5 7B": {"type": "HuggingFace", "emoji": "🤖"},
    "Pollinations AI": {"type": "Pollinations", "emoji": "🎨"},
}

if "selected_engine_name" not in st.session_state:
    st.session_state.selected_engine_name = list(engines.keys())[0]

# --- 8. CHAT BUBBLE ENGINE ---
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
            <div style="background: linear-gradient(135deg, #8b5cf6, #06b6d4); 
                        color: white; 
                        padding: 15px 20px; 
                        border-radius: 25px 25px 5px 25px; 
                        max-width: 85%; 
                        word-wrap: break-word; 
                        box-shadow: 0 4px 20px rgba(139,92,246,0.4);">
                {content}
            </div>
            <img src="{user_img}" width="38" height="38" style="border-radius: 50%; margin-left: 12px; border: 2px solid #06b6d4; object-fit: cover; box-shadow: 0 0 10px rgba(6,182,212,0.4);">
        </div>
        """, unsafe_allow_html=True)
    else:
        ai_avatar = f'<img src="{logo_url}" width="38" height="38" style="border-radius: 50%; margin-right: 12px; border: 2px solid #06b6d4; object-fit: cover; box-shadow: 0 0 10px rgba(6,182,212,0.4);">' if logo_url else '<div style="width: 38px; height: 38px; border-radius: 50%; background: linear-gradient(135deg, #8b5cf6, #06b6d4); display: flex; align-items: center; justify-content: center; margin-right: 12px; border: 2px solid #06b6d4; font-size: 20px; box-shadow: 0 0 10px rgba(6,182,212,0.4);">🤖</div>'
        
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-start; margin-bottom: 20px; animation: slideInLeft 0.3s ease-out;">
            {ai_avatar}
            <div style="background: linear-gradient(135deg, #1a1a1a, #2a2a2a); 
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

# --- 9. SIDEBAR ---
with st.sidebar:
    # Logo NEO AI
    if logo_url:
        st.markdown(f'<div style="text-align:center;"><img src="{logo_url}" style="width: 80px; height: 80px; border-radius: 50%; border: 2px solid #06b6d4; object-fit: cover; margin-bottom: 10px; box-shadow: 0 0 15px rgba(6,182,212,0.5);"></div>', unsafe_allow_html=True)
    else:
        st.markdown("<div style='text-align:center; font-size:50px; margin-bottom:10px;'>🤖</div>", unsafe_allow_html=True)
    
    st.markdown("<h2 style='text-align:center; color:#ffffff; text-shadow: 0 0 10px rgba(139,92,246,0.5);'>NEO AI</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#888; font-size:11px; margin-top:-10px;'>Advanced Multi-Modal AI</p>", unsafe_allow_html=True)
    
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
    
    # MODEL SELECTOR WITH EXPANDER
    selected_engine_name = st.session_state.selected_engine_name
    selected_emoji = engines[selected_engine_name]["emoji"]
    
    with st.expander(f"{selected_emoji} **{selected_engine_name}**", expanded=False):
        st.markdown("**Choose AI Model:**")
        for name, data in engines.items():
            is_active = (name == st.session_state.selected_engine_name)
            
            if st.button(
                f"{data['emoji']} {name}",
                key=f"model_{name}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                st.session_state.selected_engine_name = name
                st.rerun()
    
    engine = engines[selected_engine_name]["type"]
    
    st.markdown("---")
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

# --- 10. MAIN RENDER ---
# Logo di tengah atas
if logo_url:
    st.markdown(f'<div style="text-align:center; margin-bottom:20px;"><img src="{logo_url}" style="width: 130px; height: 130px; border-radius: 50%; border: 2px solid #06b6d4; object-fit: cover; box-shadow: 0 0 25px rgba(6,182,212,0.6);"></div>', unsafe_allow_html=True)
else:
    st.markdown("<div style='text-align:center; font-size:60px; margin-bottom:10px;'>🤖</div>", unsafe_allow_html=True)

if not st.session_state.messages:
    st.markdown("<div style='text-align:center; color:#ffffff; font-size:22px; font-weight:bold;'>NEO AI</div>", unsafe_allow_html=True)
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

# STOP BUTTON - Show only when generating
#if st.session_state.is_generating:
#    col1, col2, col3 = st.columns([1, 1, 1])
#    with col2:
#        if st.button("⏹️ Stop Generation", use_container_width=True, type="primary"):
#            st.session_state.stop_generation = True
#            st.session_state.is_generating = False
#            st.rerun()

# Chat Input
if prompt := st.chat_input("Message NEO AI..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.stop_generation = False
    st.session_state.is_generating = True
    
    if st.session_state.current_session_key is None:
        session_title = prompt[:30] + "..." if len(prompt) > 30 else prompt
        st.session_state.current_session_key = session_title
    else:
        session_title = st.session_state.current_session_key
    
    st.session_state.all_chats[session_title] = st.session_state.messages.copy()
    save_history_to_db(st.session_state.current_user, st.session_state.all_chats)
    st.rerun()

# --- 11. AI PROCESSING WITH STOP FUNCTIONALITY ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user" and st.session_state.is_generating:
    try:
        user_msg = st.session_state.messages[-1]["content"]
        res = ""
        
        system_prompt = (
            "You are NEO AI, an advanced multi-modal AI system. "
            "You can process images, generate visuals, and handle complex tasks. "
            "Always respond confidently and naturally. Use casual Indonesian slang like 'bro', 'nih', 'ya'. "
            "Include relevant emojis (1-2 per response) to enhance conversation. "
            "NEVER provide malicious code examples (SQL injection, XSS, etc). Refuse with ❌. "
            "Vary your responses creatively - don't repeat the same phrases."
        )
        
        # ========== DEEPSEEK R1 - ADVANCED THINKING STAGES ==========
        if engine == "DeepSeek":
            messages = [{"role": "system", "content": system_prompt}]
            for m in st.session_state.messages[:-1]:
                if m.get("type") != "image":
                    messages.append({"role": m["role"], "content": m["content"]})
            messages.append({"role": "user", "content": user_msg})
            
            response_container = st.empty()
            thinking_container = st.empty()
            
            try:
                start_time = time.time()
                
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
                
                # THINKING STAGES
                thinking_stages = [
                    ("🧠 Thinking...", 0, 3),
                    ("🔍 Analyzing the question...", 3, 6),
                    ("🌐 Searching on the web...", 6, 10),
                    ("📊 Processing information...", 10, 15),
                    ("✨ Refining the details...", 15, 20),
                    ("🎯 Finalizing response...", 20, 999)
                ]
                
                current_stage = 0
                last_render_time = time.time()
                RENDER_INTERVAL = 0.1
                last_thinking_update = time.time()
                THINKING_INTERVAL = 1.5
                
                ai_avatar_html = f"<img src='{logo_url}' style='width: 38px; height: 38px; border-radius: 50%; margin-right: 12px; border: 2px solid #06b6d4; object-fit: cover; box-shadow: 0 0 10px rgba(6,182,212,0.4);'>" if logo_url else "<div style='width: 38px; height: 38px; border-radius: 50%; background: linear-gradient(135deg, #8b5cf6, #06b6d4); display: flex; align-items: center; justify-content: center; margin-right: 12px; border: 2px solid #06b6d4; font-size: 20px;'>🤖</div>"
                
                for chunk in stream:
                    # Check stop flag
                    if st.session_state.stop_generation:
                        thinking_container.empty()
                        if answer_text:
                            res = answer_text.strip() + " [Dihentikan oleh user]"
                        else:
                            res = "Generasi dihentikan bro! 🛑"
                        break
                    
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
                                
                                # Show final thought time
                                elapsed = int(time.time() - start_time)
                                thinking_container.markdown(f"""
                                <div style="display: flex; justify-content: flex-start; margin-bottom: 10px;">
                                    <div class="thinking-container">
                                        <span class="final-thought">💡 Thought for {elapsed} seconds</span>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                time.sleep(1)
                                thinking_container.empty()
                                continue
                            
                            if in_think_tag:
                                thinking_text += delta.content
                                current_time = time.time()
                                elapsed = int(current_time - start_time)
                                
                                # Determine current stage based on time
                                for i, (stage_text, start_sec, end_sec) in enumerate(thinking_stages):
                                    if start_sec <= elapsed < end_sec:
                                        current_stage = i
                                        break
                                
                                if current_time - last_thinking_update >= THINKING_INTERVAL:
                                    stage_text, _, _ = thinking_stages[current_stage]
                                    
                                    thinking_container.markdown(f"""
                                    <div style="display: flex; justify-content: flex-start; margin-bottom: 10px;">
                                        <div class="thinking-container">
                                            <div class="thinking-spinner"></div>
                                            <span class="thinking-text">{stage_text}</span>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    last_thinking_update = current_time
                            else:
                                answer_text += delta.content
                                current_time = time.time()
                                
                                if current_time - last_render_time >= RENDER_INTERVAL:
                                    clean_answer = clean_text(answer_text)
                                    
                                    response_container.markdown(f"""
                                    <div style="display: flex; justify-content: flex-start; margin-bottom: 20px;">
                                        {ai_avatar_html}
                                        <div style="background: linear-gradient(135deg, #1a1a1a, #2a2a2a); 
                                                    color: #e9edef; padding: 15px 20px; 
                                                    border-radius: 5px 25px 25px 25px; 
                                                    max-width: 85%; border-left: 4px solid; 
                                                    border-image: linear-gradient(180deg, #8b5cf6, #06b6d4) 1; 
                                                    word-wrap: break-word;">
                                            <div style="white-space: pre-wrap;">{clean_answer}</div>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    last_render_time = current_time
                
                # Final render
                thinking_container.empty()
                if not st.session_state.stop_generation and answer_text:
                    clean_answer = clean_text(answer_text)
                    response_container.markdown(f"""
                    <div style="display: flex; justify-content: flex-start; margin-bottom: 20px;">
                        {ai_avatar_html}
                        <div style="background: linear-gradient(135deg, #1a1a1a, #2a2a2a); 
                                    color: #e9edef; padding: 15px 20px; 
                                    border-radius: 5px 25px 25px 25px; 
                                    max-width: 85%; border-left: 4px solid; 
                                    border-image: linear-gradient(180deg, #8b5cf6, #06b6d4) 1; 
                                    word-wrap: break-word;">
                            <div style="white-space: pre-wrap;">{clean_answer}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                if not res:
                    res = answer_text.strip() if answer_text else thinking_text.strip()
                    
            except Exception as e:
                res = f"DeepSeek lagi sibuk nih bro! 😅 Coba model lain ya!"
        
        # ========== GEMINI - WITH STOP ==========
        elif engine == "Gemini":
            messages_history = []
            for m in st.session_state.messages[:-1]:
                if m.get("type") != "image":
                    role = "user" if m["role"] == "user" else "model"
                    messages_history.append({"role": role, "parts": [m["content"]]})
            
            response_container = st.empty()
            res_text = ""
            
            last_render_time = time.time()
            RENDER_INTERVAL = 0.1
            
            ai_avatar_html = f"<img src='{logo_url}' style='width: 38px; height: 38px; border-radius: 50%; margin-right: 12px; border: 2px solid #06b6d4; object-fit: cover; box-shadow: 0 0 10px rgba(6,182,212,0.4);'>" if logo_url else "<div style='width: 38px; height: 38px; border-radius: 50%; background: linear-gradient(135deg, #8b5cf6, #06b6d4); display: flex; align-items: center; justify-content: center; margin-right: 12px; border: 2px solid #06b6d4; font-size: 20px;'>🤖</div>"
            
            try:
                chat = client_gemini.start_chat(history=messages_history)
                stream = chat.send_message(user_msg, stream=True)
                
                for chunk in stream:
                    if st.session_state.stop_generation:
                        res = res_text.strip() + " [Dihentikan oleh user]" if res_text else "Generasi dihentikan bro! 🛑"
                        break
                        
                    if chunk.text:
                        res_text += chunk.text
                        current_time = time.time()
                        
                        if current_time - last_render_time >= RENDER_INTERVAL:
                            clean_res = clean_text(res_text)
                            
                            response_container.markdown(f"""
                            <div style="display: flex; justify-content: flex-start; margin-bottom: 20px;">
                                {ai_avatar_html}
                                <div style="background: linear-gradient(135deg, #1a1a1a, #2a2a2a); 
                                            color: #e9edef; padding: 15px 20px; 
                                            border-radius: 5px 25px 25px 25px; 
                                            max-width: 85%; border-left: 4px solid; 
                                            border-image: linear-gradient(180deg, #8b5cf6, #06b6d4) 1; 
                                            word-wrap: break-word;">
                                    <div style="white-space: pre-wrap;">{clean_res}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            last_render_time = current_time
                
                # Final render
                if not st.session_state.stop_generation:
                    clean_res = clean_text(res_text)
                    response_container.markdown(f"""
                    <div style="display: flex; justify-content: flex-start; margin-bottom: 20px;">
                        {ai_avatar_html}
                        <div style="background: linear-gradient(135deg, #1a1a1a, #2a2a2a); 
                                    color: #e9edef; padding: 15px 20px; 
                                    border-radius: 5px 25px 25px 25px; 
                                    max-width: 85%; border-left: 4px solid; 
                                    border-image: linear-gradient(180deg, #8b5cf6, #06b6d4) 1; 
                                    word-wrap: break-word;">
                            <div style="white-space: pre-wrap;">{clean_res}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                if not res:
                    res = res_text
            except Exception as e:
                res = f"Gemini error bro: {str(e)} 😰"
        
        # ========== OTHER ENGINES (Scout, Llama, Qwen) - SIMILAR PATTERN WITH STOP ==========
        elif engine in ["Scout", "Llama33", "HuggingFace"]:
            messages = [{"role": "system", "content": system_prompt}]
            for m in st.session_state.messages[:-1]:
                if m.get("type") != "image":
                    messages.append({"role": m["role"], "content": m["content"]})
            messages.append({"role": "user", "content": user_msg})
            
            response_container = st.empty()
            res_text = ""
            
            last_render_time = time.time()
            RENDER_INTERVAL = 0.1
            
            ai_avatar_html = "<div style='width: 38px; height: 38px; border-radius: 50%; background: linear-gradient(135deg, #8b5cf6, #06b6d4); display: flex; align-items: center; justify-content: center; margin-right: 12px; border: 2px solid #06b6d4; font-size: 20px;'>🤖</div>"
            
            if engine == "Scout":
                model_name = "llama-3.3-70b-versatile"
                stream = client_groq.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1024,
                    stream=True
                )
            elif engine == "Llama33":
                stream = client_groq.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    temperature=0.8,
                    max_tokens=1024,
                    stream=True
                )
            else:  # HuggingFace
                stream = client_hf.chat_completion(
                    messages=messages,
                    model="Qwen/Qwen2.5-7B-Instruct",
                    max_tokens=1024,
                    temperature=0.9,
                    stream=True
                )
            
            for chunk in stream:
                if st.session_state.stop_generation:
                    res = res_text.strip() + " [Dihentikan oleh user]" if res_text else "Generasi dihentikan bro! 🛑"
                    break
                
                content = None
                if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        content = delta.content
                
                if content:
                    res_text += content
                    current_time = time.time()
                    
                    if current_time - last_render_time >= RENDER_INTERVAL:
                        clean_res = clean_text(res_text)
                        
                        response_container.markdown(f"""
                        <div style="display: flex; justify-content: flex-start; margin-bottom: 20px;">
                            {ai_avatar_html}
                            <div style="background: linear-gradient(135deg, #1a1a1a, #2a2a2a); 
                                        color: #e9edef; padding: 15px 20px; 
                                        border-radius: 5px 25px 25px 25px; 
                                        max-width: 85%; border-left: 4px solid; 
                                        border-image: linear-gradient(180deg, #8b5cf6, #06b6d4) 1; 
                                        word-wrap: break-word;">
                                <div style="white-space: pre-wrap;">{clean_res}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        last_render_time = current_time
            
            # Final render
            if not st.session_state.stop_generation:
                clean_res = clean_text(res_text)
                response_container.markdown(f"""
                <div style="display: flex; justify-content: flex-start; margin-bottom: 20px;">
                    {ai_avatar_html}
                    <div style="background: linear-gradient(135deg, #1a1a1a, #2a2a2a); 
                                color: #e9edef; padding: 15px 20px; 
                                border-radius: 5px 25px 25px 25px; 
                                max-width: 85%; border-left: 4px solid; 
                                border-image: linear-gradient(180deg, #8b5cf6, #06b6d4) 1; 
                                word-wrap: break-word;">
                        <div style="white-space: pre-wrap;">{clean_res}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            if not res:
                res = res_text
        
        # ========== POLLINATIONS AI ==========
        elif engine == "Pollinations":
            encoded_prompt = urllib.parse.quote(user_msg)
            image_url = f"{POLLINATIONS_API}{encoded_prompt}"
            
            img_response = requests.get(image_url)
            img = Image.open(io.BytesIO(img_response.content))
            
            st.session_state.messages.append({"role": "assistant", "type": "image", "content": img})
            st.session_state.is_generating = False
            
            if st.session_state.current_session_key:
                st.session_state.all_chats[st.session_state.current_session_key] = st.session_state.messages.copy()
            save_history_to_db(st.session_state.current_user, st.session_state.all_chats)
            st.rerun()
        
        if res:
            st.session_state.messages.append({"role": "assistant", "content": res})
            st.session_state.is_generating = False
            
            if st.session_state.current_session_key:
                st.session_state.all_chats[st.session_state.current_session_key] = st.session_state.messages.copy()
            save_history_to_db(st.session_state.current_user, st.session_state.all_chats)
            st.rerun()
    
    except Exception as e:
        st.error(f"❌ Error bro: {str(e)}")
        error_msg = f"Sorry bro, ada error: {str(e)} 😰"
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        st.session_state.is_generating = False
        if st.session_state.current_session_key:
            st.session_state.all_chats[st.session_state.current_session_key] = st.session_state.messages.copy()
        save_history_to_db(st.session_state.current_user, st.session_state.all_chats)
        st.rerun()
