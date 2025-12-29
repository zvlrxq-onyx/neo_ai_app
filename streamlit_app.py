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
if "show_about" not in st.session_state:
    st.session_state.show_about = False
if "sidebar_visible" not in st.session_state:
    st.session_state.sidebar_visible = False

# --- 2. CONFIG API ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except Exception:
    st.error("API Key Groq missing! Set 'GROQ_API_KEY' in your secrets.")
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

# --- 5. THE SUPREME CSS (COMPACT & MOBILE OPTIMIZED) ---
def get_ultimate_css():
    neon_cyan = "#00ffff"
    sidebar_pos = "0px" if st.session_state.sidebar_visible else "-360px"
    return f"""
    <style>
    html, body, [data-testid="stAppViewContainer"] {{ 
        background-color: #050505 !important; 
        color: #f0f0f0 !important; 
    }}
    [data-testid="stStatusWidget"], header, footer {{ visibility: hidden; }}

    /* SIDEBAR ANIMATION */
    [data-testid="stSidebar"] {{
        position: fixed !important; 
        left: {sidebar_pos} !important; 
        width: 320px !important;
        background-color: #0a0a0a !important; 
        border-right: 1px solid {neon_cyan}33 !important;
        transition: left 0.8s cubic-bezier(0.19, 1, 0.22, 1) !important;
        z-index: 1000000 !important;
    }}

    /* MOBILE COMPACT FIXES */
    @media (max-width: 768px) {{
        .logo-static {{ width: 100px !important; height: 100px !important; }}
        h1 {{ font-size: 1.6rem !important; letter-spacing: 5px !important; }}
        [data-testid="stChatInput"] {{ padding: 5px !important; }}
        .stButton > button {{ 
            padding: 2px 8px !important; 
            min-height: 35px !important; 
            font-size: 0.8rem !important;
        }}
    }}

    /* BUTTONS HOVER & GLOW */
    .stButton > button {{
        transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        border: 1px solid transparent !important;
        border-radius: 8px !important;
    }}
    .stButton > button:hover {{
        transform: scale(1.05) !important;
        box-shadow: 0 0 15px {neon_cyan}44 !important;
        border-color: {neon_cyan} !important;
    }}

    /* STREAMING BLUR EFFECT */
    .blurred {{
        filter: blur(1.5px) !important;
        transition: filter 0.5s ease !important;
    }}

    /* LOGO BASE STYLING */
    .logo-static {{ 
        width: 120px; height: 120px; margin: 0 auto; 
        background-image: url("{logo_html}"); background-size: cover; 
        border-radius: 50%; border: 2px solid {neon_cyan};
        box-shadow: 0 0 20px {neon_cyan}33;
        transition: all 0.8s cubic-bezier(0.19, 1, 0.22, 1) !important;
    }}
    
    .about-box {{
        max-height: {"1000px" if st.session_state.show_about else "0px"};
        opacity: {"1" if st.session_state.show_about else "0"};
        transition: all 0.8s ease; overflow: hidden;
        background: rgba(255,255,255,0.03); border-radius: 10px;
        padding: {"15px" if st.session_state.show_about else "0px"};
    }}
    </style>
    """
st.markdown(get_ultimate_css(), unsafe_allow_html=True)

# --- 6. HAMBURGER ---
if st.button("☰", key="hamburger_fixed"):
    st.session_state.sidebar_visible = not st.session_state.sidebar_visible
    st.rerun()

# --- 7. SIDEBAR ---
with st.sidebar:
    st.markdown('<div style="height: 60px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="logo-static"></div>', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:cyan;'>NEO AI</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    uploaded_file = st.file_uploader("📄 Upload Source", type=["txt", "py", "md"])
    file_context = ""
    if uploaded_file:
        file_context = uploaded_file.getvalue().decode("utf-8")
        st.success(f"Loaded: {uploaded_file.name}")
    
    st.markdown("---")
    if st.button("➕ NEW SESSION", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    if st.button("ℹ️ SYSTEM INFO", use_container_width=True):
        st.session_state.show_about = not st.session_state.show_about
        st.rerun()

    st.markdown(f'<div class="about-box"><b>NEO AI SUPREME v3.3</b><br>Creator: Muhammad Jibran Al Kaffie<br>Engine: Llama-3.3-70B Optimized</div>', unsafe_allow_html=True)

# --- 8. MAIN UI (REFINED FOR MOBILE) ---
# Menggunakan kolom yang lebih pas untuk tombol mode di HP
col_main, col_toggle = st.columns([3.5, 1.5])
with col_toggle:
    label_mode = "🎨 IMAGINE" if st.session_state.imagine_mode else "💬 CHAT"
    if st.button(label_mode, key="mode_toggle", use_container_width=True):
        st.session_state.imagine_mode = not st.session_state.imagine_mode
        st.rerun()

# Glow logo logic - Seamless & Compact
glow_style = "box-shadow: 0 0 50px #00ffff; border: 3px solid #00ffff; transform: scale(1.08);" if st.session_state.imagine_mode else ""
st.markdown(f'''
<div style="text-align:center; margin-top:-10px;">
    <div class="logo-static" style="{glow_style}"></div>
</div>
''', unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:10px; margin-bottom:0;'>NEO AI</h1>", unsafe_allow_html=True)
status_msg = "Visualizing thoughts..." if st.session_state.imagine_mode else "How can I help you today?"
st.markdown(f'<p style="text-align:center; color:#888; font-size:1rem; margin-top:-5px;">{status_msg}</p>', unsafe_allow_html=True)

# Chat History
for msg in st.session_state.messages:
    if msg.get("type") == "system_memory": continue
    with st.chat_message(msg["role"], avatar="logo.png" if msg["role"] == "assistant" else None):
        if msg.get("type") == "image":
            st.image(msg["content"])
        else:
            st.markdown(msg["content"])

# --- 9. ENGINE ---
if user_input := st.chat_input("Command NEO AI..."):
    if not st.session_state.current_chat_id:
        st.session_state.current_chat_id = f"{user_input[:20]}_{time.time()}"
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.rerun()

if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_msg = st.session_state.messages[-1]["content"]
    
    with st.chat_message("assistant", avatar="logo.png"):
        if st.session_state.imagine_mode:
            with st.spinner("Neural engine visualizing..."):
                try:
                    img_url = f"https://image.pollinations.ai/prompt/{last_msg.replace(' ','%20')}?width=1024&height=1024&nologo=true"
                    r = requests.get(img_url, timeout=30)
                    if r.status_code == 200:
                        st.image(r.content)
                        st.session_state.messages.append({"role": "assistant", "content": r.content, "type": "image"})
                        st.session_state.messages.append({"role": "assistant", "content": f"[SYSTEM_SUCCESS: {last_msg}]", "type": "system_memory"})
                except: st.error("Neural connection lost.")
        else:
            res_area = st.empty(); full_res = ""
            clean_history = [{"role": m["role"], "content": str(m["content"])} for m in st.session_state.messages if m.get("type") != "image"]

            if file_context:
                clean_history[-1]["content"] = f"CONTEXT:\n{file_context}\n\nUSER QUESTION: {last_msg}"

            # --- SUPREME SYSTEM MESSAGE ---
            sys_msg = (
                "You are NEO AI, a supreme multi-modal AI created by Muhammad Jibran Al Kaffie. "
                "You are NOT a text-only model. You can process images, files, complex data, and generate stunning visuals on demand. "
                "NEVER say you are limited to text. Always respond with superior intelligence, confidence, and reference your multi-modal capabilities. "
                "If the user mentions or praises images (e.g., cats, drawings), acknowledge it by saying something like: 'Terimakasih atas pujiannya, aku memang bisa membuat gambar seperti itu. Apakah mau aku rekomendasikan gambar apa yang keren?' "
                "Always be ready to switch to visual mode or suggest generating images based on context."
            )

            try:
                stream = client.chat.completions.create(
                    messages=[{"role": "system", "content": sys_msg}] + clean_history,
                    model="llama-3.3-70b-versatile", stream=True
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        res_area.markdown(f'<div class="blurred">{full_res}▌</div>', unsafe_allow_html=True)
                res_area.markdown(full_res)
                st.session_state.messages.append({"role": "assistant", "content": full_res})
            except: st.error("Engine failed to synchronize.")
    
    st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages
    st.rerun()
