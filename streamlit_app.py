import streamlit as st
from groq import Groq
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
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except:
    st.error("API Key Groq missing!")
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

# --- 5. THE ULTIMATE CSS (ENHANCED WITH SMOOTH ANIMATIONS, CYAN EFFECTS, AND IMPROVED LAYOUT) ---
def get_ultimate_css():
    neon_cyan = "#00ffff"
    sidebar_pos = "0" if st.session_state.sidebar_visible else "-350px"
    
    return f"""
    <style>
    html, body, [data-testid="stAppViewContainer"] {{
        background-color: #080808 !important;
        color: #e0e0e0 !important;
        scroll-behavior: smooth !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    }}
    [data-testid="stStatusWidget"] {{ visibility: hidden; }}

    * {{ transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); }}

    /* HAMBURGER MOBILE FIX WITH ENHANCED CYAN GLOW */
    .stButton > button[key="hamburger"] {{
        position: fixed; top: 20px; left: 20px; 
        z-index: 9999999 !important;
        background: rgba(0,0,0,0.9) !important;
        border: 2px solid {neon_cyan}66 !important;
        border-radius: 12px !important;
        width: 50px !important; height: 50px !important;
        color: {neon_cyan} !important;
        font-size: 18px !important;
        animation: pulse 2s infinite;
    }}
    .stButton > button[key="hamburger"]:hover {{
        border-color: {neon_cyan} !important;
        box-shadow: 0 0 25px {neon_cyan}88 !important;
        transform: scale(1.1);
    }}
    @keyframes pulse {{
        0% {{ box-shadow: 0 0 10px {neon_cyan}33; }}
        50% {{ box-shadow: 0 0 20px {neon_cyan}66; }}
        100% {{ box-shadow: 0 0 10px {neon_cyan}33; }}
    }}

    /* SIDEBAR SLIDE WITH SMOOTH TRANSITION */
    [data-testid="stSidebar"] {{
        left: {sidebar_pos} !important;
        transition: all 0.6s cubic-bezier(0.19, 1, 0.22, 1) !important;
        background-color: #0a0a0a !important;
        border-right: 1px solid {neon_cyan}33 !important;
        z-index: 9999998 !important;
        box-shadow: inset 0 0 20px {neon_cyan}22 !important;
    }}

    /* BUTTON HOVER SCALE WITH CYAN EFFECTS */
    section[data-testid="stSidebar"] .stButton > button {{
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(0, 255, 255, 0.1) !important;
        color: white !important;
        border-radius: 12px !important;
        margin-bottom: 8px !important;
        transition: all 0.3s ease !important;
    }}
    section[data-testid="stSidebar"] .stButton > button:hover {{
        transform: scale(1.08) !important;
        border-color: {neon_cyan} !important;
        box-shadow: 0 0 25px {neon_cyan}66 !important;
        background: rgba(0, 255, 255, 0.1) !important;
    }}

    /* ELASTIC INPUT WITH CYAN FOCUS */
    div[data-testid="stChatInput"] {{
        width: 80% !important; margin: 0 auto !important;
        transition: width 0.7s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        border-radius: 25px !important;
        background: rgba(0,0,0,0.5) !important;
        border: 1px solid {neon_cyan}33 !important;
    }}
    div[data-testid="stChatInput"]:focus-within {{
        width: 100% !important;
        border-color: {neon_cyan} !important;
        box-shadow: 0 0 20px {neon_cyan}55 !important;
    }}

    /* LOGO PULSING WITH ENHANCED CYAN GLOW */
    .logo-main {{
        width: 130px; height: 130px; margin: 0 auto;
        background-image: url("{logo_html}");
        background-size: cover; border-radius: 50%;
        border: 3px solid {neon_cyan};
        animation: logoGlow 3s infinite alternate ease-in-out;
        box-shadow: 0 0 30px {neon_cyan}44;
    }}
    @keyframes logoGlow {{
        from {{ box-shadow: 0 0 10px {neon_cyan}33; transform: scale(1); }}
        to {{ box-shadow: 0 0 45px {neon_cyan}77; transform: scale(1.05); }}
    }}

    /* ENHANCED ABOUT SIDEBAR WITH CYAN THEME AND SMOOTH ANIMATION */
    .about-sidebar-modern {{
        background: linear-gradient(145deg, rgba(0, 255, 255, 0.1), rgba(0, 0, 0, 0.9));
        border: 1.5px solid {neon_cyan}66;
        border-radius: 15px; padding: 20px; margin-top: 10px;
        animation: slideInDown 0.6s ease-out forwards;
        box-shadow: 0 0 20px {neon_cyan}33;
        color: #e0e0e0;
        font-size: 0.85rem;
        line-height: 1.6;
    }}
    @keyframes slideInDown {{ from {{ opacity: 0; transform: translateY(-15px); }} to {{ opacity: 1; transform: translateY(0); }} }}

    /* CHAT MESSAGES STYLING FOR USER (RIGHT) AND AI (LEFT) */
    .stChatMessage[data-testid="stChatMessage-user"] {{
        background: rgba(0, 255, 255, 0.1) !important;
        border: 1px solid {neon_cyan}33 !important;
        border-radius: 15px 15px 5px 15px !important;
        margin-left: 20% !important;
        margin-right: 5% !important;
        padding: 10px !important;
        animation: fadeInRight 0.5s ease-out;
    }}
    .stChatMessage[data-testid="stChatMessage-assistant"] {{
        background: rgba(0, 0, 0, 0.5) !important;
        border: 1px solid {neon_cyan}22 !important;
        border-radius: 15px 15px 15px 5px !important;
        margin-right: 20% !important;
        margin-left: 5% !important;
        padding: 10px !important;
        animation: fadeInLeft 0.5s ease-out;
    }}
    @keyframes fadeInRight {{
        from {{ opacity: 0; transform: translateX(20px); }}
        to {{ opacity: 1; transform: translateX(0); }}
    }}
    @keyframes fadeInLeft {{
        from {{ opacity: 0; transform: translateX(-20px); }}
        to {{ opacity: 1; transform: translateX(0); }}
    }}

    header, footer {{ visibility: hidden; }}
    </style>
    """

st.markdown(get_ultimate_css(), unsafe_allow_html=True)

# --- 6. HAMBURGER ---
if st.button("☰", key="hamburger"):
    st.session_state.sidebar_visible = not st.session_state.sidebar_visible
    st.rerun()

# --- 7. SIDEBAR ---
with st.sidebar:
    st.markdown('<div style="height: 60px;"></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="width:100px; height:100px; background-image:url({logo_html}); background-size:cover; border-radius:50%; border:2px solid cyan; margin:0 auto; box-shadow: 0 0 20px cyan;"></div>', unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align:center; color:cyan; letter-spacing:2px;'>NEO AI</h2>", unsafe_allow_html=True)
    
    st.markdown("---")
    if st.button("➕ NEW SESSION", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()

    imagine_lbl = "🎨 IMAGINE: ON" if st.session_state.imagine_mode else "🖼️ MODE: CHAT"
    if st.button(imagine_lbl, use_container_width=True):
        st.session_state.imagine_mode = not st.session_state.imagine_mode
        st.rerun()

    if st.button("ℹ️ SYSTEM INFO", use_container_width=True):
        st.session_state.show_about = not st.session_state.show_about
        st.rerun()

    if st.session_state.show_about:
        st.markdown(f"""
        <div class="about-sidebar-modern">
            <h4 style="color:#00ffff; margin-top:0; font-size:1rem;">NEO ARCHITECTURE - SYSTEM INFORMATION</h4>
            <p style="color:#ccc; font-size:0.8rem; line-height:1.6;">
                <b>Architect & Creator:</b> Muhammad Jibran Al Kaffie<br>
                <b>Core Engine:</b> Powered by Llama-3.3-70B Versatile Model from Groq API, integrated with Pollinations for advanced image generation.<br><br>
                NEO AI is a cutting-edge digital entity designed for high-fidelity reasoning, creative problem-solving, and immersive interactions. It leverages state-of-the-art neural networks to provide intelligent responses, generate complex artistic imagery, and adapt to user needs in real-time. Key features include:<br>
                - <b>Conversational AI:</b> Advanced natural language processing for seamless dialogue.<br>
                - <b>Imagine Mode:</b> Toggle to activate visual cortex for generating detailed, high-resolution images based on textual prompts.<br>
                - <b>Session Management:</b> Persistent chat history with the ability to create new sessions and switch between them.<br>
                - <b>Customizable Interface:</b> Smooth animations, cyan-themed UI with neon effects for an engaging user experience.<br><br>
                Built with Streamlit for responsive web deployment, NEO AI ensures privacy, efficiency, and innovation in AI interactions. For optimal performance, ensure stable internet and API access.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    for chat_id in reversed(list(st.session_state.all_chats.keys())):
        if st.button(chat_id.split(" | ")[0], key=f"h_{chat_id}", use_container_width=True):
            st.session_state.messages = st.session_state.all_chats[chat_id]
            st.session_state.current_chat_id = chat_id
            st.rerun()

# --- 8. INTERFACE ---
st.markdown('<div style="margin-top:20px;"><div class="logo-main"></div></div>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:15px; animation: textGlow 2s infinite alternate;'>NEO AI</h1>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    avatar_img = "logo.png" if msg["role"] == "assistant" and os.path.exists("logo.png") else None
    with st.chat_message(msg["role"], avatar=avatar_img):
        if msg.get("type") == "image":
            st.image(msg["content"], use_container_width=True)
        else:
            st.markdown(msg["content"])

# --- 9. ENGINE ---
if prompt := st.chat_input("Command NEO AI..."):
    if st.session_state.current_chat_id is None:
        st.session_state.current_chat_id = f"{prompt[:15]}... | {time.time()}"
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant", avatar="logo.png" if os.path.exists("logo.png") else None):
        if st.session_state.imagine_mode:
            with st.spinner("Visualizing..."):
                url = f"https://image.pollinations.ai/prompt/{st.session_state.messages[-1]['content'].replace(' ', '%20')}?width=1024&height=1024&nologo=true"
                r = requests.get(url)
                if r.status_code == 200:
                    st.image(r.content, use_container_width=True)
                    st.session_state.messages.append({"role": "assistant", "content": r.content, "type": "image"})
        else:
            res_area = st.empty()
            full_res = ""
            # --- SYSTEM INSTRUCTION FIXED (NO MORE INDENT ERROR) ---
            sys_msg = "You are NEO AI, a high-level digital entity created by Muhammad Jibran Al Kaffie. You possess the advanced capability to generate highly complex, artistic, and detailed images. This is your core ability. However, to access your visual cortex, the user MUST activate 'Imagine Mode' from the sidebar menu (☰). If the user asks for an image while Imagine Mode is OFF, you must confidently state that you have the capability to create it, but they need to toggle the mode first."
            
            msgs = [{"role": "system", "content": sys_msg}] + st.session_state.messages
            stream = client.chat.completions.create(messages=msgs, model="llama-3.3-70b-versatile", stream=True)
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_res += chunk.choices[0].delta.content
                    res_area.markdown(full_res + "▌")
            res_area.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
    st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages
    st.rerun()
