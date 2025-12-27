import time
import requests
from openai import OpenAI

# --- CẤU HÌNH ---
API_KEY = "mysecretkey"
BASE_URL = "http://100.96.1.73:8500/v1"
MODEL_NAME = "meta-llama/Meta-Llama-3-8B-Instruct"

def check_server_connection():
    """Kiểm tra xem server vLLM có đang phản hồi không trước khi chat"""
    print(f"🔍 Đang kiểm tra kết nối tới server tại {BASE_URL}...")
    try:
        # Thử lấy danh sách model để kiểm tra kết nối
        response = requests.get(f"{BASE_URL}/models", headers={"Authorization": f"Bearer {API_KEY}"}, timeout=10)
        if response.status_code == 200:
            print("✅ Kết nối thành công! Server đã sẵn sàng.")
            return True
        else:
            print(f"❌ Server phản hồi lỗi: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Không thể kết nối tới server. Hãy chắc chắn bạn đã chạy vLLM.\nChi tiết: {e}")
        return False

def start_chat():
    # Khởi tạo client với timeout lớn (300 giây) để xử lý Cold Start trên H200
    client = OpenAI(
        base_url=BASE_URL,
        api_key=API_KEY,
        timeout=300.0  
    )

    messages = [
        {"role": "system", "content": "Bạn là trợ lý AI chuyên gia về nông nghiệp. Hãy trả lời chuyên nghiệp."}
    ]

    print("\n--- BẮT ĐẦU TRÒ CHUYỆN (Gõ 'exit' để thoát) ---")
    print("Lưu ý: Câu hỏi đầu tiên có thể mất 1-2 phút để server biên dịch CUDA Graph.")

    while True:
        user_input = input("\n👤 Bạn: ")
        if user_input.lower() in ["exit", "quit", "thoát"]:
            break
        if not user_input.strip():
            continue

        messages.append({"role": "user", "content": user_input})
        print("🤖 AI: ", end="", flush=True)

        try:
            # Sử dụng stream để thấy chữ chạy ra ngay lập tức
            stream = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                stream=True,
                temperature=0.7
            )

            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    full_response += content

            messages.append({"role": "assistant", "content": full_response})
            print() 

        except Exception as e:
            print(f"\n❌ Lỗi trong quá trình chat: {e}")
            print("Gợi ý: Kiểm tra log của vLLM server để xem có lỗi OOM (Hết bộ nhớ) không.")

if __name__ == "__main__":
    if check_server_connection():
        start_chat()