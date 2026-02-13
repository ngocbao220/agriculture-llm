# 🌾 AgriMind AI - Hệ thống Tư vấn Nông nghiệp Thông minh

**RAG + Fine-tuned LLM cho lĩnh vực Nông nghiệp Việt Nam**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 📋 Mục lục

- [Giới thiệu](#giới-thiệu)
- [Tính năng](#tính-năng)
- [Kiến trúc hệ thống](#kiến-trúc-hệ-thống)
- [Cài đặt](#cài-đặt)
- [Sử dụng](#sử-dụng)
- [Cấu hình](#cấu-hình)
- [Cấu trúc dự án](#cấu-trúc-dự-án)

## 🎯 Giới thiệu

AgriMind AI là hệ thống tư vấn nông nghiệp thông minh sử dụng kết hợp:

- **RAG (Retrieval-Augmented Generation)**: Truy xuất thông tin từ cơ sở tri thức nông nghiệp
- **Fine-tuned LLM**: Mô hình ngôn ngữ lớn được tinh chỉnh cho lĩnh vực nông nghiệp
- **Vision AI**: Phân tích hình ảnh cây trồng để chẩn đoán bệnh

Hệ thống hỗ trợ **8 loại cây trồng** chính: Sầu riêng, Lúa, Cà phê, Thanh long, Dưa hấu, Ngô, Khoai tây, Cà chua.

## ✨ Tính năng

### 1. 💬 Chatbot Tư vấn Nông nghiệp

- Trả lời câu hỏi về kỹ thuật canh tác, phòng trừ sâu bệnh
- Tư vấn phân bón, chăm sóc cây trồng
- Hỗ trợ tiếng Việt tự nhiên

### 2. 🔍 RAG System

- Vector database với FAISS
- Embedding model: **BAAI/bge-m3** (tối ưu cho tiếng Việt)
- Semantic search với metadata filtering theo loại cây trồng

### 3. 🖼️ Vision AI

- Phân tích hình ảnh cây trồng
- Chẩn đoán bệnh và đưa ra khuyến nghị
- API endpoint riêng biệt

### 4. 🎨 Web Interface

- Giao diện Streamlit/Gradio thân thiện
- Streaming response như ChatGPT
- Upload ảnh và phân tích trực tiếp

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────┐
│   User Input    │
│ (Text/Image)    │
└────────┬────────┘
         │
         ├──────────────┐
         │              │
    ┌────▼─────┐   ┌───▼────────┐
    │ Logic API│   │ Vision API  │
    │  (RAG)   │   │  (Image)    │
    └────┬─────┘   └───┬────────┘
         │             │
    ┌────▼─────────────▼─────┐
    │   FAISS Vector DB      │
    │   (Agricultural KB)    │
    └────────┬───────────────┘
             │
    ┌────────▼───────────────┐
    │  vLLM + Fine-tuned    │
    │  Qwen2.5-32B-Instruct │
    └───────────────────────┘
```

## 🚀 Cài đặt

### Bước 1: Clone repository

```bash
git clone https://github.com/your-username/agriculture-llm.git
cd agriculture-llm
```

### Bước 2: Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### Bước 3: Chuẩn bị dữ liệu

```bash
# Scrape dữ liệu nông nghiệp
python src/scrappers/scrap_sfarm.py

# Tạo vector database
python src/processing/indexer.py
```

### Bước 4: Khởi động vLLM server (optional)

```bash
vllm serve Qwen/Qwen2.5-32B-Instruct \
  --host 0.0.0.0 \
  --port 8500 \
  --enable-lora \
  --lora-modules agri-lora=/path/to/lora (pretrained LoRA weights)
```

## 💻 Sử dụng

### 1. Khởi động Web UI

```bash
streamlit run src/app/demo_ui.py
```

Truy cập: `http://localhost:8501`

### 2. Sử dụng API

#### Logic API (RAG)

```python
import requests

response = requests.post(
    "http://localhost:33778/ask",
    json={"question": "Cách phòng trừ sâu đục thân trên cây lúa?"}
)
print(response.json()["answer"])
```

#### Vision API

```python
import requests

with open("image.jpg", "rb") as f:
    files = {"file": f}
    response = requests.post(
        "http://localhost:35239/analyze",
        files=files
    )
print(response.json()["symptoms"])
```

## 📁 Cấu trúc dự án

```
agriculture-llm/
├── config.py                 # Cấu hình chung
├── requirements.txt          # Dependencies
├── README.md
│
├── src/
│   ├── main.py              # Entry point
│   ├── app/
│   │   ├── demo_ui.py       # Streamlit UI
│   │   ├── logic_api.py     # RAG API
│   │   ├── vision_api.py    # Vision API
│   │   └── rag.py           # RAG core logic
│   │
│   ├── processing/
│   │   └── indexer.py       # FAISS indexing
│   │
│   └── scrappers/
│       ├── scrap_sfarm.py   # Data scraping
│       └── vn_agri_news.py  # News scraping
│
├── data/
│   ├── raw/                 # Raw JSONL data
│   ├── vector_db/           # FAISS index
│   └── conversation.jsonl   # Chat logs
│
└── setup/                   # Setup notes & guides
```

## 🛠️ API Endpoints

### Logic API

- **URL**: `http://tcp-endpoint.serverless.fptcloud.jp:33778/ask`
- **Method**: POST
- **Body**: `{"question": "string"}`
- **Response**: `{"answer": "string", "sources": [...]}`

### Vision API

- **URL**: `http://tcp-endpoint.serverless.fptcloud.jp:35239/analyze`
- **Method**: POST
- **Body**: `multipart/form-data` with image file
- **Response**: `{"symptoms": "string", "recommendations": "string"}`

## 🔧 Development

### Scrape dữ liệu mới

```bash
python src/scrappers/scrap_sfarm.py
```

### Rebuild vector database

```bash
python src/processing/indexer.py
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 👥 Authors

- Ngọc Bảo - [GitHub](https://github.com/your-username)

## 🙏 Acknowledgments

- [Qwen2.5](https://huggingface.co/Qwen) for the base LLM
- [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3) for Vietnamese embeddings
- Vietnamese agriculture communities for domain knowledge

---
