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

# --- 1. SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "all_chats" not in st.session_state: st.session_state.all_chats = {}
if "current_chat_id" not in st.session_state: st.session_state.current_chat_id = None
if "imagine_mode" not in st.session_state: st.session_state.imagine_mode = False
if "show_about" not in st.session_state: st.session_state.show_about = False
if "sidebar_visible" not in st.session_state: st.session_state.sidebar_visible = False

# --- 2. API CONFIG ---
try:
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    # Gunakan inisialisasi yang paling stabil
    gemini_client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error(f"Konfigurasi API Error: {e}")
    st.stop()

# --- 3. PAGE CONFIG ---
st.set_page_config(page_title="NEO AI SUPREME", page_icon="⚡", layout="centered")

# --- 4. AUTO-SCROLL JS ---
def auto_scroll():
    html("<script>window.parent.document.querySelector('.main').scrollTo({top: 1000000, behavior: 'smooth'});</script>", height=0)

# --- 5. CSS (SMOOTH & FIX) ---
def get_ultimate_css():
    neon = "#00ffff"
    sidebar_pos = "0px" if st.session_state.sidebar_visible else "-360px"
    return f"""
    <style>
    html, body, [data-testid="stAppViewContainer"] {{ background-color: #050505 !important; color: #f0f0f0 !important; scroll-behavior: smooth; }}
    [data-testid="stSidebar"] {{ position: fixed !important; left: {sidebar_pos} !important; width: 350px !important; background-color: #0a0a0a !important; border-right: 1px solid {neon}33 !important; transition: left 0.8s cubic-bezier(0.19, 1, 0.22, 1) !important; z-index: 1000000 !important; }}
    .stButton > button {{ transition: all 0.4s ease !important; border-radius: 10px !important; }}
    .stButton > button:hover {{ transform: scale(1.05); box-shadow: 0 0 15px {neon}44; border-color: {neon}; }}
    [data-testid="stChatInput"] {{ transition: all 0.5s ease; }}
    .about-box {{ max-height: {"1500px" if st.session_state.show_about else "0px"}; opacity: {"1" if st.session_state.show_about else "0"}; transition: all 0.8s ease; overflow: hidden; background: rgba(255,255,255,0.02); padding: {"20px" if st.session_state.show_about else "0px"}; border-left: 3px solid {neon}; }}
    </style>
    """
st.markdown(get_ultimate_css(), unsafe_allow_html=True)

# --- 6. SIDEBAR ---
if st.button("☰", key="hamburger_fixed"):
    st.session_state.sidebar_visible = not st.session_state.sidebar_visible
    st.rerun()

with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:cyan;'>NEO AI</h1>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload Image/Data", type=["txt", "py", "md", "png", "jpg", "jpeg"], key="v5_up")
    st.markdown("---")
    if st.button("➕ NEW SESSION", use_container_width=True): st.session_state.messages = []; st.rerun()
    mode_label = "🎨 IMAGINE MODE" if st.session_state.imagine_mode else "💬 CHAT MODE"
    if st.button(mode_label, use_container_width=True): st.session_state.imagine_mode = not st.session_state.imagine_mode; st.rerun()
    if st.button("ℹ️ SYSTEM INFO", use_container_width=True): st.session_state.show_about = not st.session_state.show_about; st.rerun()
    st.markdown(f'<div class="about-box"><b>Architect:</b> Muhammad Jibran Al Kaffie<br><b>Engine:</b> Gemini 3 Pro Supreme<br><br>NEO AI adalah entitas cerdas yang mampu melihat dan berpikir.</div>', unsafe_allow_html=True)

# --- 7. MAIN UI ---
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:10px;'>NEO AI</h1>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "image": st.image(msg["content"])
        else: st.markdown(msg["content"])

# --- 8. ENGINE ---
if user_input := st.chat_input("Command NEO AI..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant"):
        res_area = st.empty()
        
        # A. MODE IMAGINE
        if st.session_state.imagine_mode:
            try:
                url = f"https://image.pollinations.ai/prompt/{user_input.replace(' ','%20')}?width=1024&height=1024&nologo=true"
                r = requests.get(url)
                st.image(r.content)
                st.session_state.messages.append({"role": "assistant", "content": r.content, "type": "image"})
            except: st.error("Imagine Failed.")

        # B. MODE VISION (FIXED)
        elif uploaded_file is not None:
            with st.spinner("NEO Vision Thinking..."):
                try:
                    raw_bytes = uploaded_file.getvalue()
                    if uploaded_file.type.startswith("image/"):
                        # Cara paling aman untuk Gemini: Kirim PIL Image
                        img = PIL.Image.open(io.BytesIO(raw_bytes)).convert("RGB")
                        # Pastikan menggunakan model 'gemini-1.5-flash' atau 'gemini-1.5-pro' jika 'gemini-3' belum stabil di regionmu
                        response = gemini_client.models.generate_content(
                            model="gemini-1.5-pro", # Menggunakan 1.5 Pro yang lebih stabil untuk Vision
                            contents=[user_input, img]
                        )
                    else:
                        response = gemini_client.models.generate_content(
                            model="gemini-1.5-pro",
                            contents=[user_input, raw_bytes.decode()]
                        )
                    res_area.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"Vision Error: {e}")

        # C. MODE CHAT
        else:
            full_res = ""
            stream = groq_client.chat.completions.create(
                messages=[{"role": "system", "content": "You are NEO AI by Jibran. You are supreme."}] + 
                         [{"role": m["role"], "content": str(m["content"])} for m in st.session_state.messages],
                model="llama-3.3-70b-versatile", stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_res += chunk.choices[0].delta.content
                    res_area.markdown(full_res + "▌")
                    auto_scroll()
            res_area.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
    
    st.rerun()
