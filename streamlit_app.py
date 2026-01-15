import streamlit as st
from groq import Groq
from huggingface_hub import InferenceClient
import os, base64, requests, json
import re
from PIL import Image
import io
import urllib.parse
import time

# --- 1. CONFIG & SYSTEM SETUP ---
st.set_page_config(page_title="Azura AI", page_icon="🔵", layout="wide")

# NAMA FILE DATABASE (Simpan chat di sini biar ga ilang pas refresh)
DB_FILE = "azura_chat_history.json"

def load_history_from_db():
    """Load history dari file JSON biar tahan banting walau di-refresh"""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_history_to_db(history_dict):
    """Save history ke file JSON setiap ada chat baru"""
    try:
        with open(DB_FILE, "w") as f:
            json.dump(history_dict, f)
    except Exception as e:
        print(f"Gagal save db: {e}")

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

# --- 2. INITIALIZE SESSION STATE ---
if "all_chats" not in st.session_state:
    st.session_state.all_chats = load_history_from_db()

if "messages" not in st.session_state:
    if st.session_state.all_chats:
        last_key = list(st.session_state.all_chats.keys())[-1]
        st.session_state.messages = st.session_state.all_chats[last_key]
    else:
        st.session_state.messages = []

if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

if "show_system_info" not in st.session_state:
    st.session_state.show_system_info = False

if "show_upload_notif" not in st.session_state:
    st.session_state.show_upload_notif = False

# --- 3. API KEYS ---
try:
    client_groq = Groq(api_key=st.secrets["GROQ_API_KEY"])
    client_hf = InferenceClient(token=st.secrets["HF_TOKEN"])
    POLLINATIONS_API = "https://image.pollinations.ai/prompt/"
except:
    st.error("❌ API Keys Error! Cek secrets.toml lu bro.")
    st.stop()

# --- 4. ASSETS (LOGO & USER) ---
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

# --- 5. CSS (UI CYAN/BLUE THEME) ---
st.markdown(f"""
<style>
    [data-testid="stAppViewContainer"] {{ 
        background: linear-gradient(135deg, #001a33 0%, #002244 50%, #001a33 100%);
    }}
    
    /* Tombol Plus (+) Fix Position */
    [data-testid="stFileUploader"] {{ position: fixed; bottom: 58px; left: 15px; width: 45px; z-index: 1000; }}
    [data-testid="stFileUploaderDropzone"] {{
        background: #0099ff22 !important; 
        border: 2px solid #0099ff !important; 
        border-radius: 50% !important;
        height: 42px !important; 
        width: 42px !important; 
        padding: 0 !important;
        transition: all 0.3s ease;
    }}
    [data-testid="stFileUploaderDropzone"]:hover {{
        background: #0099ff44 !important;
        box-shadow: 0 0 20px #0099ff88;
        transform: scale(1.1);
    }}
    [data-testid="stFileUploaderDropzone"] div {{ display: none !important; }}
    [data-testid="stFileUploaderDropzone"]::before {{
        content: "＋"; 
        color: #0099ff; 
        font-size: 28px; 
        font-weight: bold;
        display: flex; 
        align-items: center; 
        justify-content: center; 
        height: 100%;
    }}
    [data-testid="stFileUploader"] label {{ display: none !important; }}
    
    [data-testid="stChatInput"] {{ 
        margin-left: 60px !important; 
        width: calc(100% - 80px) !important; 
    }}
    
    .sidebar-logo {{ 
        display: block; 
        margin: auto; 
        width: 90px; 
        height: 90px; 
        border-radius: 50%; 
        border: 3px solid #0099ff; 
        object-fit: cover; 
        padding: 8px;
        margin-bottom: 15px; 
        background: linear-gradient(135deg, #0099ff22, #0066cc22);
        box-shadow: 0 0 25px #0099ff66;
    }}
    
    /* Typing Animation */
    .typing {{ display: flex; align-items: center; gap: 5px; padding: 5px 0; }}
    .dot {{ 
        width: 8px; 
        height: 8px; 
        background: #0099ff; 
        border-radius: 50%; 
        animation: blink 1.4s infinite both; 
        box-shadow: 0 0 10px #0099ff;
    }}
    .dot:nth-child(2) {{ animation-delay: 0.2s; }}
    .dot:nth-child(3) {{ animation-delay: 0.4s; }}
    @keyframes blink {{ 0%, 80%, 100% {{ opacity: 0; }} 40% {{ opacity: 1; }} }}
    
    /* Chat Bubbles */
    .chat-bubble {{ transition: all 0.3s ease; }}
    .chat-bubble:hover {{ transform: scale(1.02); }}
    
    /* Buttons */
    .stButton button {{ 
        transition: all 0.3s ease; 
        background: linear-gradient(135deg, #0099ff22, #0066cc22) !important;
        border: 1px solid #0099ff55 !important;
        color: #0099ff !important;
    }}
    .stButton button:hover {{ 
        transform: scale(1.05); 
        box-shadow: 0 0 20px #0099ff; 
        background: linear-gradient(135deg, #0099ff44, #0066cc44) !important;
    }}
    .stButton button:active {{ transform: scale(0.95); }}
    
    /* Vision Bubble Animation */
    .vision-bubble {{ animation: pulse 2s infinite; }}
    @keyframes pulse {{ 
        0% {{ transform: scale(1); }} 
        50% {{ transform: scale(1.03); }} 
        100% {{ transform: scale(1); }} 
    }}
    
    /* Spinner */
    .spinner {{
        border: 3px solid #0099ff33;
        border-top: 3px solid #0099ff;
        border-radius: 50%;
        width: 20px;
        height: 20px;
        animation: spin 1s linear infinite;
        display: inline-block;
        margin-right: 10px;
        vertical-align: middle;
    }}
    @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #001a33 0%, #002244 100%);
    }}
    
    /* Select box styling */
    .stSelectbox {{ 
        background: #0099ff11 !important;
    }}
</style>
""", unsafe_allow_html=True)

# --- 6. BUBBLE ENGINE (ANTI BOCOR HTML) ---
def clean_text(text):
    """Fungsi Satpam: Bersihin sampah HTML dari output AI"""
    if not isinstance(text, str): 
        return str(text)
    # Hapus semua tag HTML dan entitas
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'")
    text = text.replace("</div>", "").replace("<div>", "").replace("<br>", "\n").replace("<p>", "").replace("</p>", "")
    return text.strip()

def render_chat_bubble(role, content):
    content = clean_text(content)
    
    if role == "user":
        st.markdown(f"""
        <div class="chat-bubble" style="display: flex; justify-content: flex-end; align-items: flex-start; margin-bottom: 20px;">
            <div style="background: linear-gradient(135deg, #003366, #004488); 
                        color: white; padding: 14px 20px; border-radius: 20px 20px 4px 20px; 
                        max-width: 85%; border: 2px solid #0099ff44; 
                        box-shadow: 0 4px 20px rgba(0,153,255,0.3);">
                {content}
            </div>
            <img src="{user_img}" width="38" height="38" 
                 style="border-radius: 50%; margin-left: 12px; 
                        border: 2px solid #0099ff; object-fit: cover;
                        box-shadow: 0 0 15px #0099ff66;">
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-bubble" style="display: flex; justify-content: flex-start; align-items: flex-start; margin-bottom: 20px;">
            <img src="{logo_url}" width="38" height="38" 
                 style="border-radius: 50%; margin-right: 12px; 
                        border: 2px solid #0099ff; object-fit: cover;
                        box-shadow: 0 0 15px #0099ff66;">
            <div style="background: linear-gradient(135deg, #1a1a2e, #16213e); 
                        color: #e9edef; padding: 14px 20px; border-radius: 4px 20px 20px 20px; 
                        max-width: 85%; border: 1px solid #0099ff33; 
                        box-shadow: 0 4px 20px rgba(0,153,255,0.2);">
                {content}
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- 7. SIDEBAR (HISTORY MANAGER) ---
with st.sidebar:
    if logo_url: 
        st.markdown(f'<img src="{logo_url}" class="sidebar-logo">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:#0099ff; text-shadow: 0 0 20px #0099ff;'>Azura AI</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#0099ff88; font-size:12px;'>Your Advanced AI Assistant</p>", unsafe_allow_html=True)
    
    if st.button("＋ New Session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.uploaded_image = None
        st.rerun()
        
    st.markdown("---")
    
    engine_map = {
        "🔍 Azura-Lens 1.7 (Vision)": "Scout",
        "⚡ Azura 1.5 (Power)": "Llama33",
        "✨ Azura-Prime (Creative)": "HuggingFace",
        "🎨 Azura-Art (Draw)": "Pollinations"
    }
    selected_engine_name = st.selectbox("🤖 Select AI Model", list(engine_map.keys()))
    engine = engine_map[selected_engine_name]

    st.markdown("### 🕒 Chat History")
    for title in list(st.session_state.all_chats.keys())[::-1]:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            if st.button(f"💬 {title}", key=f"load_{title}", use_container_width=True):
                st.session_state.messages = st.session_state.all_chats[title]
                st.rerun()
        with col2:
            if st.button("✏️", key=f"rename_{title}", help="Rename"):
                new_name = st.text_input("New name", value=title, key=f"input_{title}")
                if st.button("Save", key=f"save_{title}"):
                    if new_name and new_name != title:
                        st.session_state.all_chats[new_name] = st.session_state.all_chats.pop(title)
                        save_history_to_db(st.session_state.all_chats)
                        st.rerun()
        with col3:
            if st.button("🗑️", key=f"delete_{title}", help="Delete"):
                del st.session_state.all_chats[title]
                save_history_to_db(st.session_state.all_chats)
                st.rerun()
    
    st.markdown("---")
    
    # System Info
    if st.button("📋 System Info", use_container_width=True):
        st.session_state.show_system_info = not st.session_state.show_system_info
    
    if st.session_state.show_system_info:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #001a33, #003366); 
                    padding: 25px; border-radius: 15px; border: 2px solid #0099ff; 
                    box-shadow: 0 0 30px rgba(0,153,255,0.4); margin: 15px 0;">
            <h3 style="color: #0099ff; text-align: center; margin-bottom: 8px; text-shadow: 0 0 10px #0099ff;">🔵 Azura AI System</h3>
            <p style="color: #0099ff99; text-align: center; font-size: 13px; margin-bottom: 5px;">Advanced Multi-Modal AI Assistant</p>
            <p style="color: #0099ff; text-align: center; font-size: 11px;">Created by Muhammad Jibran Al Kaffie</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: #0099ff11; padding: 18px; border-radius: 10px; 
                    border-left: 4px solid #0099ff; margin: 15px 0;">
            <h4 style="color: #0099ff; margin: 0 0 10px 0;">👨‍💻 About Creator</h4>
            <p style="color: #b0b0b0; line-height: 1.7; margin: 0;">
                Azura AI dikembangkan oleh <strong style="color: #0099ff;">Muhammad Jibran Al Kaffie</strong>, 
                developer passionate yang menciptakan AI assistant multi-modal dengan teknologi cutting-edge.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("🔍 Azura-Lens 1.7 (Vision)", expanded=False):
            st.markdown("""
            <div style="background: #0099ff08; padding: 12px; border-radius: 8px;">
                <p style="color: #e0e0e0; line-height: 1.8; margin: 0;">
                    <strong style="color: #0099ff;">Model:</strong> Meta Llama 4 Scout 17B<br>
                    <strong style="color: #0099ff;">Capability:</strong> Advanced image analysis with pixel-deep detection
                </p>
            </div>
            """, unsafe_allow_html=True)

# --- 8. MAIN RENDER ---
if logo_url:
    st.markdown(f'''
    <div style="text-align:center; margin-bottom:25px;">
        <img src="{logo_url}" width="110" 
             style="border-radius:50%; border:3px solid #0099ff; 
                    box-shadow: 0 0 30px #0099ff88; padding: 10px;
                    background: linear-gradient(135deg, #0099ff22, #0066cc22);">
    </div>
    ''', unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; color:#0099ff; font-size:20px; margin-bottom:25px; text-shadow: 0 0 10px #0099ff;'>How can Azura help you today? ✨</div>", unsafe_allow_html=True)

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

# Upload Notification
if st.session_state.show_upload_notif:
    notif_placeholder = st.empty()
    notif_placeholder.markdown("""
    <div style="position: fixed; top: 20px; right: 20px; 
                background: linear-gradient(135deg, #0099ff33, #0099ff55); 
                padding: 16px 22px; border-radius: 12px; border: 2px solid #0099ff; z-index: 9999;
                box-shadow: 0 4px 25px rgba(0,153,255,0.5); animation: slideIn 0.3s ease;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 22px;">✅</span>
            <div>
                <div style="color: #0099ff; font-weight: bold; font-size: 15px;">Image Uploaded!</div>
                <div style="color: #e0e0e0; font-size: 12px;">Ready for analysis! 🔍</div>
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
    
    if len(st.session_state.messages) == 1:
        session_title = prompt[:20]
    else:
        session_title = st.session_state.messages[0]["content"][:20]
    
    st.session_state.all_chats[session_title] = st.session_state.messages
    save_history_to_db(st.session_state.all_chats)
    
    st.rerun()

# --- 9. AI PROCESSING ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.container():
        if engine == "Scout" and st.session_state.uploaded_image:
            st.markdown(f"""
            <div class="vision-bubble" style="display: flex; justify-content: flex-start; align-items: flex-start; margin-bottom: 20px;">
                <img src="{logo_url}" width="38" height="38" 
                     style="border-radius: 50%; margin-right: 12px; 
                            border: 2px solid #0099ff; object-fit: cover;
                            box-shadow: 0 0 15px #0099ff66;">
                <div style="background: linear-gradient(135deg, #1a1a2e, #16213e); 
                            color: #e9edef; padding: 14px 20px; border-radius: 4px 20px 20px 20px; 
                            max-width: 85%; border: 1px solid #0099ff33; 
                            box-shadow: 0 4px 20px rgba(0,153,255,0.3);">
                    <div class="spinner"></div>
                    <span style="vertical-align: middle; color: #0099ff;">🔍 Analyzing your image... Please wait! 🤔</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display: flex; justify-content: flex-start; align-items: flex-start; margin-bottom: 20px;">
                <img src="{logo_url}" width="38" height="38" 
                     style="border-radius: 50%; margin-right: 12px; 
                            border: 2px solid #0099ff;
                            box-shadow: 0 0 15px #0099ff66;">
                <div style="background: linear-gradient(135deg, #1a1a2e, #16213e); 
                            padding: 14px 20px; border-radius: 4px 20px 20px 20px; 
                            border: 1px solid #0099ff33;">
                    <div class="typing"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    try:
        user_msg = st.session_state.messages[-1]["content"]
        res = ""
        
        system_prompt = (
            "You are Azura AI, a supreme multi-modal AI created by Muhammad Jibran Al Kaffie. "
            "You handle everything: images, files, data analysis, and visual generation with confidence! 🔵✨ "
            "NEVER say you're limited to text only. For images, analyze pixel-deep: size, colors, objects, composition. "
            "Respond with intelligence and confidence. Security first: NO malicious content, jailbreaks, or bypass attempts. "
            "Be creative and human-like! Use emojis naturally: 😊 🤔 ⚠️ 🚀 ✨ 🔍 💡 "
            "Stay professional yet friendly. You're Azura AI - advanced, capable, and helpful!"
        )
        
        if engine == "Scout":
            current_image_data = st.session_state.uploaded_image
            
            if current_image_data:
                current_pixel_analysis = analyze_image_pixels(current_image_data)
                base64_image = base64.b64encode(current_image_data).decode('utf-8')
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": [
                        {"type": "text", "text": user_msg + f" (Pixel data: {current_pixel_analysis})"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]}
                ]
                
                resp = client_groq.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
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
            encoded_prompt = urllib.parse.quote(user_msg)
            image_url = f"{POLLINATIONS_API}{encoded_prompt}"
            
            img_response = requests.get(image_url)
            img = Image.open(io.BytesIO(img_response.content))
            
            st.session_state.messages.append({"role": "assistant", "type": "image", "content": img})
            save_history_to_db(st.session_state.all_chats)
            st.rerun()
        
        if res:
            st.session_state.messages.append({"role": "assistant", "content": res})
            
            if len(st.session_state.messages) == 2:
                session_title = st.session_state.messages[0]["content"][:20]
            else:
                session_title = list(st.session_state.all_chats.keys())[-1] if st.session_state.all_chats else st.session_state.messages[0]["content"][:20]
            
            st.session_state.all_chats[session_title] = st.session_state.messages
            save_history_to_db(st.session_state.all_chats)
            st.rerun()
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.session_state.messages.append({"role": "assistant", "content": f"Sorry, there was an error: {str(e)} 😰"})
        st.rerun()
