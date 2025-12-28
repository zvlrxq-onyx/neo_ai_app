import streamlit as st
from groq import Groq
import time
import os
import base64
import requests

# --- 1. INITIALIZE SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "all_chats" not in st.session_state:
    st.session_state.all_chats = {}
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "imagine_mode" not in st.session_state:
    st.session_state.imagine_mode = False
if "show_about" not in st.session_state:
    st.session_state.show_about = False
if "sidebar_visible" not in st.session_state:
    st.session_state.sidebar_visible = False

# --- 2. CONFIG API ---
try:
    # Pastikan Anda sudah setting GROQ_API_KEY di .streamlit/secrets.toml atau Secrets Streamlit Cloud
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except Exception:
    st.error("API Key Groq missing! Set 'GROQ_API_KEY' in your secrets.")
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

# --- 5. THE SUPREME CSS (SMOOTH, SEAMLESS, NO FLICKER) ---
def get_ultimate_css():
    neon_cyan = "#00ffff"
    sidebar_pos = "0px" if st.session_state.sidebar_visible else "-360px"
    return f"""
    <style>
    html, body, [data-testid="stAppViewContainer"] {{ 
        background-color: #050505 !important; 
        color: #f0f0f0 !important; 
    }}
    [data-testid="stStatusWidget"], header, footer {{ visibility: hidden; }}

    /* SIDEBAR TRANSITION 0.7s - SEAMLESS & NO FLICKER */
    [data-testid="stSidebar"] {{
        position: fixed !important; 
        left: {sidebar_pos} !important; 
        width: 350px !important;
        background-color: #0a0a0a !important; 
        border-right: 1px solid {neon_cyan}33 !important;
        transition: left 0.7s cubic-bezier(0.19, 1, 0.22, 1) !important;
        z-index: 1000000 !important; 
        display: block !important; 
        visibility: visible !important;
    }}

    /* HAMBURGER BUTTON */
    .stButton > button[key="hamburger_fixed"] {{
        position: fixed; top: 20px; left: 20px; z-index: 2000001 !important;
        background: rgba(0,0,0,0.9) !important; 
        border: 2px solid {neon_cyan}44 !important;
        border-radius: 50% !important; 
        width: 50px !important; 
        height: 50px !important; 
        color: {neon_cyan} !important;
        display: flex; align-items: center; justify-content: center;
    }}
    
    /* HOVER EFFECTS */
    [data-testid="stSidebarContent"] .stButton > button {{
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    }}
    [data-testid="stSidebarContent"] .stButton > button:hover {{
        transform: scale(1.02) !important; 
        border-color: {neon_cyan} !important;
        box-shadow: 0 0 15px {neon_cyan}44 !important;
    }}

    /* LOGO STATIC & GLOW */
    .logo-static {{ 
        width: 130px; height: 130px; margin: 0 auto; 
        background-image: url("{logo_html}"); 
        background-size: cover; 
        border-radius: 50%; 
        border: 3px solid {neon_cyan};
        box-shadow: 0 0 20px {neon_cyan}33;
    }}

    .about-box {{
        max-height: {"1000px" if st.session_state.show_about else "0px"};
        opacity: {"1" if st.session_state.show_about else "0"};
        overflow: hidden; 
        transition: all 0.8s cubic-bezier(0.19, 1, 0.22, 1);
        padding: {"20px" if st.session_state.show_about else "0px"};
        background: rgba(255,255,255,0.03); 
        border-radius: 15px;
    }}
    </style>
    """
st.markdown(get_ultimate_css(), unsafe_allow_html=True)

# --- 6. HAMBURGER BUTTON ---
if st.button("☰", key="hamburger_fixed"):
    st.session_state.sidebar_visible = not st.session_state.sidebar_visible
    st.rerun()

# --- 7. SIDEBAR CONTENT ---
with st.sidebar:
    st.markdown('<div style="height: 60px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="logo-static" style="width:100px; height:100px;"></div>', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:cyan;'>NEO CONTROL</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    # DATA SOURCE
    st.markdown("### 📄 DATA SOURCE")
    uploaded_doc = st.file_uploader("Upload file (.txt, .py, .md)", type=["txt", "py", "md"])
    doc_content = ""
    if uploaded_doc:
        try:
            doc_content = uploaded_doc.getvalue().decode("utf-8")
            st.success(f"✅ {uploaded_doc.name} Loaded!")
        except:
            st.error("Gagal membaca file.")

    st.markdown("---")
    if st.button("➕ NEW SESSION", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()
    
    # Toggle Mode Imagine
    label_mode = "🎨 IMAGINE: ON" if st.session_state.imagine_mode else "🖼️ MODE: CHAT"
    if st.button(label_mode, use_container_width=True):
        st.session_state.imagine_mode = not st.session_state.imagine_mode
        st.rerun()

    if st.button("ℹ️ SYSTEM INFO", use_container_width=True):
        st.session_state.show_about = not st.session_state.show_about
        st.rerun()

    st.markdown(f"""<div class="about-box"><p style="font-size:0.8rem; color:#ccc;"><b>Architect:</b> Muhammad Jibran Al Kaffie<br><b>Engine:</b> NEO Engine 3.3 Stable</p></div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🕒 RECENT CHATS")
    for cid in reversed(list(st.session_state.all_chats.keys())):
        display_name = cid.split(" | ")[0]
        if st.button(display_name, key=f"h_{cid}", use_container_width=True):
            st.session_state.messages = st.session_state.all_chats[cid]
            st.session_state.current_chat_id = cid
            st.rerun()

# --- 8. MAIN UI DISPLAY ---
st.markdown('<div style="margin-top:20px;"><div class="logo-static"></div></div>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:15px;'>NEO AI</h1>", unsafe_allow_html=True)

# Loop Chat (Menampilkan pesan di UI)
for msg in st.session_state.messages:
    if msg.get("type") == "system_memory":
        continue  # Jangan tampilkan memori internal ke user
    
    with st.chat_message(msg["role"], avatar="logo.png" if msg["role"] == "assistant" else None):
        if msg.get("type") == "image":
            # Pastikan content adalah bytes atau URL yang valid
            st.image(msg["content"], use_container_width=True)
        else:
            st.markdown(msg["content"])

# --- 9. ENGINE (LOGIC CHAT & IMAGINE) ---
if user_input := st.chat_input("Command NEO AI..."):
    if st.session_state.current_chat_id is None:
        st.session_state.current_chat_id = f"{user_input[:20]}... | {time.time()}"
    
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.rerun()

# Memproses respon asisten
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_user_msg = st.session_state.messages[-1]["content"]
    
    with st.chat_message("assistant", avatar="logo.png"):
        
        # --- A. JIKA MODE IMAGINE AKTIF ---
        if st.session_state.imagine_mode:
            with st.spinner("Visualizing your imagination..."):
                try:
                    query = last_user_msg.replace(' ', '%20')
                    img_url = f"https://image.pollinations.ai/prompt/{query}?width=1024&height=1024&nologo=true"
                    r = requests.get(img_url, timeout=30)
                    
                    if r.status_code == 200:
                        st.image(r.content, use_container_width=True)
                        # Simpan gambar ke history
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": r.content, 
                            "type": "image"
                        })
                        # Simpan memori rahasia agar AI "tahu" dia baru saja menggambar ini
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": f"[SYSTEM_MEMORI: Kamu baru saja menggambar '{last_user_msg}'.]", 
                            "type": "system_memory"
                        })
                    else:
                        st.error("Gagal menjangkau server gambar.")
                except Exception as e:
                    st.error(f"Error Imaging: {e}")
        
        # --- B. JIKA MODE CHAT AKTIF ---
        else:
            res_area = st.empty()
            full_res = ""
            
            # Filter history: Hapus data biner (gambar) agar tidak error saat dikirim ke Groq
            # Kita ubah system_memory menjadi instruksi teks agar AI nyambung
            clean_history = []
            for m in st.session_state.messages:
                if m.get("type") == "image":
                    continue
                
                # Masukkan konten teks saja
                content_text = str(m["content"])
                clean_history.append({"role": m["role"], "content": content_text})
            
            # Injeksi Dokumen jika ada
            if doc_content and clean_history:
                clean_history[-1]["content"] = f"KONTEKS FILE:\n{doc_content}\n\nPERTANYAAN USER: {last_user_msg}"

            sys_instruction = (
                "You are NEO AI by Muhammad Jibran Al Kaffie. Respond professionally and futuristically. "
                "You are aware of everything you have done in this session. If you previously generated an image, "
                "and the user asks about it, answer based on the '[SYSTEM_MEMORI]' notes in the history."
            )

            try:
                stream = client.chat.completions.create(
                    messages=[{"role": "system", "content": sys_instruction}] + clean_history,
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
                st.error(f"Groq Engine Error: {e}")

    # Update Global Chat History & Sync
    st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages
    st.rerun()
