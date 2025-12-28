import requests
from bs4 import BeautifulSoup
import json
import os
import time

# --- CẤU HÌNH DANH SÁCH CÂY TRỒNG ---
# Danh sách các URL bạn muốn lấy
TARGET_CROPS = [
    {"name": "Cây lúa", "url": "https://camnangcaytrong.com/cay-lua-ctd2.html"},
    {"name": "Cây ngô (Bắp)", "url": "https://camnangcaytrong.com/cay-ngo-bap-ctd5.html"},
    {"name": "Cây khoai tây", "url": "https://camnangcaytrong.com/cay-khoai-tay-ctd15.html"},
    {"name": "Cây cà chua", "url": "https://camnangcaytrong.com/cay-ca-chua-ctd6.html"},
    {"name": "Cây cà phê", "url": "https://camnangcaytrong.com/cay-ca-phe-coffee-ctd17.html"},
    {"name": "Cây thanh long", "url": "https://camnangcaytrong.com/cay-thanh-long-ctd22.html"},
    {"name": "Cây dưa hấu", "url": "https://camnangcaytrong.com/cay-dua-hau-ctd31.html"},
    {"name": "Cây sầu riêng", "url": "https://camnangcaytrong.com/cay-sau-rieng-ctd46.html"}
]

BASE_URL = "https://camnangcaytrong.com"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
}

def get_links_from_category(category_url, max_pages=5):
    """
    Lấy danh sách link bài viết, hỗ trợ phân trang (page=1, page=2...)
    """
    all_links = []
    print(f"   📂 Đang quét: {category_url}")

    for page in range(1, max_pages + 1):
        # Tạo URL phân trang: url?page=x
        separator = "&" if "?" in category_url else "?"
        paged_url = f"{category_url}{separator}page={page}"
        
        print(f"      ➡️ Trang {page}...")
        
        try:
            response = requests.get(paged_url, headers=HEADERS, timeout=15)
            if response.status_code != 200:
                print(f"      ❌ Lỗi kết nối: {response.status_code}")
                break
            
            soup = BeautifulSoup(response.content, 'html.parser')

            # Tìm khung danh sách (listview)
            list_div = soup.find('div', class_='listview')
            if not list_div:
                print("      ⚠️ Hết trang hoặc không tìm thấy danh sách.")
                break

            items = list_div.find_all('li', class_='listitem')
            if not items:
                print("      ⚠️ Không có bài viết nào ở trang này.")
                break
            
            page_count = 0
            for item in items:
                a_tag = item.find('a', class_='title')
                if a_tag and a_tag.get('href'):
                    link = a_tag['href']
                    title = a_tag.get_text(strip=True)
                    
                    if not link.startswith('http'):
                        link = BASE_URL + link
                    
                    # Kiểm tra trùng lặp
                    if not any(x['url'] == link for x in all_links):
                        all_links.append({"url": link, "title": title})
                        page_count += 1
            
            print(f"      + Tìm thấy {page_count} bài mới.")
            
            # Nếu trang này tìm được ít hơn 2 bài, có thể là trang cuối hoặc lỗi -> Dừng sớm để tiết kiệm thời gian
            if page_count < 2:
                break
                
            time.sleep(1) # Nghỉ giữa các trang danh sách

        except Exception as e:
            print(f"      ❌ Lỗi quét trang: {e}")
            break
            
    return all_links

def parse_article_content(item, category_name):
    """Lấy nội dung chi tiết bài viết"""
    url = item['url']
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        content_div = soup.find('div', class_='content-detail')
        if not content_div:
            return None

        # --- LÀM SẠCH RÁC ---
        # Xóa các thành phần không mong muốn
        for junk in content_div.find_all(['div', 'p'], class_=['chude', 'source', 'clear', 'relate', 'pagination-container']):
            junk.decompose()
            
        for a in content_div.find_all('a'):
            if "booking" in a.get('href', '') or "ViewMore" in a.get('href', ''):
                a.decompose()
            if "fancybox" in a.get('class', []):
                a.unwrap()

        # --- TRÍCH XUẤT TEXT ---
        clean_text = ""
        for elem in content_div.find_all(['h2', 'h3', 'p', 'ul', 'img']):
            if elem.name in ['h2', 'h3']:
                text = elem.get_text(strip=True)
                if text: clean_text += f"\n\n### {text}\n"
            
            elif elem.name == 'p':
                # Bỏ qua p nếu nằm trong li
                if elem.find_parent('li'): continue
                text = elem.get_text(strip=True)
                if text: clean_text += f"{text}\n"
                
            elif elem.name == 'ul':
                for li in elem.find_all('li'):
                    li_text = li.get_text(strip=True)
                    if li_text: clean_text += f"- {li_text}\n"
                    
            elif elem.name == 'img':
                alt = elem.get('alt')
                if alt: clean_text += f"[Ảnh: {alt}]\n"

        return {
            "category": category_name, # Gắn nhãn tên cây vào dữ liệu
            "title": item['title'],
            "url": url,
            "content": clean_text.strip(),
            "scraped_at": time.strftime("%Y-%m-%d")
        }

    except Exception as e:
        print(f"      ⚠️ Lỗi đọc bài: {e}")
        return None

def main():
    print("="*60)
    print("🌾 SCRAPER NÔNG NGHIỆP ĐA CÂY TRỒNG")
    print("="*60)
    
    os.makedirs("data", exist_ok=True)
    total_articles = 0
    
    # Duyệt qua từng loại cây trong danh sách
    for crop in TARGET_CROPS:
        print(f"\n🌱 ĐANG XỬ LÝ: {crop['name'].upper()}")
        
        # 1. Lấy danh sách link (quét 5 trang đầu)
        links = get_links_from_category(crop['url'], max_pages=5)
        print(f"   -> Tổng cộng: {len(links)} bài viết cần tải.")
        
        crop_data = []
        
        # 2. Tải chi tiết từng bài
        for i, link in enumerate(links):
            print(f"   [{i+1}/{len(links)}] Đọc: {link['title'][:40]}...")
            
            data = parse_article_content(link, crop['name'])
            
            if data and len(data['content']) > 50:
                crop_data.append(data)
            else:
                print("      ⚠️ Nội dung quá ngắn/Lỗi")
            
            time.sleep(0.5) # Delay nhẹ
            
        # 3. Lưu file riêng cho từng loại cây (cho dễ quản lý)
        # Tên file: cay_ngo_bap.jsonl
        safe_name = crop['name'].replace(" ", "_").replace("(", "").replace(")", "").lower()
        filename = f"data/{safe_name}.jsonl"
        
        with open(filename, "w", encoding="utf-8") as f:
            for item in crop_data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        
        print(f"✅ Đã lưu {len(crop_data)} bài vào {filename}")
        total_articles += len(crop_data)
        
        print("-" * 40)
        time.sleep(2) # Nghỉ giữa các loại cây

    print("\n" + "="*60)
    print(f"🎉 TỔNG KẾT: Đã thu thập {total_articles} bài viết cho tất cả các loại cây.")

if __name__ == "__main__":
    main()