import streamlit as st
from groq import Groq
import google.generativeai as genai
import time
import os
import base64
import requests
from PIL import Image

# --- 1. INITIALIZE SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "all_chats" not in st.session_state:
    st.session_state.all_chats = {}
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "imagine_mode" not in st.session_state:
    st.session_state.imagine_mode = False
if "sidebar_visible" not in st.session_state:
    st.session_state.sidebar_visible = False

# --- 2. CONFIG API (GROQ & GEMINI) ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    
    # Init Groq
    client = Groq(api_key=GROQ_API_KEY)
    
    # Init Gemini (Dibuat lebih kuat)
    genai.configure(api_key=GEMINI_API_KEY)
    # Kita pakai gemini-1.5-flash sebagai standar paling stabil saat ini
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"❌ Konfigurasi API Gagal: {e}")
    st.stop()

# --- 3. PAGE CONFIG ---
st.set_page_config(page_title="NEO AI", page_icon="⚡", layout="centered")

# --- 4. CSS SUPREME (Smooth & Futuristic) ---
def get_ultimate_css():
    neon_cyan = "#00ffff"
    sidebar_pos = "0px" if st.session_state.sidebar_visible else "-360px"
    return f"""
    <style>
    html, body, [data-testid="stAppViewContainer"] {{ background-color: #050505 !important; color: #f0f0f0 !important; }}
    [data-testid="stStatusWidget"], header, footer {{ visibility: hidden; }}
    
    /* Sidebar Animation */
    [data-testid="stSidebar"] {{
        position: fixed !important; left: {sidebar_pos} !important; width: 350px !important;
        background-color: #0a0a0a !important; border-right: 1px solid {neon_cyan}33 !important;
        transition: left 0.5s cubic-bezier(0.4, 0, 0.2, 1) !important; z-index: 1000000 !important;
        visibility: visible !important; display: block !important;
    }}
    
    /* Hamburger Menu */
    .stButton > button[key="hamburger"] {{
        position: fixed; top: 20px; left: 20px; z-index: 2000000 !important;
        background: rgba(0,0,0,0.8) !important; border: 1px solid {neon_cyan} !important;
        color: {neon_cyan} !important; border-radius: 10px; width: 45px; height: 45px;
    }}
    
    /* Chat Bubble Styling */
    .stChatMessage {{ border-radius: 15px; margin-bottom: 10px; border: 1px solid #222; }}
    </style>
    """
st.markdown(get_ultimate_css(), unsafe_allow_html=True)

# --- 5. SIDEBAR & NAVIGATION ---
if st.button("☰", key="hamburger"):
    st.session_state.sidebar_visible = not st.session_state.sidebar_visible
    st.rerun()

with st.sidebar:
    st.markdown("<h2 style='text-align:center; color:cyan;'>NEO CONTROL</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Upload Gambar di Sidebar
    st.markdown("### 📷 Vision Input")
    uploaded_file = st.file_uploader("Upload gambar untuk dianalisis", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        st.image(uploaded_file, caption="Gambar Terdeteksi", use_container_width=True)
    
    st.markdown("---")
    if st.button("➕ NEW SESSION", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()
    
    mode_text = "🎨 IMAGINE: ON" if st.session_state.imagine_mode else "🖼️ MODE: CHAT"
    if st.button(mode_text, use_container_width=True):
        st.session_state.imagine_mode = not st.session_state.imagine_mode
        st.rerun()

# --- 6. MAIN UI ---
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:10px;'>NEO AI</h1>", unsafe_allow_html=True)

# Menampilkan chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "image":
            st.image(msg["content"], use_container_width=True)
        else:
            st.markdown(msg["content"])

# --- 7. CHAT LOGIC (DUAL ENGINE) ---
if user_input := st.chat_input("Tanya apa saja ke NEO AI..."):
    # Set Chat ID jika baru
    if st.session_state.current_chat_id is None:
        st.session_state.current_chat_id = f"{user_input[:15]}... | {time.time()}"
    
    # Simpan pesan user
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.rerun()

# Proses Response
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_user_msg = st.session_state.messages[-1]["content"]
    
    with st.chat_message("assistant"):
        # A. VISION ENGINE (Jika ada gambar)
        if uploaded_file is not None:
            with st.spinner("NEO AI sedang memproses gambar..."):
                try:
                    img = Image.open(uploaded_file)
                    # Memanggil Gemini
                    response = gemini_model.generate_content([last_user_msg, img])
                    answer = response.text
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.error(f"⚠️ Gemini Error: {str(e)}")
                    st.info("Tips: Coba cek API Key Gemini atau ganti format gambar.")
        
        # B. IMAGINE ENGINE (Generate Gambar)
        elif st.session_state.imagine_mode:
            with st.spinner("Sedang melukis..."):
                try:
                    query = last_user_msg.replace(' ', '%20')
                    img_url = f"https://image.pollinations.ai/prompt/{query}?width=1024&height=1024&nologo=true"
                    img_data = requests.get(img_url).content
                    st.image(img_data, use_container_width=True)
                    st.session_state.messages.append({"role": "assistant", "content": img_data, "type": "image"})
                except:
                    st.error("Gagal membuat gambar.")

        # C. CHAT ENGINE (Groq Llama 3.3)
        else:
            res_area = st.empty()
            full_res = ""
            
            # Filter history untuk Groq (tidak bisa kirim file gambar mentah)
            chat_history = []
            for m in st.session_state.messages:
                if m.get("type") != "image":
                    chat_history.append({"role": m["role"], "content": m["content"]})
            
            try:
                stream = client.chat.completions.create(
                    messages=[{"role": "system", "content": "You are NEO AI, a helpful and futuristic assistant."}] + chat_history,
                    model="llama-3.3-70b-versatile",
                    stream=True
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        res_area.markdown(full_res + "▌")
                res_area.markdown(full_res)
                st.session_state.messages.append({"role": "assistant", "content": full_res})
            except Exception as e:
                st.error(f"Groq Error: {e}")

    # Simpan ke memori sesi
    st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages
    st.rerun()
