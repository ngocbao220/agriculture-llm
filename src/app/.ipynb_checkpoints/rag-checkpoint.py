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
            context = "Kho tri thức hiện tại không có thông tin liên quan trực tiếp."
        else:
            context = "\n\n".join(f"- {d.page_content}" for d in docs)
    
        return f"""
            Bạn là người tư vấn nông nghiệp, giao tiếp thân thiện và dễ hiểu.
            
            Phong cách trả lời:
            - Thân thiện, gần gũi
            - Tư vấn thực tế, không học thuật cứng nhắc
            - Không kể chuyện lan man
            - Không dùng câu sáo rỗng hoặc cảnh báo máy móc
            
            Nguyên tắc nội dung:
            - Ưu tiên sử dụng thông tin trong [NGỮ CẢNH]
            - Có thể bổ sung kiến thức nông nghiệp phổ biến nếu cần để làm rõ ý
            - Không bịa đặt số liệu hoặc kỹ thuật chuyên sâu ngoài ngữ cảnh
            - Không bắt buộc phải nói rằng dữ liệu thiếu nếu vẫn trả lời được
            
            Cách trả lời:
            - Trả lời chi tiết, có chiều sâu
            - Nêu rõ: cách làm, điều kiện áp dụng và lưu ý
            - Có thể dùng gạch đầu dòng cho dễ theo dõi
            Cách trình bày (bắt buộc):
                - Không dùng định dạng Markdown
                - Không dùng gạch đầu dòng có dấu "-"
                - Không in đậm, in nghiêng
                - Trình bày bằng đoạn văn, có thể xuống dòng tự nhiên

            
            [NGỮ CẢNH]
            {context}
            
            [CÂU HỎI]
            {question}
            
            [TRẢ LỜI]
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
