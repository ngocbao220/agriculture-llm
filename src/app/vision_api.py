import base64
from io import BytesIO
from fastapi import FastAPI, UploadFile, File, HTTPException
from openai import OpenAI
from PIL import Image
import uvicorn

app = FastAPI(title="Agri-Vision-Service")

# Kết nối tới vLLM chạy Qwen2.5-VL (Cổng 8080)
client_vl = OpenAI(base_url="http://localhost:8080/v1", api_key="hello")

@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    try:
        # Chuyển ảnh sang base64
        img = Image.open(file.file).convert("RGB")
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        base64_img = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        # Gọi vLLM trích xuất triệu chứng
        # Gọi vLLM trích xuất triệu chứng với Prompt đã tối ưu
        response = client_vl.chat.completions.create(
            model="Qwen/Qwen2.5-VL-7B-Instruct",
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Bạn là chuyên gia thị giác máy tính trong nông nghiệp. "
                        "Nhiệm vụ của bạn là quan sát ảnh và cung cấp dữ liệu mô tả khách quan, "
                        "làm đầu vào cho hệ thống chẩn đoán chuyên sâu."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Phân tích ảnh cây trồng theo các bước sau:\n"
                                "Bước 1: Liệt kê các triệu chứng quan sát được trên lá, thân, quả (vết đốm, màu sắc, biến dạng).\n"
                                "Bước 2: Tổng hợp thành một đoạn mô tả ngắn gọn.\n\n"
                                "Yêu cầu nghiêm ngặt:\n"
                                "- Trả lời bằng tiếng Việt.\n"
                                "- Cung cấp tên cây rõ ràng ở ngay đầu câu.\n"
                                "- Chỉ mô tả những gì thấy trong ảnh, không chẩn đoán tên bệnh, không tư vấn.\n"
                                "- Ngôn ngữ ngắn gọn, tập trung vào tính chất vật lý (ví dụ: đốm vàng viền nâu, cháy lá từ chóp, héo rũ)."
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_img}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=250,
            temperature=0.1 # Để kết quả mang tính nhất quán, khách quan
        )
        return {"symptoms": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9001)