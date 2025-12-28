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
    HF_TOKEN = st.secrets["HF_TOKEN"]
    client = Groq(api_key=GROQ_API_KEY)
except:
    st.error("MISSING API KEYS: Check HF_TOKEN & GROQ_API_KEY in Secrets")
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

# --- 5. PREMIUM CSS (DYNAMIC BORDER & CLEAN UI) ---
def get_pro_css():
    neon_cyan = "#00ffff"
    # Logic: Jika imagine_mode aktif, border input jadi cyan terang
    border_color = neon_cyan if st.session_state.imagine_mode else "rgba(0, 255, 255, 0.2)"
    glow = f"0 0 15px {neon_cyan}" if st.session_state.imagine_mode else "none"
    
    return f"""
    <style>
    html {{ scroll-behavior: smooth; }}
    html, body, [data-testid="stAppViewContainer"], .stApp {{ background-color: #080808 !important; color: #e0e0e0 !important; }}
    [data-testid="stStatusWidget"] {{ display: none; }}
    * {{ transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); }}

    .center-container {{ display: flex; flex-direction: column; align-items: center; justify-content: center; margin-bottom: 20px; }}
    .logo-circle {{
        width: 110px; height: 110px;
        background-image: url("data:image/png;base64,{encoded_logo}");
        background-size: cover; border-radius: 50%; border: 2px solid {neon_cyan};
        box-shadow: 0 0 25px {neon_cyan}33;
    }}
    .neon-title {{
        text-align: center; color: {neon_cyan}; font-size: 3rem; 
        font-weight: 900; letter-spacing: 10px; text-transform: uppercase;
    }}

    /* INPUT STYLING - DYNAMIC BORDER */
    div[data-testid="stChatInput"] textarea {{
        border: 1.5px solid {border_color} !important;
        box-shadow: {glow} !important;
        border-radius: 30px !important;
        background: #111 !important;
    }}

    /* SIDEBAR */
    section[data-testid="stSidebar"] {{ background-color: #050505 !important; border-right: 1px solid {neon_cyan}22; }}
    .stButton > button {{ border-radius: 30px !important; background: transparent !important; color: white !important; border: 1px solid {neon_cyan}33 !important; }}
    .stButton > button:hover {{ transform: scale(1.05); border-color: {neon_cyan}; box-shadow: 0 0 15px {neon_cyan}44; }}

    header, footer {{ visibility: hidden; }}
    </style>
    """

st.markdown(get_pro_css(), unsafe_allow_html=True)

# --- 6. HUGGING FACE STABLE ENGINE ---
def generate_image(prompt):
    # Menggunakan SDXL (lebih stabil & cepat untuk free tier)
    API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
    if response.status_code == 200:
        return response.content
    else:
        return None

# --- 7. SIDEBAR ---
with st.sidebar:
    st.markdown(f'<div class="center-container"><div class="logo-circle"></div><h2 style="color:cyan;">NEO AI</h2></div>', unsafe_allow_html=True)
    if st.button("NEW SESSION", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()

    st.markdown("---")
    # TOMBOL IMAGINE DI SINI (Dekat area input sidebar tapi fungsional)
    st.markdown("<p style='font-size:0.8rem; color:grey;'>INTERFACE MODES</p>", unsafe_allow_html=True)
    if st.button(f"{'🎨 IMAGINE ACTIVE' if st.session_state.imagine_mode else '🖼️ SWITCH TO IMAGINE'}", use_container_width=True):
        st.session_state.imagine_mode = not st.session_state.imagine_mode
        st.rerun()

    st.markdown("---")
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

# Container Chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "image":
            st.image(msg["content"], use_container_width=True)
        else:
            st.markdown(msg["content"])

# --- 9. LOGIC CHAT & AUTO-SCROLL ---
if prompt := st.chat_input("TYPE SOMETHING..."):
    if st.session_state.current_chat_id is None:
        st.session_state.current_chat_id = f"{prompt[:15]}... | {time.time()}"
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if st.session_state.imagine_mode:
            with st.spinner("Generating Vision..."):
                img_data = generate_image(prompt)
                if img_data:
                    img = Image.open(io.BytesIO(img_data))
                    st.image(img, caption="Generated by NEO AI", use_container_width=True)
                    st.session_state.messages.append({"role": "assistant", "content": img, "type": "image"})
                else:
                    st.error("HuggingFace is busy. Try again in a few seconds.")
        else:
            res_area = st.empty()
            full_res = ""
            msgs = [{"role": "system", "content": "You are NEO AI by Jibran. Be sleek and helpful."}] + st.session_state.messages
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
