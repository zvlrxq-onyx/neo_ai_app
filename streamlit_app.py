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
st.set_page_config(page_title="ZETRO", page_icon="/images/photo1769259058.jpg", layout="wide")

# Simple Session State
if "cookies_ready" not in st.session_state:
    st.session_state.cookies_ready = True

# Database folder
DB_FOLDER = "zetro_users_db"
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
                    border: 2px solid;
                    border-image: linear-gradient(135deg, #8b5cf6, #06b6d4) 1;
                    box-shadow: 0 0 40px rgba(6,182,212,0.3); text-align: center; max-width: 400px;">
            <h1 style="color: #ffffff; margin-bottom: 10px;">ZETRO</h1>
            <p style="color: #888; margin-bottom: 30px;">Sistem AI Terintegrasi</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            st.markdown("<h3 style='text-align:center; color:#ffffff; margin-bottom:20px;'>Login</h3>", unsafe_allow_html=True)
            login_username = st.text_input("Username", placeholder="Your username", key="login_user")
            login_password = st.text_input("Password", type="password", placeholder="Your password", key="login_pass")
            
            if st.button("Login", use_container_width=True, key="btn_login"):
                if login_username.strip() and login_password.strip():
                    if verify_user(login_username.strip(), login_password.strip()):
                        st.session_state.current_user = login_username.strip()
                        st.success("Login successful!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Username atau password salah!")
                else:
                    st.error("Isi username dan password!")
        
        with tab2:
            st.markdown("<h3 style='text-align:center; color:#ffffff; margin-bottom:20px;'>Register</h3>", unsafe_allow_html=True)
            reg_username = st.text_input("Username", placeholder="Choose a username", key="reg_user")
            reg_password = st.text_input("Password", type="password", placeholder="Choose a password", key="reg_pass")
            reg_confirm = st.text_input("Confirm Password", type="password", placeholder="Confirm your password", key="reg_confirm")
            
            if st.button("Register", use_container_width=True, key="btn_register"):
                if reg_username.strip() and reg_password.strip() and reg_confirm.strip():
                    if reg_password != reg_confirm:
                        st.error("Password tidak sama!")
                    elif len(reg_password) < 4:
                        st.error("Password minimal 4 karakter!")
                    else:
                        success, message = register_user(reg_username.strip(), reg_password.strip())
                        if success:
                            st.success(message + " Silakan login!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)
                else:
                    st.error("Isi semua field!")
    st.stop()

# --- 3. SESSION STATE ---
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

# --- 4. API KEYS ---
try:
    client_groq = Groq(api_key=st.secrets["GROQ_API_KEY"])
    client_hf = InferenceClient(token=st.secrets["HF_TOKEN"])
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    client_gemini = genai.GenerativeModel('gemini-2.0-flash-exp')
    POLLINATIONS_API = "https://image.pollinations.ai/prompt/"
except Exception as e:
    st.error(f"API Keys Error: {e}")
    st.stop()

# --- 5. LOAD LOGO ---
@st.cache_data
def get_base64_img(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo_data = get_base64_img('/images/photo1769259058.jpg')
logo_url = f"data:image/png;base64,{logo_data}" if logo_data else ""

# --- 6. CSS ---
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background: #0a0a0a; }
    
    /* File Uploader */
    [data-testid="stFileUploader"] { position: fixed; bottom: 58px; left: 15px; width: 45px; z-index: 1000; }
    [data-testid="stFileUploaderDropzone"] {
        background: #1a1a1a !important; 
        border: 2px solid;
        border-image: linear-gradient(135deg, #8b5cf6, #06b6d4) 1 !important;
        border-radius: 50% !important;
        height: 42px !important; 
        width: 42px !important; 
        padding: 0 !important;
        transition: all 0.3s ease !important;
    }
    [data-testid="stFileUploaderDropzone"]:hover {
        transform: scale(1.1) !important;
        box-shadow: 0 0 20px rgba(6,182,212,0.4) !important;
    }
    [data-testid="stFileUploaderDropzone"] div { display: none !important; }
    [data-testid="stFileUploaderDropzone"]::before {
        content: "+"; color: #06b6d4; font-size: 24px; font-weight: bold;
        display: flex; align-items: center; justify-content: center; height: 100%;
    }
    [data-testid="stFileUploader"] label { display: none !important; }
    
    /* Chat Input */
    [data-testid="stChatInput"] { margin-left: 60px !important; width: calc(100% - 80px) !important; }
    [data-testid="stChatInputTextArea"] {
        border-radius: 0px !important;
        border: 2px solid;
        border-image: linear-gradient(135deg, #8b5cf6, #06b6d4) 1 !important;
        background: #1a1a1a !important;
        padding: 12px 50px 12px 20px !important;
    }
    
    /* Submit Button - Arrow Up */
    [data-testid="stChatInputSubmitButton"] {
        background: linear-gradient(135deg, #8b5cf6, #06b6d4) !important;
        border-radius: 50% !important;
        width: 40px !important;
        height: 40px !important;
        border: none !important;
    }
    [data-testid="stChatInputSubmitButton"]:hover {
        transform: scale(1.1) !important;
        box-shadow: 0 0 20px rgba(139,92,246,0.5) !important;
    }
    [data-testid="stChatInputSubmitButton"] svg {
        color: white !important;
        transform: rotate(-90deg) !important;
    }
    
    /* Logo with gradient border */
    .logo-container {
        width: 80px;
        height: 80px;
        margin: 0 auto 15px;
        border-radius: 50%;
        padding: 3px;
        background: linear-gradient(135deg, #8b5cf6, #06b6d4);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .logo-inner {
        width: 100%;
        height: 100%;
        border-radius: 50%;
        background: #0a0a0a;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
    }
    .logo-inner img {
        width: 90%;
        height: 90%;
        object-fit: cover;
        border-radius: 50%;
    }
    
    /* Model logo circle */
    .model-logo {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid;
        border-image: linear-gradient(135deg, #8b5cf6, #06b6d4) 1;
    }
    
    /* User badge */
    .user-badge {
        background: #1a1a1a;
        border: 2px solid;
        border-image: linear-gradient(135deg, #8b5cf6, #06b6d4) 1;
        padding: 8px 16px;
        border-radius: 20px;
        color: #ffffff;
        font-size: 13px;
        text-align: center;
        margin-bottom: 15px;
    }
    
    /* Buttons */
    .stButton button {
        border: 1px solid;
        border-image: linear-gradient(135deg, #8b5cf6, #06b6d4) 1 !important;
        background: #1a1a1a !important;
        color: #ffffff !important;
        border-radius: 15px !important;
        transition: all 0.3s ease !important;
    }
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 20px rgba(6,182,212,0.3) !important;
    }
    
    /* Selectbox */
    [data-testid="stSelectbox"] > div {
        border-radius: 15px !important;
        border: 2px solid;
        border-image: linear-gradient(135deg, #8b5cf6, #06b6d4) 1 !important;
    }
    
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
</style>
""", unsafe_allow_html=True)

# --- 7. CHAT BUBBLE ---
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
                        border: 2px solid;
                        border-image: linear-gradient(135deg, #8b5cf6, #06b6d4) 1;
                        color: white; 
                        padding: 12px 18px; 
                        border-radius: 20px 20px 5px 20px; 
                        max-width: 70%; 
                        word-wrap: break-word;">
                {content}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-start; margin-bottom: 20px; animation: slideInLeft 0.3s ease-out;">
            <div style="background: #1a1a1a;
                        border: 2px solid;
                        border-image: linear-gradient(135deg, #8b5cf6, #06b6d4) 1;
                        color: #e9edef; 
                        padding: 12px 18px; 
                        border-radius: 5px 20px 20px 20px; 
                        max-width: 70%; 
                        word-wrap: break-word;">
                {content}
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- 8. SIDEBAR ---
with st.sidebar:
    if logo_url:
        st.markdown(f"""
        <div class="logo-container">
            <div class="logo-inner">
                <img src="{logo_url}">
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<h2 style='text-align:center; color:#ffffff;'>ZETRO</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#888; font-size:11px; margin-top:-10px;'>AI multi modal</p>", unsafe_allow_html=True)
    
    st.markdown(f'<div class="user-badge">{st.session_state.current_user}</div>', unsafe_allow_html=True)
    
    if st.button("Logout", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    if st.button("New Session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.uploaded_image = None
        st.session_state.current_session_key = None
        st.rerun()
        
    st.markdown("---")
    st.markdown("### AI Model")
    
    # Provider structure
    PROVIDERS = {
        "Gemini": {
            "logo": "/images/photo1769259061.jpg",
            "display_name": "Google Gemini",
            "models": [
                {"name": "Gemini 2.0 Flash", "engine": "Gemini", "model_id": "gemini-2.0-flash-exp"}
            ]
        },
        "Groq": {
            "logo": "assets/groq.png",
            "display_name": "Groq",
            "models": [
                {"name": "LLaMA 3.3 70B", "engine": "Fast", "model_id": "llama-3.3-70b-versatile"},
                {"name": "LLaMA 4 Scout (Vision)", "engine": "Vision", "model_id": "meta-llama/llama-4-scout-17b-16e-instruct"}
            ]
        },
        "DeepSeek": {
            "logo": "assets/deepseek.png",
            "display_name": "DeepSeek",
            "models": [
                {"name": "DeepSeek R1", "engine": "DeepSeek", "model_id": "deepseek-ai/DeepSeek-R1-Distill-Llama-70B"}
            ]
        },
        "HuggingFace": {
            "logo": "/images/photo1769259058.jpg",
            "display_name": "Qwen",
            "models": [
                {"name": "Qwen 2.5 7B", "engine": "HuggingFace", "model_id": "Qwen/Qwen2.5-7B-Instruct"}
            ]
        },
        "Pollinations": {
            "logo": "/images/Pollinations.jpg",
            "display_name": "Pollinations",
            "models": [
                {"name": "Image Generator", "engine": "Image Generator", "model_id": "pollinations-image-gen"}
            ]
        }
    }
    
    # Session state
    if "selected_provider" not in st.session_state:
        st.session_state.selected_provider = "Gemini"
    if "selected_model_key" not in st.session_state:
        st.session_state.selected_model_key = "Gemini_Gemini 2.0 Flash"
    
    # Provider selection
    provider_options = list(PROVIDERS.keys())
    provider_labels = [PROVIDERS[p]["display_name"] for p in provider_options]
    
    selected_provider_idx = provider_options.index(st.session_state.selected_provider) if st.session_state.selected_provider in provider_options else 0
    
    selected_provider_label = st.selectbox(
        "Provider",
        provider_labels,
        index=selected_provider_idx,
        key="provider_selector"
    )
    
    selected_provider = provider_options[provider_labels.index(selected_provider_label)]
    
    if selected_provider != st.session_state.selected_provider:
        st.session_state.selected_provider = selected_provider
        first_model = PROVIDERS[selected_provider]["models"][0]
        st.session_state.selected_model_key = f"{selected_provider}_{first_model['name']}"
    
    # Model selection
    st.markdown("**Model:**")
    
    provider_data = PROVIDERS[selected_provider]
    
    # Load provider logo
    provider_logo_data = get_base64_img(provider_data["logo"])
    provider_logo_url = f"data:image/png;base64,{provider_logo_data}" if provider_logo_data else ""
    
    for model_info in provider_data["models"]:
        model_key = f"{selected_provider}_{model_info['name']}"
        is_active = model_key == st.session_state.selected_model_key
        
        col1, col2 = st.columns([1, 5])
        with col1:
            if provider_logo_url:
                st.markdown(f'<img src="{provider_logo_url}" class="model-logo">', unsafe_allow_html=True)
        with col2:
            if st.button(
                model_info['name'],
                key=f"model_btn_{model_key}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                st.session_state.selected_model_key = model_key
                st.rerun()
    
    # Expose variables
    selected_model_data = None
    for model_info in PROVIDERS[selected_provider]["models"]:
        if f"{selected_provider}_{model_info['name']}" == st.session_state.selected_model_key:
            selected_model_data = model_info
            break
    
    if selected_model_data:
        engine = selected_model_data["engine"]
        model_id = selected_model_data["model_id"]
    else:
        engine = "Gemini"
        model_id = "gemini-2.0-flash-exp"
    
    st.markdown("---")
    st.markdown("### History")
    
    chat_keys = list(st.session_state.all_chats.keys())[::-1]
    
    if chat_keys:
        for title in chat_keys:
            col1, col2 = st.columns([4, 1])
            with col1:
                button_label = f"{'✓ ' if title == st.session_state.current_session_key else ''}{title}"
                if st.button(button_label, key=f"load_{title}", use_container_width=True):
                    st.session_state.messages = st.session_state.all_chats[title].copy()
                    st.session_state.current_session_key = title
                    st.rerun()
            with col2:
                if st.button("×", key=f"delete_{title}", use_container_width=True):
                    del st.session_state.all_chats[title]
                    if st.session_state.current_session_key == title:
                        st.session_state.current_session_key = None
                        st.session_state.messages = []
                    save_history_to_db(st.session_state.current_user, st.session_state.all_chats)
                    st.rerun()
    else:
        st.info("No history yet")

# --- 9. MAIN ---
if not st.session_state.messages:
    st.markdown("<div style='text-align:center; color:#ffffff; font-size:24px; font-weight:bold; margin-top:100px;'>ZETRO</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; color:#888; font-size:16px; margin-top:10px;'>How can I help you today?</div>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    if msg.get("type") == "image": 
        st.image(msg["content"], width=400)
    else:
        render_chat_bubble(msg["role"], msg["content"])

up = st.file_uploader("", type=["png","jpg","jpeg"], label_visibility="collapsed")
if up: 
    st.session_state.uploaded_image = up.getvalue()
    st.toast("Image uploaded!")

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
            "You are ZETRO, an advanced AI assistant. "
            "Respond naturally and helpfully. Keep responses concise and clear."
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
                    model=model_id,
                    max_tokens=2048,
                    temperature=0.7,
                    stream=True
                )
                
                answer_text = ""
                
                for chunk in stream:
                    if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, 'content') and delta.content:
                            answer_text += delta.content
                            clean_answer = clean_text(answer_text)
                            
                            response_container.markdown(f"""
                            <div style="display: flex; justify-content: flex-start; margin-bottom: 20px;">
                                <div style="background: #1a1a1a; border: 2px solid; border-image: linear-gradient(135deg, #8b5cf6, #06b6d4) 1;
                                            color: #e9edef; padding: 12px 18px; border-radius: 5px 20px 20px 20px; max-width: 70%; word-wrap: break-word;">
                                    <div style="white-space: pre-wrap;">{clean_answer}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            time.sleep(0.01)
                
                res = answer_text.strip()
                    
            except Exception as e:
                res = f"DeepSeek error: {str(e)}"
        
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
                        <div style="display: flex; justify-content: flex-start; margin-bottom: 20px;">
                            <div style="background: #1a1a1a; border: 2px solid; border-image: linear-gradient(135deg, #8b5cf6, #06b6d4) 1;
                                        color: #e9edef; padding: 12px 18px; border-radius: 5px 20px 20px 20px; max-width: 70%; word-wrap: break-word;">
                                <div style="white-space: pre-wrap;">{clean_res}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        time.sleep(0.01)
                
                res = res_text
            except Exception as e:
                res = f"Gemini error: {str(e)}"
        
        elif engine == "Vision":
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
                    model=model_id,
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
                            <div style="background: #1a1a1a; border: 2px solid; border-image: linear-gradient(135deg, #8b5cf6, #06b6d4) 1;
                                        color: #e9edef; padding: 12px 18px; border-radius: 5px 20px 20px 20px; max-width: 70%; word-wrap: break-word;">
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
                    model=model_id,
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
                            <div style="background: #1a1a1a; border: 2px solid; border-image: linear-gradient(135deg, #8b5cf6, #06b6d4) 1;
                                        color: #e9edef; padding: 12px 18px; border-radius: 5px 20px 20px 20px; max-width: 70%; word-wrap: break-word;">
                                <div style="white-space: pre-wrap;">{clean_res}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        time.sleep(0.02)
                
                res = res_text
        
        elif engine == "Fast":
            messages = [{"role": "system", "content": system_prompt}]
            for m in st.session_state.messages[:-1]:
                if m.get("type") != "image":
                    messages.append({"role": m["role"], "content": m["content"]})
            messages.append({"role": "user", "content": user_msg})
            
            response_container = st.empty()
            res_text = ""
            
            stream = client_groq.chat.completions.create(
                model=model_id,
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
                        <div style="background: #1a1a1a; border: 2px solid; border-image: linear-gradient(135deg, #8b5cf6, #06b6d4) 1;
                                    color: #e9edef; padding: 12px 18px; border-radius: 5px 20px 20px 20px; max-width: 70%; word-wrap: break-word;">
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
                model=model_id,
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
                            <div style="background: #1a1a1a; border: 2px solid; border-image: linear-gradient(135deg, #8b5cf6, #06b6d4) 1;
                                        color: #e9edef; padding: 12px 18px; border-radius: 5px 20px 20px 20px; max-width: 70%; word-wrap: break-word;">
                                <div style="white-space: pre-wrap;">{clean_res}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        time.sleep(0.02)
            
            res = res_text
        
        elif engine == "Image Generator":
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
        st.error(f"Error: {str(e)}")
        error_msg = f"Error: {str(e)}"
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        if st.session_state.current_session_key:
            st.session_state.all_chats[st.session_state.current_session_key] = st.session_state.messages.copy()
        save_history_to_db(st.session_state.current_user, st.session_state.all_chats)
        st.rerun()
