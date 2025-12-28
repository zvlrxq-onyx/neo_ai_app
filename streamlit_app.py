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
if "current_chat_id" not in st.session_state: st.session_state.current_chat_id = None
if "imagine_mode" not in st.session_state: st.session_state.imagine_mode = False
if "show_about" not in st.session_state: st.session_state.show_about = False
if "sidebar_visible" not in st.session_state: st.session_state.sidebar_visible = False

# --- 2. CONFIG API ---
try:
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    # Inisialisasi Gemini 3 Client
    gemini_client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error(f"⚠️ API Key Error: {e}")
    st.stop()

# --- 3. PAGE CONFIG ---
st.set_page_config(page_title="NEO AI", page_icon="⚡", layout="centered")

# --- 4. AUTO-SCROLL JS ---
def auto_scroll():
    js = """<script>var body = window.parent.document.querySelector(".main"); body.scrollTop = body.scrollHeight;</script>"""
    return html(js, height=0)

# --- 5. ASSETS ---
@st.cache_data
def get_base64_logo():
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f: return base64.b64encode(f.read()).decode()
    return ""
logo_html = f'data:image/png;base64,{get_base64_logo()}'

# --- 6. SUPREME CSS ---
def get_ultimate_css():
    neon_cyan = "#00ffff"
    sidebar_pos = "0px" if st.session_state.sidebar_visible else "-360px"
    return f"""
    <style>
    html, body, [data-testid="stAppViewContainer"] {{ background-color: #050505 !important; color: #f0f0f0 !important; }}
    [data-testid="stStatusWidget"], header, footer {{ visibility: hidden; }}

    [data-testid="stSidebar"] {{
        position: fixed !important; left: {sidebar_pos} !important; width: 350px !important;
        background-color: #0a0a0a !important; border-right: 1px solid {neon_cyan}33 !important;
        transition: left 0.8s cubic-bezier(0.19, 1, 0.22, 1) !important; z-index: 1000000 !important;
    }}
    
    .stButton > button[key="hamburger_fixed"] {{
        position: fixed; top: 20px; left: 20px; z-index: 2000001 !important;
        background: rgba(0,0,0,0.8) !important; border: 1px solid {neon_cyan}44 !important; border-radius: 50% !important;
    }}

    .stButton > button {{ transition: all 0.5s ease !important; }}
    .stButton > button:hover {{ transform: scale(1.08) !important; box-shadow: 0 0 20px {neon_cyan}66 !important; }}

    [data-testid="stChatInput"] {{ transition: all 0.6s ease !important; }}
    [data-testid="stChatInput"]:focus-within {{ transform: scaleX(1.03) !important; }}

    .logo-static {{ 
        width: 120px; height: 120px; margin: 0 auto; background-image: url("{logo_html}"); 
        background-size: cover; border-radius: 50%; border: 3px solid {neon_cyan};
    }}

    .about-box {{
        max-height: {"1500px" if st.session_state.show_about else "0px"}; opacity: {"1" if st.session_state.show_about else "0"};
        transition: all 0.8s ease; overflow: hidden; background: rgba(255,255,255,0.03);
        border-left: 3px solid {neon_cyan}; padding: {"20px" if st.session_state.show_about else "0px"}; margin-top: 10px;
    }}
    </style>
    """
st.markdown(get_ultimate_css(), unsafe_allow_html=True)

# --- 7. SIDEBAR ---
if st.button("☰", key="hamburger_fixed"):
    st.session_state.sidebar_visible = not st.session_state.sidebar_visible
    st.rerun()

with st.sidebar:
    st.markdown('<div style="height: 60px;"></div><div class="logo-static"></div>', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:cyan;'>NEO AI</h2>", unsafe_allow_html=True)
    st.markdown("---")
    uploaded_file = st.file_uploader("Upload Image/Data", type=["txt", "py", "md", "png", "jpg", "jpeg"], key="neo_vision_up")
    st.markdown("---")
    if st.button("➕ NEW SESSION", use_container_width=True): st.session_state.messages = []; st.session_state.current_chat_id = None; st.rerun()
    if st.button("🖼️ MODE: " + ("IMAGINE" if st.session_state.imagine_mode else "CHAT"), use_container_width=True):
        st.session_state.imagine_mode = not st.session_state.imagine_mode; st.rerun()
    if st.button("ℹ️ SYSTEM INFO", use_container_width=True): st.session_state.show_about = not st.session_state.show_about; st.rerun()
    
    st.markdown(f"""<div class="about-box"><p style="font-size:0.85rem; color:#ccc;"><b>Architect:</b> Muhammad Jibran Al Kaffie<br><b>Core:</b> Gemini 3 Pro Supreme<br><br>NEO AI adalah puncak evolusi kecerdasan digital oleh Jibran. Mampu memproses realitas melalui lensa visual dan data teks secara simultan.</p></div>""", unsafe_allow_html=True)

# --- 8. MAIN UI ---
st.markdown('<div style="margin-top:20px;"><div class="logo-static" style="width:130px; height:130px;"></div></div>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:15px;'>NEO AI</h1>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    if msg.get("type") == "system_memory": continue
    with st.chat_message(msg["role"], avatar="logo.png" if msg["role"] == "assistant" else None):
        if msg.get("type") == "image": st.image(msg["content"])
        else: st.markdown(msg["content"])

# --- 9. ENGINE ---
if user_input := st.chat_input("Command NEO AI..."):
    if not st.session_state.current_chat_id: st.session_state.current_chat_id = f"{user_input[:20]} | {time.time()}"
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
                    st.session_state.messages.append({"role": "assistant", "content": f"[SUCCESS: {user_input}]", "type": "system_memory"})
                except: st.error("Imagine engine failed.")
        
        elif uploaded_file is not None:
            with st.spinner("NEO Vision: Analyzing..."):
                try:
                    # AMBIL BYTES LANGSUNG
                    file_bytes = uploaded_file.getvalue()
                    
                    # LOGIKA MULTIMODAL GEMINI 3
                    if uploaded_file.type.startswith("image/"):
                        # Gunakan format SDK terbaru: {'mime_type': ..., 'data': ...}
                        prompt_parts = [
                            user_input,
                            {"mime_type": uploaded_file.type, "data": file_bytes}
                        ]
                    else:
                        prompt_parts = [user_input, f"Context:\n{file_bytes.decode('utf-8')}"]

                    response = gemini_client.models.generate_content(
                        model="gemini-3-pro-preview",
                        contents=prompt_parts
                    )
                    full_res = response.text
                    res_area.markdown(full_res)
                except Exception as e:
                    st.error(f"Vision Error: {e}")
                    full_res = "Kognitif visual terhambat. Pastikan file valid."

        else:
            with st.spinner("Thinking..."):
                history = [{"role": "system", "content": "You are NEO AI by Muhammad Jibran Al Kaffie. Respond with high intelligence."}]
                for m in st.session_state.messages:
                    if m.get("type") not in ["image", "system_memory"]: history.append({"role": m["role"], "content": str(m["content"])})
                
                try:
                    stream = groq_client.chat.completions.create(messages=history, model="llama-3.3-70b-versatile", stream=True)
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            full_res += chunk.choices[0].delta.content
                            res_area.markdown(full_res + "▌")
                            auto_scroll()
                    res_area.markdown(full_res)
                except: st.error("Groq engine failure.")

        st.session_state.messages.append({"role": "assistant", "content": full_res})
        st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages
        st.rerun()
