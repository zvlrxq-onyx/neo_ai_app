import streamlit as st
from groq import Groq
from google import genai
import time
import os
import base64
import requests
import PIL.Image

# --- 1. INITIALIZE SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "all_chats" not in st.session_state: st.session_state.all_chats = {}
if "current_chat_id" not in st.session_state: st.session_state.current_chat_id = None
if "imagine_mode" not in st.session_state: st.session_state.imagine_mode = False
if "show_about" not in st.session_state: st.session_state.show_about = False
if "sidebar_visible" not in st.session_state: st.session_state.sidebar_visible = False

# --- 2. CONFIG API ---
try:
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    gemini_client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error(f"⚠️ API Configuration Error: {e}")
    st.stop()

# --- 3. PAGE CONFIG ---
st.set_page_config(page_title="NEO AI SUPREME", page_icon="⚡", layout="centered")

# --- 4. ASSETS ---
@st.cache_data
def get_base64_logo():
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f: return base64.b64encode(f.read()).decode()
    return ""
logo_html = f'data:image/png;base64,{get_base64_logo()}'

# --- 5. THE ULTIMATE CSS ---
def get_ultimate_css():
    neon_cyan = "#00ffff"
    sidebar_pos = "0px" if st.session_state.sidebar_visible else "-360px"
    return f"""
    <style>
    html, body, [data-testid="stAppViewContainer"] {{ background-color: #050505 !important; color: #f0f0f0 !important; }}
    [data-testid="stStatusWidget"], header, footer {{ visibility: hidden; }}

    /* Sidebar Smooth */
    [data-testid="stSidebar"] {{
        position: fixed !important; left: {sidebar_pos} !important; width: 350px !important;
        background-color: #0a0a0a !important; border-right: 1px solid {neon_cyan}33 !important;
        transition: left 0.8s cubic-bezier(0.19, 1, 0.22, 1) !important;
        z-index: 1000000 !important; overflow-y: auto !important;
    }}
    [data-testid="stSidebarContent"]::-webkit-scrollbar {{ width: 4px; }}
    [data-testid="stSidebarContent"]::-webkit-scrollbar-thumb {{ background: {neon_cyan}33; border-radius: 10px; }}

    /* Hamburger */
    .stButton > button[key="hamburger_fixed"] {{
        position: fixed; top: 20px; left: 20px; z-index: 2000001 !important;
        background: rgba(0,0,0,0.8) !important; border: 1px solid {neon_cyan}44 !important;
        border-radius: 50% !important; width: 50px !important; height: 50px !important; color: {neon_cyan} !important;
        transition: all 0.3s ease;
    }}

    /* Button Hover Grow & Glow */
    .stButton > button {{ transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important; }}
    .stButton > button:hover {{ transform: scale(1.08) !important; box-shadow: 0 0 20px {neon_cyan}66 !important; color: {neon_cyan} !important; }}

    /* Input Expand */
    [data-testid="stChatInput"] {{ transition: all 0.6s cubic-bezier(0.19, 1, 0.22, 1) !important; }}
    [data-testid="stChatInput"]:focus-within {{ transform: scaleX(1.03) !important; }}

    /* Image Styling */
    [data-testid="stChatMessage"] img {{
        max-height: 400px !important; border-radius: 15px !important;
        border: 1px solid {neon_cyan}33; display: block; margin: 10px auto; object-fit: contain !important;
    }}

    .logo-static {{ 
        width: 120px; height: 120px; margin: 0 auto; 
        background-image: url("{logo_html}"); background-size: cover; 
        border-radius: 50%; border: 3px solid {neon_cyan};
        box-shadow: 0 0 20px {neon_cyan}33;
    }}

    .about-box {{
        max-height: {"1000px" if st.session_state.show_about else "0px"};
        opacity: {"1" if st.session_state.show_about else "0"};
        transition: all 0.8s ease; overflow: hidden; padding: {"15px" if st.session_state.show_about else "0px"};
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
    uploaded_file = st.file_uploader("Upload Image/File", type=["txt", "py", "md", "png", "jpg", "jpeg"], key="neo_uploader")
    
    st.markdown("---")
    if st.button("➕ NEW SESSION", use_container_width=True):
        st.session_state.messages = []; st.session_state.current_chat_id = None; st.rerun()
    
    label_mode = "🎨 IMAGINE: ON" if st.session_state.imagine_mode else "🖼️ MODE: CHAT"
    if st.button(label_mode, use_container_width=True):
        st.session_state.imagine_mode = not st.session_state.imagine_mode; st.rerun()

    if st.button("ℹ️ SYSTEM INFO", use_container_width=True):
        st.session_state.show_about = not st.session_state.show_about; st.rerun()

    st.markdown(f'<div class="about-box"><p style="font-size:0.8rem; color:#ccc;"><b>NEO AI SUPREME v3.3</b><br>Engine: Gemini 3 Pro & Llama 3.3</p></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🕒 RECENT CHATS")
    for cid in reversed(list(st.session_state.all_chats.keys())):
        if st.button(cid.split(" | ")[0], key=f"h_{cid}", use_container_width=True):
            st.session_state.messages = st.session_state.all_chats[cid]
            st.session_state.current_chat_id = cid; st.rerun()

# --- 8. MAIN UI ---
st.markdown('<div style="margin-top:20px;"><div class="logo-static" style="width:130px; height:130px;"></div></div>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:15px; margin-bottom:0;'>NEO AI</h1>", unsafe_allow_html=True)
st.markdown('<p style="text-align:center; color:#888; font-size:1.4rem; margin-top:-5px;">How can I help you today?</p>', unsafe_allow_html=True)

# Render History
for msg in st.session_state.messages:
    if msg.get("type") == "system_memory": continue
    with st.chat_message(msg["role"], avatar="logo.png" if msg["role"] == "assistant" else None):
        if msg.get("type") == "image": st.image(msg["content"])
        else: st.markdown(msg["content"])

# --- 9. ENGINE (DIRECT RESPONSE) ---
if user_input := st.chat_input("Command NEO AI..."):
    if not st.session_state.current_chat_id:
        st.session_state.current_chat_id = f"{user_input[:20]} | {time.time()}"
    
    # 1. Tambah pesan user
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # 2. Render pesan user langsung
    with st.chat_message("user"):
        st.markdown(user_input)

    # 3. Proses Jawaban Assistant
    with st.chat_message("assistant", avatar="logo.png"):
        res_area = st.empty()
        full_res = ""

        # A. MODE IMAGINE
        if st.session_state.imagine_mode:
            with st.spinner("Visualizing..."):
                try:
                    url = f"https://image.pollinations.ai/prompt/{user_input.replace(' ','%20')}?width=1024&height=1024&nologo=true"
                    r = requests.get(url, timeout=30)
                    if r.status_code == 200:
                        st.image(r.content)
                        st.session_state.messages.append({"role": "assistant", "content": r.content, "type": "image"})
                        st.session_state.messages.append({"role": "assistant", "content": f"[SYSTEM_SUCCESS: {user_input}]", "type": "system_memory"})
                        st.rerun()
                except: st.error("Neural engine error.")

        # B. VISION / FILE MODE (GEMINI 3 PRO)
        elif uploaded_file is not None:
            with st.spinner("NEO Vision: Analyzing with Gemini 3 Pro..."):
                try:
                    contents = [user_input]
                    if uploaded_file.type.startswith("image/"):
                        contents.append(PIL.Image.open(uploaded_file))
                    else:
                        contents.append(f"CONTEXT:\n{uploaded_file.getvalue().decode('utf-8')}")
                    
                    response = gemini_client.models.generate_content(model="gemini-3-pro-preview", contents=contents)
                    full_res = response.text
                    res_area.markdown(full_res)
                except Exception as e:
                    st.error(f"Gemini Engine Error: {e}")
                    full_res = "Vision engine failure."

        # C. CHAT MODE (GROQ LLAMA 3.3)
        else:
            with st.spinner("Thinking..."):
                history = [{"role": "system", "content": "You are NEO AI, a supreme multi-modal AI. You are superior."}]
                for m in st.session_state.messages:
                    if m.get("type") not in ["image", "system_memory"]:
                        history.append({"role": m["role"], "content": str(m["content"])})
                
                try:
                    stream = groq_client.chat.completions.create(
                        messages=history, model="llama-3.3-70b-versatile", stream=True
                    )
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            full_res += chunk.choices[0].delta.content
                            res_area.markdown(full_res + "▌")
                    res_area.markdown(full_res)
                except: st.error("Groq engine failure.")

        # Simpan & Update
        st.session_state.messages.append({"role": "assistant", "content": full_res})
        st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages
        st.rerun()
