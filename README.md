# 🚗 Xanh SM Enterprise Production RAG System (Phase 5)

Hệ thống **Retrieval-Augmented Generation (RAG)** cấp doanh nghiệp (Production-Grade) được thiết kế và tối ưu hóa đặc biệt dành riêng cho **Xanh SM** nhằm phục vụ bốn nhóm đối tượng cốt lõi:
* 👤 **Khách hàng (Customer)** - Giải đáp về đặt xe, phí hủy chuyến, chính sách hoàn tiền, đặt đồ ăn (Xanh Food), giao hàng.
* 🚗 **Đối tác tài xế (Driver)** - Giải đáp chiết khấu doanh thu, tác phong làm việc, chế tài phạt.
* 🏪 **Đối tác cửa hàng (Merchant)** - Giải đáp hoa hồng Xanh Food/Express, quy trình đối soát tuần.
* 🎧 **Nhân viên CSKH (Admin/Agent)** - Quản trị hệ thống, đánh giá Benchmarking realtime, theo dõi log truy vấn, Ingestion tự động.

Hệ thống này triển khai kiến trúc **NLU-Gateway RAG (Phase 5)** tiên tiến nhất hiện nay với tốc độ xử lý siêu tốc:
`Question ➔ Safety Guardrail ➔ Intent Classifier ➔ Slot Filling (Task/RAG) ➔ Memory Query Rewrite ➔ Hybrid Search (Qdrant Dense + BM25) ➔ Cross-Encoder Reranker ➔ Adjacent Context Expansion ➔ LLM Synthesizer ➔ Server-Sent Events (SSE) Stream ➔ Citation Validator`.

> [!IMPORTANT]
> **🚀 LIVE PRODUCTION:** Hệ thống hỗ trợ hoàn chỉnh đăng nhập Google Auth, lưu trữ lịch sử chat cá nhân, và giao diện Dashboard quản trị mạnh mẽ.

---

## 🏗️ 1. Kiến Trúc Thư Mục Dự Án

Mã nguồn được tổ chức theo cấu trúc Full-Stack hiện đại:

```text
RAG_XANH_SM/
│
├── app/                      # Backend FastAPI Cốt Lõi
│   ├── ingestion/            # Pipeline nạp dữ liệu & dọn dẹp sạch sẽ CSDL vector cũ
│   │   ├── chunking.py       # Phân đoạn heading-aware với Parent-Child (400 ký tự)
│   │   ├── embedding.py      # Bộ sinh Dense Vector (OpenAI)
│   │   └── ingest.py         # Quét thư mục, bóc tách và Upsert vào Qdrant + Postgres
│   │
│   ├── vectordb/
│   │   └── qdrant_client.py  # Quản lý giao tiếp Qdrant (Hỗ trợ Native Hybrid Search & RRF)
│   │
│   ├── retrieval/
│   │   ├── hybrid_search.py  # Hybrid Search kết hợp Dense/Sparse Vector từ Qdrant
│   │   ├── multi_query.py    # Query Expansion mở rộng truy vấn đồng nghĩa tiếng Việt
│   │   └── reranker.py       # Cross-Encoder Reranker xếp hạng lại Top 10 tài liệu
│   │
│   ├── rag/
│   │   ├── prompt.py         # Prompt hệ thống tối ưu hóa tác phong và trích nguồn
│   │   ├── gateway.py        # Conversation Gateway (Regex chặn từ cấm tức thì ~0ms)
│   │   ├── classifier.py     # Intent Classifier & Slot Filling (Xử lý Small-talk & Task-agent)
│   │   └── chain.py          # Chuỗi RAG chính, xử lý SSE Stream trả về Frontend
│   │
│   ├── api/                  # FastAPI REST Endpoints
│   │   ├── admin.py          # Quản trị hệ thống, Benchmark Ragas và Ingestion
│   │   ├── auth.py           # Xác thực Google OAuth2 & Guest Session
│   │   ├── chat.py           # Phân phối luồng chat stream SSE
│   │   └── conversations.py  # Quản lý lịch sử hội thoại khách hàng
│   │
│   ├── core/                 # Cấu hình & Tiện ích chung
│   │   ├── config.py         # Cấu hình biến môi trường và thiết lập hệ thống
│   │   ├── security.py       # Xử lý JWT Token và bảo mật phân quyền admin
│   │   └── logger.py         # Ghi log CSV cấu trúc tách biệt hệ thống và lỗi
│   │
│   └── db/                   # Quản lý Database PostgreSQL/SQLite (Lịch sử Chat, Users, Logs, Chunks)
│
├── crawler/                  # Module cào dữ liệu từ trang chủ Xanh SM
│   ├── crawler.py            # Page Crawler thu thập HTML/PDF
│   ├── discovery.py          # URL Discovery tự động phát hiện liên kết
│   ├── run_crawler.py        # Điều phối Orchestration cào dữ liệu
│   └── storage.py            # Lưu trữ tài liệu thô
│
├── data/                     # Thư mục chứa tài liệu Markdown thô (Crawler tạo ra)
│
├── logs/                     # Thư mục chứa log hệ thống dạng CSV (system_logs.csv, error_log.csv)
│
├── frontend/                 # React + Vite Frontend UI (Stitch Architecture)
│   ├── src/components/       # Component UI module hóa (ChatLayout, Dashboard...)
│   └── src/api.js            # Xử lý REST API và đọc luồng SSE theo thời gian thực
│
├── evaluation/               # Hệ thống Benchmark Ragas tự động đánh giá RAG
│   ├── golden_dataset.py     # Bộ dữ liệu câu hỏi và câu trả lời chuẩn (Ground Truth)
│   └── ragas_eval.py         # Script chạy đánh giá tự động đo lường chất lượng RAG
│
├── docs/                     # Tài liệu đặc tả kỹ thuật nội bộ
├── requirements.txt          # Thư viện phụ thuộc (FastAPI, Qdrant-client, Sentence-transformers...)
└── README.md                 # Hướng dẫn khởi chạy và vận hành
```

---

## ⚡ 2. Luồng Xử Lý Phase 5 NLU-Gateway RAG (Tối Ưu Unification & Early Cache)

Hệ thống hoạt động qua các bước khép kín với các lớp bảo vệ và tối ưu hóa hiệu năng vượt trội:

```mermaid
graph TD
    A([👤 User Input]) --> B[🛡️ API Gateway & Guardrails]
    B -- "Từ chối (~0ms)" --> Block[❌ Chặn nội dung vi phạm]
    B -- "Hợp lệ" --> C{⚡ 1. Early Cache Lookup}
    
    %% Cache Hit từ câu hỏi gốc
    C -- "Có (Cache Hit - ~5ms)" --> I([📡 Trả về kết quả ngay lập tức])
    
    %% Cache Miss
    C -- "Không (Cache Miss)" --> D[🔮 2. NLU Gateway 3-trong-1]
    
    %% Phân nhánh Ý định
    D -- "small-talk" --> Stalk[🤖 Trả lời xã giao nhanh]
    D -- "rag" --> E{⚡ 3. Second Cache Lookup}
    
    %% Cache Hit từ câu hỏi đã viết lại
    E -- "Có (Cache Hit)" --> I
    
    %% Luồng RAG đầy đủ
    E -- "Không (Cache Miss)" --> F[🔎 Hybrid Search Qdrant]
    F --> G[⚡ Cross-Encoder Reranker]
    G --> H[🔄 Parent-Child Context Expansion]
    H --> J[🧠 LLM Context Synthesis]
    J --> K[📝 Lưu Cache kép cho cả câu thô & câu viết lại]
    K --> I
    
    style A fill:#00A651,stroke:#fff,color:#fff
    style I fill:#00A651,stroke:#fff,color:#fff
    style Block fill:#ff4444,stroke:#fff,color:#fff
    style Stalk fill:#0099ff,stroke:#fff,color:#fff
```

### Chi tiết các công nghệ và thông số kỹ thuật:
- **API Gateway & Guardrails**: Sử dụng biểu thức chính quy (`re` Python) để kiểm tra heuristic siêu tốc với độ trễ ~0ms. Chặn tức thì các câu hỏi chứa từ cấm hoặc nhạy cảm.
- **Early Cache Lookup (Kiểm tra Cache sớm)**: Truy vấn chính xác câu hỏi gốc trong cơ sở dữ liệu `SemanticCache` (SQL). Nếu khớp, hệ thống trả về kết quả ngay lập tức trong **~5-10ms** mà không phải gọi bất kỳ API LLM nào, tối ưu hóa 100% tài nguyên và chi phí.
- **NLU Gateway 3-trong-1**: Tích hợp gộp 3 bước (Query Rewrite, Intent Classification, và Query Expansion) vào **1 lần gọi LLM duy nhất** (GPT-4o-mini). Nhờ đó, giảm độ trễ xử lý tiền RAG từ **~4.5s xuống còn ~1.5s**.
  - Ý định được phân loại thành: `small-talk` (lời chào, tán gẫu) hoặc `rag` (các câu hỏi tra cứu chính sách).
  - Tác vụ sinh ra thêm **1 câu hỏi đồng nghĩa** để hỗ trợ tìm kiếm đa chiều.
- **Second Cache Lookup**: Nếu câu hỏi được LLM viết lại khác với câu hỏi thô, hệ thống kiểm tra cache lần 2 để tăng tỷ lệ trúng cache trước khi truy vấn Qdrant.
- **Hybrid Search**: Giao tiếp với **Qdrant Vector Database** (`qdrant-client`). Hệ thống quét và lấy ra **Top 25 tài liệu thô** (`limit=25`) bằng công nghệ Native RRF kết hợp Dense Vector (`text-embedding-3-small`) và Sparse Vector (FastEmbed BM25).
- **Cross-Encoder Reranker**: Chấm điểm lại 25 tài liệu trên bằng PyTorch `sentence_transformers` (mô hình `cross-encoder/ms-marco-MiniLM-L-6-v2`) và chỉ giữ lại **Top 10 tài liệu tinh** khắt khe nhất. Điều này giúp loại bỏ kết quả nhiễu trước khi mở rộng ngữ cảnh.
- **Adaptive Parent-Child Section Expansion**: Mở rộng ngữ cảnh động bằng kiến trúc Parent-Child đối với 10 tài liệu đã qua sàng lọc. Nếu chunk thô đạt điểm xếp hạng lại (`rerank_score`) >= 0.7, hệ thống truy quét Qdrant để lấy toàn bộ các chunk con thuộc cùng mục lớn (`parent_chunk_id`), tối đa 10 chunks, nhằm tái cấu trúc trọn vẹn phần/điều khoản gốc. Với các chunk có điểm < 0.7, hệ thống giữ nguyên chunk gốc để tránh loãng ngữ cảnh. Khi gộp các chunk, hệ thống tự động loại bỏ các tiêu đề trùng lặp ở đầu các chunk con thứ cấp (idx > 0) và loại bỏ trùng lặp nếu chunk thô khác nằm gọn trong khối đã mở rộng để tối ưu hóa kích thước prompt.
- **LLM Synthesis & Stream**: Tổng hợp ngữ cảnh bằng `openai` (GPT-4o-mini), truyền dữ liệu từng chữ về trình duyệt (Server-Sent Events) kèm chuỗi JSON chứa Nguồn tài liệu (`sources`). Độ trễ (`total_latency_ms` và `generation_latency_ms`) được tính toán và chốt ngay khi hệ thống nhận được ký tự đầu tiên chứa nội dung từ OpenAI (TTFT). Điều này giúp loại bỏ hoàn toàn thời gian LLM nhả chữ/typewriter kéo dài sau đó, đảm bảo chỉ số phản ánh chính xác hiệu năng xử lý thực tế của máy chủ.

---

## 🛠️ 3. Các Tính Năng Nổi Bật Chuẩn Production

### 💎 A. Trích Dẫn Nguồn Minh Bạch (Citations)
Mọi câu trả lời từ RAG đều đi kèm với các thẻ trích dẫn chính xác (Nguồn file, mục điều khoản). Frontend sẽ tự động đọc luồng JSON ở cuối Stream và render thành các nút bấm URL để khách hàng có thể click mở file gốc kiểm chứng.

### 💎 B. Đồng Bộ Hóa VectorDB & PostgreSQL Tự Động (Ingestion)
Khi nhân viên bấm nút **Nạp dữ liệu**, hệ thống sẽ:
1. Xóa toàn bộ dữ liệu Chunk cũ của tài liệu đó trong **Postgres**.
2. Nạp mới toàn bộ Chunk vào Postgres để hiển thị minh bạch cho Admin.
3. Sinh Dense + Sparse Vectors và Upsert trực tiếp vào **Qdrant** qua UUID đồng bộ.

### 💎 C. Tự Động Sửa Lỗi Encoding & OpenMP (Crash-Free)
Hệ thống được lập trình phòng ngự vững chắc để đối phó với môi trường Windows:
- Ngăn chặn lỗi C++ `libiomp5md.dll` khi dùng PyTorch.
- Ép buộc luồng stdout của Windows Console sang `utf-8` để ngăn chặn lỗi Crash `UnicodeEncodeError` khi stream các ký tự Tiếng Việt (Á, Ế, Ố).

### 💎 D. Realtime Benchmarking (Đánh Giá RAGAS)
Hệ thống tích hợp Framework đánh giá AI `ragas`. Quản trị viên có thể bấm nút đánh giá Realtime trên Dashboard để hệ thống tự động bốc ngẫu nhiên câu hỏi, chạy thử RAG, và tính toán điểm **Faithfulness** (Độ trung thực) và **Answer Relevance** (Độ chính xác).

### 💎 E. Hệ Thống Ghi Log Đa Kênh Tích Hợp Database (PostgreSQL & CSV)
Hệ thống sử dụng bộ ghi log tùy biến mạnh mẽ (`logger.py`) để ghi nhận toàn bộ tiến trình hoạt động và lỗi phát sinh. Màn hình console/terminal được tắt in logs để tối ưu hóa hiệu năng và bảo mật.
- **Log File (CSV)**: Phân tách dữ liệu thành `logs/system_logs.csv` (lưu mọi cấp độ logs) và `logs/error_log.csv` (chỉ lưu `WARN`/`ERROR`).
- **Log Database (PostgreSQL/SQLite)**: Đồng bộ ghi logs vào bảng `system_logs` trong CSDL nhằm hỗ trợ đọc và lưu trữ logs lâu dài khi triển khai trên các đám mây không có ổ đĩa ghi đè (như Railway).
- **Quản trị API**: Admin có thể truy vấn trực tiếp logs hệ thống qua API GET `/api/admin/system-logs`. Mỗi log lưu trữ đầy đủ `timestamp`, `level`, `phase` (giai đoạn xảy ra: `AUTH`, `CHAT`, `NLU`, `TASK_AGENT`, `RETRIEVAL`, `RERANK`, `LLM_GEN`, `CACHE`, `INGESTION`, `EVAL`, `CRAWLER`), `error_type` (như `ValueError`), `message`, và `details`.

### 💎 F. Thiết Kế Nhận Biết Bảng Biểu Tránh Vỡ Dữ Liệu (Table-Aware Chunking)
Hệ thống tích hợp bộ phát hiện và xử lý bảng biểu Markdown thông minh (Table-Aware Splitter) trong Ingestion Pipeline:
1. **Cô lập cấu trúc bảng (Table Isolation)**: Tự động phát hiện các khối bảng biểu Markdown. Khi khối bảng có kích thước dưới 1500 ký tự, hệ thống sẽ cô lập bảng đó thành một chunk độc lập hoàn chỉnh, tránh việc trộn lẫn với các đoạn văn bản xung quanh hoặc bị phân tách dở dang làm phá vỡ cấu trúc cột/dòng.
2. **Bảo toàn ngữ nghĩa cột (Header Replication)**: Đối với các bảng biểu lớn vượt quá 1500 ký tự, thuật toán tự động chia nhỏ bảng theo dòng nhưng luôn nhân bản phần tiêu đề cột (column headers) vào đầu mỗi chunk con. Điều này đảm bảo tính toàn vẹn ngữ nghĩa của cấu trúc cột/dòng bảng biểu, giúp mô hình Embedding ghi nhận ngữ cảnh chính xác và LLM tổng hợp thông tin chuẩn xác nhất.

---

## 🚀 4. Hướng Dẫn Khởi Chạy Cục Bộ (Local)

### 📦 A. Yêu Cầu Môi Trường
- **Python 3.10+**
- **Node.js 18+**
- **Docker & Docker Compose** (Chạy Qdrant và PostgreSQL)

### 📦 B. Khởi Động Databases Bằng Docker
```bash
# Trong thư mục dự án, chạy lệnh:
docker-compose up -d
```
Lệnh này sẽ khởi động:
- **Qdrant** trên cổng `6333`
- **PostgreSQL** trên cổng `5432`

### 📦 C. Cài Đặt & Cấu Hình Backend
1. **Tạo môi trường ảo & Cài thư viện:**
```bash
python -m venv venv
venv\Scripts\activate  # Trên Windows
# source venv/bin/activate  # Trên Linux/macOS
pip install -r requirements.txt
```

2. **Cấu hình biến môi trường (`.env`):**
Copy file `.env.example` thành `.env` và điền key OpenAI của bạn:
```env
OPENAI_API_KEY=sk-proj-xxxx...
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4o-mini
RERANKER_PROVIDER=local
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2

DATABASE_URL=postgresql://postgres:password@localhost:5432/greensm_db
QDRANT_URL=http://localhost:6333
```
*Lưu ý:* Lần đầu chạy, hệ thống chưa có dữ liệu vector. Hãy mở Dashboard và bấm **Crawl** -> **Ingestion** để nạp tri thức vào Qdrant!

3. **Chạy Server FastAPI:**
```bash
# KHÔNG dùng cờ --reload khi đang test môi trường production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 📦 D. Cài Đặt & Khởi Chạy Frontend
Mở một Terminal thứ 2:
```bash
cd frontend
npm install
npm run dev
```
Truy cập hệ thống tại: **[http://localhost:5173](http://localhost:5173)**

---

## ☁️ 5. Hướng Dẫn Triển Khai Lên Đám Mây Railway (Deploy)

Hệ thống được thiết kế để dễ dàng đưa lên Production thông qua [Railway.app](https://railway.app).

1. Tạo một project trên Railway.
2. Thêm **PostgreSQL Database** plugin từ Railway.
3. Liên kết Github Repo của dự án vào Railway.
4. Chuyển sang tab **Variables** và cấu hình các thông số y hệt file `.env`:
   - `OPENAI_API_KEY`: Key của bạn.
   - `DATABASE_URL`: Sử dụng Connection URL nội bộ của PostgreSQL plugin (Railway tự cấp phát).
   - `QDRANT_URL`: URL cụm Qdrant Cloud của bạn (Nên tạo tài khoản trên Qdrant Cloud miễn phí).
   - `GOOGLE_CLIENT_ID`: Client ID Google Auth.
   - `PORT`: `8000`.
5. Railway sẽ tự động detect Python (thông qua `requirements.txt`) và chạy lệnh `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. 
6. Đối với frontend (`React/Vite`), bạn có thể deploy lên **Vercel**, **Netlify**, hoặc tạo một service tĩnh (Static Site) thứ 2 ngay trong Railway. Đừng quên thay đổi biến `API_BASE` ở `frontend/src/api.js` trỏ về domain backend Railway của bạn!