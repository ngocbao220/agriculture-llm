import sys
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # tự động tìm file .env

# --- THÔNG SỐ KẾT NỐI---
FPT_ENDPOINT = os.getenv("FPT_ENDPOINT")
FPT_PORT = os.getenv("FPT_PORT")
API_KEY = os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")

# Khởi tạo OpenAI Client
client = OpenAI(
    base_url=f"http://{FPT_ENDPOINT}:{FPT_PORT}/v1",
    api_key=API_KEY,
    timeout=300.0
)

def start_chat():
    # Cấu hình "bộ não" cho AI chuyên về nông nghiệp Việt Nam
    messages = [
        {
            "role": "system", 
            "content": (
                "Bạn là chuyên gia tư vấn nông nghiệp cao cấp tại Việt Nam. "
                "Bạn am hiểu về kỹ thuật trồng nông nghiệp, chẩn đoán sâu bệnh và biện pháp phòng trừ."
                "Hãy trả lời bằng tiếng Việt, đưa ra các biện pháp canh tác hữu cơ và thuốc bảo vệ thực vật đúng danh mục."
            )
        }
    ]

    print(f"📍 Endpoint: {FPT_ENDPOINT}:{FPT_PORT}")
    print("--- Bạn có thể bắt đầu hỏi về nông nghiệp (Gõ 'exit' để thoát) ---")

    while True:
        try:
            user_input = input("\n👤 Bạn: ").strip()
            if user_input.lower() in ["exit", "quit", "thoát"]:
                break
            if not user_input:
                continue

            messages.append({"role": "user", "content": user_input})
            print("🤖 AI: ", end="", flush=True)

            # Gọi API streaming giúp chữ chảy ra mượt mà
            stream = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                stream=True,
                temperature=0.3 # Giảm độ sáng tạo để tăng tính chính xác kỹ thuật
            )

            full_res = ""
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    print(content, end="", flush=True)
                    full_res += content

            # Lưu lại câu trả lời vào lịch sử để AI nhớ ngữ cảnh câu hỏi sau
            messages.append({"role": "assistant", "content": full_res})
            print() 

        except Exception as e:
            print(f"\n❌ Lỗi: {e}")
            print("👉 Kiểm tra xem trên Web Console của FPT bạn đã chạy lệnh khởi động vLLM chưa.")

if __name__ == "__main__":
    start_chat()