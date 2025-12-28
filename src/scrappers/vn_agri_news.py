# src/scrapers/vn_agri_news.py
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import CROPS

def scrape_crop_data(crop_name):
    """Scrape tin tức nông nghiệp cho một loại cây trồng"""
    print(f"\n🔍 Đang tìm thông tin về: {crop_name}...")
    
    crop_keyword = crop_name.replace(" ", "+").lower()

    search_url = f"https://nongnghiepmoitruong.vn/{crop_keyword}-search/from-to-category-20/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': 'https://nongnghiepmoitruong.vn/'
    }
    
    results = []
    
    try:
        print(f"🔗 URL: {search_url}")
        response = requests.get(search_url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"   ❌ Status code: {response.status_code}")
            return results
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Tìm search count để xác nhận có kết quả
        search_count = soup.find('p', class_='search-count')
        if search_count:
            print(f"   📊 {search_count.text.strip()}")
        
        # Tìm list-news-home div
        news_list = soup.find('div', class_='list-news-home')
        if not news_list:
            print("   ❌ Không tìm thấy list-news-home")
            return results
        
        # Tìm tất cả các items
        articles = news_list.find_all('li', class_='news-home-item')
        print(f"   📰 Tìm thấy {len(articles)} bài viết")
        
        if not articles:
            print("   ⚠️ Không có bài viết nào")
            return results
        
        for art in articles[:5]:  # Lấy 5 bài đầu
            try:
                # Tìm thẻ <a> với href
                link_tag = art.find('a', href=True)
                if not link_tag:
                    continue
                
                link = link_tag['href']
                if not link.startswith('http'):
                    link = 'https://nongnghiepmoitruong.vn' + link
                
                # Lấy title từ attribute title của thẻ <a>
                title = link_tag.get('title', '').strip()
                
                # Nếu không có title attribute, thử tìm trong news-info
                if not title:
                    news_info = art.find('div', class_='news-info')
                    if news_info:
                        title_tag = news_info.find('a')
                        if title_tag:
                            title = title_tag.get('title', title_tag.text.strip())
                
                if not title:
                    print(f"   ⚠️ Không tìm thấy tiêu đề cho {link}")
                    continue
                
                # Kiểm tra trùng lặp
                if any(r['url'] == link for r in results):
                    continue
                
                print(f"   ✓ {title[:60]}...")
                
                # Lấy nội dung chi tiết
                time.sleep(1)  # Delay để tránh spam
                detail_response = requests.get(link, headers=headers, timeout=15)
                
                if detail_response.status_code != 200:
                    print(f"   ⚠️ Không lấy được nội dung: status {detail_response.status_code}")
                    content = "Không lấy được nội dung chi tiết"
                else:
                    d_soup = BeautifulSoup(detail_response.content, 'html.parser')
                    
                    # Tìm nội dung bài viết
                    content_div = (
                        d_soup.find('div', class_='detail-content') or
                        d_soup.find('div', class_='content-detail') or
                        d_soup.find('div', class_='entry-content') or
                        d_soup.find('article', class_='content')
                    )
                    
                    if content_div:
                        # Lấy tất cả đoạn văn
                        paragraphs = content_div.find_all('p')
                        content_parts = []
                        for p in paragraphs:
                            text = p.get_text(strip=True)
                            if text and len(text) > 20:  # Chỉ lấy đoạn có nội dung
                                content_parts.append(text)
                        
                        content = " ".join(content_parts)
                        
                        # Nếu không có content, thử lấy toàn bộ text
                        if not content:
                            content = content_div.get_text(strip=True)
                    else:
                        content = "Không tìm thấy nội dung chi tiết"
                
                results.append({
                    "crop": crop_name,
                    "title": title,
                    "content": content[:2000] if len(content) > 2000 else content,  # Giới hạn 2000 ký tự
                    "url": link,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "scraped_at": datetime.now().isoformat()
                })
                
            except Exception as e:
                print(f"   ⚠️ Lỗi khi xử lý bài viết: {str(e)}")
                continue
        
    except Exception as e:
        print(f"   ❌ Lỗi khi scrape: {str(e)}")
    
    print(f"✅ Tìm được {len(results)} bài viết cho {crop_name}")
    return results

def main():
    """Hàm chính để chạy scraper"""
    print("=" * 70)
    print("🌾 BẮT ĐẦU SCRAPE DỮ LIỆU TIN TỨC NÔNG NGHIỆP")
    print("=" * 70)
    
    all_news = []
    failed_crops = []
    
    for i, crop in enumerate(CROPS, 1):
        try:
            print(f"\n[{i}/{len(CROPS)}] Đang xử lý: {crop}")
            crop_news = scrape_crop_data(crop)
            
            if crop_news:
                all_news.extend(crop_news)
            else:
                failed_crops.append(crop)
            
            # Delay giữa các loại cây để tránh bị chặn
            if i < len(CROPS):
                time.sleep(2)
                
        except Exception as e:
            print(f"❌ Lỗi nghiêm trọng khi scrape {crop}: {str(e)}")
            failed_crops.append(crop)
    
    # Lưu kết quả
    os.makedirs("data/raw", exist_ok=True)
    output_file = "data/raw/latest_news.jsonl"
    
    with open(output_file, "w", encoding="utf-8") as f:
        for item in all_news:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    # In báo cáo tổng kết
    print("\n" + "=" * 70)
    print(f"✅ HOÀN THÀNH!")
    print(f"📊 Đã lưu {len(all_news)} bài báo vào {output_file}")
    
    if failed_crops:
        print(f"\n⚠️ Không tìm được tin tức cho {len(failed_crops)} loại cây:")
        for crop in failed_crops:
            print(f"   - {crop}")
    
    # Thống kê chi tiết
    if all_news:
        print("\n📈 Thống kê theo loại cây:")
        crop_counts = {}
        for item in all_news:
            crop_counts[item['crop']] = crop_counts.get(item['crop'], 0) + 1
        
        for crop, count in sorted(crop_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {crop}: {count} bài")
        
        # Tính tổng số ký tự
        total_chars = sum(len(item['content']) for item in all_news)
        print(f"\n📝 Tổng số ký tự nội dung: {total_chars:,}")
    
    print("=" * 70)
    return len(all_news)

if __name__ == "__main__":
    main()