import gradio as gr
from openai import OpenAI
import base64
from io import BytesIO
from PIL import Image

# Khởi tạo OpenAI Client kết nối tới vLLM
# Thay đổi base_url nếu bạn chạy trên máy khác
client = OpenAI(
    api_key="EMPTY",
    base_url="http://localhost:8080/v1",
)

def encode_image(image):
    """Chuyển đổi PIL Image sang chuỗi base64 để gửi qua API"""
    if image is None:
        return None
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def predict(image, prompt):
    if not prompt:
        return "Vui lòng nhập câu hỏi!"
    
    messages = []
    content = [{"type": "text", "text": prompt}]
    
    # Nếu có ảnh, thêm vào nội dung tin nhắn theo định dạng của Qwen-VL
    if image is not None:
        base64_image = encode_image(image)
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{base64_image}"}
        })
    
    messages.append({"role": "user", "content": content})

    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-VL-7B-Instruct", # Tên model khớp với lệnh chạy vLLM
            messages=messages,
            max_tokens=512,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Lỗi kết nối API: {str(e)}"

# Giao diện Gradio
with gr.Blocks(title="Qwen2.5-VL Test Tool") as demo:
    gr.Markdown("# 🤖 Qwen2.5-VL-7B (vLLM) Tester")
    gr.Markdown("Tải ảnh lên và đặt câu hỏi để kiểm tra khả năng của mô hình.")
    
    with gr.Row():
        with gr.Column():
            input_img = gr.Image(type="pil", label="Tải ảnh lên (Tùy chọn)")
            input_text = gr.Textbox(lines=4, placeholder="Ví dụ: Mô tả hình ảnh này giúp tôi...", label="Câu hỏi")
            btn = gr.Button("Gửi yêu cầu", variant="primary")
        
        with gr.Column():
            output_text = gr.Textbox(label="Phản hồi từ mô hình", lines=12)

    btn.click(fn=predict, inputs=[input_img, input_text], outputs=output_text)

if __name__ == "__main__":
    # Chạy giao diện trên local (mặc định port 7860)
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)