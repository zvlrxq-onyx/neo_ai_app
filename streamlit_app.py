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
if "show_about" not in st.session_state: st.session_state.show_about = False
if "editing_chat_id" not in st.session_state: st.session_state.editing_chat_id = None
if "imagine_mode" not in st.session_state: st.session_state.imagine_mode = False

# --- 2. CONFIG API ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    HF_TOKEN = st.secrets["HF_TOKEN"] # Tambahkan ini di secrets.toml kamu!
    client = Groq(api_key=GROQ_API_KEY)
except:
    st.error("SYSTEM ERROR: API KEYS MISSING (GROQ_API_KEY or HF_TOKEN)")
    st.stop()

# --- 3. PAGE CONFIG ---
st.set_page_config(page_title="NEO AI", page_icon="⚡", layout="centered")

# --- 4. OPTIMIZED LOGO LOADER ---
@st.cache_data
def get_base64_logo():
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

encoded_logo = get_base64_logo()

# --- 5. ULTRA PREMIUM CSS (SMOOTH & ANTI-FLASH) ---
def get_pro_css():
    neon_cyan = "#00ffff"
    return f"""
    <style>
    html {{ scroll-behavior: smooth; }}
    html, body, [data-testid="stAppViewContainer"], .stApp {{
        background-color: #080808 !important; color: #e0e0e0 !important;
    }}
    [data-testid="stStatusWidget"] {{ display: none; }}
    * {{ transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); }}

    .center-container {{ display: flex; flex-direction: column; align-items: center; justify-content: center; margin-bottom: 20px; }}
    .logo-circle {{
        width: 110px; height: 110px;
        background-image: url("data:image/png;base64,{encoded_logo}");
        background-size: cover; background-position: center;
        border-radius: 50%; border: 2px solid {neon_cyan};
        box-shadow: 0 0 25px {neon_cyan}33;
    }}
    .neon-title {{
        text-align: center; color: {neon_cyan}; font-size: 3rem; 
        font-weight: 900; letter-spacing: 10px; margin-bottom: 5px;
        text-transform: uppercase; text-shadow: 0 0 15px {neon_cyan}44;
    }}
    
    .mode-indicator {{
        position: fixed; bottom: 100px; left: 50%; transform: translateX(-50%);
        background: rgba(0, 255, 255, 0.15); border: 1px solid {neon_cyan};
        padding: 5px 20px; border-radius: 20px; font-size: 0.8rem;
        color: {neon_cyan}; font-weight: bold; z-index: 99; animation: pulse 2s infinite;
    }}
    @keyframes pulse {{ 0% {{opacity: 0.4;}} 50% {{opacity: 1;}} 100% {{opacity: 0.4;}} }}

    .fluid-box {{
        background: rgba(0, 255, 255, 0.05); border-left: 4px solid {neon_cyan};
        border-radius: 15px; padding: 15px; margin-top: 10px;
        animation: slideUp 0.5s ease-out;
    }}
    @keyframes slideUp {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}

    section[data-testid="stSidebar"] {{ background-color: #050505 !important; border-right: 1px solid {neon_cyan}22; }}
    header, footer {{ visibility: hidden; }}
    </style>
    """

st.markdown(get_pro_css(), unsafe_allow_html=True)

# --- 6. HUGGING FACE IMAGE GEN FUNCTION ---
def query_image(prompt):
    API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
    return response.content

# --- 7. SIDEBAR ---
with st.sidebar:
    st.markdown(f'<div class="center-container"><div class="logo-circle"></div></div>', unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align:center; color:cyan;'>NEO AI</h2>", unsafe_allow_html=True)
    
    if st.button("NEW SESSION", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()

    st.markdown("---")
    # Toggle Imagine Mode
    st.session_state.imagine_mode = st.toggle("🎨 IMAGINE MODE", value=st.session_state.imagine_mode)
    st.caption("When active, NEO will generate images via HuggingFace.")

    st.markdown("---")
    # History & Rename
    for chat_id in reversed(list(st.session_state.all_chats.keys())):
        name = chat_id.split(" | ")[0]
        c1, c2 = st.columns([0.8, 0.2])
        with c1:
            if st.button(name, key=f"h_{chat_id}", use_container_width=True):
                st.session_state.messages = st.session_state.all_chats[chat_id]
                st.session_state.current_chat_id = chat_id
                st.rerun()
        with c2:
            if st.button("✏️", key=f"e_{chat_id}"):
                st.session_state.editing_chat_id = chat_id
                st.rerun()

    if st.button("ABOUT NEO", use_container_width=True):
        st.session_state.show_about = not st.session_state.show_about
        st.rerun()

# --- 8. MAIN INTERFACE ---
st.markdown(f'<div class="center-container"><div class="logo-circle"></div><h1 class="neon-title">NEO AI</h1></div>', unsafe_allow_html=True)
st.markdown("<p style='text-align:center; opacity:0.7;'>Hi, is there anything I can help you with?</p>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "image":
            st.image(msg["content"], caption="Generated by NEO AI")
        else:
            st.markdown(msg["content"])

if st.session_state.imagine_mode:
    st.markdown('<div class="mode-indicator">🎨 IMAGINE MODE ACTIVE</div>', unsafe_allow_html=True)

# --- 9. CHAT & IMAGE LOGIC ---
if prompt := st.chat_input("ENTER COMMAND..."):
    if st.session_state.current_chat_id is None:
        st.session_state.current_chat_id = f"{prompt[:15]}... | {time.time()}"
    
    # User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if st.session_state.imagine_mode:
            with st.spinner("Visualizing your imagination..."):
                try:
                    img_bytes = query_image(prompt)
                    image = Image.open(io.BytesIO(img_bytes))
                    st.image(image, caption=f"Result for: {prompt}")
                    st.session_state.messages.append({"role": "assistant", "content": image, "type": "image"})
                except:
                    st.error("Failed to generate image. HuggingFace might be busy.")
        else:
            res_area = st.empty()
            full_res = ""
            msgs = [{"role": "system", "content": "You are NEO AI by Jibran."}] + st.session_state.messages
            try:
                stream = client.chat.completions.create(messages=msgs, model="llama-3.3-70b-versatile", stream=True)
                for chunk in stream:
                    content = chunk.choices[0].delta.content
                    if content:
                        full_res += content
                        res_area.markdown(full_res + "▌")
                res_area.markdown(full_res)
                st.session_state.messages.append({"role": "assistant", "content": full_res})
            except:
                st.error("GROQ CONNECTION ERROR")
        
        st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages

    st.rerun() # Auto-scroll trigger
