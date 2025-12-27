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

# --- 5. FIXED LAYOUT CSS ---
def get_pro_css():
    neon_cyan = "#00ffff"
    return f"""
    <style>
    /* Hide Default Elements */
    [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {{ display: none; }}
    header, footer {{ visibility: hidden; }}

    /* Global Transitions */
    * {{ transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1); }}
    
    .stApp {{ background: #080808; color: #e0e0e0; overflow: hidden; }}

    /* Main Content Shift */
    .main-content {{
        margin-left: 320px;
        transition: margin-left 0.6s cubic-bezier(0.16, 1, 0.3, 1);
        padding: 20px;
        height: 100vh;
        overflow-y: auto;
    }}

    /* Sidebar Locked to Left */
    .custom-sidebar {{
        position: fixed;
        left: 0; top: 0; bottom: 0;
        width: 300px;
        background: #050505;
        border-right: 1px solid {neon_cyan}22;
        z-index: 1000;
        padding: 25px;
        transform: translateX(0);
        transition: transform 0.6s cubic-bezier(0.16, 1, 0.3, 1);
        display: flex;
        flex-direction: column;
    }}

    /* Toggle Logic */
    #sidebar-toggle {{ display: none; }}
    #sidebar-toggle:checked ~ .custom-sidebar {{ transform: translateX(-100%); }}
    #sidebar-toggle:checked ~ .main-content {{ margin-left: 0; }}

    /* Hamburger Menu */
    .hamburger {{
        position: fixed;
        left: 20px; top: 20px;
        z-index: 1001;
        cursor: pointer;
        padding: 10px;
        background: #0d0d0d;
        border: 1px solid {neon_cyan}44;
        border-radius: 50%;
        width: 45px; height: 45px;
        display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px;
    }}
    .bar {{ width: 20px; height: 2px; background: {neon_cyan}; border-radius: 2px; }}

    /* Element Styling */
    .logo-circle-sidebar {{
        width: 80px; height: 80px;
        background-image: url("data:image/png;base64,{encoded_logo}");
        background-size: cover; background-position: center;
        border-radius: 50%; border: 2px solid {neon_cyan};
        margin: 0 auto 15px;
    }}

    .neon-title {{
        text-align: center; color: {neon_cyan}; font-size: 3rem; 
        font-weight: 900; letter-spacing: 10px; text-transform: uppercase;
        text-shadow: 0 0 20px {neon_cyan}44;
    }}

    /* Round Buttons */
    .stButton > button {{
        border-radius: 30px !important;
        border: 1px solid {neon_cyan}44 !important;
        background: transparent !important;
        color: white !important;
        text-transform: uppercase;
        font-weight: 600 !important;
        letter-spacing: 1px;
    }}
    .stButton > button:hover {{ 
        border-color: {neon_cyan} !important;
        background: {neon_cyan}11 !important;
        transform: scale(1.02);
    }}

    /* Chat Input Fix */
    div[data-testid="stChatInput"] {{
        width: 80% !important; margin: 0 auto !important;
    }}
    .stChatInput textarea {{ border-radius: 25px !important; }}

    /* Fluid About Box */
    .fluid-box {{
        background: rgba(0, 255, 255, 0.03);
        border: 1px solid {neon_cyan}22;
        border-left: 4px solid {neon_cyan};
        border-radius: 15px; padding: 12px; margin-top: 10px;
        font-size: 0.8rem;
    }}

    /* Pencil Icon */
    div[data-testid="column"]:nth-child(2) button {{
        filter: hue-rotate(170deg) brightness(1.2);
        border: none !important;
    }}
    </style>

    <input type="checkbox" id="sidebar-toggle">
    <label for="sidebar-toggle" class="hamburger">
        <div class="bar"></div>
        <div class="bar"></div>
        <div class="bar"></div>
    </label>
    """

st.markdown(get_pro_css(), unsafe_allow_html=True)

# --- 6. SIDEBAR CONTENT (WRAPPED) ---
with st.container():
    st.markdown('<div class="custom-sidebar">', unsafe_allow_html=True)
    st.markdown('<div class="logo-circle-sidebar"></div>', unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align:center; color:#00ffff; letter-spacing:3px;'>NEO AI</h3>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color:#ffffff11; margin: 10px 0;'>", unsafe_allow_html=True)
    
    # Sidebar Actions
    if st.button("NEW SESSION", key="new_sess_btn", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()
    
    st.markdown("<p style='font-size:0.6rem; color:#555; margin-top:15px; margin-left:10px;'>RECENT HISTORY</p>", unsafe_allow_html=True)
    
    # History Area (Scrollable)
    hist_container = st.container()
    with hist_container:
        for chat_id in reversed(list(st.session_state.all_chats.keys())):
            display_name = chat_id.split(" | ")[0]
            c1, c2 = st.columns([0.8, 0.2])
            with c1:
                if st.button(display_name, key=f"h_{chat_id}", use_container_width=True):
                    st.session_state.messages = st.session_state.all_chats[chat_id]
                    st.session_state.current_chat_id = chat_id
                    st.rerun()
            with c2:
                if st.button("✏️", key=f"e_{chat_id}"):
                    st.session_state.editing_chat_id = chat_id
                    st.rerun()

    # Bottom Sidebar
    st.markdown("<div style='flex-grow:1;'></div>", unsafe_allow_html=True)
    if st.button("ABOUT", key="about_btn", use_container_width=True):
        st.session_state.show_about = not st.session_state.show_about
        st.rerun()

    if st.session_state.show_about:
        st.markdown("""<div class="fluid-box"><b>Architect:</b> M. Jibran Al Kaffie<br><b>Engine:</b> Llama-3.3-70B</div>""", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# --- 7. MAIN CONTENT AREA ---
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# Main Title & Greeting
st.markdown('<div style="text-align:center; margin-top:50px;">', unsafe_allow_html=True)
st.markdown(f'<h1 class="neon-title">NEO AI</h1>', unsafe_allow_html=True)
st.markdown('<p style="color:white; font-size:1.4rem; opacity:0.8;">Hi, is there anything I can help you with?</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Chat Display
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input Logic
if prompt := st.chat_input("COMMAND..."):
    if st.session_state.current_chat_id is None:
        st.session_state.current_chat_id = f"{prompt[:20]} | {time.time()}"
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

st.markdown('</div>', unsafe_allow_html=True)
