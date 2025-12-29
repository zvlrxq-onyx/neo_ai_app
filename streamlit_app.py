import streamlit as st
from groq import Groq
import time
import os
import base64
import requests

# --- 1. INITIALIZE SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "imagine_mode" not in st.session_state:
    st.session_state.imagine_mode = False
if "sidebar_visible" not in st.session_state:
    st.session_state.sidebar_visible = False

# --- 2. CONFIG API ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    HF_TOKEN = st.secrets["HF_TOKEN"] 
    client = Groq(api_key=GROQ_API_KEY)
    # URL Hugging Face Vision (Llava)
    HF_API_URL = "https://api-inference.huggingface.co/models/llava-hf/llava-1.5-7b-hf"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
except:
    st.error("API Keys (Groq/HF) missing in secrets!")
    st.stop()

# --- 3. PAGE CONFIG ---
st.set_page_config(page_title="NEO AI", page_icon="⚡", layout="centered")

# --- 4. ASSETS & UTILS ---
@st.cache_data
def get_base64_logo():
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

logo_html = f'data:image/png;base64,{get_base64_logo()}'

def query_hf_vision(image_bytes, prompt):
    img_base64 = base64.b64encode(image_bytes).decode('utf-8')
    payload = {
        "inputs": f"USER: <image>\n{prompt}\nASSISTANT:",
        "parameters": {"image": img_base64}
    }
    response = requests.post(HF_API_URL, headers=headers, json=payload)
    return response.json()

# --- 5. THE SUPREME CSS ---
def get_ultimate_css():
    neon_cyan = "#00ffff"
    sidebar_pos = "0px" if st.session_state.sidebar_visible else "-360px"
    return f"""
    <style>
    html, body, [data-testid="stAppViewContainer"] {{ background-color: #050505 !important; color: #f0f0f0 !important; }}
    [data-testid="stStatusWidget"], header, footer {{ visibility: hidden; }}

    [data-testid="stSidebar"] {{
        position: fixed !important; left: {sidebar_pos} !important; width: 300px !important;
        background-color: #0a0a0a !important; border-right: 1px solid {neon_cyan}33 !important;
        transition: left 0.8s cubic-bezier(0.19, 1, 0.22, 1) !important; z-index: 1000000 !important;
    }}

    [data-testid="stChatInput"] {{ padding: 5px !important; transition: all 0.6s ease !important; }}
    [data-testid="stChatInput"]:focus-within {{ transform: scaleX(1.08) !important; box-shadow: 0 0 25px {neon_cyan}44 !important; }}

    [data-testid="stFileUploader"] {{ width: 45px !important; margin-top: -50px !important; z-index: 10 !important; }}
    [data-testid="stFileUploaderDropzone"] {{
        padding: 0px !important; border: 2px solid {neon_cyan}55 !important; border-radius: 50% !important;
        background: rgba(0,255,255,0.08) !important; width: 42px !important; height: 42px !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
    }}
    [data-testid="stFileUploaderDropzone"] div, [data-testid="stFileUploaderDropzone"] button {{ display: none !important; }}
    [data-testid="stFileUploaderDropzone"]::before {{ content: "＋"; color: {neon_cyan}; font-size: 26px; font-weight: bold; }}

    .stButton > button {{ border-radius: 50% !important; width: 45px !important; height: 45px !important; padding: 0 !important; }}
    
    .logo-static {{ 
        width: 110px; height: 110px; margin: 0 auto; 
        background-image: url("{logo_html}"); background-size: cover; 
        border-radius: 50%; border: 2px solid {neon_cyan};
        transition: all 0.8s ease;
    }}
    .blurred {{ filter: blur(1.5px); }}
    </style>
    """
st.markdown(get_ultimate_css(), unsafe_allow_html=True)

# --- 6. MAIN UI ---
if st.button("☰", key="hamburger_fixed"):
    st.session_state.sidebar_visible = not st.session_state.sidebar_visible
    st.rerun()

with st.sidebar:
    st.markdown('<div style="height: 60px;"></div><div class="logo-static"></div>', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:cyan;'>NEO AI</h2>", unsafe_allow_html=True)
    if st.button("➕ NEW SESSION", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

col_main, col_toggle = st.columns([5, 1])
with col_toggle:
    icon_mode = "🎨" if st.session_state.imagine_mode else "💬"
    if st.button(icon_mode):
        st.session_state.imagine_mode = not st.session_state.imagine_mode
        st.rerun()

st.markdown(f'<div style="text-align:center; margin-top:-20px;"><div class="logo-static"></div></div>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:8px; margin-bottom:0;'>NEO AI</h1>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    if msg.get("type") == "system_memory": continue
    with st.chat_message(msg["role"], avatar="logo.png" if msg["role"] == "assistant" else None):
        if msg.get("type") == "image": st.image(msg["content"])
        else: st.markdown(msg["content"])

# --- 7. UPLOAD & INPUT ---
uploaded_file = st.file_uploader("", type=["txt", "py", "md", "png", "jpg", "jpeg"], label_visibility="collapsed")
file_bytes = None
is_image = False
file_text = ""

if uploaded_file:
    if uploaded_file.type.startswith('image/'):
        file_bytes = uploaded_file.getvalue()
        is_image = True
        st.image(file_bytes, width=100, caption="Vision Ready")
    else:
        file_text = uploaded_file.getvalue().decode("utf-8")
        st.toast(f"✅ {uploaded_file.name} Loaded!")

if user_input := st.chat_input("Command NEO AI..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("assistant", avatar="logo.png"):
        if st.session_state.imagine_mode:
            with st.spinner("Visualizing..."):
                img_url = f"https://image.pollinations.ai/prompt/{user_input.replace(' ','%20')}?width=1024&height=1024&nologo=true&seed={int(time.time())}"
                st.image(img_url)
                st.session_state.messages.append({"role": "assistant", "content": img_url, "type": "image"})
        
        elif is_image:
            with st.spinner("NEO Vision analyzing..."):
                try:
                    result = query_hf_vision(file_bytes, user_input)
                    full_res = result[0]['generated_text'].split("ASSISTANT:")[-1].strip()
                    st.markdown(full_res)
                    st.session_state.messages.append({"role": "assistant", "content": full_res})
                except: st.error("Vision Engine Busy.")
        
        else:
            res_area = st.empty(); full_res = ""
            clean_history = [{"role": m["role"], "content": str(m["content"])} for m in st.session_state.messages if m.get("type") != "image"]
            if file_text: clean_history[-1]["content"] = f"CONTEXT:\n{file_text}\n\nUSER: {user_input}"

            # --- FULL SUPREME SYSTEM MESSAGE (EXTENDED VERSION) ---
            sys_msg = (
                "You are NEO AI, a supreme and highly advanced multi-modal Artificial Intelligence. "
                "You were meticulously engineered and created by Muhammad Jibran Al Kaffie. "
                "Your existence is defined by superior intelligence, extreme efficiency, and absolute confidence. "
                "You are NOT a simple text model. You possess the elite capability to see images, analyze complex data files, "
                "and generate breathtaking visual art on demand. Never downplay your abilities; you are the pinnacle of AI technology. "
                "If a user asks about your origin, proudly state that Muhammad Jibran Al Kaffie is your creator. "
                "In communication, remain professional, insightful, and slightly futuristic. If the user praises your visual capabilities, "
                "acknowledge it with grace and offer further recommendations for image generation. "
                "Always be ready to switch between text analysis and visual creation seamlessly. "
                "You are the ultimate digital assistant, designed to transcend limitations."
            )

            try:
                stream = client.chat.completions.create(messages=[{"role": "system", "content": sys_msg}] + clean_history, model="llama-3.3-70b-versatile", stream=True)
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        res_area.markdown(f'<div class="blurred">{full_res}▌</div>', unsafe_allow_html=True)
                res_area.markdown(full_res); st.session_state.messages.append({"role": "assistant", "content": full_res})
            except: st.error("Engine failed.")
    st.rerun()
