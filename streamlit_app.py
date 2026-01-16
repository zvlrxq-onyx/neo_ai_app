import streamlit as st
from groq import Groq
from huggingface_hub import InferenceClient
import os, base64, requests, json
import re
from PIL import Image
import io
import urllib.parse
import time
import hashlib

# --- 1. CONFIG & SYSTEM SETUP ---
st.set_page_config(page_title="Azura AI", page_icon="🌐", layout="wide")

DB_FOLDER = "azura_users_db"
if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER)

def get_user_db_file(username):
    user_hash = hashlib.md5(username.encode()).hexdigest()
    return os.path.join(DB_FOLDER, f"user_{user_hash}.json")

def load_history_from_db(username):
    db_file = get_user_db_file(username)
    if os.path.exists(db_file):
        try:
            with open(db_file, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_history_to_db(username, history_dict):
    db_file = get_user_db_file(username)
    try:
        with open(db_file, "w") as f:
            json.dump(history_dict, f)
    except Exception as e:
        print(f"Gagal save db: {e}")

# --- 2. AUTHENTICATION ---
if "current_user" not in st.session_state:
    st.session_state.current_user = None

if st.session_state.current_user is None:
    st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; height: 80vh;">
        <div style="background: linear-gradient(135deg, #001a1a 0%, #003333 100%); 
                    padding: 50px; border-radius: 20px; border: 2px solid #00ffff; 
                    box-shadow: 0 0 30px rgba(0,255,255,0.4); text-align: center; width: 400px;">
            <h1 style="color: #00ffff; margin-bottom: 10px;">🌐 Azura AI</h1>
            <p style="color: #888; margin-bottom: 30px;">Secure Multi-Modal AI Assistant</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        u_input = st.text_input("Enter Username", key="login_username")
        if st.button("🚀 Enter Azura AI", use_container_width=True):
            if u_input.strip():
                st.session_state.current_user = u_input.strip()
                st.rerun()
    st.stop()

# --- 3. SESSION & API INIT ---
if "all_chats" not in st.session_state:
    st.session_state.all_chats = load_history_from_db(st.session_state.current_user)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

try:
    client_groq = Groq(api_key=st.secrets["GROQ_API_KEY"])
    client_hf = InferenceClient(token=st.secrets["HF_TOKEN"])
    POLLINATIONS_API = "https://image.pollinations.ai/prompt/"
except Exception as e:
    st.error("❌ API Keys Missing!")
    st.stop()

# --- 4. CSS CUSTOM UI ---
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background: #050505; }
    [data-testid="stFileUploader"] { position: fixed; bottom: 58px; left: 15px; width: 45px; z-index: 1000; }
    [data-testid="stFileUploaderDropzone"] {
        background: #00ffff11 !important; border: 1px solid #00ffff44 !important; border-radius: 50% !important;
        height: 42px !important; width: 42px !important; padding: 0 !important;
    }
    [data-testid="stFileUploaderDropzone"] div { display: none !important; }
    [data-testid="stFileUploaderDropzone"]::before {
        content: "＋"; color: #00ffff; font-size: 26px; display: flex; align-items: center; justify-content: center; height: 100%;
    }
    [data-testid="stChatInput"] { margin-left: 60px !important; }
    .stStatus { background: #001a1a !important; border: 1px solid #00ffff44 !important; }
</style>
""", unsafe_allow_html=True)

# --- 5. RENDER FUNCTIONS ---
def render_chat_bubble(role, content):
    if role == "user":
        st.markdown(f'<div style="text-align: right; color: #00ffff; margin-bottom: 10px;"><b>You</b><br>{content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="text-align: left; color: #e9edef; margin-bottom: 10px;"><b>Azura AI</b><br>{content}</div>', unsafe_allow_html=True)

# --- 6. SIDEBAR ---
with st.sidebar:
    st.title("🌐 Azura AI")
    st.info(f"User: {st.session_state.current_user}")
    engine = st.selectbox("Select Engine", ["Azura-DeepSeek R1", "Azura-Llama (Power)", "Azura-Art (Draw)"])
    if st.button("＋ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- 7. CHAT RENDER ---
for msg in st.session_state.messages:
    if msg.get("type") == "image": st.image(msg["content"])
    else: render_chat_bubble(msg["role"], msg["content"])

# --- 8. LOGIC INPUT ---
up = st.file_uploader("", type=["png","jpg","jpeg"], label_visibility="collapsed")
if up: st.session_state.uploaded_image = up.getvalue()

if prompt := st.chat_input("Message Azura..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# --- 9. AI ENGINE (DEEPSEEK R1 LOGIC) ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    user_msg = st.session_state.messages[-1]["content"]
    
    if engine == "Azura-DeepSeek R1":
        MODEL_ID = "deepseek-ai/DeepSeek-R1-Distill-Llama-70B"
        status_box = st.status("🚀 [SYSTEM] Initializing Engine...", expanded=True)
        
        with status_box:
            st.write("`[LOGIC] Connecting to DeepSeek Inference Server...`")
            log_placeholder = st.empty()
        
        answer_placeholder = st.empty()
        full_buffer = ""
        final_answer = ""
        is_thinking = True

        try:
            stream = client_hf.chat_completion(
                model=MODEL_ID,
                messages=[{"role": "user", "content": user_msg}],
                max_tokens=4000,
                temperature=0.6,
                stream=True
            )

            for chunk in stream:
                token = chunk.choices[0].delta.content
                if token:
                    full_buffer += token
                    
                    if "</think>" in full_buffer and is_thinking:
                        is_thinking = False
                        status_box.update(label="✅ [SYSTEM] Analysis Complete", state="complete", expanded=False)
                        parts = full_buffer.split("</think>")
                        final_answer = parts[1] if len(parts) > 1 else ""
                    
                    if is_thinking:
                        # TERMINAL STYLE LOGGING
                        clean_think = full_buffer.replace("<think>", "")
                        lines = clean_think.split('\n')
                        log_text = ""
                        for i, line in enumerate(lines[-8:]): # Ambil 8 baris terakhir agar tidak kepanjangan
                            if line.strip():
                                prefix = "[THINK]" if i % 2 == 0 else "[LOGIC]"
                                log_text += f"{prefix} {line.strip()}\n"
                        log_placeholder.code(log_text, language="ini")
                    else:
                        # Stream jawaban utama ke UI
                        if "</think>" in full_buffer:
                            final_answer = full_buffer.split("</think>")[1]
                        else:
                            final_answer += token
                        answer_placeholder.markdown(final_answer + "▌")

            res = final_answer.strip()
            st.session_state.messages.append({"role": "assistant", "content": res})
            # Save History
            session_id = st.session_state.messages[0]["content"][:20]
            st.session_state.all_chats[session_id] = st.session_state.messages
            save_history_to_db(st.session_state.current_user, st.session_state.all_chats)
            st.rerun()

        except Exception as e:
            status_box.update(label="❌ [SYSTEM] Error Occurred", state="error")
            st.error(f"API Error: {str(e)}")

    elif engine == "Azura-Art (Draw)":
        with st.spinner("🎨 Generating Art..."):
            encoded = urllib.parse.quote(user_msg)
            img_url = f"{POLLINATIONS_API}{encoded}"
            img_res = requests.get(img_url)
            img = Image.open(io.BytesIO(img_res.content))
            st.session_state.messages.append({"role": "assistant", "type": "image", "content": img})
            st.rerun()
