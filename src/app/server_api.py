from fastapi import FastAPI
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from openai import OpenAI
import uvicorn
import os

app = FastAPI()

# 1. Khởi tạo tài nguyên trên H200
# Sử dụng GPU để Embedding cho nhanh
embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    model_kwargs={'device': 'cuda'} 
)

# Kết nối nội bộ tới vLLM đang chạy ở cổng 8500
client = OpenAI(base_url="http://0.0.0.0:8500/v1", api_key="hello")

# 2. Load bộ nhớ tri thức
vectorstores = {}
DB_PATH = "data/vector_db"

if os.path.exists(DB_PATH):
    for crop_folder in os.listdir(DB_PATH):
        folder_path = os.path.join(DB_PATH, crop_folder)
        if os.path.isdir(folder_path):
            try:
                vectorstores[crop_folder.lower()] = FAISS.load_local(
                    folder_path, 
                    embeddings, 
                    allow_dangerous_deserialization=True
                )
                print(f"✅ Đã nạp tri thức cho cây: {crop_folder}")
            except Exception as e:
                print(f"⚠️ Không thể nạp {crop_folder}: {e}")

@app.post("/ask_agri")
async def ask_rag(question: str):
    # --- BƯỚC 1: NHẬN DIỆN LOẠI CÂY TỪ CÂU HỎI ---
    selected_db = None
    query_lower = question.lower()
    
    # Tìm xem trong câu hỏi có nhắc đến loại cây nào đã có trong DB không
    for crop in vectorstores.keys():
        if crop in query_lower:
            selected_db = vectorstores[crop]
            break
    
    # Nếu không tìm thấy từ khóa cụ thể, mặc định lấy sầu riêng hoặc gộp tri thức
    if not selected_db:
        selected_db = vectorstores.get("sầu riêng") # Hoặc logic gộp tri thức

    # --- BƯỚC 2: TRUY XUẤT (RETRIEVAL) ---
    context = ""
    sources = []
    if selected_db:
        docs = selected_db.similarity_search(question, k=3)
        context = "\n".join([d.page_content for d in docs])
        sources = [d.metadata for d in docs]
        
    # 2. Prompt "Lai" (Hybrid Prompt)
    # Đây là chìa khóa để AI trả lời được cả câu "Bạn bao nhiêu tuổi"
    hybrid_prompt = f"""
    Bạn là một chuyên gia nông nghiệp Việt Nam thông minh.
    
    HƯỚNG DẪN TRẢ LỜI:
    1. Nếu câu hỏi liên quan đến kiến thức nông nghiệp, hãy ưu tiên sử dụng thông tin trong phần [NGỮ CẢNH] dưới đây.
    2. Nếu thông tin trong [NGỮ CẢNH] không đủ hoặc không liên quan (ví dụ câu hỏi về bản thân bạn, hoặc kiến thức chung), hãy sử dụng tri thức nội tại của bạn để trả lời một cách tự nhiên và lịch sự.
    3. Tránh việc nói "Context của bạn không cung cấp thông tin" trừ khi đó là một yêu cầu tra cứu dữ liệu cực kỳ cụ thể mà bạn không biết.

    [NGỮ CẢNH]:
    {context}
    
    CÂU HỎI: {question}
    """
    
    response = client.chat.completions.create(
        model=os.getenv("MODEL_NAME"),
        messages=[
            {"role": "system", "content": "Bạn là trợ lý AI chuyên gia, có khả năng kết hợp dữ liệu được cung cấp và kiến thức cá nhân."},
            {"role": "user", "content": hybrid_prompt}
        ],
        temperature=0.4 # Tăng nhẹ độ sáng tạo để câu trả lời tự nhiên hơn
    )
    
    return {
        "answer": response.choices[0].message.content, 
        "sources": [d.metadata for d in docs] # Gửi kèm metadata (chứa URL)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)