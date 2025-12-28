import streamlit as st
from groq import Groq
import time
import os
import base64
import requests
import io
from PIL import Image

# --- 1. INITIALIZE SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "all_chats" not in st.session_state: st.session_state.all_chats = {}
if "current_chat_id" not in st.session_state: st.session_state.current_chat_id = None
if "imagine_mode" not in st.session_state: st.session_state.imagine_mode = False

# --- 2. CONFIG API ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    # HF_TOKEN opsional jika pakai Pollinations, tapi tetap simpan jika pakai HF
    HF_TOKEN = st.secrets.get("HF_TOKEN", "") 
    client = Groq(api_key=GROQ_API_KEY)
except:
    st.error("GROQ_API_KEY Missing!")
    st.stop()

# --- 3. PAGE CONFIG ---
st.set_page_config(page_title="NEO AI", page_icon="⚡", layout="centered")

# --- 4. LOGO LOADER ---
@st.cache_data
def get_base64_logo():
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""
encoded_logo = get_base64_logo()

# --- 5. CLEAN & DYNAMIC CSS ---
def get_pro_css():
    neon_cyan = "#00ffff"
    # Border berubah warna jika Imagine Mode Aktif
    input_border = neon_cyan if st.session_state.imagine_mode else "rgba(0, 255, 255, 0.2)"
    input_glow = f"0 0 15px {neon_cyan}66" if st.session_state.imagine_mode else "none"
    
    return f"""
    <style>
    html {{ scroll-behavior: smooth; }}
    body, .stApp {{ background-color: #080808 !important; color: #e0e0e0 !important; }}
    * {{ transition: all 0.4s ease-in-out; }}
    
    /* INPUT BOX DYNAMIC */
    div[data-testid="stChatInput"] textarea {{
        border: 2px solid {input_border} !important;
        box-shadow: {input_glow} !important;
        border-radius: 25px !important;
        background: #111 !important;
    }}

    .logo-circle {{
        width: 100px; height: 100px; margin: 0 auto;
        background-image: url("data:image/png;base64,{encoded_logo}");
        background-size: cover; border-radius: 50%; border: 2px solid {neon_cyan};
        box-shadow: 0 0 20px {neon_cyan}33;
    }}
    
    /* Hide boring elements */
    header, footer, [data-testid="stStatusWidget"] {{ visibility: hidden; }}
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {{ background-color: #050505 !important; }}
    </style>
    """

st.markdown(get_pro_css(), unsafe_allow_html=True)

# --- 6. SUPER STABLE IMAGE GENERATOR (Pollinations Bypass) ---
def get_image_ai(prompt):
    # Pakai Pollinations karena lebih jarang 'busy' dibanding HF Free Tier
    # Ini akan beneran menghasilkan file gambar, bukan tulisan/ASCII
    prompt_encoded = prompt.replace(" ", "%20")
    image_url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1024&height=1024&nologo=true"
    response = requests.get(image_url)
    if response.status_code == 200:
        return response.content
    return None

# --- 7. SIDEBAR ---
with st.sidebar:
    st.markdown('<div class="logo-circle"></div>', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:cyan;'>NEO AI</h2>", unsafe_allow_html=True)
    
    if st.button("NEW SESSION", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()

    st.markdown("---")
    # TOMBOL SWITCH MODE
    mode_label = "🎨 IMAGINE MODE: ON" if st.session_state.imagine_mode else "🖼️ SWITCH TO IMAGINE"
    if st.button(mode_label, use_container_width=True):
        st.session_state.imagine_mode = not st.session_state.imagine_mode
        st.rerun()
    
    st.markdown("---")
    # History
    for chat_id in reversed(list(st.session_state.all_chats.keys())):
        if st.button(chat_id.split(" | ")[0], key=f"h_{chat_id}", use_container_width=True):
            st.session_state.messages = st.session_state.all_chats[chat_id]
            st.session_state.current_chat_id = chat_id
            st.rerun()

# --- 8. MAIN INTERFACE ---
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:10px;'>NEO AI</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align:center; opacity:0.6;'>{'Mode: Imagine (High Quality Image)' if st.session_state.imagine_mode else 'Mode: Chat (Llama-3.3)'}</p>", unsafe_allow_html=True)

# Render Chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "image":
            st.image(msg["content"])
        else:
            st.markdown(msg["content"])

# --- 9. CHAT LOGIC ---
if prompt := st.chat_input("Enter command..."):
    if st.session_state.current_chat_id is None:
        st.session_state.current_chat_id = f"{prompt[:15]}... | {time.time()}"
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if st.session_state.imagine_mode:
            # JALUR KHUSUS GAMBAR (Tidak lewat Groq)
            with st.spinner("🎨 Creating Masterpiece..."):
                img_bytes = get_image_ai(prompt)
                if img_bytes:
                    st.image(img_bytes, caption=f"NEO Imagination: {prompt}")
                    st.session_state.messages.append({"role": "assistant", "content": img_bytes, "type": "image"})
                else:
                    st.error("Failed to render image.")
        else:
            # JALUR KHUSUS CHAT (Groq)
            res_area = st.empty()
            full_res = ""
            msgs = [{"role": "system", "content": "You are NEO AI."}] + st.session_state.messages
            stream = client.chat.completions.create(messages=msgs, model="llama-3.3-70b-versatile", stream=True)
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    full_res += content
                    res_area.markdown(full_res + "▌")
            res_area.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
    
    st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages
    st.rerun()
