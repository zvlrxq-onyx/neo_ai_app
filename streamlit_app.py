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
    
    .stApp {{ background: #080808; color: #e0e0e0; }}

    /* Logo & Title */
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

    /* Tombol Utama (New Session, About) */
    .stButton > button {{
        background: transparent !important;
        color: #ffffff !important;
        border: 1px solid {neon_cyan}44 !important;
        border-radius: 4px !important;
        padding: 10px !important;
        width: 100% !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 600 !important;
    }}

    .stButton > button:hover {{
        transform: scale(1.05) !important;
        border-color: {neon_cyan} !important;
        background: rgba(0, 255, 255, 0.05) !important;
        box-shadow: 0 0 15px {neon_cyan}33 !important;
    }}

    /* KHUSUS Tombol Pensil (Pencil Only) */
    div[data-testid="column"]:nth-child(2) button {{
        filter: hue-rotate(170deg) brightness(1.2) drop-shadow(0 0 8px {neon_cyan});
        border: none !important;
        background: transparent !important;
        font-size: 1.2rem !important;
    }}

    .stButton > button:active {{
        transform: scale(0.98) !important;
    }}

    /* About Box */
    .about-box {{
        background: rgba(0, 255, 255, 0.02);
        border: 1px solid {neon_cyan}22;
        border-left: 4px solid {neon_cyan};
        border-radius: 4px; padding: 15px;
        margin-top: 15px;
        animation: aboutSlide 0.5s ease-out;
    }}
    
    @keyframes aboutSlide {{
        from {{ opacity: 0; transform: scale(0.95); }}
        to {{ opacity: 1; transform: scale(1); }}
    }}

    .about-header {{ color: {neon_cyan}; font-size: 0.9rem; font-weight: 800; letter-spacing: 2px; margin-bottom: 8px; }}
    .about-body {{ color: #999; font-size: 0.8rem; line-height: 1.5; }}

    /* Chat Input */
    div[data-testid="stChatInput"] {{
        width: 75% !important; margin: 0 auto !important;
        transition: width 0.8s cubic-bezier(0.19, 1, 0.22, 1) !important;
    }}
    div[data-testid="stChatInput"]:focus-within {{ width: 100% !important; }}

    header, footer {{ visibility: hidden; }}
    </style>
    """

st.markdown(get_pro_css(), unsafe_allow_html=True)

# --- 6. SIDEBAR (LOGIC) ---
with st.sidebar:
    st.markdown(f'<div class="center-container"><div class="logo-circle"></div></div>', unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align:center; color:#00ffff; letter-spacing:5px; font-size:2.2rem; text-shadow: 0 0 10px #00ffff; margin-bottom:20px;'>NEO AI</h1>", unsafe_allow_html=True)
    
    if st.button("NEW SESSION", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()

    st.markdown("---")
    st.markdown("<p style='font-size:0.6rem; color:#444; letter-spacing:1px; margin-left:5px;'>HISTORY</p>", unsafe_allow_html=True)
    
    # Render History List
    for chat_id in reversed(list(st.session_state.all_chats.keys())):
        display_name = chat_id.split(" | ")[0]
        col_main, col_edit = st.columns([0.8, 0.2])
        
        with col_main:
            if st.button(display_name, key=f"hist_{chat_id}", use_container_width=True):
                st.session_state.messages = st.session_state.all_chats[chat_id]
                st.session_state.current_chat_id = chat_id
                st.rerun()
        with col_edit:
            # Menggunakan Pensil Biasa (Tanpa Kertas)
            if st.button("✏️", key=f"edit_{chat_id}"):
                st.session_state.editing_chat_id = chat_id
                st.rerun()

    # Rename Modal
    if st.session_state.editing_chat_id:
        st.markdown("<br>", unsafe_allow_html=True)
        new_name = st.text_input("NEW NAME:", value=st.session_state.editing_chat_id.split(" | ")[0])
        c1, c2 = st.columns(2)
        with c1:
            if st.button("SAVE"):
                unique_suffix = st.session_state.editing_chat_id.split(" | ")[1]
                new_full_id = f"{new_name} | {unique_suffix}"
                st.session_state.all_chats[new_full_id] = st.session_state.all_chats.pop(st.session_state.editing_chat_id)
                if st.session_state.current_chat_id == st.session_state.editing_chat_id:
                    st.session_state.current_chat_id = new_full_id
                st.session_state.editing_chat_id = None
                st.rerun()
        with c2:
            if st.button("BACK"):
                st.session_state.editing_chat_id = None
                st.rerun()

    st.markdown("<div style='height:15vh;'></div>", unsafe_allow_html=True)
    
    if st.button("ABOUT", use_container_width=True):
        st.session_state.show_about = not st.session_state.show_about
        st.rerun()

    if st.session_state.show_about:
        st.markdown(f"""
        <div class="about-box">
            <div class="about-header">SYSTEM INFO</div>
            <div class="about-body">
                <b>Developer:</b> Muhammad Jibran Al Kaffie<br>
                <b>Core:</b> Llama-3.3-70B<br><br>
                NEO AI adalah sistem cerdas berbasis neural-network dengan antarmuka futuristik untuk analisis data real-time.
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- 7. MAIN INTERFACE ---
st.markdown(f'<div class="center-container"><div class="logo-circle"></div><h1 class="neon-title">NEO AI</h1></div>', unsafe_allow_html=True)

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
        msgs = [{"role": "system", "content": "Kamu adalah NEO AI buatan Muhammad Jibran Al Kaffie."}] + st.session_state.messages
        
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
            st.error(f"OVERLOAD: {e}")
            
    st.rerun()
