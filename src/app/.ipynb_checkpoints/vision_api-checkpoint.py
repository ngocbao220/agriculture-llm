from fastapi import FastAPI, UploadFile, File
from PIL import Image
import torch
from transformers import AutoProcessor, AutoModelForVision2Seq

app = FastAPI(title="Qwen2.5-VL Vision API")

MODEL_ID = "Qwen/Qwen2.5-VL-7B-Instruct"

processor = AutoProcessor.from_pretrained(MODEL_ID)
model = AutoModelForVision2Seq.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.bfloat16,
    device_map="auto"
)
model.eval()


@app.post("/analyze_image")
async def analyze_image(
    image: UploadFile = File(...),
    prompt: str = "Hãy mô tả triệu chứng bệnh trên cây trồng."
):
    img = Image.open(image.file).convert("RGB")

    inputs = processor(
        text=prompt,
        images=img,
        return_tensors="pt"
    ).to(model.device)

    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=512
        )

    result = processor.decode(output[0], skip_special_tokens=True)
    return {"result": result}
