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
API_URL = f"http://{BASE_URL}:9000/ask_agri"

def chat_with_h200():
    print("--- 🌾 Hệ thống Chẩn đoán Nông nghiệp (UET AI Lab) ---")
    print("--- Gõ 'exit' để thoát ---")

    while True:
        user_input = input("\n👤 Bạn: ").strip()
        if user_input.lower() in ["exit", "quit", "thoát"]: break
        if not user_input: continue

        try:
            print("🤖 AI đang suy nghĩ...", end="\r")
            
            response = requests.post(API_URL, params={"question": user_input}, timeout=300)

            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")
                sources = data.get("sources", [])

                print(f"🤖 AI: {answer}")
                
                # HIỂN THỊ NGUỒN: Sửa key từ 'url' thành 'source'
                if sources:
                    links = set() # Dùng set để tránh trùng lặp link
                    for src in sources:
                        link = src.get('source') # Lấy key 'source' đã lưu trong FAISS
                        if link: links.add(link)
                    
                    if links:
                        print("\n📚 Nguồn tham khảo:")
                        for l in links: print(f"   - {l}")
            else:
                print(f"❌ Lỗi Server: {response.status_code}")
        except Exception as e:
            print(f"❌ Lỗi kết nối: {e}")

if __name__ == "__main__":
    chat_with_h200()