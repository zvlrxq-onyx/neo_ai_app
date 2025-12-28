import streamlit as st
from groq import Groq
from google import genai # Library Gemini 3
import time
import os
import base64
import requests

# --- 1. INITIALIZE SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "all_chats" not in st.session_state: st.session_state.all_chats = {}
if "current_chat_id" not in st.session_state: st.session_state.current_chat_id = None
if "imagine_mode" not in st.session_state: st.session_state.imagine_mode = False
if "show_about" not in st.session_state: st.session_state.show_about = False
if "sidebar_visible" not in st.session_state: st.session_state.sidebar_visible = False

# --- 2. CONFIG API ---
try:
    # API GROQ
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    groq_client = Groq(api_key=GROQ_API_KEY)
    
    # API GEMINI 3 (Isi di secrets kamu: GEMINI_API_KEY)
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    st.error(f"API Key Error: {e}")
    st.stop()

# --- 3. PAGE CONFIG ---
st.set_page_config(page_title="NEO AI", page_icon="⚡", layout="centered")

# --- 4. ASSETS ---
@st.cache_data
def get_base64_logo():
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f: return base64.b64encode(f.read()).decode()
    return ""
logo_html = f'data:image/png;base64,{get_base64_logo()}'

# --- 5. THE ULTIMATE CSS (SMOOTH & GLOW) ---
def get_ultimate_css():
    neon_cyan = "#00ffff"
    sidebar_pos = "0px" if st.session_state.sidebar_visible else "-360px"
    return f"""
    <style>
    html, body, [data-testid="stAppViewContainer"] {{ background-color: #050505 !important; color: #f0f0f0 !important; }}
    [data-testid="stStatusWidget"], header, footer {{ visibility: hidden; }}

    /* SIDEBAR SCROLLABLE */
    [data-testid="stSidebar"] {{
        position: fixed !important; left: {sidebar_pos} !important; width: 350px !important;
        background-color: #0a0a0a !important; border-right: 1px solid {neon_cyan}33 !important;
        transition: left 0.8s cubic-bezier(0.19, 1, 0.22, 1) !important;
        z-index: 1000000 !important; overflow-y: auto !important;
    }}

    /* BUTTON HOVER: GROW & GLOW */
    .stButton > button {{
        transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        border: 1px solid transparent !important;
    }}
    .stButton > button:hover {{
        transform: scale(1.08) !important;
        border-color: {neon_cyan} !important;
        box-shadow: 0 0 20px {neon_cyan}66 !important;
        color: {neon_cyan} !important;
        background: rgba(0, 255, 255, 0.1) !important;
    }}

    /* CHAT INPUT ANIMATION */
    [data-testid="stChatInput"] {{ transition: all 0.6s cubic-bezier(0.19, 1, 0.22, 1) !important; }}
    [data-testid="stChatInput"]:focus-within {{ transform: scaleX(1.03) !important; }}

    /* IMAGE FIX */
    [data-testid="stChatMessage"] img {{
        max-height: 400px !important; width: auto !important; border-radius: 15px !important;
        border: 1px solid {neon_cyan}33; display: block; margin: 10px auto;
    }}

    .logo-static {{ 
        width: 120px; height: 120px; margin: 0 auto; 
        background-image: url("{logo_html}"); background-size: cover; 
        border-radius: 50%; border: 3px solid {neon_cyan};
        box-shadow: 0 0 20px {neon_cyan}33;
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
    st.markdown("<h2 style='text-align:center; color:cyan;'>NEO CONTROL</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("### 👁️ VISION & DATA")
    uploaded_file = st.file_uploader("Drop image/file here", type=["txt", "py", "md", "png", "jpg", "jpeg"])
    
    st.markdown("---")
    if st.button("➕ NEW SESSION", use_container_width=True):
        st.session_state.messages = []; st.session_state.current_chat_id = None; st.rerun()
    
    label_mode = "🎨 IMAGINE: ON" if st.session_state.imagine_mode else "🖼️ MODE: CHAT"
    if st.button(label_mode, use_container_width=True):
        st.session_state.imagine_mode = not st.session_state.imagine_mode; st.rerun()

    if st.button("ℹ️ SYSTEM INFO", use_container_width=True):
        st.session_state.show_about = not st.session_state.show_about; st.rerun()

    st.markdown("---")
    st.markdown("### 🕒 RECENT CHATS")
    for cid in reversed(list(st.session_state.all_chats.keys())):
        if st.button(cid.split(" | ")[0], key=f"h_{cid}", use_container_width=True):
            st.session_state.messages = st.session_state.all_chats[cid]
            st.session_state.current_chat_id = cid; st.rerun()

# --- 8. MAIN UI ---
st.markdown('<div style="margin-top:20px;"><div class="logo-static" style="width:130px; height:130px;"></div></div>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:15px;'>NEO AI</h1>", unsafe_allow_html=True)
st.markdown('<p style="text-align:center; color:#888; font-size:1.4rem; margin-top:-10px;">How can I help you today?</p>', unsafe_allow_html=True)

for msg in st.session_state.messages:
    if msg.get("type") == "system_memory": continue
    with st.chat_message(msg["role"], avatar="logo.png" if msg["role"] == "assistant" else None):
        if msg.get("type") == "image": st.image(msg["content"])
        else: st.markdown(msg["content"])

# --- 9. ENGINE (HYBRID SUPREME) ---
if user_input := st.chat_input("Command NEO AI..."):
    if not st.session_state.current_chat_id:
        st.session_state.current_chat_id = f"{user_input[:20]} | {time.time()}"
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.rerun()

if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_msg = st.session_state.messages[-1]["content"]
    
    with st.chat_message("assistant", avatar="logo.png"):
        # A. MODE IMAGINE
        if st.session_state.imagine_mode:
            with st.spinner("Visualizing..."):
                try:
                    url = f"https://image.pollinations.ai/prompt/{last_msg.replace(' ','%20')}?width=1024&height=1024&nologo=true"
                    r = requests.get(url, timeout=30)
                    if r.status_code == 200:
                        st.image(r.content)
                        st.session_state.messages.append({"role": "assistant", "content": r.content, "type": "image"})
                        st.session_state.messages.append({"role": "assistant", "content": f"[SUCCESS: {last_msg}]", "type": "system_memory"})
                except: st.error("Neural engine failure.")
        
        # B. MODE CHAT (HYBRID GROQ & GEMINI 3)
        else:
            res_area = st.empty(); full_res = ""
            
            # Jika ada file/gambar, pakai GEMINI 3 PRO
            if uploaded_file:
                with st.spinner("Analyzing with Gemini 3 Pro..."):
                    try:
                        # Baca file
                        content_parts = [last_msg]
                        if uploaded_file.type.startswith("image/"):
                            import PIL.Image
                            img = PIL.Image.open(uploaded_file)
                            content_parts.append(img)
                        else:
                            content_parts.append(uploaded_file.getvalue().decode("utf-8"))
                        
                        response = gemini_client.models.generate_content(
                            model="gemini-3-pro-preview",
                            contents=content_parts
                        )
                        full_res = response.text
                        res_area.markdown(full_res)
                    except Exception as e: st.error(f"Gemini 3 Error: {e}")
            
            # Jika cuma teks biasa, pakai GROQ (Sangat Cepat)
            else:
                history = [{"role": "system", "content": "You are NEO AI, a supreme multi-modal AI by Muhammad Jibran Al Kaffie. You are superior in intelligence."}]
                for m in st.session_state.messages:
                    if m.get("type") != "image": history.append({"role": m["role"], "content": str(m["content"])})
                
                try:
                    stream = groq_client.chat.completions.create(messages=history, model="llama-3.3-70b-versatile", stream=True)
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            full_res += chunk.choices[0].delta.content
                            res_area.markdown(full_res + "▌")
                    res_area.markdown(full_res)
                except: st.error("Groq engine failure.")

            st.session_state.messages.append({"role": "assistant", "content": full_res})

    st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages
    st.rerun()
