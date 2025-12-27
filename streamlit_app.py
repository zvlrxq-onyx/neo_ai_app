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
    * {{ transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275); }}
    .stApp {{ background: #0a0a0a; color: #e0e0e0; }}
    .center-container {{ display: flex; flex-direction: column; align-items: center; justify-content: center; margin-bottom: 20px; }}
    .logo-circle {{
        width: 120px; height: 120px;
        background-image: url("data:image/png;base64,{encoded_logo}");
        background-size: cover; background-position: center;
        border-radius: 50%; border: 2px solid {neon_cyan};
        box-shadow: 0 0 25px {neon_cyan}44; margin-bottom: 10px;
    }}
    .logo-circle:hover {{ transform: scale(1.1) rotate(5deg); box-shadow: 0 0 45px {neon_cyan}; }}
    .neon-title {{
        text-align: center; color: {neon_cyan}; font-size: 3.5rem; 
        font-weight: 900; letter-spacing: 12px; margin-bottom: 40px;
        text-transform: uppercase; text-shadow: 0 0 15px {neon_cyan}33;
    }}
    div[data-testid="stChatInput"] {{
        width: 70% !important; margin: 0 auto !important;
        transition: width 0.7s cubic-bezier(0.19, 1, 0.22, 1) !important;
    }}
    div[data-testid="stChatInput"]:focus-within {{ width: 100% !important; }}
    .stChatInput textarea {{
        border-radius: 25px !important; border: 1px solid {neon_cyan}44 !important;
        background-color: rgba(20, 20, 20, 0.9) !important; color: white !important;
    }}
    .about-box {{
        background: rgba(0, 255, 255, 0.03); border-left: 4px solid {neon_cyan};
        border-radius: 4px 20px 20px 4px; padding: 25px; margin-top: 15px;
        animation: proScaleIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
    }}
    @keyframes proScaleIn {{ from {{ transform: scale(0.9); opacity: 0; }} to {{ transform: scale(1); opacity: 1; }} }}
    section[data-testid="stSidebar"] {{ background-color: #080808 !important; border-right: 1px solid {neon_cyan}22; }}
    
    /* Edit Button Styling */
    .edit-btn {{
        font-size: 0.8rem;
        color: {neon_cyan};
        background: transparent;
        border: none;
        cursor: pointer;
    }}
    
    header, footer {{ visibility: hidden; }}
    </style>
    """

st.markdown(get_pro_css(), unsafe_allow_html=True)

# --- 6. SIDEBAR (HISTORY & EDITING) ---
with st.sidebar:
    st.markdown(f'<div class="center-container"><div class="logo-circle"></div></div>', unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align:center; color:#00ffff; letter-spacing:5px; font-size:2.2rem; text-shadow: 0 0 10px #00ffff; margin-bottom:20px;'>NEO AI</h1>", unsafe_allow_html=True)
    
    if st.button("NEW SESSION", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()

    st.markdown("---")
    st.markdown("<p style='font-size:0.7rem; color:#444; margin-left:5px;'>HISTORY LOGS</p>", unsafe_allow_html=True)
    
    # Render History Lists with Rename Feature
    for chat_id in reversed(list(st.session_state.all_chats.keys())):
        display_name = chat_id.split(" | ")[0]
        
        col1, col2 = st.columns([0.8, 0.2])
        
        with col1:
            if st.button(display_name, key=f"hist_{chat_id}", use_container_width=True):
                st.session_state.messages = st.session_state.all_chats[chat_id]
                st.session_state.current_chat_id = chat_id
                st.rerun()
        
        with col2:
            if st.button("✏️", key=f"edit_{chat_id}"):
                st.session_state.editing_chat_id = chat_id
                st.rerun()

    # Rename Input Box (Only show when editing)
    if st.session_state.editing_chat_id:
        st.markdown("---")
        new_name = st.text_input("Rename to:", value=st.session_state.editing_chat_id.split(" | ")[0])
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Save"):
                unique_suffix = st.session_state.editing_chat_id.split(" | ")[1]
                new_full_id = f"{new_name} | {unique_suffix}"
                
                # Update dictionary
                st.session_state.all_chats[new_full_id] = st.session_state.all_chats.pop(st.session_state.editing_chat_id)
                
                # Update current chat ID if we are in it
                if st.session_state.current_chat_id == st.session_state.editing_chat_id:
                    st.session_state.current_chat_id = new_full_id
                
                st.session_state.editing_chat_id = None
                st.rerun()
        with col_b:
            if st.button("Cancel"):
                st.session_state.editing_chat_id = None
                st.rerun()

    st.markdown("<div style='height:15vh;'></div>", unsafe_allow_html=True)
    if st.button("ABOUT NEO AI", use_container_width=True):
        st.session_state.show_about = not st.session_state.show_about
        st.rerun()

    if st.session_state.show_about:
        st.markdown(f"""
        <div class="about-box">
            <p style='color:cyan; font-weight:bold;'>PROJECT SPECIFICATION</p>
            <p style='font-size:0.8rem;'><b>DEV:</b> Muhammad Jibran Al Kaffie<br><b>CORE:</b> Llama-3.3-70B</p>
        </div>
        """, unsafe_allow_html=True)

# --- 7. MAIN INTERFACE ---
st.markdown(f'<div class="center-container"><div class="logo-circle"></div><h1 class="neon-title">NEO AI</h1></div>', unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 8. CHAT CORE LOGIC ---
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
            st.error(f"OFFLINE: {e}")
            
    st.rerun()
