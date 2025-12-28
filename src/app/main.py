# src/app/main.py
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import LLM_MODEL, EMBED_MODEL
from dotenv import load_dotenv
load_dotenv()  # tự động tìm file .env

BASE_URL = f"http://{os.getenv('FPT_ENDPOINT')}:{os.getenv('FPT_PORT')}/v1"
API_KEY = os.getenv("API_KEY")

# 1. Khởi tạo LLM trên H200
llm = ChatOpenAI(base_url=BASE_URL, api_key=API_KEY, model=LLM_MODEL, temperature=0.2)
embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

def get_rag_chain(crop_type):
    path = f"data/vector_db/{crop_type}"
    if not os.path.exists(path): return None
    
    vectorstore = FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
    
    prompt = ChatPromptTemplate.from_template("""
    Bạn là chuyên gia tư vấn nông nghiệp số của UET. 
    Dựa vào các bài báo và tài liệu sau:
    {context}
    
    Hãy trả lời câu hỏi: {input}
    (Nếu có thông tin, hãy ghi rõ: "Theo nguồn Nông nghiệp Môi trường...")
    """)
    
    doc_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(vectorstore.as_retriever(), doc_chain)

def start_chatbot():
    print("--- 🌾 Hệ thống RAG Nông nghiệp Việt Nam (H200 Powered) ---")
    current_crop = "sầu riêng" # Mặc định
    
    while True:
        user_input = input(f"\n👤 [{current_crop}] Bạn: ").strip()
        if user_input.lower() in ['exit', 'quit']: break
        
        # Logic chuyển đổi loại cây thông minh
        if "lúa" in user_input.lower(): current_crop = "lúa"
        elif "cà phê" in user_input.lower(): current_crop = "cà phê"
        
        chain = get_rag_chain(current_crop)
        if not chain:
            print("⚠️ Chưa có dữ liệu cho loại cây này. Hãy chạy scraper trước!")
            continue
            
        print("🤖 AI: ", end="", flush=True)
        response = chain.invoke({"input": user_input})
        print(response["answer"])

if __name__ == "__main__":
    start_chatbot()