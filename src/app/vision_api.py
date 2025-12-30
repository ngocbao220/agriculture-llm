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
        response = client_vl.chat.completions.create(
            model="Qwen/Qwen2.5-VL-7B-Instruct",
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Bạn là chuyên gia nông nghiệp Việt Nam, có kinh nghiệm chẩn đoán bệnh cây trồng "
                        "dựa trên hình ảnh thực tế ngoài môi trường."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Quan sát kỹ hình ảnh cây trồng được cung cấp.\n"
                                "Chỉ tập trung vào các loại cây phổ biến ở Việt Nam gồm: "
                                "Lúa, Ngô, Khoai tây, Dưa hấu, Cà chua, Sầu riêng, Thanh long.\n\n"
                
                                "Yêu cầu:\n"
                                "1. Xác định loại cây trồng (nếu có thể).\n"
                                "2. Mô tả chi tiết các triệu chứng bệnh *nhìn thấy trực tiếp trong ảnh* "
                                "(màu sắc lá, đốm bệnh, héo, thối, biến dạng, vết cháy...).\n"
                
                                "Không suy đoán vượt quá những gì quan sát được từ ảnh. "
                                "Chỉ dừng lại ở mức chỉ ra các đặc điểm quan trọng"
                                "Không đưa ra hướng dẫn điều trị."
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
            max_tokens=300
        )
        return {"symptoms": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9001)