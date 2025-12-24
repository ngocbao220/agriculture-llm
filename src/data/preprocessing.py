import os
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

PDF_PATH = "data/pdfs"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100

def preprocess_pdfs():
    """
    Duyệt qua các thư mục PDF, parse nội dung và chia nhỏ thành các chunk.
    """
    all_chunks = []
    
    if not os.path.exists(PDF_PATH):
        print(f"Thư mục {PDF_PATH} không tồn tại.")
        return []

    for plant_folder in os.listdir(PDF_PATH):
        folder_path = os.path.join(PDF_PATH, plant_folder)
        if not os.path.isdir(folder_path):
            continue
            
        print(f"--- Đang xử lý tài liệu cho: {plant_folder.upper()} ---")
        
        for pdf_file in os.listdir(folder_path):
            if not pdf_file.lower().endswith(".pdf"):
                continue
                
            file_path = os.path.join(folder_path, pdf_file)
            print(f"Đang parse: {pdf_file}")
            
            try:
                # Sử dụng Unstructured để parse PDF
                loader = UnstructuredPDFLoader(file_path)
                docs = loader.load()
                
                # Chia nhỏ văn bản
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=CHUNK_SIZE,
                    chunk_overlap=CHUNK_OVERLAP,
                    length_function=len,
                )
                chunks = text_splitter.split_documents(docs)
                
                # Gán thêm metadata về cây trồng
                for chunk in chunks:
                    chunk.metadata["plant"] = plant_folder
                    chunk.metadata["source"] = pdf_file
                
                all_chunks.extend(chunks)
                print(f"Đã tạo {len(chunks)} chunks từ {pdf_file}")
                
            except Exception as e:
                print(f"Lỗi khi xử lý {pdf_file}: {e}")
                
    return all_chunks

if __name__ == "__main__":
    chunks = preprocess_pdfs()
    print(f"Tổng cộng đã tạo {len(chunks)} chunks.")
