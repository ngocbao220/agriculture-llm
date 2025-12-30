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


RAW_DIR = "data/raw"
VECTOR_DB_PATH = "data/vector_db/agri_vector"


def load_all_raw_data():
    all_items = []

    for filename in os.listdir(RAW_DIR):
        file_path = os.path.join(RAW_DIR, filename)

        if filename.endswith(".jsonl"):
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    all_items.append(json.loads(line))

        elif filename.endswith(".json"):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_items.extend(data)

    return all_items


def update_knowledge_base():
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )

    raw_data = load_all_raw_data()
    langchain_docs = []

    for item in raw_data:
        doc = Document(
            page_content=(
                f"Cây trồng: {item.get('crop', 'N/A')}\n"
                f"Tiêu đề: {item.get('title', '')}\n"
                f"Nội dung: {item.get('content', '')}"
            ),
            metadata={
                "source": item.get("url", ""),
                "date": item.get("date", ""),
                "crop": item.get("crop", "")
            }
        )
        langchain_docs.append(doc)

    final_chunks = text_splitter.split_documents(langchain_docs)

    if os.path.exists(VECTOR_DB_PATH):
        vectorstore = FAISS.load_local(
            VECTOR_DB_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )
        vectorstore.add_documents(final_chunks)
    else:
        vectorstore = FAISS.from_documents(final_chunks, embeddings)

    vectorstore.save_local(VECTOR_DB_PATH)
    print(f"✅ Đã cập nhật FAISS cho toàn bộ dữ liệu nông nghiệp")


if __name__ == "__main__":
    update_knowledge_base()
