import streamlit as st
import requests
import time
from datetime import datetime

# ==================== CONFIG ====================
st.set_page_config(page_title="AgriMind AI", layout="wide")

LOGIC_API_URL = "http://tcp-endpoint.serverless.fptcloud.jp:33197/ask"
VISION_API_URL = "http://tcp-endpoint.serverless.fptcloud.jp:36432/analyze"

USER_AVATAR = "https://www.svgrepo.com/show/401101/angry-face.svg"
BOT_AVATAR = "https://www.svgrepo.com/show/401095/alien-monster.svg"

# ==================== MODERN UI CSS ====================
st.markdown(f"""
    <style>
    [data-testid="stChatMessage"] p {{
        font-size: 20px !important;  /* Tăng từ mặc định ~14px lên 18px */
        line-height: 1.6;
    }}

    /* 2. Font chữ trong ô nhập liệu (Input) */
    .stChatInput textarea {{
        font-size: 20px !important;
    }}

    /* 3. Font chữ trong Box kết quả Vision ở Sidebar */
    .vision-sidebar-box {{
        font-size: 20px !important;
        line-height: 1.5;
    }}

    /* 4. Font chữ cho các tiêu đề (Headers) */
    h1 {{ font-size: 32px !important; }}
    h2 {{ font-size: 28px !important; }}
    h3 {{ font-size: 22px !important; }}
    
    /* Căn giữa khung chat rộng hơn một chút để chứa font chữ to */
    .main .block-container {{
        max-width: 900px;
    }}
    /* Nền tổng thể */
    .stApp {{
        background-color: #ffffff;
    }}
    
    /* Căn giữa khung chat để giống ChatGPT */
    .main .block-container {{
        max-width: 850px;
        padding-top: 2rem;
    }}

    /* Tinh chỉnh bong bóng chat */
    [data-testid="stChatMessage"] {{
        background-color: transparent;
        border-radius: 10px;
        margin-bottom: 5px;
    }}
    
    /* Hiệu ứng highlight nhẹ cho user */
    [data-testid="stChatMessage"]:nth-child(even) {{
        background-color: #f7f7f8;
    }}

    /* Sidebar - Vision Box */
    .vision-sidebar-box {{
        background: #f9f9f9;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #eee;
        font-size: 14px;
        color: #333;
        line-height: 1.5;
    }}
    
    /* Fix khung input ở dưới */
    .stChatFloatingInputContainer {{
        padding-bottom: 30px;
    }}
    </style>
    """, unsafe_allow_html=True)

# ==================== SESSION STATE ====================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vision_result" not in st.session_state:
    st.session_state.vision_result = "Chưa có dữ liệu phân tích."

# ==================== LOGIC FUNCTIONS ====================
def stream_text(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.02)

def call_vision_api(image_bytes):
    try:
        files = {"file": ("image.jpg", image_bytes, "image/jpeg")} 
        res = requests.post(VISION_API_URL, files=files, timeout=60)
        return res.json().get("symptoms", "Không tìm thấy triệu chứng.") if res.status_code == 200 else "⚠️ Lỗi Vision API"
    except Exception as e:
        return f"❌ Lỗi: {e}"

def call_logic_api(question, symptoms=""):
    try:
        payload = {"question": f"Dựa trên ảnh: {symptoms}\nCâu hỏi: {question}" if symptoms else question}
        res = requests.post(LOGIC_API_URL, json=payload, timeout=120)
        if res.status_code == 200:
            data = res.json()
            ans = data.get("answer", "")
            if data.get("sources"):
                ans += "\n\n📚 **Nguồn:** " + ", ".join(data["sources"])
            return ans
        return "⚠️ Lỗi kết nối Logic API."
    except Exception as e:
        return f"❌ Lỗi hệ thống: {e}"

# ==================== SIDEBAR: VISION PANEL ====================
with st.sidebar:
    st.image("https://www.svgrepo.com/show/424002/agriculture-barley-corn.svg", width=50)
    
    st.subheader("📷 Phân tích ảnh")
    uploaded_file = st.file_uploader("Tải lên ảnh cây trồng", type=["jpg", "png", "jpeg"])
    
    if uploaded_file:
        st.image(uploaded_file, use_container_width=True, caption="Ảnh đang chọn")
    
    st.markdown("### 🧪 Kết quả nhận diện")
    st.markdown(f'<div class="vision-sidebar-box">{st.session_state.vision_result}</div>', unsafe_allow_html=True)
    
    if st.button("Xóa lịch sử chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.vision_result = "Chưa có dữ liệu phân tích."
        st.rerun()

# ==================== MAIN CHAT INTERFACE ====================
st.markdown("<h2 style='text-align: center;'>🌿 AgriMind Assistant</h2>", unsafe_allow_html=True)

# Hiển thị lịch sử chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=USER_AVATAR if msg["role"] == "user" else BOT_AVATAR):
        st.markdown(msg["content"])

# Ô nhập liệu cố định ở dưới
if prompt := st.chat_input("Hỏi tôi về kỹ thuật canh tác, sâu bệnh..."):
    
    # 1. User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    # 2. Assistant Response
    with st.chat_message("assistant", avatar=BOT_AVATAR):
        symptoms = ""
        # Nếu có ảnh, tự động phân tích trước
        if uploaded_file:
            with st.status("🔍 Đang phân tích hình ảnh...", expanded=False):
                symptoms = call_vision_api(uploaded_file.getvalue())
                st.session_state.vision_result = symptoms
        
        # Gọi Logic API
        with st.spinner("🤖 AgriMind đang suy nghĩ..."):
            full_response = call_logic_api(prompt, symptoms)
        
        # Hiệu ứng gõ chữ
        streamed_ans = st.write_stream(stream_text(full_response))
        st.session_state.messages.append({"role": "assistant", "content": streamed_ans})
        
    st.rerun()