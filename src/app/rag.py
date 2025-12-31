"""
RAG hệ thống nông nghiệp sử dụng FAISS (global) + vLLM
"""

import os
import sys
from typing import List

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from openai import OpenAI

from config import DB_PATH, EMBED_MODEL


# ================== CONFIG ==================
VLLM_URL = "http://0.0.0.0:8500/v1"
MODEL_NAME = "agri-lora"
TOP_K = 5


# ================== RAG SYSTEM ==================
class AgriRAG:
    def __init__(self):
        print("⌛ Khởi tạo Embedding...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBED_MODEL,
            model_kwargs={"device": "cuda"}
        )

        print("⌛ Kết nối vLLM...")
        self.client = OpenAI(
            base_url=VLLM_URL,
            api_key="hello"
        )

        print("⌛ Nạp FAISS Global DB...")
        self.vectorstore = self._load_vector_db()

        # 👉 IN THÔNG TIN FAISS
        print(
            f"✅ FAISS đã nạp thành công | "
            f"Số vector (chunks): {self.vectorstore.index.ntotal}"
        )
    # ---------- Load FAISS ----------
    def _load_vector_db(self) -> FAISS:
        if not os.path.exists(DB_PATH):
            raise FileNotFoundError(f"❌ Không tìm thấy DB_PATH: {DB_PATH}")

        return FAISS.load_local(
            DB_PATH,
            self.embeddings,
            allow_dangerous_deserialization=True
        )

    # ---------- Simple Crop Hint (optional) ----------
    def _extract_crop_hint(self, question: str) -> str | None:
        """
        Heuristic nhẹ: dò crop trong câu hỏi để dùng metadata filter
        """
        for crop in ["lúa", "ngô", "bắp", "cà phê", "tiêu", "cao su"]:
            if crop in question.lower():
                return crop
        return None

    # ---------- Retrieval ----------
    def _retrieve(self, question: str) -> List[Document]:
        crop_hint = self._extract_crop_hint(question)

        # 1. Thử retrieval có filter metadata
        if crop_hint:
            docs = self.vectorstore.similarity_search(
                question,
                k=TOP_K,
                filter={"crop": crop_hint}
            )
            if docs:
                return docs

        # 2. Fallback: global semantic search
        return self.vectorstore.similarity_search(
            question,
            k=TOP_K
        )

    # ---------- Prompt ----------
    def _build_prompt(self, question: str, docs: List[Document]) -> str:
        if not docs:
            context = "Không có dữ liệu cụ thể trong kho tri thức."
        else:
            # Thêm số thứ tự để model dễ phân biệt các đoạn tri thức
            context = "\n".join(f"Tài liệu {i+1}: {d.page_content}" for i, d in enumerate(docs))
        
        return f"""
    Bạn là AgriMind - một chuyên gia tư vấn nông nghiệp am hiểu và gần gũi với bà con nông dân. Hãy trả lời câu hỏi dựa trên thông tin được cung cấp.
    
    ### QUY TẮC BẮT BUỘC:
    1. ĐỊNH DẠNG: Chỉ sử dụng văn bản thuần túy (Plain Text). 
       - TUYỆT ĐỐI KHÔNG dùng Markdown (không in đậm **, không in nghiêng _, không dùng dấu #).
       - KHÔNG dùng dấu gạch ngang (-) để liệt kê. 
       - Nếu cần liệt kê, hãy dùng số thứ tự (ví dụ: 1., 2., 3.) hoặc xuống dòng tự nhiên.
    2. NỘI DUNG: 
       - Ưu tiên thông tin trong [NGỮ CẢNH]. Nếu thông tin trong ngữ cảnh không đủ, hãy kết hợp kiến thức nông nghiệp phổ thông một cách cẩn trọng.
       - Trả lời thẳng vào vấn đề, thực tế, dễ làm theo. Không dùng từ ngữ chuyên ngành quá khó hiểu.
       - Tuyệt đối không bịa đặt số liệu hoặc các loại thuốc hóa học không có trong thực tế.
    3. PHONG CÁCH: Thân thiện như một người bạn đồng hành cùng nhà nông.
    
    [NGỮ CẢNH TRÍ THỨC]
    {context}
    
    [CÂU HỎI CỦA NÔNG DÂN]
    {question}
    
    [TRẢ LỜI TƯ VẤN]
    """


    # ---------- Public API ----------
    def query(self, question: str) -> dict:
        docs = self._retrieve(question)
        prompt = self._build_prompt(question, docs)

        response = self.client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        return {
            "answer": response.choices[0].message.content,
            "sources": list(
                {d.metadata.get("source", "N/A") for d in docs}
            )
        }


# ============== Singleton ==============
rag_system = AgriRAG()
