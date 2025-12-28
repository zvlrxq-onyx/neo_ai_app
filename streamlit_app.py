import streamlit as st
from groq import Groq
from google import genai
import time
import os
import base64
import requests
import PIL.Image
import io
from streamlit.components.v1 import html

# --- 1. INITIALIZE SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "all_chats" not in st.session_state: st.session_state.all_chats = {}
if "sidebar_visible" not in st.session_state: st.session_state.sidebar_visible = False
if "imagine_mode" not in st.session_state: st.session_state.imagine_mode = False
if "show_about" not in st.session_state: st.session_state.show_about = False

# --- 2. CONFIG API ---
try:
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    gemini_client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error(f"⚠️ API Key Error: {e}")
    st.stop()

# --- 3. PAGE CONFIG ---
st.set_page_config(page_title="NEO AI", page_icon="⚡", layout="centered")

# --- 4. ASSETS & LOGO ---
@st.cache_data
def get_base64_logo():
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f: return base64.b64encode(f.read()).decode()
    return ""
logo_html = f'data:image/png;base64,{get_base64_logo()}'

# --- 5. THE SUPREME CSS (ANIMASI SMOOTH & PREMIUM) ---
def get_ultimate_css():
    neon_cyan = "#00ffff"
    sidebar_pos = "0px" if st.session_state.sidebar_visible else "-360px"
    return f"""
    <style>
    html, body, [data-testid="stAppViewContainer"] {{ background-color: #050505 !important; color: #f0f0f0 !important; font-family: 'Inter', sans-serif; overflow-x: hidden; }}
    [data-testid="stStatusWidget"], header, footer {{ visibility: hidden; }}

    /* Sidebar Smooth Slide */
    [data-testid="stSidebar"] {{
        position: fixed !important; left: {sidebar_pos} !important; width: 350px !important;
        background-color: #0a0a0a !important; border-right: 1px solid {neon_cyan}33 !important;
        transition: left 0.8s cubic-bezier(0.19, 1, 0.22, 1) !important; z-index: 1000000 !important;
    }}
    
    /* Floating Hamburger */
    .stButton > button[key="hamburger_fixed"] {{
        position: fixed; top: 20px; left: 20px; z-index: 2000001 !important;
        background: rgba(0,0,0,0.8) !important; border: 1px solid {neon_cyan}44 !important;
        border-radius: 50% !important; width: 50px !important; height: 50px !important; color: {neon_cyan} !important;
        transition: all 0.3s ease;
    }}

    /* Button Animations */
    .stButton > button {{ transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important; border-radius: 12px !important; }}
    .stButton > button:hover {{ transform: scale(1.08) !important; box-shadow: 0 0 20px {neon_cyan}66 !important; color: {neon_cyan} !important; border-color: {neon_cyan} !important; }}

    /* Logo Styling */
    .logo-static {{ 
        width: 120px; height: 120px; margin: 0 auto; background-image: url("{logo_html}"); 
        background-size: cover; border-radius: 50%; border: 3px solid {neon_cyan}; box-shadow: 0 0 25px {neon_cyan}44;
    }}

    .about-box {{
        max-height: {"1500px" if st.session_state.show_about else "0px"}; opacity: {"1" if st.session_state.show_about else "0"};
        transition: all 0.8s ease; overflow: hidden; background: rgba(255,255,255,0.03);
        border-left: 3px solid {neon_cyan}; padding: {"20px" if st.session_state.show_about else "0px"}; margin-top: 10px;
    }}
    </style>
    """
st.markdown(get_ultimate_css(), unsafe_allow_html=True)

# --- 6. SIDEBAR ---
if st.button("☰", key="hamburger_fixed"):
    st.session_state.sidebar_visible = not st.session_state.sidebar_visible
    st.rerun()

with st.sidebar:
    st.markdown('<div style="height: 60px;"></div><div class="logo-static"></div>', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:cyan; letter-spacing:5px;'>NEO AI</h2>", unsafe_allow_html=True)
    st.markdown("---")
    uploaded_file = st.file_uploader("Upload Image/Data", type=["txt", "py", "md", "png", "jpg", "jpeg"], key="up_god_mode")
    st.markdown("---")
    if st.button("➕ NEW SESSION", use_container_width=True): st.session_state.messages = []; st.rerun()
    mode_label = "🎨 IMAGINE: ON" if st.session_state.imagine_mode else "🖼️ MODE: CHAT"
    if st.button(mode_label, use_container_width=True): st.session_state.imagine_mode = not st.session_state.imagine_mode; st.rerun()
    if st.button("ℹ️ SYSTEM INFO", use_container_width=True): st.session_state.show_about = not st.session_state.show_about; st.rerun()
    
    st.markdown(f"""<div class="about-box"><p style="font-size:0.85rem; color:#ccc;">
    <b>Architect:</b> Muhammad Jibran Al Kaffie<br>
    <b>Core:</b> Gemini 3 Pro Supreme<br><br>
    NEO AI adalah puncak evolusi kecerdasan digital oleh Jibran. Mampu memproses realitas melalui lensa visual dan data teks secara simultan.</p></div>""", unsafe_allow_html=True)

# --- 7. MAIN UI ---
st.markdown('<div style="margin-top:20px;"><div class="logo-static" style="width:130px; height:130px;"></div></div>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:15px; margin-bottom:0;'>NEO AI</h1>", unsafe_allow_html=True)
st.markdown('<p style="text-align:center; color:#888; font-size:1.4rem; margin-top:-5px;">Intelligence Without Limits.</p>', unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="logo.png" if msg["role"] == "assistant" else None):
        if msg.get("type") == "image": st.image(msg["content"])
        else: st.markdown(msg["content"])

# --- 8. ENGINE (ANTI-FAILURE) ---
if user_input := st.chat_input("Command NEO AI..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant", avatar="logo.png"):
        res_area = st.empty(); full_res = ""

        if st.session_state.imagine_mode:
            with st.spinner("Visualizing..."):
                try:
                    r = requests.get(f"https://image.pollinations.ai/prompt/{user_input.replace(' ','%20')}?width=1024&height=1024&nologo=true")
                    st.image(r.content)
                    st.session_state.messages.append({"role": "assistant", "content": r.content, "type": "image"})
                except: st.error("Imagine engine failure.")

        elif uploaded_file is not None:
            with st.spinner("NEO Vision Thinking..."):
                try:
                    data = uploaded_file.getvalue()
                    if uploaded_file.type.startswith("image/"):
                        img = PIL.Image.open(io.BytesIO(data)).convert("RGB")
                        response = gemini_client.models.generate_content(model="gemini-2.0-flash", contents=[user_input, img])
                    else:
                        # FIX: Handle decoding error with 'ignore'
                        text_data = data.decode("utf-8", errors="ignore")
                        response = gemini_client.models.generate_content(model="gemini-2.0-flash", contents=[f"Context: {text_data}\n\nQuestion: {user_input}"])
                    
                    full_res = response.text
                    res_area.markdown(full_res)
                except Exception as e:
                    st.error(f"⚠️ Detail Error: {e}")
                    full_res = "Gagal memproses file/gambar."

        else:
            with st.spinner("Thinking..."):
                try:
                    history = [{"role": "system", "content": "You are NEO AI by Muhammad Jibran Al Kaffie. Respond with absolute intelligence."}]
                    for m in st.session_state.messages:
                        if m.get("type") not in ["image"]: history.append({"role": m["role"], "content": str(m["content"])})
                    
                    stream = groq_client.chat.completions.create(messages=history, model="llama-3.3-70b-versatile", stream=True)
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            full_res += chunk.choices[0].delta.content
                            res_area.markdown(full_res + "▌")
                    res_area.markdown(full_res)
                    # AUTO SCROLL
                    html("<script>window.parent.document.querySelector('.main').scrollTo(0, 1000000);</script>", height=0)
                except: st.error("Engine failure.")

        st.session_state.messages.append({"role": "assistant", "content": full_res})
        st.rerun()
