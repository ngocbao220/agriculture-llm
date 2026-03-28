import requests
import time
import json
import os
from bs4 import BeautifulSoup
from datetime import datetime

# =========================
# GOOGLE SEARCH CONFIG
# =========================
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
CX_ID = "f77c64a16502f4fe8"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

KEYWORDS_1 = ["kỹ thuật", "chăm sóc", "sâu bệnh", "phòng trừ"]

TARGET_CROPS = [
    {"name": "Cây lúa", "file": "data/cay_lua.jsonl"},
    {"name": "Cây ngô (Bắp)", "file": "data/cay_ngo.jsonl"},
    {"name": "Cây khoai tây", "file": "data/cay_khoai_tay.jsonl"},
    {"name": "Cây cà chua", "file": "data/cay_ca_chua.jsonl"},
    {"name": "Cây cà phê", "file": "data/cay_ca_phe.jsonl"},
    {"name": "Cây thanh long", "file": "data/cay_thanh_long.jsonl"},
    {"name": "Cây dưa hấu", "file": "data/cay_dua_hau.jsonl"},
    {"name": "Cây sầu riêng", "file": "data/cay_sau_rieng.jsonl"}
]

# =========================
# GOOGLE SEARCH
# =========================
def google_search(query, num=10):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": CX_ID,
        "q": query,
        "num": num
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    return [item["link"] for item in data.get("items", [])]

# =========================
# LOAD EXISTING URLS (JSONL)
# =========================
def load_existing_urls(path):
    urls = set()
    if not os.path.exists(path):
        return urls

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                urls.add(obj.get("url"))
            except json.JSONDecodeError:
                continue
    return urls

# =========================
# TEXT NORMALIZATION
# =========================
def normalize_text(text):
    text = text.replace("\n", " ")
    return " ".join(text.split())

# =========================
# CRAWL SFARM ARTICLE
# =========================
def crawl_sfarm_article(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else ""

    content_div = soup.find("div", class_="entry-content single-page")
    if not content_div:
        return None

    for tag in content_div.find_all(["script", "style", "iframe", "img", "figure"]):
        tag.decompose()

    text = "\n".join(
        t.get_text(strip=True)
        for t in content_div.find_all(["p", "h2", "h3", "li"])
    )

    text = normalize_text(text)
    if not text:
        return None

    text_lower = text.lower()
    if "sâu" in text_lower or "côn trùng" in text_lower:
        group = "Sâu, côn trùng hại"
    elif "bệnh" in text_lower:
        group = "Bệnh hại"
    elif "kỹ thuật" in text_lower or "chăm sóc" in text_lower:
        group = "Kỹ thuật canh tác"
    else:
        group = "Khác"

    return {
        "title": title,
        "group": group,
        "content": text
    }

# =========================
# APPEND JSONL RECORD
# =========================
def append_record(file_path, category, data, url):
    record = {
        "category": category,
        "group": data["group"],
        "title": data["title"],
        "url": url,
        "content": data["content"],
        "scraped_at": datetime.now().strftime("%Y-%m-%d")
    }

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

# =========================
# MAIN PIPELINE
# =========================
def crawl_and_append_crop(crop):
    crop_name = crop["name"]
    file_path = crop["file"]

    print(f"\n🌱 Đang crawl: {crop_name}")
    existing_urls = load_existing_urls(file_path)

    urls = set()
    for kw in KEYWORDS_1:
        query = f"{kw} {crop_name} site:sfarm.vn"
        try:
            urls.update(google_search(query))
            time.sleep(1)
        except Exception as e:
            print("❌ Search error:", e)

    print(f"🔗 Tìm được {len(urls)} link")

    for url in urls:
        if url in existing_urls:
            continue

        try:
            data = crawl_sfarm_article(url)
            if not data:
                continue

            append_record(file_path, crop_name, data, url)
            print("✅ Saved:", url)
            time.sleep(1)

        except Exception as e:
            print("❌ Crawl error:", url, e)

# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    for crop in TARGET_CROPS:
        crawl_and_append_crop(crop)

    print("\n🎉 HOÀN THÀNH TOÀN BỘ")
