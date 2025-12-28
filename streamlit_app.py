import streamlit as st
from groq import Groq
import google.generativeai as genai
import time
import os
import base64
import requests
from PIL import Image

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

# --- 2. CONFIG API (GROQ & GEMINI) ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    
    client = Groq(api_key=GROQ_API_KEY)
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"API Key Error: {e}")
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

# --- 5. THE SUPREME CSS (STILL SMOOTH) ---
def get_ultimate_css():
    neon_cyan = "#00ffff"
    sidebar_pos = "0px" if st.session_state.sidebar_visible else "-360px"
    return f"""
    <style>
    html, body, [data-testid="stAppViewContainer"] {{ background-color: #050505 !important; color: #f0f0f0 !important; }}
    [data-testid="stStatusWidget"], header, footer {{ visibility: hidden; }}
    [data-testid="stSidebar"] {{
        position: fixed !important; left: {sidebar_pos} !important; width: 350px !important;
        background-color: #0a0a0a !important; border-right: 1px solid {neon_cyan}33 !important;
        transition: left 0.7s cubic-bezier(0.19, 1, 0.22, 1) !important; z-index: 1000000 !important; display: block !important; visibility: visible !important;
    }}
    .stButton > button[key="hamburger_fixed"] {{
        position: fixed; top: 20px; left: 20px; z-index: 2000000 !important;
        background: rgba(0,0,0,0.9) !important; border: 2px solid {neon_cyan}44 !important;
        border-radius: 50% !important; width: 50px !important; height: 50px !important; color: {neon_cyan} !important;
    }}
    .logo-static {{ width: 130px; height: 130px; margin: 0 auto; background-image: url("{logo_html}"); background-size: cover; border-radius: 50%; border: 3px solid {neon_cyan}; }}
    div[data-testid="stChatInput"] {{ width: 80% !important; margin: 0 auto !important; transition: 0.7s !important; }}
    div[data-testid="stChatInput"]:focus-within {{ width: 100% !important; }}
    </style>
    """
st.markdown(get_ultimate_css(), unsafe_allow_html=True)

# --- 6. HAMBURGER ---
if st.button("☰", key="hamburger_fixed"):
    st.session_state.sidebar_visible = not st.session_state.sidebar_visible
    st.rerun()

# --- 7. SIDEBAR (VISION ENABLED) ---
with st.sidebar:
    st.markdown('<div style="height: 60px;"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="logo-static" style="width:100px; height:100px;"></div>', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:cyan;'>NEO AI</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Vision Module: File Uploader
    uploaded_file = st.file_uploader("📷 ANALYZE IMAGE", type=["jpg", "jpeg", "png"])
    
    if st.button("➕ NEW SESSION", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()
    
    label_mode = "🎨 IMAGINE: ON" if st.session_state.imagine_mode else "🖼️ MODE: CHAT"
    if st.button(label_mode, use_container_width=True):
        st.session_state.imagine_mode = not st.session_state.imagine_mode
        st.rerun()

    st.markdown("---")
    for cid in reversed(list(st.session_state.all_chats.keys())):
        if st.button(cid.split(" | ")[0], key=f"h_{cid}", use_container_width=True):
            st.session_state.messages = st.session_state.all_chats[cid]
            st.session_state.current_chat_id = cid
            st.rerun()

# --- 8. MAIN UI ---
st.markdown('<div style="margin-top:20px;"><div class="logo-static"></div></div>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:15px;'>NEO AI</h1>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="logo.png" if msg["role"] == "assistant" else None):
        if msg.get("type") == "image":
            st.image(msg["content"], use_container_width=True)
        else:
            st.markdown(msg["content"])

# --- 9. ENGINE (DUAL-ENGINE: GROQ + GEMINI) ---
if user_input := st.chat_input("Ask NEO AI..."):
    if st.session_state.current_chat_id is None:
        st.session_state.current_chat_id = f"{user_input[:15]}... | {time.time()}"
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.rerun()

if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_user_msg = st.session_state.messages[-1]["content"]
    
    with st.chat_message("assistant", avatar="logo.png"):
        # CASE 1: VISION MODE (Jika ada file diupload)
        if uploaded_file is not None:
            with st.spinner("NEO AI is analyzing the image via Gemini..."):
                img = Image.open(uploaded_file)
                response = gemini_model.generate_content([last_user_msg, img])
                full_res = response.text
                st.markdown(full_res)
                st.session_state.messages.append({"role": "assistant", "content": full_res})
        
        # CASE 2: IMAGINE MODE (Generate Image)
        elif st.session_state.imagine_mode:
            with st.spinner("Visualizing..."):
                query = last_user_msg.replace(' ', '%20')
                img_url = f"https://image.pollinations.ai/prompt/{query}?width=1024&height=1024&nologo=true"
                r = requests.get(img_url)
                if r.status_code == 200:
                    st.image(r.content, use_container_width=True)
                    st.session_state.messages.append({"role": "assistant", "content": r.content, "type": "image"})
        
        # CASE 3: CHAT MODE (Groq - Llama 3.3)
        else:
            res_area = st.empty()
            full_res = ""
            text_hist = []
            for m in st.session_state.messages:
                if m.get("type") == "image":
                    text_hist.append({"role": "assistant", "content": "[SYSTEM: You generated an image for the user.]"})
                else:
                    text_hist.append({"role": m["role"], "content": m["content"]})
            
            sys_msg = "You are NEO AI by Muhammad Jibran Al Kaffie. Professional and futuristic. If a user praises a previous visualization, be warm and acknowledge it."
            
            stream = client.chat.completions.create(
                messages=[{"role": "system", "content": sys_msg}] + text_hist,
                model="llama-3.3-70b-versatile",
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_res += chunk.choices[0].delta.content
                    res_area.markdown(full_res + "▌")
            res_area.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            
    st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages
    st.rerun()
