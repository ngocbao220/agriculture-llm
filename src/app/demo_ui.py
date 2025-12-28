import gradio as gr
import requests

# Địa chỉ FastAPI nội bộ
API_URL = "http://0.0.0.0:9000/ask"

def predict(message, history):
    try:
        payload = {"question": message}
        response = requests.post(API_URL, json=payload, timeout=300)
        
        if response.status_code == 200:
            data = response.json()
            answer = data["answer"]
            sources = data["sources"]
            
            full_res = answer
            if sources:
                full_res += "\n\n📚 **Nguồn tham khảo:**\n" + "\n".join([f"- {s}" for s in sources])
            return full_res
        else:
            return f"❌ Lỗi Server: {response.status_code}"
    except Exception as e:
        return f"❌ Lỗi kết nối: {e}"

# Thiết kế giao diện
demo = gr.ChatInterface(
    predict,
    title="🌾 Chuyên gia Nông nghiệp AI - UET Factory",
    description="Hệ thống RAG chẩn đoán bệnh cây trồng chạy trên NVIDIA H200. Hỗ trợ Sầu riêng, Lúa, Cà phê, Khoai tây...",
    examples=["Lá sầu riêng bị cháy là bệnh gì?", "Kỹ thuật bón phân cho lúa mùa"]
)

if __name__ == "__main__":
    # server_name="0.0.0.0" để bên ngoài truy cập qua IP
    # share=True để tạo Public Link (gradio.live) gửi cho bạn bè
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)