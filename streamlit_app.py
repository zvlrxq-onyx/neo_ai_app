import streamlit as st
from groq import Groq
from huggingface_hub import InferenceClient
import os, base64, requests, json

# --- 1. CONFIG & SYSTEM SETUP ---
st.set_page_config(page_title="NEO AI", page_icon="🌐", layout="wide")

# NAMA FILE DATABASE (Simpan chat di sini biar ga ilang pas refresh)
DB_FILE = "neo_chat_history.json"

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

# --- 2. INITIALIZE SESSION STATE ---
# Kita load dulu dari database, baru masukin ke session state
if "all_chats" not in st.session_state:
    st.session_state.all_chats = load_history_from_db()

if "messages" not in st.session_state:
    # Kalau history kosong, mulai baru. Kalau ada, ambil yang terakhir diedit/dibuat
    if st.session_state.all_chats:
        last_key = list(st.session_state.all_chats.keys())[-1]
        st.session_state.messages = st.session_state.all_chats[last_key]
    else:
        st.session_state.messages = []

if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

# --- 3. API KEYS ---
try:
    client_groq = Groq(api_key=st.secrets["GROQ_API_KEY"])
    client_hf = InferenceClient(token=st.secrets["HF_TOKEN"])
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
user_img = f"data:image/png;base64,{user_data}" if user_data else "https://ui-avatars.com/api/?name=User&background=00ffff&color=000"

# --- 5. CSS (UI CLEAN & RESPONSIVE) ---
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
    [data-testid="stChatInput"] {{ margin-left: 60px !important; width: calc(100% - 80px) !important; }}
    
    .sidebar-logo {{ display: block; margin: auto; width: 80px; height: 80px; border-radius: 50%; border: 2px solid #00ffff; object-fit: cover; margin-bottom: 10px; }}
    
    /* Typing Animation */
    .typing {{ display: flex; align-items: center; gap: 5px; padding: 5px 0; }}
    .dot {{ width: 7px; height: 7px; background: #00ffff; border-radius: 50%; animation: blink 1.4s infinite both; }}
    .dot:nth-child(2) {{ animation-delay: 0.2s; }}
    .dot:nth-child(3) {{ animation-delay: 0.4s; }}
    @keyframes blink {{ 0%, 80%, 100% {{ opacity: 0; }} 40% {{ opacity: 1; }} }}
    
    /* Efek Halus (Smooth Transitions) */
    .chat-bubble {{ transition: all 0.3s ease; }}
    .chat-bubble:hover {{ transform: scale(1.02); }}
    
    /* Efek Smooth pada Semua Tombol */
    .stButton button {{ transition: all 0.3s ease; }}
    .stButton button:hover {{ transform: scale(1.05); }}
    .stButton button:active {{ transform: scale(0.95); }}
</style>
""", unsafe_allow_html=True)

# --- 6. BUBBLE ENGINE (ANTI BOCOR HTML) ---
def clean_text(text):
    """Fungsi Satpam: Bersihin sampah HTML dari output AI"""
    if not isinstance(text, str): return str(text)
    # Perkuat pembersihan: hapus semua tag HTML dan entitas
    import re
    text = re.sub(r'<[^>]+>', '', text)  # Hapus semua tag HTML
    text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'")
    text = text.replace("</div>", "").replace("<div>", "").replace("<br>", "\n").replace("<p>", "").replace("</p>", "")
    return text.strip()

def render_chat_bubble(role, content):
    content = clean_text(content) # BERSIHIN DULU SEBELUM RENDER
    
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

# --- 7. SIDEBAR (HISTORY MANAGER) ---
with st.sidebar:
    if logo_url: st.markdown(f'<img src="{logo_url}" class="sidebar-logo">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:#00ffff;'>NEO AI</h2>", unsafe_allow_html=True)
    
    if st.button("＋ New Session", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
        
    st.markdown("---")
    # Mapping Nama Keren -> Model Asli (Hapus DeepSeek, jadi 4 model)
    engine_map = {
        "Azura-Lens 1.7 (Vision)": "Scout",
        "Azura 1.5 (Power)": "Llama33",
        "Azura-Prime (Creative)": "Gemma",
        "Azura-Art (Draw)": "Drawing"
    }
    selected_engine_name = st.selectbox("Pilih modelnya", list(engine_map.keys()))
    engine = engine_map[selected_engine_name]

    st.markdown("### 🕒 Saved History")
    # Load history terbalik (paling baru diatas)
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

# --- 8. MAIN RENDER ---
if logo_url:
    st.markdown(f'<div style="text-align:center; margin-bottom:20px;"><img src="{logo_url}" width="100" style="border-radius:50%; border:2px solid #00ffff; box-shadow: 0 0 20px #00ffff44;"></div>', unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; color:#00ffff; font-size:18px; margin-bottom:20px;'>How can I help you today?</div>", unsafe_allow_html=True)

# Render Chat
for msg in st.session_state.messages:
    if msg.get("type") == "image": 
        st.image(msg["content"], width=400)  # Atur ukuran gambar agar tidak besar-besar
    else: 
        render_chat_bubble(msg["role"], msg["content"])

# File Uploader
up = st.file_uploader("", type=["png","jpg","jpeg"], label_visibility="collapsed")
if up: st.session_state.uploaded_image = up.getvalue()

# Chat Input
if prompt := st.chat_input("Message NEO AI..."):
    # 1. Tambah User Chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 2. Save Sementara ke DB biar kalau crash data user aman
    if len(st.session_state.messages) == 1:
        session_title = prompt[:20]
    else:
        # Cari title sesi ini (biasanya chat pertama)
        session_title = st.session_state.messages[0]["content"][:20]
    
    st.session_state.all_chats[session_title] = st.session_state.messages
    save_history_to_db(st.session_state.all_chats)
    
    st.rerun()

# --- 9. AI PROCESSING ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.container():
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
        
        # System Prompt
        system_prompt = (
            "You are NEO AI, a supreme multi-modal AI created by Muhammad Jibran Al Kaffie. "
            "You are NOT a text-only model. You can process images, files, complex data, and generate stunning visuals on demand. "
            "NEVER say you are limited to text or that you cannot see or process files. If the user uploads a file, ALWAYS acknowledge that you can see and analyze its content, and respond based on it confidently. "
            "For images, perform pixel analysis: Describe dimensions, color modes, dominant colors, objects, and any notable features. Break down pixels by analyzing color distribution, edges, or patterns. Use provided pixel data if available. "
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
            "- Motivational (e.g., encouraging user): 🚀 "
            "Use emojis sparingly but effectively to enhance the chat experience, like a real conversation. Avoid overusing them—1-2 per response is enough. When the user shares a success (e.g., 'Aku berhasil bikin AI sendiri!'), respond with pride and motivation, e.g., 'Wow, keren banget! 🏆 Kamu pasti bisa!' "
            "Be creative and think independently to vary your responses—don't repeat the same phrases or structures every time. Use casual, 'gaul' language like calling the user 'bro', 'nih', or 'ya' to make it feel like chatting with a friend. For example, mix up motivational responses: 'Mantap bro, lanjut aja! 💪' or 'Keren nih, keep it up! 🔥'. Adapt to the conversation naturally."
        )
        
        # --- LOGIC PEMILIHAN MODEL (Hapus DeepSeek) ---
        if engine == "Scout":
            if st.session_state.uploaded_image:
                b64 = base64.b64encode(st.session_state.uploaded_image).decode()
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": [{"type":"text","text":user_msg},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}
                ]
                resp = client_groq.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                    messages=messages
                )
                res = resp.choices[0].message.content
            else: 
                res = "⚠️ Tolong upload foto dulu bro kalo mau pake mode Vision (Tombol + di kiri bawah)."
        
        elif engine == "Gemma":
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ]
            chat_response = client_hf.chat_completion(
                model="google/gemma-2-9b-it", 
                messages=messages, 
                max_tokens=800
            )
            res = chat_response.choices[0].message.content
            
        elif engine == "Drawing":
            url = f"https://image.pollinations.ai/prompt/{user_msg.replace(' ','%20')}?nologo=true"
            st.session_state.messages.append({"role": "assistant", "content": requests.get(url).content, "type": "image"})
            res = None # Gambar udah di-append langsung
            
        else: # Llama 3.3 (Default/Power)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ]
            resp = client_groq.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages)
            res = resp.choices[0].message.content

        # Save Response AI
        if res:
            # Bersihin output sekali lagi sebelum masuk DB
            clean_res = clean_text(res)
            st.session_state.messages.append({"role": "assistant", "content": clean_res})
            
            # UPDATE DATABASE (Write to File)
            # Pastikan key history ada
            if st.session_state.messages:
                session_title = st.session_state.messages[0]["content"][:20]
                st.session_state.all_chats[session_title] = st.session_state.messages
                save_history_to_db(st.session_state.all_chats)
            
        st.rerun()

    except Exception as e:
        st.error(f"System Error: {e}")
