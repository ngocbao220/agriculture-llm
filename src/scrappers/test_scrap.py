import requests
from bs4 import BeautifulSoup
import json
import os
import time

# --- CẤU HÌNH DANH SÁCH CÂY TRỒNG ---
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

def get_all_links_for_crop(crop_url, max_pages=5):
    """
    Hàm tổng hợp link từ cả 2 nguồn:
    1. .listitems (Sâu, bệnh - thường chỉ cần lấy ở trang 1)
    2. .listview (Bài viết chung - cần lật trang)
    """
    collected_links = []
    seen_urls = set() # Dùng để lọc trùng lặp ngay lập tức

    print(f"   📂 Bắt đầu quét link cho: {crop_url}")

    # --- GIAI ĐOẠN 1: QUÉT TRANG ĐẦU (Lấy Sâu/Bệnh + Kỹ thuật mới nhất) ---
    try:
        response = requests.get(crop_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')

        # A. LẤY SÂU & BỆNH (Class: listitems) - Chỉ cần làm ở trang 1
        # Trang thường có 2 khối listitems: 1 cho Sâu, 1 cho Bệnh
        pest_disease_blocks = soup.find_all('div', class_='listitems')
        
        print(f"      + Tìm thấy {len(pest_disease_blocks)} khối Sâu/Bệnh (listitems).")
        
        for block in pest_disease_blocks:
            # Lấy tiêu đề khối (VD: "Sâu, côn trùng hại" hoặc "Bệnh hại")
            block_title = block.find('div', class_='list-title')
            group_name = block_title.get_text(strip=True) if block_title else "Sâu bệnh khác"
            
            # Lấy danh sách link bên trong
            links = block.find_all('a')
            for a in links:
                href = a.get('href')
                title = a.get_text(strip=True)
                
                if href and ".html" in href:
                    full_link = href if href.startswith('http') else BASE_URL + href
                    
                    if full_link not in seen_urls:
                        seen_urls.add(full_link)
                        collected_links.append({
                            "url": full_link,
                            "title": title,
                            "group": group_name # Lưu lại nhóm để biết là sâu hay bệnh
                        })

        # B. LẤY BÀI VIẾT KỸ THUẬT (Class: listview) - Trang 1
        listview = soup.find('div', class_='listview')
        if listview:
            items = listview.find_all('li', class_='listitem')
            for item in items:
                a_tag = item.find('a', class_='title')
                if a_tag:
                    full_link = a_tag['href'] if a_tag['href'].startswith('http') else BASE_URL + a_tag['href']
                    if full_link not in seen_urls:
                        seen_urls.add(full_link)
                        collected_links.append({
                            "url": full_link,
                            "title": a_tag.get_text(strip=True),
                            "group": "Kỹ thuật canh tác"
                        })
                        
    except Exception as e:
        print(f"      ❌ Lỗi quét trang 1: {e}")

    # --- GIAI ĐOẠN 2: PHÂN TRANG (Chỉ lấy thêm bài Kỹ thuật ở listview) ---
    # Sâu bệnh thường cố định ở mọi trang hoặc chỉ trang 1, nên ta không quét lại listitems để tránh trùng
    for page in range(2, max_pages + 1):
        separator = "&" if "?" in crop_url else "?"
        paged_url = f"{crop_url}{separator}page={page}"
        
        print(f"      ➡️ Đang quét trang {page} (tìm bài viết cũ hơn)...")
        try:
            resp = requests.get(paged_url, headers=HEADERS, timeout=15)
            if resp.status_code != 200: break
            
            p_soup = BeautifulSoup(resp.content, 'html.parser')
            
            # Chỉ tìm trong listview (bỏ qua listitems ở các trang sau)
            listview = p_soup.find('div', class_='listview')
            if not listview:
                print("      ⚠️ Hết danh sách bài viết.")
                break
                
            items = listview.find_all('li', class_='listitem')
            if not items: break
            
            count_new = 0
            for item in items:
                a_tag = item.find('a', class_='title')
                if a_tag:
                    full_link = a_tag['href'] if a_tag['href'].startswith('http') else BASE_URL + a_tag['href']
                    if full_link not in seen_urls:
                        seen_urls.add(full_link)
                        collected_links.append({
                            "url": full_link,
                            "title": a_tag.get_text(strip=True),
                            "group": "Kỹ thuật canh tác"
                        })
                        count_new += 1
            
            if count_new == 0:
                print("      ⚠️ Không tìm thấy bài mới ở trang này, dừng phân trang.")
                break
                
            time.sleep(1)
            
        except Exception as e:
            print(f"      ❌ Lỗi phân trang: {e}")
            break
            
    return collected_links

def parse_article_content(item, crop_name):
    """Lấy nội dung chi tiết bài viết"""
    url = item['url']
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        content_div = soup.find('div', class_='content-detail')
        if not content_div:
            return None

        # --- LÀM SẠCH RÁC ---
        # Xóa các phần không mong muốn (quảng cáo, tin liên quan, nguồn)
        for junk in content_div.find_all(['div', 'p'], class_=['chude', 'source', 'clear', 'relate', 'pagination-container']):
            junk.decompose()
            
        for a in content_div.find_all('a'):
            if "booking" in a.get('href', '') or "ViewMore" in a.get('href', ''):
                a.decompose()

        # --- TRÍCH XUẤT TEXT ---
        clean_text = ""
        # Thêm thông tin nhóm vào đầu bài (VD: ### Sâu, côn trùng hại)
        clean_text += f"Phân loại: {item['group']}\n" 
        
        for elem in content_div.find_all(['h2', 'h3', 'p', 'ul', 'table']):
            if elem.name in ['h2', 'h3']:
                text = elem.get_text(strip=True)
                if text: clean_text += f"\n### {text}\n"
            
            elif elem.name == 'p':
                if elem.find_parent('li') or elem.find_parent('table'): continue
                text = elem.get_text(strip=True)
                if text: clean_text += f"{text}\n"
                
            elif elem.name == 'ul':
                for li in elem.find_all('li'):
                    li_text = li.get_text(strip=True)
                    if li_text: clean_text += f"- {li_text}\n"
            
            # Xử lý bảng (Table) - rất quan trọng cho bài thuốc BVTV
            elif elem.name == 'table':
                rows = elem.find_all('tr')
                for row in rows:
                    cols = [c.get_text(strip=True) for c in row.find_all(['td', 'th'])]
                    clean_text += " | ".join(cols) + "\n"

        return {
            "category": crop_name,
            "group": item['group'], # Lưu thêm thông tin: Sâu hại, Bệnh hại, hay Kỹ thuật
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
    print("🌾 SCRAPER TOÀN DIỆN (SÂU BỆNH + KỸ THUẬT)")
    print("="*60)
    
    os.makedirs("data/raw", exist_ok=True) # Lưu vào data/raw để chuẩn bị cho bước embed
    
    for crop in TARGET_CROPS:
        print(f"\n🌱 ĐANG XỬ LÝ: {crop['name'].upper()}")
        
        # 1. Lấy danh sách link (Listitems + Listview)
        links = get_all_links_for_crop(crop['url'], max_pages=3)
        print(f"   -> Tổng cộng: {len(links)} bài viết (Sâu/Bệnh/Kỹ thuật).")
        
        crop_data = []
        
        # 2. Tải chi tiết từng bài
        for i, link_item in enumerate(links):
            print(f"   [{i+1}/{len(links)}] [{link_item['group']}] {link_item['title'][:40]}...")
            
            data = parse_article_content(link_item, crop['name'])
            
            if data and len(data['content']) > 50:
                crop_data.append(data)
            
            time.sleep(0.5) 
            
        # 3. Lưu file chuẩn hóa tên (lúa.jsonl, ngô.jsonl...)
        # Tự động map tên file đẹp: Cây lúa -> cay_lua.jsonl
        import unicodedata
        safe_name = unicodedata.normalize('NFKD', crop['name']).encode('ascii', 'ignore').decode('utf-8')
        safe_name = safe_name.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_")
        if "ngo" in safe_name: safe_name = "cay_ngo" # Fix riêng cho ngô/bắp
        
        filename = f"data/raw/{safe_name}.jsonl"
        
        with open(filename, "w", encoding="utf-8") as f:
            for item in crop_data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        
        print(f"✅ Đã lưu {len(crop_data)} bài vào {filename}")
        time.sleep(2)

    print("\n" + "="*60)
    print("🎉 HOÀN THÀNH THU THẬP DỮ LIỆU!")

if __name__ == "__main__":
    main()