# 🚗 Xanh SM Enterprise Production RAG System

Hệ thống **Retrieval-Augmented Generation (RAG)** cấp doanh nghiệp (Production-Grade) được thiết kế và tối ưu hóa đặc biệt dành riêng cho **Xanh SM** nhằm phục vụ bốn nhóm đối tượng cốt lõi:
* 👤 **Khách hàng (Customer)** - Giải đáp về đặt xe, phí hủy chuyến, chính sách hoàn tiền.
* 🚗 **Đối tác tài xế (Driver)** - Giải đáp chiết khấu doanh thu, tác phong làm việc, chế tài phạt.
* 🏪 **Đối tác cửa hàng (Merchant)** - Giải đáp hoa hồng Xanh Food/Express, quy trình đối soát tuần.
* 🎧 **Nhân viên CSKH (Agent)** - Truy cập toàn diện để giải quyết các khiếu nại phức tạp.

Thay vì sử dụng Basic RAG (dễ gây ra sai lệch trích dẫn và ảo tưởng thông tin), hệ thống này triển khai một pipeline nâng cao:
`Question ➔ Query Understanding ➔ Hybrid Search (Dense + BM25) ➔ Reranker ➔ Context Compression ➔ LLM ➔ Answer + Verified Citation`.

---

## 🏗️ 1. Kiến Trúc Thư Mục Dự Án

Mã nguồn được tổ chức theo cấu trúc module hóa chuẩn sản xuất:

```text
RAG_XANH_SM/
│
├── app/
│   ├── crawler/
│   │   ├── crawl.py          # BFS Web Crawler thu thập link nội bộ
│   │   └── parser.py         # Chuyển đổi sạch HTML sang Markdown (giữ bảng biểu)
│   │
│   ├── ingestion/
│   │   ├── splitter.py       # Phân đoạn heading-aware (MarkdownHeaderSplitter + Recursive)
│   │   ├── embedding.py      # Bộ sinh embeddings thông minh (Tự phục hồi fallback khi key lỗi)
│   │   └── ingest.py         # Pipeline nạp dữ liệu từ thư mục data/ vào CSDL
│   │
│   ├── vectordb/
│   │   └── chroma_client.py  # Quản lý dense vector index (Hỗ trợ Singleton Fallback DB)
│   │
│   ├── retrieval/
│   │   ├── bm25_retriever.py # Mô hình từ khóa chính xác BM25 (Hỗ trợ lọc Role)
│   │   ├── hybrid_search.py  # Hybrid Search kết hợp RRF (Reciprocal Rank Fusion)
│   │   ├── multi_query.py    # Query Expansion mở rộng truy vấn đồng nghĩa tiếng Việt
│   │   └── reranker.py       # Cross-Encoder Reranker xếp hạng lại Top 5 tài liệu
│   │
│   ├── rag/
│   │   ├── prompt.py         # Prompt hệ thống tối ưu hóa tác phong và trích nguồn
│   │   └── chain.py          # Chuỗi RAG điều phối Router ➔ Search ➔ Rerank ➔ LLM
│   │
│   ├── api/
│   │   ├── routes.py         # FastAPI REST Server endpoints phục vụ tích hợp
│   │   └── streamlit_ui.py   # Dashboard giao diện Chatbot & Đồ thị Thinking Tree
│   │
│   └── config.py             # Quản lý biến môi trường và cấu hình hệ thống
│
├── data/                     # Thư mục chứa tài liệu chính sách được cấu trúc hóa
│   ├── customer/             # Chính sách khách hàng (terms.md, refund.md)
│   ├── driver/               # Quy chế tác phong tài xế & chiết khấu thưởng (commission.md)
│   ├── merchant/             # Quy định đối tác cửa hàng (merchant_policy.md)
│   └── faq/                  # Hỏi đáp đặt xe thường gặp (booking.md)
│
├── requirements.txt          # Các thư viện phụ thuộc của hệ thống
├── run_tests.py              # Suite chấm điểm và đánh giá tự động RAGAS
└── README.md                 # Hướng dẫn khởi chạy và vận hành hệ thống
```

---

## ⚡ 2. Các Tính Năng Nổi Bật Cấp Doanh Nghiệp

1. **Role Pre-Filtering (Ngăn ngừa rò rỉ dữ liệu chéo)**: Lọc chính sách dựa trên Metadata `role` trước khi tìm kiếm. Tài xế hỏi cước phí thưởng sẽ không bị lẫn sang điều khoản của khách hàng.
2. **Heading-Aware Splitter (Phân đoạn thông minh)**: Bảo vệ tính toàn vẹn của các điều khoản pháp lý bằng cách chia nhỏ tài liệu theo Heading trước, sau đó mới dùng Splitter ký tự.
3. **Hybrid Search & RRF**: Kết hợp giữa tìm kiếm ngữ nghĩa (Dense Search) và tìm kiếm từ khóa chính xác (BM25) thông qua thuật toán Reciprocal Rank Fusion (RRF).
4. **Resilient Self-Healing Fallback (Tự động phục hồi)**: 
   - Tự động bỏ qua lỗi C++ SQLite DLL trên Windows bằng cách chuyển hướng thông minh sang **In-Memory Fallback VectorDB**.
   - Tự động chuyển đổi sang Mock Embeddings & Offline Synthesis khi phát hiện OpenAI API Key nhập sai/hết hạn để đảm bảo hệ thống không bao giờ bị sập (Crash-free).

---

## 🚀 3. Hướng Dẫn Khởi Chạy Hệ Thống Chi Tiết

Dưới đây là các bước để cài đặt và chạy dự án locally trên máy tính của bạn sử dụng hệ điều hành Windows:

### Bước 1: Kích hoạt Môi trường Ảo (Virtual Environment)
Môi trường ảo `venv` và các file cấu hình đã được tạo sẵn trong thư mục gốc. Hãy mở Powershell tại thư mục dự án và chạy lệnh sau để kích hoạt:

```powershell
# Bật quyền thực thi script của Windows (nếu gặp lỗi Execution Policy)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Kích hoạt môi trường ảo
.\venv\Scripts\Activate.ps1
```

### Bước 2: Cấu hình API Key trong file `.env`
Mở file `.env` trong thư mục dự án của bạn và điền khóa OpenAI API Key của bạn để sử dụng đầy đủ tính năng sinh văn bản nâng cao:

```env
# Mở file .env và cập nhật khóa của bạn:
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx
```

### Bước 3: Nạp và Phân tích Dữ liệu Chính sách (Ingestion)
Để đọc toàn bộ tài liệu chính sách chi tiết trong thư mục `data/`, thực hiện cắt phân đoạn thông minh và nạp vào cơ sở dữ liệu:

```powershell
python app/ingestion/ingest.py
```

### Bước 4: Khởi chạy Premium Streamlit Dashboard (Khuyên dùng)
Đây là giao diện Dashboard cao cấp hiển thị song song khung Chatbot (bên trái) và **Đồ thị Thinking Tree** + các bước suy nghĩ chi tiết của RAG (bên phải), kèm Tab đánh giá tự động:

```powershell
.\venv\Scripts\streamlit.exe run app/api/streamlit_ui.py
```
*Trình duyệt sẽ tự động mở trang Dashboard tại địa chỉ: **`http://localhost:8501`***

### Bước 5: Khởi chạy FastAPI Server (Dành cho nhà phát triển)
Nếu bạn muốn tích hợp chatbot RAG này vào ứng dụng di động Xanh SM hoặc website chính thức, khởi chạy REST API Server:

```powershell
.\venv\Scripts\uvicorn.exe app.api.routes:app --reload --port 8000
```
*Truy cập cổng Swagger UI tương tác để thử nghiệm API tại: **`http://127.0.0.1:8000/docs`***

### Bước 6: Chạy Suite Đánh Giá Chất Lượng RAGAS tự động
Để đo lường độ trễ phản hồi, độ chính xác định dạng trích nguồn (Citations) và tỷ lệ thu hồi từ khóa trên bộ 5 kịch bản vàng (Gold Dataset):

```powershell
python run_tests.py
```

---