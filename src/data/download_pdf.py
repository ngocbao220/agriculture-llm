URL_PATH = "data/urls" # Thư mục lưu URL
PDF_PATH = "data/pdfs"  # Thư mục lưu PDF đã tải về

"""
Tải các file pdf ở thư mục url về thư mục pdf
"""

import os
import requests

def download_pdfs():
    os.makedirs(PDF_PATH, exist_ok=True)
    for url_file in os.listdir(URL_PATH):
        print("--- Đang xử lý cho cây trồng:", url_file.upper().replace(".txt", ""), "---")
        with open(os.path.join(URL_PATH, url_file), "r") as f:
            for line in f:
                url = line.strip()
                if not url:
                    continue
                try:
                    # Thêm timeout 10 giây để tránh bị treo
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    pdf_name = url.split('/')[-1]

                    plant_folder = url_file.replace('.txt', '')
                    plant_folder_path = os.path.join(PDF_PATH, plant_folder)

                    os.makedirs(plant_folder_path, exist_ok=True)
                    pdf_path = os.path.join(plant_folder_path, pdf_name)

                    with open(pdf_path, "wb") as pdf_file:
                        pdf_file.write(response.content)
                    print(f"Tải về thành công: {pdf_name}")
                except Exception as e:
                    print(f"Lỗi khi tải {url}: {e}")
