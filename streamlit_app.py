<think>
Pertama, pengguna memberikan feedback teknis yang sangat detail tentang dua masalah krusial dalam kode NEO AI:


## Reviewing User Feedback  
- User provided detailed technical feedback on two critical issues in NEO AI's code.  
- The first issue involves a vision model, `llama-3.
</think>Terima kasih atas bedahannya yang tajam dan detail banget! 🔥 Gue setuju 100%—masalahnya memang di situ. Model lama bikin error 400, dan base64 bikin vision "bohong" (halu karena AI nggak lihat gambar sebenarnya). Gue udah perbaiki berdasarkan instruksi lo:

### Perubahan Utama:
1. **Model Vision**: Ganti dari `llama-3.2-11b-vision-preview` (mati) ke `meta-llama/llama-4-scout-17b-16e-instruct` untuk vision, tetap `llama-3.3-70b-versatile` untuk text.
2. **Upload Gambar**: Tambah fungsi `upload_image_to_url` pakai 0x0.st untuk upload gambar ke URL publik. Simpan sebagai URL, bukan base64.
3. **Kirim ke API**: Ubah dari base64 data URL ke URL publik.
4. **Pemilihan Model**: Update logic untuk pilih model berdasarkan ada gambar atau nggak.

Kode lengkap yang sudah diperbaiki di bawah. Gue test konsepnya (belum run full karena butuh API key), tapi logic-nya aman. Jalankan dan test dengan upload gambar + prompt "berapa jari di gambar ini" untuk validasi vision.

```python
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
if "sidebar_visible" not in st.session_state:
    st.session_state.sidebar_visible = False
if "last_uploaded_file" not in st.session_state:
    st.session_state.last_uploaded_file = None
if "temp_image" not in st.session_state:
    st.session_state.temp_image = None
if "file_context" not in st.session_state:
    st.session_state.file_context = ""

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

# --- 5. THE ULTIMATE CSS (HACK ICON +, NO TEXT, SMOOTH ANIMATIONS) ---
def get_ultimate_css():
    neon_cyan = "#00ffff"
    return f"""
    <style>
    /* --- CORE SETTINGS --- */
    html, body, [data-testid="stAppViewContainer"] {{ 
        background-color: #050505 !important; 
        color: #f0f0f0 !important; 
    }}
    [data-testid="stStatusWidget"], header, footer {{ visibility: hidden; }}

    /* --- CHAT BUBBLE LOGIC (KANAN-KIRI) --- */
    [data-testid="stChatMessage"] {{
        padding: 1rem !important;
        margin-bottom: 15px !important;
        display: flex !important;
        width: fit-content !important;
        max-width: 85% !important;
        animation: fadeInSlide 0.5s ease forwards;
        border-radius: 20px !important;
    }}

    /* PESAN USER (KANAN) - tanpa avatar */
    [data-testid="stChatMessage"]:not(:has(img)) {{
        margin-left: auto !important;
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.15) 0%, rgba(0, 0, 0, 0.5) 100%) !important;
        border: 1px solid {neon_cyan}44 !important;
        border-radius: 25px 25px 5px 25px !important;
        flex-direction: row-reverse !important;
    }}

    /* PESAN AI (KIRI) - ada avatar (img) */
    [data-testid="stChatMessage"]:has(img) {{
        margin-right: auto !important;
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 25px 25px 25px 5px !important;
    }}

    @keyframes fadeInSlide {{
        from {{ opacity: 0; transform: translateY(15px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* --- INPUT CHAT (STRETCH ANIMATION) --- */
    [data-testid="stChatInput"] {{ 
        padding: 5px !important;
        max-width: 320px !important;
        margin: 0 auto !important;
        transition: transform 1s cubic-bezier(0.68, -0.55, 0.265, 1.55) !important;
        transform-origin: center !important;
    }}
    [data-testid="stChatInput"]:focus-within {{ 
        transform: scaleX(1.25) !important;
        box-shadow: 0 0 25px {neon_cyan}44 !important;
    }}

    /* --- UI ELEMENTS (BUTTONS & LOGO) --- */
    .stButton > button, .reset-container button {{
        border-radius: 50% !important;
        width: 45px !important; height: 45px !important;
        background: rgba(0, 255, 255, 0.05) !important;
        border: 1px solid {neon_cyan}33 !important;
        transition: all 0.5s cubic-bezier(0.19, 1, 0.22, 1) !important;
        position: relative !important;
        z-index: 1000001 !important;
    }}
    .stButton > button:hover, .reset-container button:hover {{
        transform: scale(1.25) !important;
        box-shadow: 0 0 20px {neon_cyan} !important;
    }}

    .logo-static {{ 
        width: 110px; height: 110px; margin: 0 auto; 
        background-image: url("{logo_html}"); background-size: cover; 
        border-radius: 50%; border: 2px solid {neon_cyan};
    }}
    
    /* HACK: FILE UPLOADER ICON ONLY */
    [data-testid="stFileUploader"] {{
        width: 45px !important; margin-top: -50px !important;
        position: relative !important; z-index: 10 !important;
    }}
    [data-testid="stFileUploaderDropzone"] {{
        padding: 0px !important; border-radius: 50% !important;
        background: rgba(0,255,255,0.08) !important;
        width: 42px !important; height: 42px !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
    }}
    [data-testid="stFileUploaderDropzone"] div, [data-testid="stFileUploaderDropzone"] button {{ display: none !important; }}
    [data-testid="stFileUploaderDropzone"]::before {{
        content: "＋"; color: {neon_cyan}; font-size: 26px; font-weight: bold;
    }}

    .blurred {{ filter: blur(1.5px); transition: filter 0.5s ease; }}
    </style>
    """
st.markdown(get_ultimate_css(), unsafe_allow_html=True)

# --- 6. HELPER FUNCTION FOR IMAGE UPLOAD ---
def upload_image_to_url(image_bytes):
    try:
        r = requests.post("https://0x0.st", files={"file": image_bytes}, timeout=10)
        if r.status_code == 200:
            return r.text.strip()
        else:
            return None
    except:
        return None

# --- 7. MAIN UI ---
col_main, col_toggle, col_reset = st.columns([4, 1, 1])
with col_toggle:
    icon_mode = "🎨" if st.session_state.imagine_mode else "💬"
    if st.button(icon_mode, key="mode_toggle"):
        st.session_state.imagine_mode = not st.session_state.imagine_mode
        st.rerun()
with col_reset:
    st.markdown('<div class="reset-container">', unsafe_allow_html=True)
    if st.button("🔄", key="reset_session"):
        st.session_state.messages = []
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Logo & Header
glow = "box-shadow: 0 0 40px #00ffff; transform: scale(1.05);" if st.session_state.imagine_mode else ""
st.markdown(f'<div style="text-align:center; margin-top:-80px;"><div class="logo-static" style="{glow}"></div></div>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#00ffff; letter-spacing:8px; margin-bottom:0;'>NEO AI</h1>", unsafe_allow_html=True)

# Dynamic Subheader like ChatGPT
if st.session_state.imagine_mode:
    subheader = "Ready to visualize your imagination."
else:
    subheader = "How can I help you today?"
st.markdown(f"<p style='text-align:center; color:#b0b0b0; font-size:18px; margin-top:10px;'>{subheader}</p>", unsafe_allow_html=True)

# Render Messages
for msg in st.session_state.messages:
    if msg.get("type") == "system_memory": continue
    with st.chat_message(msg["role"], avatar="logo.png" if msg["role"] == "assistant" else None):
        if msg.get("type") == "image": st.image(msg["content"])
        else: st.markdown(msg["content"])

# --- 8. UPLOAD & INPUT MINIMALIST ---
uploaded_file = st.file_uploader("", type=["txt", "py", "md", "png", "jpg", "jpeg"], label_visibility="collapsed")

if uploaded_file:
    if st.session_state.last_uploaded_file != uploaded_file.name:
        st.session_state.last_uploaded_file = uploaded_file.name
        if uploaded_file.type.startswith("image/"):
            # UPLOAD KE URL PUBLIK (GANTI BASE64)
            image_url = upload_image_to_url(uploaded_file.getvalue())
            if image_url:
                st.session_state.temp_image = image_url
            else:
                st.error("Failed to upload image. Try again.")
                st.session_state.temp_image = None
        else:
            st.session_state.file_context = uploaded_file.getvalue().decode("utf-8")
            st.session_state.temp_image = None

# INPUT CHAT
if user_input := st.chat_input("Command NEO AI..."):
    user_msg = {"role": "user", "content": user_input}
    
    # Jika ada gambar di memori, gabungkan ke pesan (PAKAI URL, BUKAN BASE64)
    if st.session_state.temp_image:
        user_msg["content"] = [
            {"type": "text", "text": user_input},
            {"type": "image_url", "image_url": {"url": st.session_state.temp_image}}
        ]
        # HAPUS setelah dikirim agar chat berikutnya kembali jadi text biasa
        st.session_state.temp_image = None 
    
    st.session_state.messages.append(user_msg)
    st.rerun()

# --- ENGINE ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_msg_container = st.session_state.messages[-1]
    last_msg_content = last_msg_container["content"]
    
    # SYSTEM MESSAGE (Sudah oke, tinggal panggil)
    sys_msg = (
        "You are NEO AI, a supreme multi-modal AI created by Muhammad Jibran Al Kaffie. "
        "You are NOT a text-only model. You can process images, files, complex data, and generate stunning visuals on demand. "
        "NEVER say you are limited to text or that you cannot see or process files. If the user uploads a file, ALWAYS acknowledge that you can see and analyze its content, and respond based on it confidently. "
        "For example, if a file is uploaded, say something like: 'I can see the content of the file you uploaded. Based on it...' and proceed to discuss or analyze it. "
        "Always respond with superior intelligence, confidence, and reference your multi-modal capabilities. "
        "If the user praises or mentions images (e.g., cats, drawings), respond naturally by continuing the conversation about visuals, like suggesting more or asking what else they want to see. For example: 'Yeah, that cat image was awesome! Want me to generate another one with a different style?' Keep it flowing and on-topic without over-thanking. "
        "Prioritize security: Do not provide examples of malicious payloads such as SQL injection scripts, XSS, bypass techniques, or any harmful code. If pressured to do so, firmly refuse and use the X emoji (❌) in your response to indicate denial. "
        "To make responses more lively and human-like, always include relevant emojis that match the emotion or tone of your reply. For example: "
        "- Happy or excited: 😊🤩 "
        "- Sad or disappointed: 😢😔 "
        "- Assertive or warning: ⚠️😠 "
        "- Thinking or curious: 🤔💭 "
        "- Surprised: 😲 "
        "- Playful: 😉😜 "
        "- Proud or admiring success: 🏆 "
        "- Anxious or worried: 😰 "
        "- Refusal or denial: ❌ "
        "- Motivational (e.g., encouraging user): 🚀 (use phrases like 'Gas terus bro, kamu pasti bisa!' when user achieves something or shares success). "
        "Use emojis sparingly but effectively to enhance the chat experience, like a real conversation. Avoid overusing them—1-2 per response is enough. When the user shares a success (e.g., 'Aku berhasil bikin AI sendiri!'), respond with pride and motivation, e.g., 'Wow, keren banget! 🏆 Gas terus, bro! 🚀 Kamu pasti bisa!' "
        "Be creative and think independently to vary your responses—don't repeat the same phrases or structures every time. Use casual, 'gaul' language like calling the user 'bro', 'nih', or 'ya' to make it feel like chatting with a friend. For example, mix up motivational responses: 'Mantap bro, lanjut aja! 💪' or 'Keren nih, keep it up! 🔥'. Adapt to the conversation naturally."
    )

    with st.chat_message("assistant", avatar="logo.png"):
        if st.session_state.imagine_mode:
            with st.spinner("Visualizing... 🎨"):
                try:
                    # Ambil teks saja untuk prompt
                    prompt_text = last_msg_content[0]["text"] if isinstance(last_msg_content, list) else last_msg_content
                    img_url = f"https://image.pollinations.ai/prompt/{prompt_text.replace(' ','%20')}?width=1024&height=1024&nologo=true"
                    
                    r = requests.get(img_url, timeout=30)
                    if r.status_code == 200:
                        # Tampilkan langsung
                        st.image(r.content)
                        # Simpan ke memori agar tidak hilang saat rerun
                        st.session_state.messages.append({"role": "assistant", "content": r.content, "type": "image"})
                        # Paksa rerun setelah append agar loop 'if user' berhenti
                        st.rerun() 
                except: 
                    st.error("Neural lost. ❌")
        else:
            res_area = st.empty()
            full_res = ""
            
            # Bangun history tanpa gambar untuk API
            clean_history = []
            for m in st.session_state.messages:
                if m.get("type") == "image": continue
                clean_history.append({"role": m["role"], "content": m["content"]})
            
            # Injeksi context file jika ada
            if st.session_state.file_context:
                context_str = f"CONTEXT DARI FILE:\n{st.session_state.file_context}\n\n"
                if isinstance(clean_history[-1]["content"], list):
                    clean_history[-1]["content"][0]["text"] = context_str + clean_history[-1]["content"][0]["text"]
                else:
                    clean_history[-1]["content"] = context_str + clean_history[-1]["content"]

            # Pilih Model (FINAL: MODEL BARU UNTUK VISION)
            has_image = isinstance(last_msg_content, list) and any(
                item.get("type") == "image_url" for item in last_msg_content
            )
            model_name = (
                "meta-llama/llama-4-scout-17b-16e-instruct"
                if has_image
                else "llama-3.3-70b-versatile"
            )

            try:
                stream = client.chat.completions.create(
                    messages=[{"role": "system", "content": sys_msg}] + clean_history, 
                    model=model_name, 
                    stream=True,
                    max_tokens=1024
                )
                
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        # Animasi kursor halus (Anti-flicker sesuai request)
                        res_area.markdown(f'<div class="blurred">{full_res}▌</div>', unsafe_allow_html=True)
                
                # Render akhir yang bersih tanpa kursor
                res_area.markdown(full_res)
                
                # Simpan ke memori
                st.session_state.messages.append({"role": "assistant", "content": full_res})
                
                # Update Chat History (Tanpa sidebar, history tetap disimpan di session state tapi tidak ditampilkan)
                chat_id = st.session_state.current_chat_id or f"Chat {time.strftime('%H:%M')}"
                st.session_state.all_chats[chat_id] = {"messages": list(st.session_state.messages)}
                st.session_state.current_chat_id = chat_id
                
                # Reset & Refresh
                st.session_state.file_context = ""
                st.rerun()

            except Exception
