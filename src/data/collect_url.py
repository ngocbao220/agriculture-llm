# Cài đặt: pip install ddgs
import unicodedata
import os
import time
from ddgs import DDGS

URL_PATH = "data/urls" # Thư mục lưu URL
os.makedirs(URL_PATH, exist_ok=True)

# Hàm loại bỏ dấu tiếng Việt
def clean_vi_text(text):
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text

# Tìm kiếm tài liệu nông nghiệp
def find_url_documents(plant, num_pdf_files=20):
    # Refined query: Use parentheses for OR and keep it simpler for DDG
    query = f'"{plant}" "kỹ thuật trồng" filetype:pdf (site:gov.vn OR site:edu.vn)'
    print(f"--- Đang tìm tài liệu về: {plant} ---")
    
    results = []
    try:
        with DDGS() as ddgs:
            # Search and filter for relevance
            for r in ddgs.text(query, max_results=num_pdf_files * 10):
                url = r['href']
                title = r.get('title', '').lower()
                
                # Strict filtering: Must be PDF and title/URL should mention the plant or "kỹ thuật"
                if url.lower().endswith(".pdf"):
                    if plant.lower() in title or plant.lower() in url.lower():
                        print(f"Tìm thấy PDF phù hợp: {url}")
                        results.append(url)
                        if len(results) >= num_pdf_files:
                            break
    except Exception as e:
        print(f"Lỗi khi tìm kiếm chính cho {plant}: {e}")
    
    if len(results) < num_pdf_files:
        print(f"Không tìm thấy đủ file PDF chuẩn cho {plant}. Đang thử tìm kiếm rộng hơn...")
        query_fallback = f'"{plant}" "kỹ thuật trồng" filetype:pdf'
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(query_fallback, max_results=num_pdf_files * 10):
                    url = r['href']
                    title = r.get('title', '').lower()
                    if url.lower().endswith(".pdf"):
                        if plant.lower() in title or plant.lower() in url.lower():
                            print(f"Tìm thấy PDF (nguồn ngoài): {url}")
                            results.append(url)
                            if len(results) >= num_pdf_files:
                                break
        except Exception as e:
            print(f"Lỗi khi tìm kiếm rộng cho {plant}: {e}")
            
    return results

# Thu thập URL cho danh sách cây trồng
def collect_urls(plants, num_pdf_files=20):
    for plant in plants:
        tai_lieu = find_url_documents(plant, num_pdf_files=num_pdf_files)
        plant_file = clean_vi_text(plant).lower().replace(" ", "_")
        with open(f"{URL_PATH}/{plant_file}.txt", "w") as f:
            for url in tai_lieu:
                f.write(url + "\n")
        # Nghỉ 2 giây giữa các lần tìm kiếm để tránh bị chặn/timeout
        time.sleep(2)