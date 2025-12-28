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

# --- 5. THE SUPREME CSS (SCROLLBAR, SMOOTH ANIMATIONS & GLOW) ---
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

    /* SIDEBAR + SCROLLBAR CUSTOMIZATION */
    [data-testid="stSidebar"] {{
        position: fixed !important; 
        left: {sidebar_pos} !important; 
        width: 350px !important;
        background-color: #0a0a0a !important; 
        border-right: 1px solid {neon_cyan}33 !important;
        transition: left 0.8s cubic-bezier(0.19, 1, 0.22, 1) !important;
        z-index: 1000000 !important;
        overflow-y: auto !important;
    }}

    [data-testid="stSidebarContent"]::-webkit-scrollbar {{ width: 4px; }}
    [data-testid="stSidebarContent"]::-webkit-scrollbar-thumb {{ background: {neon_cyan}33; border-radius: 10px; }}

    /* BUTTONS HOVER & GLOW */
    .stButton > button {{
        transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        border: 1px solid transparent !important;
    }}
    .stButton > button:hover {{
        transform: scale(1.05) !important;
        box-shadow: 0 0 15px {neon_cyan}44 !important;
        color: {neon_cyan} !important;
        background: rgba(0, 255, 255, 0.05) !important;
        border-color: {neon_cyan} !important;
    }}

    /* CHAT INPUT EXPAND SMOOTH */
    [data-testid="stChatInput"] {{ transition: all 0.6s cubic-bezier(0.19, 1, 0.22, 1) !important; }}
    [data-testid="stChatInput"]:focus-within {{ transform: scaleX(1.02) !important; }}

    /* IMAGE STYLING */
    [data-testid="stChatMessage"] img {{
        max-height: 400px !important;
        width: auto !important;
        border-radius: 12px;
        margin: 10px auto;
        display: block;
        border: 1px solid {neon_cyan}22;
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

# --- 7. SIDEBAR (WITH DATA SOURCE) ---
with st.sidebar:
    st.markdown('<div style="height: 60px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="logo-static"></div>', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:cyan;'>NEO CONTROL</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    # --- FITUR BACA FILE (DATA SOURCE) ---
    st.markdown("### 📄 DATA SOURCE")
    uploaded_file = st.file_uploader("Upload (.txt, .py, .md)", type=["txt", "py", "md"], label_visibility="collapsed")
    file_context = ""
    if uploaded_file:
        file_context = uploaded_file.getvalue().decode("utf-8")
        st.success(f"✅ {uploaded_file.name} loaded!")
    
    st.markdown("---")
    
    if st.button("➕ NEW SESSION", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()
    
    label_mode = "🎨 IMAGINE: ON" if st.session_state.imagine_mode else "🖼️ MODE: CHAT"
    if st.button(label_mode, use_container_width=True):
        st.session_state.imagine_mode = not st.session_state.imagine_mode
        st.rerun()

    if st.button("ℹ️ SYSTEM INFO", use_container_width=True):
        st.session_state.show_about = not st.session_state.show_about
        st.rerun()

    st.markdown(f"""<div class="about-box"><p style="font-size:0.8rem; color:#ccc;">
    <b>NEO AI SUPREME v3.3</b><br>
    Architect: Muhammad Jibran Al Kaffie<br>
    Engine: Llama-3.3-70B Optimized<br><br>
    Multi-modal AI dengan kemampuan analisis data dan visualisasi instan.
    </p></div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🕒 RECENT CHATS")
    for cid in reversed(list(st.session_state.all_chats.keys())):
        if st.button(cid.split(" | ")[0], key=f"h_{cid}", use_container_width=True):
            st.session_state.messages = st.session_state.all_chats[cid]
            st.session_state.current_chat_id = cid
            st.rerun()

# --- 8. MAIN UI ---
st.markdown('<div style="margin-top:20px;"><div class="logo-static" style="width:130px; height:130px;"></div></div>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:15px; margin-bottom:0;'>NEO AI</h1>", unsafe_allow_html=True)
st.markdown('<p style="text-align:center; color:#888; font-size:1.4rem; margin-top:-5px;">How can I help you today?</p>', unsafe_allow_html=True)

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
        st.session_state.current_chat_id = f"{user_input[:20]} | {time.time()}"
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.rerun()

if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_user_msg = st.session_state.messages[-1]["content"]
    
    with st.chat_message("assistant", avatar="logo.png"):
        if st.session_state.imagine_mode:
            with st.spinner("Visualizing..."):
                try:
                    img_url = f"https://image.pollinations.ai/prompt/{last_user_msg.replace(' ','%20')}?width=1024&height=1024&nologo=true"
                    r = requests.get(img_url, timeout=30)
                    if r.status_code == 200:
                        st.image(r.content)
                        st.session_state.messages.append({"role": "assistant", "content": r.content, "type": "image"})
                        st.session_state.messages.append({"role": "assistant", "content": f"[SYSTEM_SUCCESS: {last_user_msg}]", "type": "system_memory"})
                except: st.error("Neural engine connection lost.")
        else:
            res_area = st.empty(); full_res = ""
            clean_history = []
            for m in st.session_state.messages:
                if m.get("type") == "image": continue
                clean_history.append({"role": m["role"], "content": str(m["content"])})

            # INTEGRASI DATA SOURCE KE MEMORI AKHIR
            if file_context:
                clean_history[-1]["content"] = f"USER UPLOADED FILE CONTEXT:\n{file_context}\n\nUSER QUESTION: {last_user_msg}"

            sys_msg = (
                "You are NEO AI, a supreme multi-modal AI created by Muhammad Jibran Al Kaffie. "
                "You are NOT a text-only model. You can process images, files, and complex data. "
                "NEVER say you are limited to text. Respond with superior intelligence and confidence."
            )

            try:
                stream = client.chat.completions.create(
                    messages=[{"role": "system", "content": sys_msg}] + clean_history,
                    model="llama-3.3-70b-versatile", stream=True
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        res_area.markdown(full_res + "▌")
                res_area.markdown(full_res)
                st.session_state.messages.append({"role": "assistant", "content": full_res})
            except: st.error("Engine failed to synchronize.")

    st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages
    st.rerun()
