import os    
import torch

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

VECTOR_DB_PATH = "data/faiss_index"

def create_vector_store(chunks):
    """
    Tạo vector store từ các chunks sử dụng model BGE-M3.
    """
    print("--- Đang khởi tạo Embedding Model (BGE-M3) ---")

    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available() and torch.backends.mps.is_built():
        device = "mps"
    else:
        device = "cpu"

    print(f"Using device: {device}")
    print(f"Device using: {device}")
    # Sử dụng BGE-M3 cho tiếng Việt tốt
    model_name = "BAAI/bge-m3"
    model_kwargs = {'device': device} # Chuyển sang 'cuda' hoặc 'mps' nếu có GPU
    encode_kwargs = {'normalize_embeddings': True}
    
    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )
    
    print(f"--- Đang tạo Vector Store với {len(chunks)} chunks ---")
    vector_db = FAISS.from_documents(chunks, embeddings)
    
    # Lưu vector store xuống đĩa
    os.makedirs(os.path.dirname(VECTOR_DB_PATH), exist_ok=True)
    vector_db.save_local(VECTOR_DB_PATH)
    print(f"Đã lưu Vector Store tại: {VECTOR_DB_PATH}")
    
    return vector_db

def load_vector_store():
    """
    Load vector store đã lưu.
    """
    model_name = "BAAI/bge-m3"
    embeddings = HuggingFaceEmbeddings(model_name=model_name)
    
    if os.path.exists(VECTOR_DB_PATH):
        return FAISS.load_local(VECTOR_DB_PATH, embeddings, allow_dangerous_deserialization=True)
    else:
        print("Không tìm thấy Vector Store.")
        return None
