from data.collect_url import collect_urls
from data.download_pdf import download_pdfs
from data.preprocessing import preprocess_pdfs
from rag.vector_store import create_vector_store

if __name__ == "__main__":
    plants = [
        "Lúa",
        "Ngô",
        "Khoai tây",
        "Cà phê",
        "Cao su",
        "Sầu riêng"
    ]

    # Bước 1: Thu thập URL tài liệu
    # print("Bắt đầu thu thập URL tài liệu...")
    # collect_urls(plants=plants)
    # print("Hoàn thành thu thập URL tài liệu.")

    # Bước 2: Tải các file PDF từ URL đã thu thập
    # print("Bắt đầu tải các file PDF từ URL đã thu thập...")
    # download_pdfs()
    # print("Hoàn thành tải các file PDF.")

    # Bước 3: Parse và Chunking
    print("Bắt đầu Parse và Chunking tài liệu...")
    chunks = preprocess_pdfs()
    print(f"Hoàn thành. Tổng cộng có {len(chunks)} chunks.")

    # Bước 4: Embedding và lưu vào Vector Store
    if chunks:
        print("Bắt đầu tạo Vector Store...")
        create_vector_store(chunks)
        print("Hoàn thành tạo Vector Store.")
    else:
        print("Không có dữ liệu để tạo Vector Store.")
