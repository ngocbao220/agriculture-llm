"""
Kết nối tới VLLM và sử dụng hệ thống RAG
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from openai import OpenAI

from config import DB_PATH, EMBED_MODEL

API_KEY="hello"
MODEL_NAME="Qwen/Qwen2.5-32B-Instruct"

VLLM_URL=f"http://0.0.0.0:8500/v1"

# ==================== RAG SYSTEM ====================
class AgriRAG:
    def __init__(self):
        print("⌛ Đang khởi tạo bộ máy Embedding trên GPU...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBED_MODEL,
            model_kwargs={'device': 'cuda'}
        )
        self.client = OpenAI(base_url=VLLM_URL, api_key="hello")
        self.vectorstores = self._load_all_dbs()

    def _load_all_dbs(self):
        dbs = {}
        if not os.path.exists(DB_PATH):
            return dbs
        for crop in os.listdir(DB_PATH):
            path = os.path.join(DB_PATH, crop)
            if os.path.isdir(path):
                dbs[crop.lower()] = FAISS.load_local(
                    path, self.embeddings, allow_dangerous_deserialization=True
                )
                print(f"✅ Đã nạp tri thức: {crop}")
        return dbs

    def query(self, question: str):
        # 1. Nhận diện loại cây trồng
        selected_db = None
        for crop, db in self.vectorstores.items():
            if crop in question.lower():
                selected_db = db
                break
        
        # 2. Truy xuất context (Retrieval)
        context = ""
        sources = []
        if selected_db:
            docs = selected_db.similarity_search(question, k=3)
            context = "\n".join([d.page_content for d in docs])
            sources = list(set([d.metadata.get('source', 'N/A') for d in docs]))

        # 3. Hybrid Prompt
        prompt = f"""
        Bạn là chuyên gia nông nghiệp Việt Nam cao cấp. 
        Hãy dùng [NGỮ CẢNH] bên dưới để trả lời nếu liên quan. 
        Nếu không có trong ngữ cảnh, hãy dùng kiến thức nội tại của bạn.

        [NGỮ CẢNH]: {context}
        CÂU HỎI: {question}
        """

        response = self.client.chat.completions.create(
            model=os.getenv("MODEL_NAME", "Qwen/Qwen2.5-32B-Instruct"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        return {
            "answer": response.choices[0].message.content,
            "sources": sources
        }

# Khởi tạo singleton để dùng chung
rag_system = AgriRAG()