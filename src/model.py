import requests
import json
import os

API_URL = "http://0.0.0.0:9000/ask_agri"

def chat_with_h200():
    print("--- 🌾 Hệ thống Chẩn đoán Nông nghiệp (UET AI Lab) ---")
    print("--- Gõ 'exit' để thoát ---")

    while True:
        user_input = input("\n👤 Bạn: ").strip()
        if user_input.lower() in ["exit", "quit", "thoát"]: break
        if not user_input: continue

        try:
            print("🤖 AI đang suy nghĩ...", end="\r")
            
            response = requests.post(API_URL, params={"question": user_input}, timeout=300)

            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")
                sources = data.get("sources", [])

                print(f"🤖 AI: {answer}")
                
                # HIỂN THỊ NGUỒN: Sửa key từ 'url' thành 'source'
                if sources:
                    links = set() # Dùng set để tránh trùng lặp link
                    for src in sources:
                        link = src.get('source') # Lấy key 'source' đã lưu trong FAISS
                        if link: links.add(link)
                    
                    if links:
                        print("\n📚 Nguồn tham khảo:")
                        for l in links: print(f"   - {l}")
            else:
                print(f"❌ Lỗi Server: {response.status_code}")
        except Exception as e:
            print(f"❌ Lỗi kết nối: {e}")

if __name__ == "__main__":
    chat_with_h200()