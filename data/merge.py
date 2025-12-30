import os

# Đường dẫn file
source_file = "cay_thanh_long.jsonl"
target_file = "raw/cay_thanh_long.jsonl"

# Kiểm tra file nguồn
if not os.path.exists(source_file):
    raise FileNotFoundError(f"Không tìm thấy file nguồn: {source_file}")

# Tạo thư mục data nếu chưa tồn tại
os.makedirs(os.path.dirname(target_file), exist_ok=True)

# Nếu file đích chưa tồn tại thì tạo mới
if not os.path.exists(target_file):
    open(target_file, "w", encoding="utf-8").close()

# Gộp file (append)
with open(source_file, "r", encoding="utf-8") as src, \
     open(target_file, "a", encoding="utf-8") as tgt:
    
    for line in src:
        line = line.strip()
        if line:  # bỏ dòng trống
            tgt.write(line + "\n")

print("✅ Đã gộp xong cay_ca_chua.jsonl vào raw/cay_ca_chua.jsonl")
