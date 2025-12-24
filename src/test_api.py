from openai import OpenAI
import os

# Lệnh lấy IP: curl ifconfig.me
IP_H200 = os.getenv("IP_H200", "1.2.3.4")
PORT = os.getenv("PORT", "8500")

client = OpenAI(
    base_url=f"http://{IP_H200}:{PORT}/v1",
    api_key= os.getenv("API_KEY_NLP", "token")
)

def test_connection():
    print("--- Đang kết nối ---")
    try:
        response = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            messages=[
                {"role": "system", "content": "Bạn là trợ lý chuyên gia nông nghiệp."},
                {"role": "user", "content": "Tại sao lá sầu riêng bị cháy lá?"}
            ],
            temperature=0.7,
            max_tokens=200
        )
        print("\n✅ Kết nối thành công!")
        print(f"🤖 AI trả lời: {response.choices[0].message.content}")
    except Exception as e:
        print(f"\n❌ Lỗi kết nối: {e}")

if __name__ == "__main__":
    test_connection()