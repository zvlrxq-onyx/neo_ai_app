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

# --- 5. CSS ---
def get_ultimate_css():
    neon_cyan = "#00ffff"
    sidebar_pos = "0" if st.session_state.sidebar_visible else "-350px"
    return f"""
    <style>
    html, body, [data-testid="stAppViewContainer"] {{
        background-color: #080808 !important;
        color: #e0e0e0 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
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
    st.markdown(
        f'<div style="width:100px;height:100px;background-image:url({logo_html});background-size:cover;border-radius:50%;border:2px solid cyan;margin:0 auto;"></div>',
        unsafe_allow_html=True
    )
    st.markdown("<h2 style='text-align:center;color:cyan;'>NEO AI</h2>", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("➕ NEW SESSION", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()

    imagine_lbl = "🎨 IMAGINE: ON" if st.session_state.imagine_mode else "🖼️ MODE: CHAT"
    if st.button(imagine_lbl, use_container_width=True):
        st.session_state.imagine_mode = not st.session_state.imagine_mode
        st.rerun()

# --- 8. INTERFACE (INI YANG DIEDIT) ---
st.markdown('<div style="margin-top:20px;"><div class="logo-main"></div></div>', unsafe_allow_html=True)

st.markdown("""
<h1 style="
    text-align:center;
    color:#00ffff;
    letter-spacing:15px;
    margin-bottom:6px;
">
    NEO AI
</h1>

<p style="
    text-align:center;
    color:rgba(0,255,255,0.75);
    font-size:0.95rem;
    letter-spacing:2px;
    margin-top:0;
">
    Hi, is there anything I can help you with?
</p>
""", unsafe_allow_html=True)

# --- CHAT HISTORY ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "image":
            st.image(msg["content"], use_container_width=True)
        else:
            st.markdown(msg["content"])

# --- 9. ENGINE ---
if prompt := st.chat_input("Command NEO AI..."):
    if st.session_state.current_chat_id is None:
        st.session_state.current_chat_id = f"{prompt[:15]} | {time.time()}"
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        if st.session_state.imagine_mode:
            with st.spinner("Visualizing..."):
                url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?width=1024&height=1024"
                r = requests.get(url)
                if r.status_code == 200:
                    st.image(r.content, use_container_width=True)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": r.content,
                        "type": "image"
                    })
        else:
            res = ""
            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=st.session_state.messages,
                stream=True
            )
            box = st.empty()
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    res += chunk.choices[0].delta.content
                    box.markdown(res + "▌")
            box.markdown(res)
            st.session_state.messages.append({"role": "assistant", "content": res})

    st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages
    st.rerun()
