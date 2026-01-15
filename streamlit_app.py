import streamlit as st
from groq import Groq
from huggingface_hub import InferenceClient
import os, base64, requests, json
import re
from PIL import Image
import io
import urllib.parse
import time
import hashlib

# --- 1. CONFIG & SYSTEM SETUP ---
st.set_page_config(page_title="Azura AI", page_icon="🌐", layout="wide")

# NAMA FILE DATABASE (Per-user dengan hash)
DB_FOLDER = "azura_users_db"
if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER)

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
                # Pastikan return dict, bukan list atau tipe lain
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
        colors = img.getcolors(maxcolors=10)
        return f"Size: {width}x{height}, Mode: {mode}, Dominant colors detected"
    except:
        return "Image analysis available"

# --- 2. USERNAME AUTHENTICATION ---
# PERBAIKAN: Initialize current_user di awal sebelum cek login
if "current_user" not in st.session_state:
    st.session_state.current_user = None

# Login Screen
if st.session_state.current_user is None:
    st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; height: 100vh; background: #050505;">
        <div style="background: linear-gradient(135deg, #001a1a 0%, #003333 100%); 
                    padding: 50px; border-radius: 20px; border: 2px solid #00ffff; 
                    box-shadow: 0 0 30px rgba(0,255,255,0.4); text-align: center; max-width: 400px;">
            <h1 style="color: #00ffff; margin-bottom: 10px;">🌐 Azura AI</h1>
            <p style="color: #888; margin-bottom: 30px;">Secure Multi-Modal AI Assistant</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h3 style='text-align:center; color:#00ffff; margin-bottom:20px;'>🔐 Login</h3>", unsafe_allow_html=True)
        username_input = st.text_input("Enter Username", placeholder="Your unique username", key="login_username")
        
        if st.button("🚀 Enter Azura AI", use_container_width=True):
            if username_input.strip():
                st.session_state.current_user = username_input.strip()
                # PERBAIKAN: Clear state lain untuk force reload
                if "all_chats" in st.session_state:
                    del st.session_state.all_chats
                if "messages" in st.session_state:
                    del st.session_state.messages
                st.rerun()
            else:
                st.error("❌ Username tidak boleh kosong bro!")
    st.stop()

# --- 3. INITIALIZE SESSION STATE (Per User) ---
# PERBAIKAN: Load history dulu sebelum set messages
if "all_chats" not in st.session_state:
    st.session_state.all_chats = load_history_from_db(st.session_state.current_user)

# PERBAIKAN: Logic messages initialization yang lebih clean
if "messages" not in st.session_state:
    if st.session_state.all_chats:
        # Ambil chat terakhir dari history
        last_key = list(st.session_state.all_chats.keys())[-1]
        st.session_state.messages = st.session_state.all_chats[last_key].copy()
    else:
        # Kalau belum ada history, mulai chat baru
        st.session_state.messages = []

# PERBAIKAN: Tambah flag untuk track apakah baru login
if "just_logged_in" not in st.session_state:
    st.session_state.just_logged_in = True

if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

if "show_system_info" not in st.session_state:
    st.session_state.show_system_info = False

if "show_upload_notif" not in st.session_state:
    st.session_state.show_upload_notif = False

# PERBAIKAN: Tambah current_session_key untuk track chat aktif
if "current_session_key" not in st.session_state:
    if st.session_state.all_chats:
        st.session_state.current_session_key = list(st.session_state.all_chats.keys())[-1]
    else:
        st.session_state.current_session_key = None

# --- 4. API KEYS ---
try:
    client_groq = Groq(api_key=st.secrets["GROQ_API_KEY"])
    client_hf = InferenceClient(token=st.secrets["HF_TOKEN"])
    POLLINATIONS_API = "https://image.pollinations.ai/prompt/"
except:
    st.error("❌ API Keys Error! Cek secrets.toml lu bro.")
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
user_data = get_base64_img('user.png')
user_img = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRfIrn5orx6KdLUiIvZ3IUkZTMdIyes-D6sMA&s"

# --- 6. CSS (UI CLEAN & RESPONSIVE) ---
st.markdown(f"""
<style>
    [data-testid="stAppViewContainer"] {{ background: #050505; }}
    
    /* Tombol Plus (+) Fix Position */
    [data-testid="stFileUploader"] {{ position: fixed; bottom: 58px; left: 15px; width: 45px; z-index: 1000; }}
    [data-testid="stFileUploaderDropzone"] {{
        background: #00ffff11 !important; border: 1px solid #00ffff44 !important; border-radius: 50% !important;
        height: 42px !important; width: 42px !important; padding: 0 !important;
    }}
    [data-testid="stFileUploaderDropzone"] div {{ display: none !important; }}
    [data-testid="stFileUploaderDropzone"]::before {{
        content: "＋"; color: #00ffff; font-size: 26px; font-weight: bold;
        display: flex; align-items: center; justify-content: center; height: 100%;
    }}
    [data-testid="stFileUploader"] label {{ display: none !important; }}
    
    [data-testid="stChatInput"] {{ margin-left: 60px !important; width: calc(100% - 80px) !important; }}
    
    .sidebar-logo {{ display: block; margin: auto; width: 80px; height: 80px; border-radius: 50%; border: 2px solid #00ffff; object-fit: cover; margin-bottom: 10px; }}
    
    /* Logo Berputar di Tengah */
    .rotating-logo {{
        animation: rotate 8s linear infinite;
        border-radius: 50%;
        border: 2px solid #00ffff;
    }}
    @keyframes rotate {{
        from {{ transform: rotate(0deg); }}
        to {{ transform: rotate(360deg); }}
    }}
    
    /* Typing Animation */
    .typing {{ display: flex; align-items: center; gap: 5px; padding: 5px 0; }}
    .dot {{ width: 7px; height: 7px; background: #00ffff; border-radius: 50%; animation: blink 1.4s infinite both; }}
    .dot:nth-child(2) {{ animation-delay: 0.2s; }}
    .dot:nth-child(3) {{ animation-delay: 0.4s; }}
    @keyframes blink {{ 0%, 80%, 100% {{ opacity: 0; }} 40% {{ opacity: 1; }} }}
    
    /* Efek Halus */
    .chat-bubble {{ transition: all 0.3s ease; }}
    .chat-bubble:hover {{ transform: scale(1.02); }}
    
    .stButton button {{ transition: all 0.3s ease; }}
    .stButton button:hover {{ transform: scale(1.05); box-shadow: 0 0 15px #00ffff; }}
    .stButton button:active {{ transform: scale(0.95); }}
    
    /* Vision Bubble Animation */
    .vision-bubble {{ animation: pulse 2s infinite; }}
    @keyframes pulse {{ 0% {{ transform: scale(1); }} 50% {{ transform: scale(1.05); }} 100% {{ transform: scale(1); }} }}
    
    /* Spinner Animation */
    .spinner {{
        border: 3px solid #00ffff22;
        border-top: 3px solid #00ffff;
        border-radius: 50%;
        width: 20px;
        height: 20px;
        animation: spin 1s linear infinite;
        display: inline-block;
        margin-right: 10px;
        vertical-align: middle;
    }}
    @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
    
    /* User Badge Style */
    .user-badge {{
        background: linear-gradient(135deg, #00ffff22, #00ffff44);
        padding: 8px 15px;
        border-radius: 20px;
        border: 1px solid #00ffff;
        color: #00ffff;
        font-size: 13px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 15px;
        box-shadow: 0 0 10px rgba(0,255,255,0.2);
    }}
</style>
""", unsafe_allow_html=True)

# --- 7. BUBBLE ENGINE (ANTI BOCOR HTML) ---
def clean_text(text):
    """Fungsi Satpam: Bersihin sampah HTML dari output AI"""
    if not isinstance(text, str): 
        return str(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'")
    text = text.replace("</div>", "").replace("<div>", "").replace("<br>", "\n").replace("<p>", "").replace("</p>", "")
    return text.strip()

def render_chat_bubble(role, content):
    content = clean_text(content)
    
    if role == "user":
        st.markdown(f"""
        <div class="chat-bubble" style="display: flex; justify-content: flex-end; align-items: flex-start; margin-bottom: 20px;">
            <div style="background: #002b2b; color: white; padding: 12px 18px; border-radius: 18px 18px 2px 18px; 
                        max-width: 85%; border-right: 3px solid #00ffff; box-shadow: 0 4px 15px rgba(0,255,255,0.1);">
                {content}
            </div>
            <img src="{user_img}" width="35" height="35" style="border-radius: 50%; margin-left: 10px; border: 1px solid #00ffff; object-fit: cover;">
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-bubble" style="display: flex; justify-content: flex-start; align-items: flex-start; margin-bottom: 20px;">
            <img src="{logo_url}" width="35" height="35" style="border-radius: 50%; margin-right: 10px; border: 1px solid #00ffff; object-fit: cover;">
            <div style="background: #1a1a1a; color: #e9edef; padding: 12px 18px; border-radius: 2px 18px 18px 18px; 
                        max-width: 85%; border-left: 1px solid #333; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                {content}
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- 8. SIDEBAR (HISTORY MANAGER) ---
with st.sidebar:
    if logo_url: 
        st.markdown(f'<img src="{logo_url}" class="sidebar-logo">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:#00ffff;'>Azura AI</h2>", unsafe_allow_html=True)
    
    # User Badge dengan Logout
    st.markdown(f'<div class="user-badge">👤 {st.session_state.current_user}</div>', unsafe_allow_html=True)
    if st.button("🚪 Logout", use_container_width=True):
        # PERBAIKAN: Clear semua state sebelum logout
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
        "Azura-Lens 1.7 (Vision)": "Scout",
        "Azura 1.5 (Power)": "Llama33",
        "Azura-Prime (Creative)": "HuggingFace",
        "Azura-Art (Draw)": "Pollinations"
    }
    selected_engine_name = st.selectbox("Pilih modelnya", list(engine_map.keys()))
    engine = engine_map[selected_engine_name]

    st.markdown("### 🕒 Saved History")
    
    # PERBAIKAN: Sort chats by timestamp (latest first) dan tampilkan dengan better UI
    chat_keys = list(st.session_state.all_chats.keys())[::-1]  # Reverse untuk latest first
    
    if chat_keys:
        for title in chat_keys:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                # PERBAIKAN: Highlight chat yang sedang aktif
                button_style = "💬" if title != st.session_state.current_session_key else "✅"
                if st.button(f"{button_style} {title}", key=f"load_{title}", use_container_width=True):
                    st.session_state.messages = st.session_state.all_chats[title].copy()
                    st.session_state.current_session_key = title
                    st.rerun()
            with col2:
                if st.button("✏️", key=f"rename_{title}", help="Rename"):
                    new_name = st.text_input("New name", value=title, key=f"input_{title}")
                    if st.button("Save", key=f"save_{title}"):
                        if new_name and new_name != title:
                            st.session_state.all_chats[new_name] = st.session_state.all_chats.pop(title)
                            if st.session_state.current_session_key == title:
                                st.session_state.current_session_key = new_name
                            save_history_to_db(st.session_state.current_user, st.session_state.all_chats)
                            st.rerun()
            with col3:
                if st.button("🗑️", key=f"delete_{title}", help="Delete"):
                    del st.session_state.all_chats[title]
                    if st.session_state.current_session_key == title:
                        st.session_state.current_session_key = None
                        st.session_state.messages = []
                    save_history_to_db(st.session_state.current_user, st.session_state.all_chats)
                    st.rerun()
    else:
        st.info("Belum ada history nih bro! 📝")
    
    st.markdown("---")
    
    # System Info Toggle
    if st.button("📋 System Info", use_container_width=True):
        st.session_state.show_system_info = not st.session_state.show_system_info
    
    # System Info Content - FULL VERSION
    if st.session_state.show_system_info:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #001a1a 0%, #002b2b 100%); 
                    padding: 25px; border-radius: 15px; border: 2px solid #00ffff; 
                    box-shadow: 0 0 20px rgba(0,255,255,0.3); margin: 15px 0;">
            <h3 style="color: #00ffff; text-align: center; margin-bottom: 5px;">🌐 Azura AI System</h3>
            <p style="color: #888; text-align: center; font-size: 13px; margin-bottom: 3px;">Advanced Multi-Modal AI Assistant</p>
            <p style="color: #00ffff; text-align: center; font-size: 11px;">Created by Muhammad Jibran Al Kaffie</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: #00ffff11; padding: 18px; border-radius: 10px; 
                    border-left: 4px solid #00ffff; margin: 15px 0;">
            <h4 style="color: #00ffff; margin: 0 0 10px 0;">✨ Features</h4>
            <p style="color: #b0b0b0; line-height: 1.7; margin: 0;">
                • Persistent chat history per user<br>
                • Multi-modal AI (text, vision, image gen)<br>
                • Secure user isolation with MD5<br>
                • Real-time pixel analysis<br>
                • Session management & rename
            </p>
        </div>
        """, unsafe_allow_html=True)

# --- 9. MAIN RENDER ---
if logo_url:
    st.markdown(f'<div style="text-align:center; margin-bottom:20px;"><img src="{logo_url}" width="130" class="rotating-logo"></div>', unsafe_allow_html=True)
    
    # PERBAIKAN: Tampilkan welcome message kalau baru login atau chat kosong
    if not st.session_state.messages:
        st.markdown("<div style='text-align:center; color:#00ffff; font-size:18px; margin-bottom:20px;'>How can I help you today? 👋</div>", unsafe_allow_html=True)

# Render Chat
for msg in st.session_state.messages:
    if msg.get("type") == "image": 
        st.image(msg["content"], width=400)
    else: 
        render_chat_bubble(msg["role"], msg["content"])

# File Uploader
up = st.file_uploader("", type=["png","jpg","jpeg"], label_visibility="collapsed")
if up: 
    st.session_state.uploaded_image = up.getvalue()
    st.session_state.show_upload_notif = True

# Notifikasi Upload
if st.session_state.show_upload_notif:
    notif_placeholder = st.empty()
    notif_placeholder.markdown("""
    <div style="position: fixed; top: 20px; right: 20px; background: linear-gradient(135deg, #00ffff22, #00ffff44); 
                padding: 15px 20px; border-radius: 10px; border: 1px solid #00ffff; z-index: 9999;
                box-shadow: 0 4px 15px rgba(0,255,255,0.3); animation: slideIn 0.3s ease;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 20px;">✅</span>
            <div>
                <div style="color: #00ffff; font-weight: bold; font-size: 14px;">Image Uploaded!</div>
                <div style="color: #b0b0b0; font-size: 12px;">Ready for analysis, bro! 🔍</div>
            </div>
        </div>
    </div>
    <style>
        @keyframes slideIn {
            from { transform: translateX(400px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    </style>
    """, unsafe_allow_html=True)
    
    time.sleep(3)
    notif_placeholder.empty()
    st.session_state.show_upload_notif = False

# Chat Input
if prompt := st.chat_input("Message Azura AI..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # PERBAIKAN: Generate session key yang lebih baik
    if st.session_state.current_session_key is None:
        # Chat baru, buat key baru
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        session_title = f"{prompt[:15]}... ({timestamp})"
        st.session_state.current_session_key = session_title
    else:
        # Update chat yang sudah ada
        session_title = st.session_state.current_session_key
    
    # PERBAIKAN: Save dengan current session key
    st.session_state.all_chats[session_title] = st.session_state.messages.copy()
    save_history_to_db(st.session_state.current_user, st.session_state.all_chats)
    
    st.rerun()

# --- 10. AI PROCESSING ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.container():
        if engine == "Scout" and st.session_state.uploaded_image:
            st.markdown(f"""
            <div class="vision-bubble" style="display: flex; justify-content: flex-start; align-items: flex-start; margin-bottom: 20px;">
                <img src="{logo_url}" width="35" height="35" style="border-radius: 50%; margin-right: 10px; border: 1px solid #00ffff; object-fit: cover;">
                <div style="background: #1a1a1a; color: #e9edef; padding: 12px 18px; border-radius: 2px 18px 18px 18px; 
                            max-width: 85%; border-left: 1px solid #333; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                    <div class="spinner"></div>
                    <span style="vertical-align: middle;">🔍 Analyzing your image... Bro, give me a sec! 🤔</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display: flex; justify-content: flex-start; align-items: flex-start; margin-bottom: 20px;">
                <img src="{logo_url}" width="35" height="35" style="border-radius: 50%; margin-right: 10px; border: 1px solid #00ffff;">
                <div style="background: #1a1a1a; padding: 12px 18px; border-radius: 2px 18px 18px 18px; border: 1px solid #333;">
                    <div class="typing"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    try:
        user_msg = st.session_state.messages[-1]["content"]
        res = ""
        
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
            "Use emojis sparingly but effectively to enhance the chat experience, like a real conversation. Avoid overusing them—1-2 per response is enough. "
            "Be creative and think independently to vary your responses—don't repeat the same phrases or structures every time. Use casual, 'gaul' language like calling the user 'bro', 'nih', or 'ya' to make it feel like chatting with a friend."
        )
        
        # LOGIKA PEMILIHAN MODEL
        if engine == "Scout":
            current_image_data = st.session_state.uploaded_image
            
            if current_image_data:
                current_pixel_analysis = analyze_image_pixels(current_image_data)
                base64_image = base64.b64encode(current_image_data).decode('utf-8')
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": [
                        {"type": "text", "text": user_msg + f" (Analyze the uploaded image using this pixel data: {current_pixel_analysis})"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]}
                ]
                
                active_model = "meta-llama/llama-4-scout-17b-16e-instruct"
                
                resp = client_groq.chat.completions.create(
                    model=active_model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1024
                )
                res = resp.choices[0].message.content
                st.session_state.uploaded_image = None
            else:
                messages = [{"role": "system", "content": system_prompt}]
                for m in st.session_state.messages[:-1]:
                    if m.get("type") != "image":
                        messages.append({"role": m["role"], "content": m["content"]})
                messages.append({"role": "user", "content": user_msg})
                
                resp = client_groq.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1024
                )
                res = resp.choices[0].message.content
        
                elif engine == "Llama33":
            messages = [{"role": "system", "content": system_prompt}]
            for m in st.session_state.messages[:-1]:
                if m.get("type") != "image":
                    messages.append({"role": m["role"], "content": m["content"]})
            messages.append({"role": "user", "content": user_msg})
            
            resp = client_groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.8,
                max_tokens=1024
            )
            res = resp.choices[0].message.content
        
        elif engine == "HuggingFace":
            messages = [{"role": "system", "content": system_prompt}]
            for m in st.session_state.messages[:-1]:
                if m.get("type") != "image":
                    messages.append({"role": m["role"], "content": m["content"]})
            messages.append({"role": "user", "content": user_msg})
            
            resp = client_hf.chat_completion(
                messages=messages,
                model="Qwen/Qwen2.5-7B-Instruct",
                max_tokens=1024,
                temperature=0.9
            )
            res = resp.choices[0].message.content
        
        elif engine == "Pollinations":
            import urllib.parse
            encoded_prompt = urllib.parse.quote(user_msg)
            image_url = f"{POLLINATIONS_API}{encoded_prompt}"
            
            img_response = requests.get(image_url)
            img = Image.open(io.BytesIO(img_response.content))
            
            st.session_state.messages.append({"role": "assistant", "type": "image", "content": img})
            save_history_to_db(st.session_state.current_user, st.session_state.all_chats)
            st.rerun()
        
        if res:
            st.session_state.messages.append({"role": "assistant", "content": res})
            
            if len(st.session_state.messages) == 2:
                session_title = st.session_state.messages[0]["content"][:20]
            else:
                session_title = list(st.session_state.all_chats.keys())[-1] if st.session_state.all_chats else st.session_state.messages[0]["content"][:20]
            
            st.session_state.all_chats[session_title] = st.session_state.messages
            save_history_to_db(st.session_state.current_user, st.session_state.all_chats)
            st.rerun()
    
    except Exception as e:
        st.error(f"❌ Error bro: {str(e)}")
        st.session_state.messages.append({"role": "assistant", "content": f"Sorry bro, ada error nih: {str(e)} 😰"})
        st.rerun()
