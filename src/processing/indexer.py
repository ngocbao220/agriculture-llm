# src/processing/indexer.py
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import EMBED_MODEL

def update_knowledge_base():
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    
    # Đọc dữ liệu cào được
    with open("data/raw/latest_news.jsonl", "r", encoding="utf-8") as f:
        new_data = [json.loads(line) for line in f]
    
    # Phân loại và cập nhật FAISS theo từng loại cây
    for crop in set(item['crop'] for item in new_data):
        crop_docs = [item for item in new_data if item['crop'] == crop]
        langchain_docs = []
        
        for item in crop_docs:
            doc = Document(
                page_content=f"Cây: {item['crop']}\nTiêu đề: {item['title']}\nNội dung: {item['content']}",
                metadata={"source": item['url'], "date": item['date']}
            )
            langchain_docs.append(doc)
            
        final_chunks = text_splitter.split_documents(langchain_docs)
        
        # Lưu vào folder riêng cho từng loại cây
        path = f"data/vector_db/{crop}"
        if os.path.exists(path):
            vectorstore = FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
            vectorstore.add_documents(final_chunks)
        else:
            vectorstore = FAISS.from_documents(final_chunks, embeddings)
        
        vectorstore.save_local(path)
        print(f"📂 Đã cập nhật tri thức cho cây: {crop}")

if __name__ == "__main__":
    update_knowledge_base()