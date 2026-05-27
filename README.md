# 🚗 Xanh SM Enterprise Production RAG System

Hệ thống **Retrieval-Augmented Generation (RAG)** cấp doanh nghiệp (Production-Grade) được thiết kế và tối ưu hóa đặc biệt dành riêng cho **Xanh SM** nhằm phục vụ bốn nhóm đối tượng cốt lõi:
* 👤 **Khách hàng (Customer)** - Giải đáp về đặt xe, phí hủy chuyến, chính sách hoàn tiền, đặt đồ ăn (Xanh Food), giao hàng.
* 🚗 **Đối tác tài xế (Driver)** - Giải đáp chiết khấu doanh thu, tác phong làm việc, chế tài phạt.
* 🏪 **Đối tác cửa hàng (Merchant)** - Giải đáp hoa hồng Xanh Food/Express, quy trình đối soát tuần.
* 🎧 **Nhân viên CSKH (Agent)** - Truy cập toàn diện để giải quyết các khiếu nại phức tạp.

Thay vì sử dụng Basic RAG (dễ gây ra sai lệch trích dẫn và ảo tưởng thông tin), hệ thống này triển khai một pipeline nâng cao:
`Question ➔ Query Expansion ➔ Role-Filtered Shared Search ➔ Hybrid Search (Dense + BM25) ➔ Reranker ➔ Context Compression ➔ LLM ➔ Answer + Verified Citation`.

Để hiểu sâu sắc về kiến trúc, hệ tư duy thiết kế và các bài giảng kỹ thuật của dự án, vui lòng đọc [MINDSET.md](file:///c:/Users/DUNG/Desktop/RAG_XANH_SM/MINDSET.md).

> [!IMPORTANT]
> **🚀 LIVE PRODUCTION DEMO:** Trải nghiệm trực tiếp chatbot RAG CSKH Xanh SM tại địa chỉ: **[ragxanhsmv1-production.up.railway.app](https://ragxanhsmv1-production.up.railway.app/)**

---

## 🏗️ 1. Kiến Trúc Thư Mục Dự Án

Mã nguồn được tổ chức theo cấu trúc module hóa chuẩn sản xuất:

```text
RAG_XANH_SM/
│
├── app/
│   ├── crawler/
│   │   ├── crawl.py          # BFS Web Crawler thu thập link nội bộ & Phân loại thông minh
│   │   └── parser.py         # Chuyển đổi sạch HTML sang Markdown (giữ bảng biểu)
│   │
│   ├── ingestion/
│   │   ├── splitter.py       # Phân đoạn heading-aware (MarkdownHeaderSplitter + Recursive)
│   │   ├── embedding.py      # Bộ sinh embeddings thông minh (Tự phục hồi fallback khi key lỗi)
│   │   └── ingest.py         # Pipeline nạp dữ liệu từ thư mục data/ vào CSDL
│   │
│   ├── vectordb/
│   │   └── chroma_client.py  # Quản lý dense vector index (Hỗ trợ Singleton Fallback DB & Shared Filter)
│   │
│   ├── retrieval/
│   │   ├── bm25_retriever.py # Mô hình từ khóa chính xác BM25 (Hỗ trợ lọc Role linh hoạt)
│   │   ├── hybrid_search.py  # Hybrid Search kết hợp RRF & Logic Tự Động Đồng Bộ/Nạp Startup
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
│   ├── customer/             # Chính sách đặc thù khách hàng (terms.md, refund.md)
│   ├── driver/               # Quy chế tác phong tài xế & chiết khấu thưởng (commission.md)
│   ├── merchant/             # Quy định đối tác cửa hàng (merchant_policy.md)
│   └── faq/                  # Hướng dẫn đặt xe, đặt đồ ăn, giúp đỡ chung (booking.md, vn_vi_helps.md...)
│
├── MINDSET.md                # Hệ tư duy thiết kế, sơ đồ Mermaid và nhật ký sửa lỗi phân quyền
├── requirements.txt          # Các thư viện phụ thuộc của hệ thống
├── run_tests.py              # Suite chấm điểm và đánh giá tự động RAGAS
└── README.md                 # Hướng dẫn khởi chạy và vận hành hệ thống
```

---

## ⚡ 2. Các Tính Năng Thông Minh Nổi Bật Cấp Doanh Nghiệp

### 1. Unified Shared Filter (Ngăn rò rỉ dữ liệu chéo nhưng chia sẻ tri thức chung)
Khắc phục hoàn toàn điểm yếu cô lập thông tin của các RAG cơ bản. Hệ thống ánh xạ quyền truy cập tài liệu thông minh:
* **Khách hàng (Customer)** được phép truy quét tài liệu `customer` + `faq` (mở khóa tài liệu gọi đồ ăn Xanh Food, trung tâm hỗ trợ tổng đài).
* **Tài xế (Driver)** được phép truy quét tài liệu `driver` + `faq`.
* **Cửa hàng (Merchant)** được truy quét `merchant` + `faq`.
* **CSKH (Agent)** được phép xem toàn bộ tài liệu.
Mức độ bảo mật được áp dụng trực tiếp tại tầng truy vấn Database (sử dụng toán tử `$in` của ChromaDB và lọc danh sách của BM25), ngăn chặn triệt để 100% rủi ro rò rỉ dữ liệu qua tấn công Prompt Injection của người dùng.

### 2. Auto-Sync Volume & Auto-Ingestion (Khởi chạy tự chữa lành - Self-Healing)
* **Tự động đồng bộ ổ đĩa vĩnh viễn**: Khi chạy trên đám mây (Railway) có gắn đĩa cứng vĩnh viễn (Volume), hệ thống sẽ tự động phát hiện nếu ổ đĩa trống lúc khởi chạy lần đầu và tự động sao chép toàn bộ kho tài liệu Markdown mặc định vào Volume.
* **Tự động nạp vector**: Nếu cấu hình ChromaDB thật (`CHROMA_PROVIDER=chromadb`) nhưng CSDL vector trống rỗng, hệ thống sẽ tự động phân mảnh và nạp toàn bộ tài liệu vào CSDL ngay khi khởi chạy mà không cần quản trị viên tác động.

### 3. Heading-Aware Splitter & MD5 ASCII Chunk IDs
* Bảo vệ tính toàn vẹn của các bảng biểu giá cước xe, bảng chiết khấu bằng cách phân đoạn Markdown theo Heading trước, sau đó mới gối ký tự (`chunk_size=700`, `overlap=150`).
* Tạo mã định danh Chunk ID dạng mã hóa MD5 ASCII sạch để tránh xung đột hoặc treo luồng (HNSWLib lock) trên một số nền tảng host Windows/Linux.

### 4. Resilient Self-Healing Fallback (Tự động phục hồi lỗi ngoại tuyến)
* Tự động bỏ qua lỗi C++ SQLite DLL trên Windows bằng cách chuyển hướng thông minh sang **In-Memory Fallback VectorDB**.
* Tự động chuyển đổi sang Mock Embeddings & Offline Fallback Synthesis khi phát hiện OpenAI API Key nhập sai/hết hạn để đảm bảo hệ thống không bao giờ bị sập (Crash-free) và luôn sẵn sàng phản hồi thông tin chính sách thô.

---

## 🚀 3. Hướng Dẫn Khởi Chạy Hệ Thống Chi Tiết

Dưới đây là các bước để cài đặt và chạy dự án locally trên máy tính của bạn sử dụng hệ điều hành Windows:

### Bước 1: Kích hoạt Môi trường Ảo (Virtual Environment)
Powershell tại thư mục dự án và chạy lệnh sau để kích hoạt môi trường ảo:

```powershell
# Bật quyền thực thi script của Windows (nếu gặp lỗi Execution Policy)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Kích hoạt môi trường ảo
.\venv\Scripts\Activate.ps1
```

### Bước 2: Cấu hình API Key trong file `.env`
Mở file `.env` trong thư mục gốc và điền khóa OpenAI API Key của bạn để sử dụng đầy đủ tính năng sinh văn bản nâng cao:

```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx
```

### Bước 3: Khởi chạy Premium Streamlit Dashboard (Khuyên dùng)
Đây là giao diện Dashboard cao cấp hiển thị song song khung Chatbot (bên trái) và **Đồ thị Thinking Tree** + các bước suy nghĩ chi tiết của RAG (bên phải), kèm Tab đánh giá tự động RAGAS và Kho tài liệu:

```powershell
streamlit run app/api/streamlit_ui.py
```
*Trình duyệt sẽ tự động mở trang Dashboard tại địa chỉ: **`http://localhost:8501`***

### Bước 4: Khởi chạy FastAPI Server (Dành cho lập trình viên tích hợp)
Nếu bạn muốn tích hợp chatbot RAG này vào ứng dụng di động Xanh SM hoặc website chính thức thông qua REST API:

```powershell
uvicorn app.api.routes:app --reload --port 8000
```
*Truy cập cổng Swagger UI tương tác để thử nghiệm API tại: **`http://127.0.0.1:8000/docs`***

### Bước 5: Chạy Suite Đánh Giá Chất Lượng RAGAS tự động
Để đo lường độ trễ phản hồi, độ chính xác định dạng trích nguồn (Citations) và tỷ lệ thu hồi từ khóa trên bộ 5 kịch bản vàng (Gold Dataset):

```powershell
python run_tests.py
```

---

## ☁️ 4. Hướng Dẫn Triển Khai Lên Đám Mây Railway vĩnh viễn

Khi triển khai lên Railway, do đĩa cứng mặc định của container là đĩa tạm (Ephemeral), chúng ta cần cấu hình ổ cứng vĩnh viễn (Volume) để tránh bị mất dữ liệu khi restart hoặc deploy bản mới.

### Bước 1: Tạo và gắn Railway Volume
1. Truy cập **Railway Dashboard** ➔ Chọn dịch vụ RAG của bạn.
2. Đi tới tab **Settings** ➔ Cuộn xuống mục **Volumes** ➔ Chọn **Add Volume**.
3. Cấu hình đĩa dung lượng từ `5 GB` trở lên và đặt **Mount Path** là:
   ```text
   /app/persistent_storage
   ```
4. Lưu cấu hình. Railway sẽ tự động restart dịch vụ.

### Bước 2: Cấu hình Environment Variables trên Railway
Chuyển sang tab **Variables** trên Railway và thêm các biến cấu hình sau để hệ thống tự động lưu trữ dữ liệu vĩnh viễn trên ổ đĩa vừa mount:

| Biến Môi Trường | Giá trị cấu hình | Ý nghĩa |
| :--- | :--- | :--- |
| **`CHROMA_PROVIDER`** | `chromadb` | Kích hoạt cơ sở dữ liệu ChromaDB thật chạy trên Linux |
| **`DATA_DIR`** | `/app/persistent_storage/data` | Đường dẫn lưu trữ tài liệu vĩnh viễn trên Volume |
| **`CHROMA_PERSIST_DIR`** | `/app/persistent_storage/chroma_db` | Đường dẫn lưu trữ cơ sở dữ liệu vector ChromaDB |
| **`OPENAI_API_KEY`** | `sk-proj-xxxx...` | Khóa OpenAI API Key chính thức của bạn |

*Khi có cấu hình này, hệ thống thông minh của chúng ta sẽ tự sao chép dữ liệu chính sách mặc định sang Volume và tự động nạp index ChromaDB ngay khi app khởi động lần đầu tiên trên Cloud!*