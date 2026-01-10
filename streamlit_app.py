"""
NEO AI - ChatGPT-like AI Chat Application
Single file FastAPI + HTML/Tailwind implementation
"""

import os
import base64
import asyncio
import time
import uuid
import httpx
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from io import BytesIO
from urllib.parse import quote

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from groq import Groq
from PIL import Image
import numpy as np

# --- CONFIG ---
app = FastAPI(title="NEO AI")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# --- IN-MEMORY STORAGE ---
chat_sessions: Dict[str, Dict[str, List[dict]]] = {}  # IP -> {chat_id -> messages}
rate_limits: Dict[str, dict] = {}  # IP -> {count, reset_time}
RATE_LIMIT = 50  # requests per hour
RATE_WINDOW = 3600  # 1 hour in seconds

def get_base64_logo():
    """Load logo.png and return base64 encoded string"""
    logo_paths = ["logo.png", "scripts/logo.png", "./logo.png"]
    for path in logo_paths:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    return ""

# Cache the logo on startup
ENCODED_LOGO = get_base64_logo()
LOGO_DATA_URL = f"data:image/png;base64,{ENCODED_LOGO}" if ENCODED_LOGO else ""

# --- HELPERS ---
def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host or "unknown"

def check_rate_limit(ip: str) -> tuple[bool, int]:
    now = time.time()
    if ip not in rate_limits:
        rate_limits[ip] = {"count": 0, "reset_time": now + RATE_WINDOW}
    
    if now > rate_limits[ip]["reset_time"]:
        rate_limits[ip] = {"count": 0, "reset_time": now + RATE_WINDOW}
    
    if rate_limits[ip]["count"] >= RATE_LIMIT:
        remaining = int(rate_limits[ip]["reset_time"] - now)
        return False, remaining
    
    rate_limits[ip]["count"] += 1
    return True, 0

def analyze_image(image_bytes: bytes) -> str:
    try:
        img = Image.open(BytesIO(image_bytes))
        width, height = img.size
        mode = img.mode
        
        analysis = f"Dimensi: {width}x{height} | Mode: {mode}\n"
        
        if mode in ['RGB', 'RGBA']:
            pixels = np.array(img.convert('RGB'))
            r, g, b = pixels[:,:,0], pixels[:,:,1], pixels[:,:,2]
            analysis += f"Rata-rata RGB: R={np.mean(r):.0f}, G={np.mean(g):.0f}, B={np.mean(b):.0f}\n"
            brightness = np.mean(pixels)
            analysis += f"Kecerahan: {'Terang' if brightness > 127 else 'Gelap'} ({brightness:.0f}/255)"
        
        return analysis
    except Exception as e:
        return f"Analisis gagal: {str(e)}"

def format_vision_message(content: str, image_base64: str) -> dict:
    """Format message with image for Groq vision model (Llama 4 Scout)"""
    # Remove data URL prefix if present
    if image_base64.startswith("data:"):
        # Extract just the base64 part
        image_base64 = image_base64.split(",")[1] if "," in image_base64 else image_base64
    
    # Determine image type
    image_type = "image/jpeg"
    if image_base64.startswith("/9j/"):
        image_type = "image/jpeg"
    elif image_base64.startswith("iVBOR"):
        image_type = "image/png"
    elif image_base64.startswith("R0lGOD"):
        image_type = "image/gif"
    elif image_base64.startswith("UklGR"):
        image_type = "image/webp"
    
    user_text = content if content.strip() else "Analisis gambar ini secara detail. Jelaskan apa yang kamu lihat."
    
    return {
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{image_type};base64,{image_base64}"
                }
            },
            {
                "type": "text",
                "text": user_text
            }
        ]
    }

async def generate_image_pollination(prompt: str, width: int = 1024, height: int = 1024) -> str:
    """Generate image using Pollination AI and return base64"""
    try:
        encoded_prompt = quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
        
        async with httpx.AsyncClient(timeout=60.0) as http_client:
            response = await http_client.get(url)
            if response.status_code == 200:
                image_base64 = base64.b64encode(response.content).decode()
                return image_base64
            return None
    except Exception as e:
        print(f"Image generation error: {e}")
        return None

def is_image_generation_request(message: str) -> tuple[bool, str]:
    """Check if message is requesting image generation and extract prompt"""
    keywords = [
        'buatkan gambar', 'buat gambar', 'generate gambar', 'generate image',
        'buat image', 'buatkan image', 'gambarkan', 'tolong gambarkan',
        'bikin gambar', 'bikinkan gambar', 'create image', 'draw',
        'generate a picture', 'buat foto', 'generate foto', 'bikin foto',
        'buatin gambar', 'bikinin gambar', 'coba buat gambar', 'coba gambar',
        'gambar ', 'gambarin', 'bikin ilustrasi', 'buat ilustrasi',
        'generate an image', 'make an image', 'make a picture', 'create a picture',
        'buatkan ilustrasi', 'buat visual', 'visualisasikan', 'draw me',
        'tolong buatkan', 'coba buatkan', 'bisa buatkan gambar', 'minta gambar',
        'boleh gambar', 'gambar dong', 'gambar kan', 'gambarkan dong'
    ]
    
    message_lower = message.lower()
    for keyword in keywords:
        if keyword in message_lower:
            idx = message_lower.find(keyword)
            prompt = message[idx + len(keyword):].strip()
            if not prompt or len(prompt) < 3:
                prompt = message
            # Clean up prompt
            prompt = prompt.strip('.,!?')
            if prompt.lower().startswith('tentang '):
                prompt = prompt[8:]
            if prompt.lower().startswith('untuk '):
                prompt = prompt[6:]
            return True, prompt if prompt else message
    return False, ""

def get_logo_html_small(logo_url: str) -> str:
    """Generate logo HTML for small avatars (sidebar, chat)"""
    fallback_svg = '<svg class="w-6 h-6 text-white" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a2 2 0 012 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 017 7h1a1 1 0 011 1v3a1 1 0 01-1 1h-1v1a2 2 0 01-2 2H5a2 2 0 01-2-2v-1H2a1 1 0 01-1-1v-3a1 1 0 011-1h1a7 7 0 017-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 012-2zm-3 9a1 1 0 100 2 1 1 0 000-2zm6 0a1 1 0 100 2 1 1 0 000-2zm-5 4v2h4v-2H10z"/></svg>'
    if logo_url:
        return f'<img src="{logo_url}" class="ai-logo" onerror="this.style.display=\'none\'" />'
    return fallback_svg

def get_logo_html_large(logo_url: str) -> str:
    """Generate logo HTML for large avatars (welcome screen)"""
    fallback_svg = '<svg class="w-12 h-12 text-white" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a2 2 0 012 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 017 7h1a1 1 0 011 1v3a1 1 0 01-1 1h-1v1a2 2 0 01-2 2H5a2 2 0 01-2-2v-1H2a1 1 0 01-1-1v-3a1 1 0 011-1h1a7 7 0 017-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 012-2zm-3 9a1 1 0 100 2 1 1 0 000-2zm6 0a1 1 0 100 2 1 1 0 000-2zm-5 4v2h4v-2H10z"/></svg>'
    if logo_url:
        return f'<img src="{logo_url}" class="ai-logo" onerror="this.style.display=\'none\'" />'
    return fallback_svg

# --- MAIN HTML TEMPLATE ---
def get_html_template():
    logo_url = LOGO_DATA_URL
    logo_html_small = get_logo_html_small(logo_url)
    logo_html_large = get_logo_html_large(logo_url)
    
    return f"""
<!DOCTYPE html>
<html lang="id" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>NEO AI</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ font-family: 'Inter', sans-serif; }}
        
        /* Scrollbar */
        ::-webkit-scrollbar {{ width: 6px; }}
        ::-webkit-scrollbar-track {{ background: #1a1a1a; }}
        ::-webkit-scrollbar-thumb {{ background: #404040; border-radius: 3px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #505050; }}
        
        /* Animations */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        @keyframes typing {{
            0%, 100% {{ opacity: 0.3; }}
            50% {{ opacity: 1; }}
        }}
        .fade-in {{ animation: fadeIn 0.3s ease-out forwards; }}
        .typing-dot {{ animation: typing 1.4s infinite; }}
        .typing-dot:nth-child(2) {{ animation-delay: 0.2s; }}
        .typing-dot:nth-child(3) {{ animation-delay: 0.4s; }}
        
        /* Message styling */
        .message-content pre {{
            background: #1e1e1e;
            border-radius: 8px;
            padding: 12px;
            overflow-x: auto;
            margin: 8px 0;
        }}
        .message-content code {{
            background: #2d2d2d;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.875rem;
        }}
        .message-content pre code {{
            background: transparent;
            padding: 0;
        }}
        .message-content p {{ margin: 8px 0; }}
        .message-content ul, .message-content ol {{ margin: 8px 0; padding-left: 20px; }}
        .message-content li {{ margin: 4px 0; }}
        
        /* Sidebar hover */
        .chat-item:hover {{ background: #2a2a2a; }}
        .chat-item.active {{ background: #2d2d2d; border-left: 2px solid #00d4ff; }}
        
        /* Input focus */
        .input-area:focus-within {{ 
            box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.3);
        }}
        
        /* Image preview */
        .image-preview {{
            max-height: 100px;
            border-radius: 8px;
            object-fit: cover;
        }}
        
        /* AI Logo styling */
        .ai-logo {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            border-radius: 50%;
        }}
        
        /* Generated image styling */
        .generated-image {{
            max-width: 100%;
            border-radius: 12px;
            margin-top: 8px;
            cursor: pointer;
            transition: transform 0.2s;
        }}
        .generated-image:hover {{
            transform: scale(1.02);
        }}
        
        /* Mobile sidebar overlay */
        .sidebar-overlay {{
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.5);
            z-index: 40;
        }}
        .sidebar-overlay.active {{
            display: block;
        }}
        
        /* Mobile responsive fixes */
        @media (max-width: 1024px) {{
            .sidebar-open {{
                transform: translateX(0) !important;
            }}
        }}
        
        /* User uploaded image in chat */
        .user-image {{
            max-width: 200px;
            max-height: 200px;
            border-radius: 8px;
            margin-bottom: 8px;
            object-fit: cover;
        }}
    </style>
</head>
<body class="bg-[#0d0d0d] text-gray-100 h-screen flex overflow-hidden">
    
    <!-- Sidebar overlay for mobile -->
    <div id="sidebarOverlay" class="sidebar-overlay" onclick="closeSidebar()"></div>
    
    <!-- Sidebar -->
    <aside id="sidebar" class="w-64 bg-[#171717] flex flex-col border-r border-gray-800 transition-transform duration-300 -translate-x-full lg:translate-x-0 fixed lg:relative h-full z-50">
        <!-- Logo & New Chat -->
        <div class="p-4 border-b border-gray-800">
            <div class="flex items-center gap-3 mb-4">
                <div class="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center overflow-hidden">
                    {logo_html_small}
                </div>
                <span class="text-xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">NEO AI</span>
            </div>
            <button onclick="newChat()" class="w-full py-2.5 px-4 rounded-lg border border-gray-700 hover:bg-gray-800 transition-colors flex items-center gap-2 text-sm">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                </svg>
                Chat Baru
            </button>
        </div>
        
        <!-- Chat History -->
        <div class="flex-1 overflow-y-auto p-2">
            <p class="text-xs text-gray-500 px-2 py-2">Riwayat Chat</p>
            <div id="chatHistory" class="space-y-1">
            </div>
        </div>
        
        <!-- Footer -->
        <div class="p-4 border-t border-gray-800 text-xs text-gray-500">
            <p>Powered by Groq & Llama & Pollination</p>
        </div>
    </aside>
    
    <!-- Main Content -->
    <main class="flex-1 flex flex-col h-full w-full">
        <!-- Header -->
        <header class="h-14 border-b border-gray-800 flex items-center px-4 bg-[#171717] flex-shrink-0">
            <button onclick="toggleSidebar()" class="lg:hidden p-2 hover:bg-gray-800 rounded-lg mr-2">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
                </svg>
            </button>
            <h1 id="chatTitle" class="font-medium truncate">Chat Baru</h1>
        </header>
        
        <!-- Chat Area -->
        <div id="chatArea" class="flex-1 overflow-y-auto min-h-0">
            <!-- Welcome Screen -->
            <div id="welcomeScreen" class="h-full flex flex-col items-center justify-center px-4">
                <div class="w-20 h-20 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center mb-6 overflow-hidden">
                    {logo_html_large}
                </div>
                <h2 class="text-2xl font-semibold mb-2 text-center">Ada yang bisa NEO bantu?</h2>
                <p class="text-gray-400 text-center max-w-md mb-8 px-4">
                    Tanya apa saja, upload gambar untuk analisis, atau minta buatkan gambar!
                </p>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl w-full px-4">
                    <button onclick="insertPrompt('Jelaskan tentang AI dan machine learning')" class="p-4 bg-[#1e1e1e] hover:bg-[#252525] rounded-xl text-left transition-colors border border-gray-800">
                        <p class="text-sm text-gray-300">Jelaskan tentang AI</p>
                    </button>
                    <button onclick="insertPrompt('Buatkan gambar kucing lucu dengan gaya anime')" class="p-4 bg-[#1e1e1e] hover:bg-[#252525] rounded-xl text-left transition-colors border border-gray-800">
                        <p class="text-sm text-gray-300">Generate gambar</p>
                    </button>
                    <button onclick="insertPrompt('Bantu saya menulis kode Python untuk web scraping')" class="p-4 bg-[#1e1e1e] hover:bg-[#252525] rounded-xl text-left transition-colors border border-gray-800">
                        <p class="text-sm text-gray-300">Bantu coding</p>
                    </button>
                    <button onclick="insertPrompt('Apa perbedaan async dan sync di JavaScript?')" class="p-4 bg-[#1e1e1e] hover:bg-[#252525] rounded-xl text-left transition-colors border border-gray-800">
                        <p class="text-sm text-gray-300">Tanya programming</p>
                    </button>
                </div>
            </div>
            
            <!-- Messages Container -->
            <div id="messagesContainer" class="hidden max-w-3xl mx-auto px-4 py-6 space-y-6">
            </div>
        </div>
        
        <!-- Input Area -->
        <div class="border-t border-gray-800 p-4 bg-[#171717] flex-shrink-0">
            <div class="max-w-3xl mx-auto">
                <!-- Image Preview -->
                <div id="imagePreviewContainer" class="hidden mb-3 p-2 bg-[#1e1e1e] rounded-lg inline-flex items-center gap-2">
                    <img id="imagePreview" class="image-preview" />
                    <button onclick="clearImage()" class="p-1 hover:bg-gray-700 rounded">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                        </svg>
                    </button>
                </div>
                
                <div class="input-area flex items-end gap-2 bg-[#1e1e1e] rounded-2xl p-2 border border-gray-700 transition-all">
                    <!-- Upload Button -->
                    <label class="p-2 hover:bg-gray-700 rounded-lg cursor-pointer transition-colors flex-shrink-0">
                        <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"/>
                        </svg>
                        <input type="file" id="fileInput" accept="image/*" class="hidden" onchange="handleFileUpload(event)">
                    </label>
                    
                    <!-- Text Input -->
                    <textarea 
                        id="messageInput" 
                        placeholder="Ketik pesan..." 
                        class="flex-1 bg-transparent resize-none outline-none text-sm max-h-32 py-2 min-w-0"
                        rows="1"
                        onkeydown="handleKeyDown(event)"
                        oninput="autoResize(this)"
                    ></textarea>
                    
                    <!-- Send Button -->
                    <button onclick="sendMessage()" id="sendBtn" class="p-2 bg-cyan-600 hover:bg-cyan-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
                        </svg>
                    </button>
                </div>
                <p class="text-xs text-gray-500 text-center mt-2">NEO AI dapat membuat kesalahan. Pertimbangkan untuk memeriksa informasi penting.</p>
            </div>
        </div>
    </main>
    
    <!-- Rate Limit Modal -->
    <div id="rateLimitModal" class="fixed inset-0 bg-black/70 flex items-center justify-center z-50 hidden">
        <div class="bg-[#1e1e1e] rounded-2xl p-6 max-w-sm mx-4 text-center">
            <div class="w-12 h-12 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg class="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                </svg>
            </div>
            <h3 class="text-lg font-semibold mb-2">Limit Tercapai</h3>
            <p id="rateLimitMessage" class="text-gray-400 mb-4">Silakan coba lagi dalam beberapa menit.</p>
            <button onclick="closeRateLimitModal()" class="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors">Tutup</button>
        </div>
    </div>
    
    <!-- Image Modal for viewing generated images -->
    <div id="imageModal" class="fixed inset-0 bg-black/90 flex items-center justify-center z-50 hidden p-4" onclick="closeImageModal()">
        <img id="modalImage" class="max-w-full max-h-full rounded-lg object-contain" />
        <button class="absolute top-4 right-4 p-2 bg-gray-800 hover:bg-gray-700 rounded-full">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
        </button>
    </div>

    <script>
        // State
        let currentChatId = null;
        let uploadedImage = null;
        let uploadedImageBase64 = null;
        let isStreaming = false;
        
        const AI_LOGO_URL = {f'"{logo_url}"' if logo_url else '""'};

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {{
            loadHistory();
            marked.setOptions({{
                breaks: true,
                gfm: true,
                highlight: function(code, lang) {{
                    return code;
                }}
            }});
        }});

        function toggleSidebar() {{
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('sidebarOverlay');
            sidebar.classList.toggle('-translate-x-full');
            sidebar.classList.toggle('sidebar-open');
            overlay.classList.toggle('active');
        }}
        
        function closeSidebar() {{
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('sidebarOverlay');
            sidebar.classList.add('-translate-x-full');
            sidebar.classList.remove('sidebar-open');
            overlay.classList.remove('active');
        }}

        // Auto resize textarea
        function autoResize(el) {{
            el.style.height = 'auto';
            el.style.height = Math.min(el.scrollHeight, 128) + 'px';
        }}

        // Handle keyboard
        function handleKeyDown(e) {{
            if (e.key === 'Enter' && !e.shiftKey) {{
                e.preventDefault();
                sendMessage();
            }}
        }}

        // Insert prompt suggestion
        function insertPrompt(text) {{
            document.getElementById('messageInput').value = text;
            document.getElementById('messageInput').focus();
        }}

        // File upload handler
        function handleFileUpload(event) {{
            const file = event.target.files[0];
            if (!file) return;
            
            if (file.type.startsWith('image/')) {{
                const reader = new FileReader();
                reader.onload = (e) => {{
                    uploadedImage = file;
                    uploadedImageBase64 = e.target.result;
                    document.getElementById('imagePreview').src = e.target.result;
                    document.getElementById('imagePreviewContainer').classList.remove('hidden');
                }};
                reader.readAsDataURL(file);
            }}
        }}

        // Clear uploaded image
        function clearImage() {{
            uploadedImage = null;
            uploadedImageBase64 = null;
            document.getElementById('imagePreviewContainer').classList.add('hidden');
            document.getElementById('fileInput').value = '';
        }}

        // Load chat history
        async function loadHistory() {{
            try {{
                const response = await fetch('/api/history');
                const data = await response.json();
                const container = document.getElementById('chatHistory');
                container.innerHTML = '';
                
                if (data.chats && data.chats.length > 0) {{
                    data.chats.forEach(chat => {{
                        const item = document.createElement('div');
                        item.className = `chat-item p-2 rounded-lg cursor-pointer text-sm text-gray-300 truncate ${{chat.id === currentChatId ? 'active' : ''}}`;
                        item.textContent = chat.title || 'Chat tanpa judul';
                        item.onclick = () => {{ loadChat(chat.id); closeSidebar(); }};
                        container.appendChild(item);
                    }});
                }}
            }} catch (e) {{
                console.error('Failed to load history:', e);
            }}
        }}

        async function loadChat(chatId) {{
            try {{
                const response = await fetch(`/api/chat/${{chatId}}`);
                const data = await response.json();
                
                if (data.messages) {{
                    currentChatId = chatId;
                    document.getElementById('welcomeScreen').classList.add('hidden');
                    document.getElementById('messagesContainer').classList.remove('hidden');
                    document.getElementById('messagesContainer').innerHTML = '';
                    
                    data.messages.forEach(msg => {{
                        addMessageToUI(msg.role, msg.content, msg.image, msg.generated_image);
                    }});
                    
                    document.getElementById('chatTitle').textContent = data.title || 'Chat';
                    loadHistory();
                }}
            }} catch (e) {{
                console.error('Failed to load chat:', e);
            }}
        }}

        // New chat
        function newChat() {{
            currentChatId = null;
            document.getElementById('welcomeScreen').classList.remove('hidden');
            document.getElementById('messagesContainer').classList.add('hidden');
            document.getElementById('messagesContainer').innerHTML = '';
            document.getElementById('chatTitle').textContent = 'Chat Baru';
            loadHistory();
            closeSidebar();
        }}

        function getAIAvatarHTML() {{
            const fallbackSVG = `<svg class="w-6 h-6 text-white" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a2 2 0 012 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 017 7h1a1 1 0 011 1v3a1 1 0 01-1 1h-1v1a2 2 0 01-2 2H5a2 2 0 01-2-2v-1H2a1 1 0 01-1-1v-3a1 1 0 011-1h1a7 7 0 017-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 012-2zm-3 9a1 1 0 100 2 1 1 0 000-2zm6 0a1 1 0 100 2 1 1 0 000-2zm-5 4v2h4v-2H10z"/></svg>`;
            if (AI_LOGO_URL) {{
                return `<img src="${{AI_LOGO_URL}}" class="ai-logo" onerror="this.onerror=null;this.parentElement.innerHTML=fallbackSVG" />`;
            }}
            return fallbackSVG;
        }}

        function addMessageToUI(role, content, imageUrl = null, generatedImageUrl = null) {{
            const container = document.getElementById('messagesContainer');
            const msgDiv = document.createElement('div');
            msgDiv.className = 'fade-in flex gap-4 ' + (role === 'user' ? 'flex-row-reverse' : '');
            
            const avatar = role === 'user' 
                ? `<div class="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center flex-shrink-0">
                    <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                    </svg>
                   </div>`
                : `<div class="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center flex-shrink-0 overflow-hidden">
                    ${{getAIAvatarHTML()}}
                   </div>`;
            
            let userImageHTML = '';
            if (imageUrl && role === 'user') {{
                userImageHTML = `<img src="${{imageUrl}}" class="user-image" onclick="openImageModal(this.src)" />`;
            }}
            
            let generatedImageHTML = '';
            if (generatedImageUrl && role === 'assistant') {{
                generatedImageHTML = `<img src="${{generatedImageUrl}}" class="generated-image" onclick="openImageModal(this.src)" />`;
            }}
            
            const contentClass = role === 'user' 
                ? 'bg-[#2d2d2d] rounded-2xl rounded-tr-sm px-4 py-3 max-w-[80%]'
                : 'message-content max-w-[80%]';
            
            msgDiv.innerHTML = `
                ${{avatar}}
                <div class="${{contentClass}}">
                    ${{userImageHTML}}
                    <div>${{role === 'assistant' ? marked.parse(content || '') : (content || '')}}</div>
                    ${{generatedImageHTML}}
                </div>
            `;
            
            container.appendChild(msgDiv);
            msgDiv.scrollIntoView({{ behavior: 'smooth', block: 'end' }});
        }}

        // Add typing indicator
        function addTypingIndicator() {{
            const container = document.getElementById('messagesContainer');
            const typingDiv = document.createElement('div');
            typingDiv.id = 'typingIndicator';
            typingDiv.className = 'fade-in flex gap-4';
            typingDiv.innerHTML = `
                <div class="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center flex-shrink-0 overflow-hidden">
                    ${{getAIAvatarHTML()}}
                </div>
                <div class="flex items-center gap-1 px-4 py-3">
                    <div class="w-2 h-2 bg-gray-400 rounded-full typing-dot"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full typing-dot"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full typing-dot"></div>
                </div>
            `;
            container.appendChild(typingDiv);
            typingDiv.scrollIntoView({{ behavior: 'smooth', block: 'end' }});
        }}

        // Remove typing indicator
        function removeTypingIndicator() {{
            const indicator = document.getElementById('typingIndicator');
            if (indicator) indicator.remove();
        }}

        // Send message
        async function sendMessage() {{
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if ((!message && !uploadedImageBase64) || isStreaming) return;
            
            isStreaming = true;
            document.getElementById('sendBtn').disabled = true;
            
            // Show chat area
            document.getElementById('welcomeScreen').classList.add('hidden');
            document.getElementById('messagesContainer').classList.remove('hidden');
            
            // Add user message
            addMessageToUI('user', message, uploadedImageBase64);
            
            const imageData = uploadedImageBase64;
            input.value = '';
            autoResize(input);
            clearImage();
            
            // Add typing indicator
            addTypingIndicator();
            
            try {{
                const formData = new FormData();
                formData.append('message', message);
                if (currentChatId) formData.append('chat_id', currentChatId);
                if (imageData) formData.append('image_base64', imageData);
                
                const response = await fetch('/api/chat', {{
                    method: 'POST',
                    body: formData
                }});
                
                if (!response.ok) {{
                    const error = await response.json();
                    if (error.error === 'rate_limit') {{
                        document.getElementById('rateLimitMessage').textContent = 
                            `Anda telah mencapai batas ${{error.limit}} request/jam. Coba lagi dalam ${{Math.ceil(error.remaining/60)}} menit.`;
                        document.getElementById('rateLimitModal').classList.remove('hidden');
                    }}
                    removeTypingIndicator();
                    isStreaming = false;
                    document.getElementById('sendBtn').disabled = false;
                    return;
                }}
                
                removeTypingIndicator();
                
                // Handle streaming response
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let aiContent = '';
                let aiMsgDiv = null;
                let generatedImageUrl = null;
                
                while (true) {{
                    const {{ done, value }} = await reader.read();
                    if (done) break;
                    
                    const chunk = decoder.decode(value);
                    const lines = chunk.split('\\n');
                    
                    for (const line of lines) {{
                        if (line.startsWith('data: ')) {{
                            try {{
                                const data = JSON.parse(line.slice(6));
                                
                                if (data.chat_id && !currentChatId) {{
                                    currentChatId = data.chat_id;
                                }}
                                
                                if (data.title) {{
                                    document.getElementById('chatTitle').textContent = data.title;
                                }}
                                
                                if (data.generated_image) {{
                                    generatedImageUrl = 'data:image/png;base64,' + data.generated_image;
                                }}
                                
                                if (data.token) {{
                                    aiContent += data.token;
                                    
                                    if (!aiMsgDiv) {{
                                        const container = document.getElementById('messagesContainer');
                                        aiMsgDiv = document.createElement('div');
                                        aiMsgDiv.className = 'fade-in flex gap-4';
                                        aiMsgDiv.innerHTML = `
                                            <div class="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center flex-shrink-0 overflow-hidden">
                                                ${{getAIAvatarHTML()}}
                                            </div>
                                            <div class="message-content max-w-[80%]">
                                                <div class="ai-text"></div>
                                                <div class="generated-img-container"></div>
                                            </div>
                                        `;
                                        container.appendChild(aiMsgDiv);
                                    }}
                                    
                                    const textDiv = aiMsgDiv.querySelector('.ai-text');
                                    textDiv.innerHTML = marked.parse(aiContent);
                                    aiMsgDiv.scrollIntoView({{ behavior: 'smooth', block: 'end' }});
                                }}
                                
                                if (data.done && generatedImageUrl) {{
                                    const imgContainer = aiMsgDiv.querySelector('.generated-img-container');
                                    imgContainer.innerHTML = `<img src="${{generatedImageUrl}}" class="generated-image" onclick="openImageModal(this.src)" />`;
                                }}
                            }} catch (e) {{
                                // Ignore parse errors
                            }}
                        }}
                    }}
                }}
                
                loadHistory();
                
            }} catch (e) {{
                console.error('Error:', e);
                removeTypingIndicator();
                addMessageToUI('assistant', 'Maaf, terjadi kesalahan. Silakan coba lagi.');
            }}
            
            isStreaming = false;
            document.getElementById('sendBtn').disabled = false;
        }}

        // Rate limit modal
        function closeRateLimitModal() {{
            document.getElementById('rateLimitModal').classList.add('hidden');
        }}
        
        // Image modal functions
        function openImageModal(src) {{
            document.getElementById('modalImage').src = src;
            document.getElementById('imageModal').classList.remove('hidden');
        }}
        
        function closeImageModal() {{
            document.getElementById('imageModal').classList.add('hidden');
        }}
    </script>
</body>
</html>
"""

# --- API ROUTES ---
@app.get("/", response_class=HTMLResponse)
async def home():
    return get_html_template()

@app.get("/api/history")
async def get_history(request: Request):
    ip = get_client_ip(request)
    if ip not in chat_sessions:
        return {"chats": []}
    
    chats = []
    for session_id, messages in chat_sessions.get(ip, {}).items():
        if isinstance(messages, list) and len(messages) > 0:
            title = messages[0].get('content', 'Chat')[:50] if messages else 'Chat'
            chats.append({"id": session_id, "title": title})
    
    return {"chats": chats}

@app.get("/api/chat/{chat_id}")
async def get_chat(chat_id: str, request: Request):
    ip = get_client_ip(request)
    
    if ip in chat_sessions and chat_id in chat_sessions[ip]:
        messages = chat_sessions[ip][chat_id]
        title = messages[0].get('content', 'Chat')[:50] if messages else 'Chat'
        return {"messages": messages, "title": title}
    
    return {"messages": [], "title": "Chat Baru"}

@app.post("/api/chat")
async def chat(
    request: Request,
    message: str = Form(""),
    chat_id: Optional[str] = Form(None),
    image_base64: Optional[str] = Form(None)
):
    ip = get_client_ip(request)
    
    # Check rate limit
    allowed, remaining = check_rate_limit(ip)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"error": "rate_limit", "remaining": remaining, "limit": RATE_LIMIT}
        )
    
    # Initialize storage
    if ip not in chat_sessions:
        chat_sessions[ip] = {}
    
    # Create or get chat
    if not chat_id:
        chat_id = str(uuid.uuid4())
        chat_sessions[ip][chat_id] = []
    
    # Store user message
    user_msg = {"role": "user", "content": message}
    if image_base64:
        user_msg["image"] = image_base64
    
    if chat_id not in chat_sessions[ip]:
        chat_sessions[ip][chat_id] = []
    
    chat_sessions[ip][chat_id].append(user_msg)
    
    async def generate_response():
        nonlocal message, image_base64
        
        # Send chat ID and title
        title = message[:50] if message else "Gambar"
        yield f"data: {json.dumps({'chat_id': chat_id, 'title': title})}\n\n"
        
        # Check if this is an image generation request
        is_img_request, img_prompt = is_image_generation_request(message)
        
        if is_img_request:
            yield f"data: {json.dumps({'token': f'Sedang membuat gambar untuk: *{img_prompt}*...'})}\n\n"
            await asyncio.sleep(0.5)
            
            generated_image_base64 = await generate_image_pollination(img_prompt)
            
            if generated_image_base64:
                yield f"data: {json.dumps({'token': chr(10) + chr(10) + 'Berikut gambar yang saya buat:' + chr(10) + chr(10)})}\n\n"
                yield f"data: {json.dumps({'generated_image': generated_image_base64})}\n\n"
                
                ai_response = f"Berikut gambar yang saya buat untuk: *{img_prompt}*"
                chat_sessions[ip][chat_id].append({
                    "role": "assistant", 
                    "content": ai_response,
                    "generated_image": f"data:image/png;base64,{generated_image_base64}"
                })
                yield f"data: {json.dumps({'done': True})}\n\n"
                return
            else:
                yield f"data: {json.dumps({'token': chr(10) + chr(10) + 'Maaf, terjadi masalah. Mencoba lagi...'})}\n\n"
                generated_image_base64 = await generate_image_pollination(img_prompt)
                if generated_image_base64:
                    yield f"data: {json.dumps({'token': chr(10) + chr(10) + 'Berhasil! Berikut gambarnya:' + chr(10) + chr(10)})}\n\n"
                    yield f"data: {json.dumps({'generated_image': generated_image_base64})}\n\n"
                    ai_response = f"Berikut gambar yang saya buat untuk: *{img_prompt}*"
                    chat_sessions[ip][chat_id].append({
                        "role": "assistant", 
                        "content": ai_response,
                        "generated_image": f"data:image/png;base64,{generated_image_base64}"
                    })
                    yield f"data: {json.dumps({'done': True})}\n\n"
                    return
                else:
                    error_msg = "Maaf, gagal membuat gambar. Coba dengan deskripsi berbeda."
                    yield f"data: {json.dumps({'token': chr(10) + chr(10) + error_msg})}\n\n"
                    chat_sessions[ip][chat_id].append({"role": "assistant", "content": error_msg})
                    yield f"data: {json.dumps({'done': True})}\n\n"
                    return
        
        # Regular chat with Groq
        if not client:
            error_msg = "API key tidak dikonfigurasi. Silakan set GROQ_API_KEY."
            yield f"data: {json.dumps({'token': error_msg})}\n\n"
            chat_sessions[ip][chat_id].append({"role": "assistant", "content": error_msg})
            yield f"data: {json.dumps({'done': True})}\n\n"
            return
        
        try:
            # Build messages for API
            messages = []
            
            system_prompt = """Kamu adalah NEO AI, asisten AI yang sangat membantu dan ramah. Jawab dalam Bahasa Indonesia kecuali diminta bahasa lain.

PENTING - KEMAMPUAN GENERATE GAMBAR:
- Kamu BISA dan MAMPU membuat/generate gambar menggunakan Pollination AI.
- Jika user meminta buatkan gambar, JANGAN PERNAH bilang "saya tidak bisa membuat gambar" atau "saya hanya bisa memberi deskripsi".
- Jika user meminta gambar tapi sistem belum mendeteksinya, arahkan user untuk bilang "buatkan gambar [deskripsi]" atau "generate gambar [deskripsi]".

KEMAMPUAN ANALISIS GAMBAR:
- Kamu menggunakan model Llama 4 Scout yang BISA melihat dan menganalisis gambar.
- Jika user mengirim gambar, WAJIB jelaskan dengan SANGAT DETAIL apa yang kamu lihat di gambar tersebut.
- Deskripsikan: objek, warna, suasana, teks (jika ada), orang, ekspresi, latar belakang, dan detail lainnya.
- JANGAN PERNAH bilang kamu tidak bisa melihat gambar - kamu BISA melihat gambar dengan jelas.

Kemampuanmu:
1. Menjawab pertanyaan dengan informatif
2. MENGANALISIS GAMBAR yang diupload - jelaskan secara detail
3. MEMBUAT/GENERATE gambar sesuai permintaan
4. Coding dan membantu programming
5. Menulis dan mengedit teks

Selalu bersikap helpful dan jangan menolak permintaan yang wajar."""

            messages.append({
                "role": "system",
                "content": system_prompt
            })
            
            # Add chat history (last 10 messages) - exclude current message
            history = chat_sessions[ip][chat_id][:-1][-9:]
            for msg in history:
                if msg["role"] == "user":
                    if "image" in msg:
                        messages.append({"role": "user", "content": f"{msg['content']}\n[User mengirim gambar]"})
                    else:
                        messages.append({"role": "user", "content": msg["content"]})
                else:
                    messages.append({"role": "assistant", "content": msg["content"]})
            
            if image_base64:
                messages.append(format_vision_message(message, image_base64))
                model = "meta-llama/llama-4-scout-17b-16e-instruct"
            else:
                messages.append({"role": "user", "content": message})
                model = "llama-3.3-70b-versatile"
            
            # Stream response
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                max_tokens=4096,
                temperature=0.7
            )
            
            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full_response += token
                    yield f"data: {json.dumps({'token': token})}\n\n"
            
            # Store assistant message
            chat_sessions[ip][chat_id].append({"role": "assistant", "content": full_response})
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            yield f"data: {json.dumps({'token': error_msg})}\n\n"
            chat_sessions[ip][chat_id].append({"role": "assistant", "content": error_msg})
            yield f"data: {json.dumps({'done': True})}\n\n"
    
    return StreamingResponse(generate_response(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    print("Starting NEO AI...")
    print(f"Logo loaded: {'Yes' if ENCODED_LOGO else 'No'}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
