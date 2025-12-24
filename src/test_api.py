from openai import OpenAI

# Thay '123.456.78.9' bằng địa chỉ IP thật của server H200 của bạn
IP_H200 = "123.456.78.9" 

client = OpenAI(
    base_url=f"http://{IP_H200}:8000/v1",
    api_key="secret-agri-token"
)

def test_connection():
    print("--- Đang kết nối tới H200... ---")
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
        print("Mẹo: Hãy kiểm tra xem IP có đúng không và Port 8000 đã được mở (Firewall) chưa.")

if __name__ == "__main__":
    test_connection()