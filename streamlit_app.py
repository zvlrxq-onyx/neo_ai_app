import streamlit as st
from groq import Groq
import time
import os
import base64

# --- 1. INITIALIZE SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "all_chats" not in st.session_state: st.session_state.all_chats = {}
if "current_chat_id" not in st.session_state: st.session_state.current_chat_id = None
if "show_about" not in st.session_state: st.session_state.show_about = False
if "editing_chat_id" not in st.session_state: st.session_state.editing_chat_id = None

# --- 2. CONFIG API ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except:
    st.error("SYSTEM ERROR: API KEY NOT FOUND")
    st.stop()

# --- 3. PAGE CONFIG ---
st.set_page_config(page_title="NEO AI", page_icon="⚡", layout="wide")

# --- 4. LOGO LOADER ---
encoded_logo = ""
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as f:
        encoded_logo = base64.b64encode(f.read()).decode()

# --- 5. ULTRA SMOOTH TOGGLE CSS ---
def get_pro_css():
    neon_cyan = "#00ffff"
    return f"""
    <style>
    /* Hide Default Sidebar */
    [data-testid="stSidebar"] {{ display: none; }}
    [data-testid="stSidebarCollapsedControl"] {{ display: none; }}

    /* Global Transitions */
    * {{ transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1); }}
    
    .stApp {{ background: #080808; color: #e0e0e0; }}

    /* Main Container Shift Logic */
    .main-content {{
        margin-left: 320px;
        transition: margin-left 0.7s cubic-bezier(0.16, 1, 0.3, 1);
        padding: 20px;
    }}

    /* Custom Sidebar */
    .custom-sidebar {{
        position: fixed;
        left: 0; top: 0; bottom: 0;
        width: 320px;
        background: #050505;
        border-right: 1px solid {neon_cyan}22;
        z-index: 999;
        padding: 20px;
        transform: translateX(0);
        transition: transform 0.7s cubic-bezier(0.16, 1, 0.3, 1);
        overflow-y: auto;
    }}

    /* Toggle Mechanism */
    #sidebar-toggle {{ display: none; }}
    #sidebar-toggle:checked ~ .custom-sidebar {{ transform: translateX(-100%); }}
    #sidebar-toggle:checked ~ .main-content {{ margin-left: 0; }}

    /* Hamburger Menu Icon */
    .hamburger {{
        position: fixed;
        left: 20px; top: 20px;
        z-index: 1000;
        cursor: pointer;
        padding: 10px;
        background: #080808;
        border: 1px solid {neon_cyan}44;
        border-radius: 12px;
        display: flex; flex-direction: column; gap: 5px;
        transition: transform 0.3s;
    }}
    .hamburger:hover {{ transform: scale(1.1); border-color: {neon_cyan}; box-shadow: 0 0 15px {neon_cyan}33; }}
    .bar {{ width: 25px; height: 2px; background: {neon_cyan}; border-radius: 2px; }}

    /* UI Elements */
    .logo-circle {{
        width: 100px; height: 100px;
        background-image: url("data:image/png;base64,{encoded_logo}");
        background-size: cover; background-position: center;
        border-radius: 50%; border: 2px solid {neon_cyan};
        margin: 0 auto 20px;
        box-shadow: 0 0 20px {neon_cyan}33;
    }}
    
    .neon-title {{
        text-align: center; color: {neon_cyan}; font-size: 3rem; 
        font-weight: 900; letter-spacing: 10px; margin-bottom: 5px;
        text-transform: uppercase; text-shadow: 0 0 20px {neon_cyan}44;
    }}

    .welcome-text {{
        text-align: center; color: #ffffff; font-size: 1.2rem;
        margin-bottom: 40px; opacity: 0.7;
    }}

    /* Buttons Rounded */
    .stButton > button {{
        background: transparent !important; color: white !important;
        border: 1px solid {neon_cyan}44 !important;
        border-radius: 30px !important;
        padding: 8px 15px !important;
        width: 100% !important;
    }}
    .stButton > button:hover {{ 
        transform: scale(1.05) !important; border-color: {neon_cyan} !important;
        background: {neon_cyan}11 !important;
    }}

    /* Chat Input Expand Animation */
    div[data-testid="stChatInput"] {{
        width: 80% !important; margin: 0 auto !important;
        transition: width 0.8s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }}
    div[data-testid="stChatInput"]:focus-within {{ width: 100% !important; }}
    .stChatInput textarea {{ border-radius: 25px !important; }}

    /* Fluid Box for About/Edit */
    .fluid-box {{
        background: rgba(0, 255, 255, 0.03);
        border: 1px solid {neon_cyan}22;
        border-left: 4px solid {neon_cyan};
        border-radius: 20px; padding: 15px; margin-top: 15px;
        animation: fluidIn 0.6s ease-out;
    }}
    @keyframes fluidIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}

    header, footer {{ visibility: hidden; }}
    </style>

    <input type="checkbox" id="sidebar-toggle">
    <label for="sidebar-toggle" class="hamburger">
        <div class="bar"></div>
        <div class="bar"></div>
        <div class="bar"></div>
    </label>
    """

st.markdown(get_pro_css(), unsafe_allow_html=True)

# --- 6. SIDEBAR CONTENT ---
# Kita masukkan logic sidebar ke dalam div custom-sidebar
sidebar_html = f"""
<div class="custom-sidebar">
    <div class="logo-circle"></div>
    <h2 style='text-align:center; color:#00ffff; letter-spacing:3px; font-size:1.5rem;'>NEO AI</h2>
    <hr style='border-color:#00ffff22;'>
    <p style='font-size:0.7rem; color:#444; letter-spacing:1px;'>HISTORY DATABASE</p>
"""
st.markdown(sidebar_html, unsafe_allow_html=True)

# Guna col di Streamlit tetap bisa jalan di dalam "custom-sidebar" asalkan kita wrap dengan div.
# Tapi karena kita mau full custom, kita pakai tombol streamlit biasa di sini:
with st.container():
    # Tombol New Session
    if st.button("NEW SESSION", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # List History
    for chat_id in reversed(list(st.session_state.all_chats.keys())):
        display_name = chat_id.split(" | ")[0]
        c1, c2 = st.columns([0.8, 0.2])
        with c1:
            if st.button(display_name, key=f"hist_{chat_id}"):
                st.session_state.messages = st.session_state.all_chats[chat_id]
                st.session_state.current_chat_id = chat_id
                st.rerun()
        with c2:
            if st.button("✏️", key=f"edit_{chat_id}"):
                st.session_state.editing_chat_id = chat_id
                st.rerun()

    # About
    st.markdown("<div style='height:10vh;'></div>", unsafe_allow_html=True)
    if st.button("ABOUT", use_container_width=True):
        st.session_state.show_about = not st.session_state.show_about
        st.rerun()

    if st.session_state.show_about:
        st.markdown("""<div class="fluid-box"><b>Architect:</b> M. Jibran Al Kaffie<br><b>Engine:</b> Llama-3.3-70B<br><br>Advanced neural interface.</div>""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True) # Close custom-sidebar

# --- 7. MAIN CONTENT AREA ---
st.markdown('<div class="main-content">', unsafe_allow_html=True)

st.markdown(f'<div class="center-container"><div class="logo-circle"></div><h1 class="neon-title">NEO AI</h1><p class="welcome-text">Hi, is there anything I can help you with?</p></div>', unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 8. CHAT LOGIC ---
if prompt := st.chat_input("COMMAND..."):
    if st.session_state.current_chat_id is None:
        clean_title = prompt[:20] + "..." if len(prompt) > 20 else prompt
        st.session_state.current_chat_id = f"{clean_title} | {time.time()}"

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        res_area = st.empty()
        full_res = ""
        msgs = [{"role": "system", "content": "You are NEO AI by Jibran."}] + st.session_state.messages
        try:
            comp = client.chat.completions.create(messages=msgs, model="llama-3.3-70b-versatile", stream=True)
            for chunk in comp:
                content = chunk.choices[0].delta.content
                if content:
                    full_res += content
                    res_area.markdown(full_res + "▌")
            res_area.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages
        except Exception as e:
            st.error(f"SYSTEM ERROR")
    st.rerun()

st.markdown('</div>', unsafe_allow_html=True) # Close main-content
