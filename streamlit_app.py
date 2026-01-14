import streamlit as st
from groq import Groq
from huggingface_hub import InferenceClient
import os, base64, requests, json

# --- 1. CONFIG & DATABASE SYSTEM ---
st.set_page_config(page_title="NEO AI", page_icon="🌐", layout="wide")
DB_FILE = "neo_chat_history.json"

# Load History biar ga ilang pas refresh
if "all_chats" not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: st.session_state.all_chats = json.load(f)
        except: st.session_state.all_chats = {}
    else: st.session_state.all_chats = {}

if "messages" not in st.session_state: st.session_state.messages = []
if "uploaded_image" not in st.session_state: st.session_state.uploaded_image = None

# --- 2. API KEYS ---
try:
    client_groq = Groq(api_key=st.secrets["GROQ_API_KEY"])
    client_hf = InferenceClient(token=st.secrets["HF_TOKEN"])
except:
    st.error("❌ API Keys Error! Cek secrets.toml.")
    st.stop()

# --- 3. ASSETS & HELPERS ---
@st.cache_data
def get_base64_img(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f: return base64.b64encode(f.read()).decode()
    return None

logo_url = f"data:image/png;base64,{get_base64_img('logo.png')}" if get_base64_img('logo.png') else ""
user_img = f"data:image/png;base64,{get_base64_img('user.png')}" if get_base64_img('user.png') else "https://ui-avatars.com/api/?name=User&background=00ffff&color=000"

def save_db():
    with open(DB_FILE, "w") as f: json.dump(st.session_state.all_chats, f)

def clean_text(text):
    if not isinstance(text, str): return str(text)
    return text.replace("</div>", "").replace("<div>", "").replace("<br>", "\n")

# --- 4. CSS (MOBILE & DESKTOP) ---
st.markdown(f"""
<style>
    [data-testid="stAppViewContainer"] {{ background: #050505; }}
    /* Tombol Plus di Kiri Bawah */
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
    /* Input Chat geser ke kanan */
    [data-testid="stChatInput"] {{ margin-left: 60px !important; width: calc(100% - 80px) !important; }}
    
    .sidebar-logo {{ display: block; margin: auto; width: 80px; height: 80px; border-radius: 50%; border: 2px solid #00ffff; object-fit: cover; margin-bottom: 10px; }}
    
    .typing {{ display: flex; align-items: center; gap: 5px; padding: 5px 0; }}
    .dot {{ width: 7px; height: 7px; background: #00ffff; border-radius: 50%; animation: blink 1.4s infinite both; }}
    .dot:nth-child(2) {{ animation-delay: 0.2s; }}
    .dot:nth-child(3) {{ animation-delay: 0.4s; }}
    @keyframes blink {{ 0%, 80%, 100% {{ opacity: 0; }} 40% {{ opacity: 1; }} }}
</style>
""", unsafe_allow_html=True)

# --- 5. BUBBLE RENDERER ---
def render_chat(role, content):
    content = clean_text(content)
    if role == "user":
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-end; align-items: flex-start; margin-bottom: 20px;">
            <div style="background: #002b2b; color: white; padding: 12px 18px; border-radius: 18px 18px 2px 18px; 
                        max-width: 85%; border-right: 3px solid #00ffff; box-shadow: 0 4px 15px rgba(0,255,255,0.1);">
                {content}
            </div>
            <img src="{user_img}" width="35" height="35" style="border-radius: 50%; margin-left: 10px; border: 1px solid #00ffff; object-fit: cover;">
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-start; align-items: flex-start; margin-bottom: 20px;">
            <img src="{logo_url}" width="35" height="35" style="border-radius: 50%; margin-right: 10px; border: 1px solid #00ffff; object-fit: cover;">
            <div style="background: #1a1a1a; color: #e9edef; padding: 12px 18px; border-radius: 2px 18px 18px 18px; 
                        max-width: 85%; border-left: 1px solid #333; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                {content}
            </div>
        </div>""", unsafe_allow_html=True)

# --- 6. SIDEBAR & HISTORY ---
with st.sidebar:
    if logo_url: st.markdown(f'<img src="{logo_url}" class="sidebar-logo">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:#00ffff;'>NEO AI</h2>", unsafe_allow_html=True)
    if st.button("＋ New Session", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    
    # NAMA MODEL KEREN
    engine_map = {
        "Azura-Vision (Scout)": "Scout",
        "Azura-DeepR1 (Logic)": "DeepSeek",
        "Azura-Titan (Llama3)": "Titan",
        "Azura-Prime (Gemma)": "Gemma",
        "Azura-Art (Draw)": "Drawing"
    }
    mode = st.selectbox("🧠 Brain Engine:", list(engine_map.keys()))
    engine = engine_map[mode]

    st.markdown("### 🕒 History")
    for t in list(st.session_state.all_chats.keys())[::-1]:
        if st.button(f"💬 {t}", key=t, use_container_width=True):
            st.session_state.messages = st.session_state.all_chats[t]
            st.rerun()

# --- 7. MAIN RENDER LOOP ---
if logo_url: st.markdown(f'<div style="text-align:center; margin-bottom:20px;"><img src="{logo_url}" width="100" style="border-radius:50%; border:2px solid #00ffff;"></div>', unsafe_allow_html=True)

for msg in st.session_state.messages:
    if msg.get("type") == "image": st.image(msg["content"])
    else: render_chat(msg["role"], msg["content"])

# --- 8. INPUT & LOGIC ---
up = st.file_uploader("", type=["png","jpg","jpeg"], label_visibility="collapsed")
if up: st.session_state.uploaded_image = up.getvalue()

if prompt := st.chat_input("Message NEO AI..."):
    # 1. Render User Langsung
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Save session awal
    if len(st.session_state.messages) == 1:
        st.session_state.all_chats[prompt[:20]] = st.session_state.messages
        save_db()
    st.rerun()

# Logic AI (Jalan hanya jika pesan terakhir dari User)
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.container():
        st.markdown(f"""<div style="display:flex; margin-bottom:20px;"><img src="{logo_url}" width="35" style="border-radius:50%; margin-right:10px;"><div style="background:#1a1a1a; padding:10px; border-radius:18px;"><div class="typing"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div></div></div>""", unsafe_allow_html=True)
    
    try:
        query = st.session_state.messages[-1]["content"]
        res = ""

        if engine == "Scout":
            # WAJIB PAKE MODEL INI
            if st.session_state.uploaded_image:
                b64 = base64.b64encode(st.session_state.uploaded_image).decode()
                chat = client_groq.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct", # <-- HARGA MATI
                    messages=[{"role": "user", "content": [{"type":"text","text":query},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}]
                )
                res = chat.choices[0].message.content
            else: res = "⚠️ Upload gambar dulu bro kalau mau pake Vision Scout!"

        elif engine == "DeepSeek":
            # GANTI KE MODEL YANG MASIH HIDUP (Qwen 32B)
            chat = client_groq.chat.completions.create(
                model="deepseek-r1-distill-qwen-32b", 
                messages=[{"role": "user", "content": query}]
            )
            res = chat.choices[0].message.content

        elif engine == "Gemma":
            res = client_hf.chat_completion(model="google/gemma-2-9b-it", messages=[{"role":"user","content":query}]).choices[0].message.content

        elif engine == "Drawing":
            url = f"https://image.pollinations.ai/prompt/{query.replace(' ','%20')}?nologo=true"
            st.session_state.messages.append({"role": "assistant", "content": requests.get(url).content, "type": "image"})
            res = None

        else: # Titan / Llama 3.3
            chat = client_groq.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":query}])
            res = chat.choices[0].message.content

        if res:
            st.session_state.messages.append({"role": "assistant", "content": clean_text(res)})
            # Save DB Update
            title = st.session_state.messages[0]["content"][:20]
            st.session_state.all_chats[title] = st.session_state.messages
            save_db()
        
        st.rerun()

    except Exception as e:
        st.error(f"Error Engine: {e}")
