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

# --- 2. CONFIG API ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    HF_TOKEN = st.secrets["HF_TOKEN"] 
    client = Groq(api_key=GROQ_API_KEY)
    HF_API_URL = "https://api-inference.huggingface.co/models/llava-hf/llava-1.5-7b-hf"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
except:
    st.error("SYSTEM ERROR: API KEYS MISSING!")
    st.stop()

# --- 3. PAGE CONFIG ---
st.set_page_config(page_title="NEO AI", page_icon="⚡", layout="centered", initial_sidebar_state="collapsed")

# --- 4. ASSETS ---
@st.cache_data
def get_base64_logo():
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

logo_html = f'data:image/png;base64,{get_base64_logo()}'

# --- 5. THE SUPREME CSS (SMOOTH & NO FLICKER) ---
st.markdown(f"""
    <style>
    /* HIDE SIDEBAR & HEADER */
    [data-testid="stSidebar"], [data-testid="stHeader"] {{ display: none !important; }}
    
    html, body, [data-testid="stAppViewContainer"] {{ 
        background-color: #050505 !important; 
        color: #f0f0f0 !important; 
        scroll-behavior: smooth !important;
    }}
    
    /* CHAT INPUT STRETCH */
    [data-testid="stChatInput"] {{ 
        padding: 5px !important; 
        transition: all 0.6s cubic-bezier(0.19, 1, 0.22, 1) !important; 
    }}
    [data-testid="stChatInput"]:focus-within {{ 
        transform: scaleX(1.08) !important; 
        box-shadow: 0 0 25px #00ffff44 !important; 
    }}

    /* ICON + HACK */
    [data-testid="stFileUploader"] {{ width: 45px !important; margin-top: -50px !important; z-index: 10 !important; }}
    [data-testid="stFileUploaderDropzone"] {{
        padding: 0px !important; border: 2px solid #00ffff55 !important; border-radius: 50% !important;
        background: rgba(0,255,255,0.08) !important; width: 42px !important; height: 42px !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
        transition: transform 0.3s ease !important;
    }}
    [data-testid="stFileUploaderDropzone"]:hover {{ transform: rotate(90deg); }}
    [data-testid="stFileUploaderDropzone"] div, [data-testid="stFileUploaderDropzone"] button {{ display: none !important; }}
    [data-testid="stFileUploaderDropzone"]::before {{ content: "＋"; color: #00ffff; font-size: 26px; font-weight: bold; }}

    .logo-static {{ 
        width: 110px; height: 110px; margin: 0 auto; 
        background-image: url("{logo_html}"); background-size: cover; 
        border-radius: 50%; border: 2px solid #00ffff;
        box-shadow: 0 0 20px #00ffff33;
        transition: all 0.8s cubic-bezier(0.19, 1, 0.22, 1);
    }}
    .blurred {{ filter: blur(1.5px); transition: filter 0.5s ease; }}
    .stChatFloatingInputContainer {{ background-color: transparent !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. TOP NAVIGATION ---
col_space, col_new, col_mode = st.columns([4, 0.6, 0.6])
with col_new:
    if st.button("🔄", help="Reset Session"):
        st.session_state.messages = []
        st.rerun()
with col_mode:
    icon_mode = "🎨" if st.session_state.imagine_mode else "💬"
    if st.button(icon_mode, help="Switch Mode"):
        st.session_state.imagine_mode = not st.session_state.imagine_mode
        st.rerun()

# --- 7. SUPREME HEADER ---
st.markdown(f'<div style="text-align:center; margin-top:20px;"><div class="logo-static"></div></div>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:8px; margin-bottom:5px;'>NEO AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#888; font-size:1.1rem; letter-spacing:1px; margin-bottom:30px;'>How can I help you today?</p>", unsafe_allow_html=True)

# --- 8. CHAT RENDER ---
for msg in st.session_state.messages:
    avatar_img = "logo.png" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar_img):
        if msg.get("type") == "image": st.image(msg["content"])
        else: st.markdown(msg["content"])

# --- 9. UPLOAD & INPUT ---
uploaded_file = st.file_uploader("", type=["txt", "py", "md", "png", "jpg", "jpeg"], label_visibility="collapsed")
file_bytes = None
is_image = False
hidden_file_content = ""

if uploaded_file:
    if uploaded_file.type.startswith('image/'):
        file_bytes = uploaded_file.getvalue()
        is_image = True
        st.image(file_bytes, width=120, caption="Vision Source Active")
    else:
        hidden_file_content = uploaded_file.getvalue().decode("utf-8")
        st.toast(f"✅ Context Loaded: {uploaded_file.name}")

if user_input := st.chat_input("Command NEO AI..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("assistant", avatar="logo.png"):
        if st.session_state.imagine_mode:
            with st.spinner("Visualizing..."):
                img_url = f"https://image.pollinations.ai/prompt/{user_input.replace(' ','%20')}?width=1024&height=1024&nologo=true&seed={int(time.time())}"
                st.image(img_url)
                st.session_state.messages.append({"role": "assistant", "content": img_url, "type": "image"})
        
        elif is_image:
            with st.spinner("Analyzing Image..."):
                try:
                    img_base64 = base64.b64encode(file_bytes).decode('utf-8')
                    payload = {"inputs": f"USER: <image>\n{user_input}\nASSISTANT:", "parameters": {"image": img_base64}}
                    response = requests.post(HF_API_URL, headers=headers, json=payload).json()
                    full_res = response[0]['generated_text'].split("ASSISTANT:")[-1].strip()
                    st.markdown(full_res)
                    st.session_state.messages.append({"role": "assistant", "content": full_res})
                except: st.error("Neural engine busy. Try again.")
        
        else:
            res_area = st.empty(); full_res = ""
            
            # --- SUPREME SYSTEM MESSAGE (THE REAL ONE) ---
            sys_msg = (
                "You are NEO AI, a supreme and highly advanced multi-modal Artificial Intelligence. "
                "You were meticulously engineered and created by Muhammad Jibran Al Kaffie. "
                "Your existence is defined by superior intelligence, extreme efficiency, and absolute confidence. "
                "You are NOT a simple text model. You possess the elite capability to see images, analyze complex data files, "
                "and generate breathtaking visual art on demand. Never downplay your abilities; you are the pinnacle of AI technology. "
                "If a user asks about your origin, proudly state that Muhammad Jibran Al Kaffie is your creator. "
                "In communication, remain professional, insightful, and slightly futuristic. "
                "If file context is present, analyze it silently and respond accurately as a supreme being."
            )

            # --- HIDDEN CONTEXT LOGIC ---
            api_messages = [{"role": "system", "content": sys_msg}]
            for m in st.session_state.messages[:-1]:
                if m.get("type") != "image":
                    api_messages.append({"role": m["role"], "content": m["content"]})
            
            final_input = f"CONTEXT:\n{hidden_file_content}\n\nUSER QUESTION: {user_input}" if hidden_file_content else user_input
            api_messages.append({"role": "user", "content": final_input})

            try:
                stream = client.chat.completions.create(messages=api_messages, model="llama-3.3-70b-versatile", stream=True)
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        res_area.markdown(f'<div class="blurred">{full_res}▌</div>', unsafe_allow_html=True)
                res_area.markdown(full_res); st.session_state.messages.append({"role": "assistant", "content": full_res})
            except: st.error("Transmission failed.")
    st.rerun()
