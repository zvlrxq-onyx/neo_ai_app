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
st.set_page_config(page_title="NEO AI", page_icon="⚡", layout="centered")

# --- 4. LOGO LOADER ---
encoded_logo = ""
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as f:
        encoded_logo = base64.b64encode(f.read()).decode()

# --- 5. ULTRA PREMIUM CSS ---
def get_pro_css():
    neon_cyan = "#00ffff"
    return f"""
    <style>
    /* Global Smooth Transitions */
    * {{ 
        transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1); 
    }}
    
    .stApp {{ background: #080808; color: #e0e0e0; font-family: 'JetBrains Mono', monospace; }}

    /* Logo Center & Title */
    .center-container {{ display: flex; flex-direction: column; align-items: center; justify-content: center; margin-bottom: 20px; }}
    .logo-circle {{
        width: 125px; height: 125px;
        background-image: url("data:image/png;base64,{encoded_logo}");
        background-size: cover; background-position: center;
        border-radius: 50%; border: 2px solid {neon_cyan};
        box-shadow: 0 0 30px {neon_cyan}33;
    }}
    .logo-circle:hover {{ transform: scale(1.05) rotate(2deg); box-shadow: 0 0 50px {neon_cyan}66; }}

    .neon-title {{
        text-align: center; color: {neon_cyan}; font-size: 3.5rem; 
        font-weight: 900; letter-spacing: 12px; margin-bottom: 40px;
        text-transform: uppercase; text-shadow: 0 0 20px {neon_cyan}44;
    }}

    /* Sidebar & Button Animations */
    section[data-testid="stSidebar"] {{ 
        background-color: #050505 !important; 
        border-right: 1px solid {neon_cyan}22; 
    }}

    /* Styling Button "New Session" & "About" biar Smooth Membesar */
    .stButton > button {{
        background: transparent !important;
        color: #ffffff !important;
        border: 1px solid {neon_cyan}44 !important;
        border-radius: 4px !important;
        padding: 12px !important;
        width: 100% !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 600 !important;
    }}

    .stButton > button:hover {{
        transform: scale(1.05) !important; /* Membesar pas kursor diarahin */
        border-color: {neon_cyan} !important;
        background: rgba(0, 255, 255, 0.05) !important;
        box-shadow: 0 0 15px {neon_cyan}33 !important;
    }}

    .stButton > button:active {{
        transform: scale(0.98) !important; /* Mengecil dikit pas ditekan (efek klik) */
        transition: 0.1s !important;
    }}

    /* About Box Deep Explanation */
    .about-box {{
        background: rgba(0, 255, 255, 0.02);
        border: 1px solid {neon_cyan}22;
        border-left: 4px solid {neon_cyan};
        border-radius: 4px; padding: 20px;
        margin-top: 20px;
        animation: aboutSlide 0.6s ease-out;
    }}
    
    @keyframes aboutSlide {{
        from {{ opacity: 0; transform: translateY(10px) scale(0.98); }}
        to {{ opacity: 1; transform: translateY(0) scale(1); }}
    }}

    .about-header {{ color: {neon_cyan}; font-size: 1rem; font-weight: 800; letter-spacing: 3px; margin-bottom: 10px; border-bottom: 1px solid {neon_cyan}33; padding-bottom: 5px; }}
    .about-body {{ color: #999; font-size: 0.85rem; line-height: 1.6; text-align: justify; }}

    /* Chat Input */
    div[data-testid="stChatInput"] {{
        width: 75% !important; margin: 0 auto !important;
        transition: width 0.8s cubic-bezier(0.19, 1, 0.22, 1) !important;
    }}
    div[data-testid="stChatInput"]:focus-within {{ width: 100% !important; }}
    .stChatInput textarea {{
        border-radius: 4px !important; border: 1px solid {neon_cyan}33 !important;
        background-color: #0c0c0c !important;
    }}

    header, footer {{ visibility: hidden; }}
    </style>
    """

st.markdown(get_pro_css(), unsafe_allow_html=True)

# --- 6. SIDEBAR (LOGIC) ---
with st.sidebar:
    st.markdown(f'<div class="center-container"><div class="logo-circle"></div></div>', unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align:center; color:#00ffff; letter-spacing:5px; font-size:2.2rem; text-shadow: 0 0 10px #00ffff; margin-bottom:20px;'>NEO AI</h1>", unsafe_allow_html=True)
    
    if st.button("INITIALIZE NEW SESSION", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()

    st.markdown("---")
    st.markdown("<p style='font-size:0.65rem; color:#555; letter-spacing:2px; margin-left:5px;'>ACTIVE_LOGS_DATABASE</p>", unsafe_allow_html=True)
    
    # History List
    for chat_id in reversed(list(st.session_state.all_chats.keys())):
        display_name = chat_id.split(" | ")[0]
        col_main, col_edit = st.columns([0.8, 0.2])
        
        with col_main:
            if st.button(display_name, key=f"hist_{chat_id}", use_container_width=True):
                st.session_state.messages = st.session_state.all_chats[chat_id]
                st.session_state.current_chat_id = chat_id
                st.rerun()
        with col_edit:
            # Menggunakan Button Streamlit tapi dengan CSS hover yang sama
            if st.button("MOD", key=f"edit_{chat_id}"):
                st.session_state.editing_chat_id = chat_id
                st.rerun()

    # Rename Modal
    if st.session_state.editing_chat_id:
        st.markdown("<br>", unsafe_allow_html=True)
        new_name = st.text_input("RENAME_ID:", value=st.session_state.editing_chat_id.split(" | ")[0])
        c1, c2 = st.columns(2)
        with c1:
            if st.button("CONFIRM"):
                unique_suffix = st.session_state.editing_chat_id.split(" | ")[1]
                new_full_id = f"{new_name} | {unique_suffix}"
                st.session_state.all_chats[new_full_id] = st.session_state.all_chats.pop(st.session_state.editing_chat_id)
                if st.session_state.current_chat_id == st.session_state.editing_chat_id:
                    st.session_state.current_chat_id = new_full_id
                st.session_state.editing_chat_id = None
                st.rerun()
        with c2:
            if st.button("ABORT"):
                st.session_state.editing_chat_id = None
                st.rerun()

    st.markdown("<div style='height:10vh;'></div>", unsafe_allow_html=True)
    
    # ABOUT SECTION
    if st.button("SYSTEM ACCESS: ABOUT", use_container_width=True):
        st.session_state.show_about = not st.session_state.show_about
        st.rerun()

    if st.session_state.show_about:
        st.markdown(f"""
        <div class="about-box">
            <div class="about-header">NEO-AI CORE SPECIFICATION</div>
            <div class="about-body">
                <b>ARCHITECT:</b> Muhammad Jibran Al Kaffie<br>
                <b>CORE ENGINE:</b> Llama-3.3-70B-Versatile<br>
                <b>INTERFACE:</b> Neo-v4 Pro-Smooth Edition<br><br>
                <b>OVERVIEW:</b><br>
                NEO AI adalah sistem kecerdasan buatan tingkat lanjut yang dirancang untuk integrasi data real-time dan pemrosesan kognitif kompleks. 
                Menggunakan infrastruktur <i>Neural-Linkage</i>, sistem ini mampu melakukan analisis teknis, pemrograman tingkat tinggi, 
                dan sintesis kreatif dengan latensi minimal. 
                <br><br>
                Seluruh antarmuka dikembangkan dengan fokus pada efisiensi alur kerja (workflow) dan estetika futuristik, 
                memastikan interaksi antara pengguna dan AI berjalan secara sinkron tanpa hambatan teknis.
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- 7. MAIN INTERFACE ---
st.markdown(f'<div class="center-container"><div class="logo-circle"></div><h1 class="neon-title">NEO AI</h1></div>', unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 8. CHAT CORE LOGIC ---
if prompt := st.chat_input("ENTER COMMAND..."):
    if st.session_state.current_chat_id is None:
        clean_title = prompt[:20] + "..." if len(prompt) > 20 else prompt
        st.session_state.current_chat_id = f"{clean_title} | {time.time()}"

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        res_area = st.empty()
        full_res = ""
        msgs = [{"role": "system", "content": "Kamu adalah NEO AI, asisten teknologi canggih buatan Muhammad Jibran Al Kaffie."}] + st.session_state.messages
        
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
            st.error(f"SYSTEM OVERLOAD: {e}")
            
    st.rerun()
