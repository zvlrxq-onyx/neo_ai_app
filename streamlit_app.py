import streamlit as st
from groq import Groq
import time
import os
import base64

# --- 1. INITIALIZE SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "all_chats" not in st.session_state: st.session_state.all_chats = {}
if "current_chat_id" not in st.session_state: st.session_state.current_chat_id = None
if "dark_mode" not in st.session_state: st.session_state.dark_mode = True
if "show_about" not in st.session_state: st.session_state.show_about = False

# --- 2. CONFIG API (STREAMLIT SECRETS) ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except:
    st.error("SYSTEM ERROR: GROQ_API_KEY NOT FOUND IN SECRETS")
    st.stop()

# --- 3. PAGE CONFIG ---
st.set_page_config(page_title="NEO AI", page_icon="⚡", layout="centered")

# --- 4. LOGO LOADER (ROOT DIRECTORY) ---
encoded_logo = ""
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as f:
        encoded_logo = base64.b64encode(f.read()).decode()

# --- 5. ULTRA PREMIUM CSS ---
def get_pro_css():
    neon_cyan = "#00ffff"
    return f"""
    <style>
    /* Global Smoothness */
    * {{ transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275); }}
    
    .stApp {{ background: #0a0a0a; color: #e0e0e0; }}

    /* Logo Bulat di Tengah */
    .center-container {{
        display: flex; flex-direction: column; align-items: center; justify-content: center; margin-bottom: 30px;
    }}
    .logo-circle {{
        width: 130px; height: 130px;
        background-image: url("data:image/png;base64,{encoded_logo}");
        background-size: cover; background-position: center;
        border-radius: 50%;
        border: 2px solid {neon_cyan};
        box-shadow: 0 0 25px {neon_cyan}44;
        margin-bottom: 10px;
    }}
    .logo-circle:hover {{
        transform: scale(1.1) rotate(5deg);
        box-shadow: 0 0 45px {neon_cyan};
    }}

    /* Title Styling */
    .neon-title {{
        text-align: center; color: {neon_cyan}; font-size: 3.5rem; 
        font-weight: 900; letter-spacing: 12px; margin-bottom: 40px;
        text-transform: uppercase; text-shadow: 0 0 15px {neon_cyan}33;
    }}

    /* Chat Input Animasi Memanjang */
    div[data-testid="stChatInput"] {{
        width: 70% !important; margin: 0 auto !important;
        transition: width 0.7s cubic-bezier(0.19, 1, 0.22, 1) !important;
    }}
    div[data-testid="stChatInput"]:focus-within {{
        width: 100% !important;
    }}
    .stChatInput textarea {{
        border-radius: 25px !important;
        border: 1px solid {neon_cyan}44 !important;
        background-color: rgba(20, 20, 20, 0.9) !important;
        color: white !important;
    }}

    /* About Box Smooth & Pro */
    .about-box {{
        background: rgba(0, 255, 255, 0.03);
        border-left: 4px solid {neon_cyan};
        border-radius: 4px 20px 20px 4px; 
        padding: 25px; margin-top: 15px;
        animation: proScaleIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
    }}
    @keyframes proScaleIn {{
        from {{ transform: scale(0.9); opacity: 0; }}
        to {{ transform: scale(1); opacity: 1; }}
    }}
    .about-title {{ color: {neon_cyan}; font-size: 1.1rem; font-weight: 800; letter-spacing: 2px; margin-bottom: 12px; }}
    .about-text {{ color: #d1d1d1; font-size: 0.9rem; line-height: 1.7; }}

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {{ background-color: #080808 !important; border-right: 1px solid {neon_cyan}22; }}
    .stButton button {{
        background: transparent !important; color: white !important;
        border: 1px solid {neon_cyan}33 !important; border-radius: 10px !important;
        transition: all 0.3s ease !important;
    }}
    .stButton button:hover {{
        transform: scale(1.03) !important;
        background: {neon_cyan}11 !important; border-color: {neon_cyan} !important;
        box-shadow: 0 0 15px {neon_cyan}22;
    }}

    /* Hide Default UI */
    header, footer {{ visibility: hidden; }}
    </style>
    """

st.markdown(get_pro_css(), unsafe_allow_html=True)

# --- 6. SIDEBAR (HISTORY MANAGEMENT) ---
with st.sidebar:
    st.markdown(f'<div class="center-container"><div class="logo-circle"></div></div>', unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align:center; color:#00ffff; letter-spacing:3px;'>NEO AI</h3>", unsafe_allow_html=True)
    
    if st.button("NEW SESSION", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()

    st.markdown("<br><p style='font-size:0.7rem; color:#444; margin-left:5px;'>HISTORY LOGS</p>", unsafe_allow_html=True)
    
    # Render History tanpa duplikasi (Fixed Bug)
    for chat_id in reversed(list(st.session_state.all_chats.keys())):
        if st.button(chat_id, key=f"hist_{chat_id}", use_container_width=True):
            st.session_state.messages = st.session_state.all_chats[chat_id]
            st.session_state.current_chat_id = chat_id
            st.rerun()

    st.markdown("<div style='height:25vh;'></div>", unsafe_allow_html=True)
    
    if st.button("ABOUT NEO AI", use_container_width=True):
        st.session_state.show_about = not st.session_state.show_about
        st.rerun()

    if st.session_state.show_about:
        st.markdown(f"""
        <div class="about-box">
            <div class="about-title">PROJECT SPECIFICATION</div>
            <div class="about-text">
                <b>NEO AI v4.0</b> is a high-performance artificial intelligence interface developed by 
                <b>Muhammad Jibran Al Kaffie</b>. 
                <br><br>
                This system utilizes <b>Neo-Intelligence Architecture</b> combined with <b>Llama-3.3-70B</b> core 
                to provide advanced technical analysis, creative synthesis, and real-time problem-solving capabilities. 
                Designed for speed and precision, NEO AI represents the intersection of futuristic aesthetics and 
                functional computing.
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- 7. MAIN INTERFACE ---
st.markdown(f'<div class="center-container"><div class="logo-circle"></div><h1 class="neon-title">NEO AI</h1></div>', unsafe_allow_html=True)

# Display Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 8. CHAT INPUT & CORE LOGIC (Fixed History Bug) ---
if prompt := st.chat_input("COMMAND..."):
    # Lock Chat ID pada pesan pertama
    if not st.session_state.messages:
        # Gunakan 20 karakter pertama sebagai judul permanen sesi ini
        session_id = prompt[:25] + "..." if len(prompt) > 25 else prompt
        st.session_state.current_chat_id = session_id

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        res_area = st.empty()
        full_res = ""
        # Context Memory
        msgs = [{"role": "system", "content": "Kamu adalah NEO AI buatan Muhammad Jibran Al Kaffie. Jawablah dengan nada cerdas, futuristik, dan profesional."}] + st.session_state.messages
        
        try:
            comp = client.chat.completions.create(messages=msgs, model="llama-3.3-70b-versatile", stream=True)
            for chunk in comp:
                content = chunk.choices[0].delta.content
                if content:
                    full_res += content
                    res_area.markdown(full_res + "▌")
            res_area.markdown(full_res)
            
            # Save Assistant Response
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            
            # Update History (Hanya pada ID yang sudah dikunci di awal)
            st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages
            
        except Exception as e:
            st.error(f"SYSTEM OVERLOAD: {e}")
            
    st.rerun()
