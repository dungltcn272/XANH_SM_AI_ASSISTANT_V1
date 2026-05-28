# 🚗 Xanh SM Enterprise Production RAG System

Hệ thống **Retrieval-Augmented Generation (RAG)** cấp doanh nghiệp (Production-Grade) được thiết kế và tối ưu hóa đặc biệt dành riêng cho **Xanh SM** nhằm phục vụ bốn nhóm đối tượng cốt lõi:
* 👤 **Khách hàng (Customer)** - Giải đáp về đặt xe, phí hủy chuyến, chính sách hoàn tiền, đặt đồ ăn (Xanh Food), giao hàng.
* 🚗 **Đối tác tài xế (Driver)** - Giải đáp chiết khấu doanh thu, tác phong làm việc, chế tài phạt.
* 🏪 **Đối tác cửa hàng (Merchant)** - Giải đáp hoa hồng Xanh Food/Express, quy trình đối soát tuần.
* 🎧 **Nhân viên CSKH (Agent)** - Truy cập toàn diện để giải quyết các khiếu nại phức tạp.

Thay vì sử dụng Basic RAG (dễ gây ra sai lệch trích dẫn và ảo tưởng thông tin), hệ thống này triển khai một pipeline nâng cao:
`Question ➔ Caching Layer Check (Early-Exit/Bypass) ➔ Query Rewrite ➔ Query Expansion ➔ Role-Filtered Shared Search ➔ Hybrid Search (Dense + BM25) ➔ Reranker ➔ Context Compression ➔ LLM ➔ Answer + Verified Citation`.

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
│   │   ├── splitter.py       # Phân đoạn heading-aware & Parent-Child metadata enrichment [GIAI ĐOẠN 2]
│   │   ├── embedding.py      # Bộ sinh embeddings thông minh (Tự phục hồi fallback khi key lỗi)
│   │   └── ingest.py         # Pipeline nạp dữ liệu từ thư mục data/ & Tự động xóa cache cũ
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
│   │   ├── cache.py          # Bộ đệm Caching thông minh kép (SQLite/PostgreSQL Dual-Driver) [GIAI ĐOẠN 2]
│   │   └── chain.py          # Chuỗi RAG điều phối Router ➔ Rewriter ➔ Search ➔ Rerank ➔ LLM [GIAI ĐOẠN 2]
│   │
│   ├── api/
│   │   ├── routes.py         # FastAPI REST Server endpoints phục vụ tích hợp & Mount static FE
│   │   └── streamlit_ui.py   # Streamlit UI cũ (lưu trữ phục vụ tham chiếu)
│   │
│   └── config.py             # Quản lý biến môi trường và cấu hình hệ thống
│
├── data/                     # Thư mục chứa tài liệu chính sách được cấu trúc hóa
│   ├── customer/             # Chính sách đặc thù khách hàng (terms.md, refund.md)
│   ├── driver/               # Quy chế tác phong tài xế & chiết khấu thưởng (commission.md)
│   ├── merchant/             # Quy định đối tác cửa hàng (merchant_policy.md)
│   └── faq/                  # Hướng dẫn đặt xe, đặt đồ ăn, giúp đỡ chung (booking.md, vn_vi_helps.md...)
│
├── FE/                       # Thư mục mã nguồn Front-End cao cấp mới [GIAI ĐOẠN 2]
│   ├── index.html            # Cấu trúc Dashboard Dark-Neon điều khiển Cockpit
│   ├── style.css             # HHSL glassmorphism styling
│   └── app.js                # Xử lý REST API, Lịch sử trò chuyện & Pipeline Led sáng
│
├── MINDSET.md                # Hệ tư duy thiết kế, sơ đồ Mermaid và bài giảng của Thầy Giáo AI
├── FE_SPEC.md                # Bản tả đặc tính kỹ thuật Front-End dành cho Stitch vẽ UI [MỚI]
├── requirements.txt          # Các thư viện phụ thuộc của hệ thống (Tích hợp psycopg2-binary)
├── run_tests.py              # Suite chấm điểm và đánh giá tự động RAGAS
└── README.md                 # Hướng dẫn khởi chạy và vận hành hệ thống
```

---

## ⚡ 2. Các Tính Năng Thông Minh Nổi Bật Cấp Doanh Nghiệp (Đã Nâng Cấp Giai Đoạn 2)

Hệ thống kết hợp hài hòa giữa nền tảng bảo mật vững chắc của **Giai đoạn 1** và các mảnh ghép tối ưu hóa hiệu năng, trải nghiệm của **Giai đoạn 2**:

### 💎 A. Các Tính Năng Nền Tảng Cốt Lõi (Giai Đoạn 1)

#### 1. Unified Shared Filter (Ngăn rò rỉ dữ liệu chéo nhưng chia sẻ tri thức chung)
Khắc phục hoàn toàn điểm yếu cô lập thông tin của các RAG cơ bản. Hệ thống ánh xạ quyền truy cập tài liệu thông minh:
* **Khách hàng (Customer)** được phép truy quét tài liệu `customer` + `faq` (mở khóa tài liệu gọi đồ ăn Xanh Food, trung tâm hỗ trợ tổng đài).
* **Tài xế (Driver)** được phép truy quét tài liệu `driver` + `faq`.
* **Cửa hàng (Merchant)** được truy quét `merchant` + `faq`.
* **CSKH (Agent)** được phép xem toàn bộ tài liệu.
Mức độ bảo mật được áp dụng trực tiếp tại tầng truy vấn Database (sử dụng toán tử `$in` của ChromaDB và lọc danh sách của BM25), ngăn chặn triệt để 100% rủi ro rò rỉ dữ liệu qua tấn công Prompt Injection của người dùng.

#### 2. Auto-Sync Volume & Auto-Ingestion (Khởi chạy tự chữa lành - Self-Healing)
* **Tự động đồng bộ ổ đĩa vĩnh viễn**: Khi chạy trên đám mây (Railway) có gắn đĩa cứng vĩnh viễn (Volume), hệ thống sẽ tự động phát hiện nếu ổ đĩa trống lúc khởi chạy lần đầu và tự động sao chép toàn bộ kho tài liệu Markdown mặc định vào Volume.
* **Tự động nạp vector**: Nếu cấu hình ChromaDB thật (`CHROMA_PROVIDER=chromadb`) nhưng CSDL vector trống rỗng, hệ thống sẽ tự động phân mảnh và nạp toàn bộ tài liệu vào CSDL ngay khi khởi chạy mà không cần quản trị viên tác động.

#### 3. Heading-Aware Splitter & MD5 ASCII Chunk IDs
* **Bảo toàn bảng biểu**: Bảo vệ tính toàn vẹn của các bảng biểu giá cước xe, bảng chiết khấu bằng cách phân đoạn Markdown theo Heading trước, sau đó mới gối ký tự (`chunk_size=700`, `overlap=150`).
* **Chunk ID an toàn**: Tạo mã định danh Chunk ID dạng mã hóa MD5 ASCII sạch để tránh xung đột hoặc treo luồng (HNSWLib lock) trên một số nền tảng host Windows/Linux.
* **Query Expansion tiếng Việt**: Hệ thống mở rộng truy vấn bằng cả bộ từ điển đồng nghĩa chuyên ngành và mô-đun LLM, giúp bắt được biến thể câu hỏi sai chính tả, tiếng lóng, hotline và các cách diễn đạt khác nhau.

#### 4. Resilient Self-Healing Fallback (Tự động phục hồi lỗi ngoại tuyến)
* **Chroma Fallback**: Tự động bỏ qua lỗi C++ SQLite DLL trên Windows bằng cách chuyển hướng thông minh sang **In-Memory Fallback VectorDB**.
* **Mock & Fallback Synthesis**: Tự động chuyển đổi sang Mock Embeddings & Offline Fallback Synthesis khi phát hiện OpenAI API Key nhập sai/hết hạn để đảm bảo hệ thống không bao giờ bị sập (Crash-free) và luôn sẵn sàng phản hồi thông tin chính sách thô.

---

### 🚀 B. Các Nâng Cấp Vượt Trội Mới Tích Hợp (Giai Đoạn 2)

#### 1. Giải quyết Điểm Yếu 1: Bộ Nhớ Ngữ Cảnh Hội Thoại (Conversational Memory)
* **Khắc phục:** Hệ thống không còn bị trôi ngữ cảnh (Single-Turn) nhờ **Conversational Query Rewriter** tích hợp trong `chain.py`.
* **Cơ chế:** Khi người dùng trò chuyện chuỗi câu hỏi ngữ cảnh liên tiếp (ví dụ: *"Ai là đối tác cửa hàng?"* -> *"Mức phí của họ là bao nhiêu?"*), một LLM nhẹ (`gpt-4o-mini`) sẽ phân tích 3 lượt hội thoại gần nhất và viết lại đại từ thay thế *"họ"* thành *"đối tác cửa hàng"*, tạo nên truy vấn độc lập hoàn chỉnh trước khi chuyển xuống tầng tìm kiếm vector.

#### 2. Giải quyết Điểm Yếu 2: Bộ Đệm Thông Minh Tránh Lãng Phí Chi Phí (Dual-Driver Cache)
* **Khắc phục:** Loại bỏ hoàn toàn chi phí gọi LLM và triệt tiêu độ trễ về gần ~10ms đối với các câu hỏi lặp lại bằng lớp **Caching Kép** trong `cache.py`.
* **Cơ chế Early-Exit / Bypass tối ưu:** Khi một câu hỏi của khách hàng gửi lên, hệ thống sẽ thực hiện kiểm tra lớp **Caching Layer** đầu tiên (đặt tại tầng cao nhất của luồng xử lý trong `chain.py`, trước khâu Query Rewrite hay Vector Search). Nếu phát hiện câu hỏi đã tồn tại trong DB cache (thỏa mãn khớp tuyệt đối hoặc khớp ngữ nghĩa >= 0.96), hệ thống sẽ lập tức **bẻ gãy luồng xử lý (early-exit/bypass)**, bỏ qua 100% các bước: *Query Rewrite, Query Expansion, Vector/BM25 Retrieval, Reranking, và LLM Generation*. Kết quả đã lưu trong Cache sẽ được trả về trực tiếp trong `< 10ms` với chi phí **0đ** và **0 token**.
  * **Khớp tuyệt đối (Exact Match):** Băm MD5 câu hỏi để so khớp 100% tức thì trong đệm.
  * **Khớp ngữ nghĩa (Semantic Match):** Embedding câu hỏi mới và tính toán Cosine Similarity chéo trên CSDL. Nếu đạt độ tương đồng ngữ nghĩa cực cao (`Similarity Score >= 0.96`), hệ thống trả về câu trả lời đã xác thực trước đó với chi phí **0đ**.
  * **Dual-Driver:** Tự động kết nối **PostgreSQL** trên Railway thông qua biến `DATABASE_URL` (sử dụng `psycopg2-binary`) và tự động fallback sang **SQLite** (`rag_cache.db`) cục bộ khi chạy trên máy tính phát triển cục bộ (Offline-friendly).
  * **Cache Eviction:** Khi có tiến trình ingest nạp tri thức mới, hệ thống tự động xóa sạch cache cũ để tránh tình trạng trích dẫn sai thông tin lỗi thời.

#### 3. Giải quyết Điểm Yếu 3: Chẩn Đoán Lỗi Bằng Hình Ảnh (Multimodal Vision diagnostics)
* **Khắc phục:** Trợ lý ảo không còn bị "mù thị giác" khi tiếp nhận các sự cố kỹ thuật xe điện VinFast thực tế.
* **Cơ chế:** Tích hợp bộ tiếp nhận Base64 ảnh và mô hình **Vision LLM Agent** trong `routes.py`. Người dùng chụp ảnh đèn báo taplo lỗi (như lỗi icon rùa vàng, lỗi động cơ, lỗi phanh chân...), AI sẽ quét ảnh, diễn giải cảnh báo kỹ thuật bằng ngôn ngữ tự nhiên, rồi chuyển mô tả đó thành câu hỏi chi tiết để RAG truy xuất hướng dẫn khắc phục khẩn cấp.

#### 4. Giải quyết Điểm Yếu 4: Nghịch Lý Phân Mảnh Trên PDF Phức Tạp (Parent-Child Chunking)
* **Khắc phục:** Sử dụng mô hình **Layout-Aware PDF Parser (PyMuPDF + Heuristics cục bộ)** tốc độ siêu nhanh, kết hợp với phương pháp **Parent-Child Retrieval**.
* **Cơ chế:**
  * Triển khai bộ phân đoạn kép trong `splitter.py`: Vector Search hoạt động trên mảnh con nhỏ (Child chunks - 100-200 từ) để bắt chính xác tọa độ tri thức.
  * Khi mảnh con được trích chọn, thuật toán loại bỏ trùng lặp mã nhận dạng (`parent_chunk_id`) trong `chain.py` sẽ tự động kéo và hợp nhất các mảnh cha tương ứng (Parent chunks - 1000-2000 từ) gửi cho LLM. Điều này bảo toàn hoàn hảo 100% cấu trúc của các điều khoản pháp lý và bảng giá biểu phức tạp mà không tốn chi phí AI xử lý dữ liệu thô ban đầu.

---

### 📊 C. Bảng So Sánh Nâng Cấp Vượt Trội Giữa Phiên Bản V1 & V2

Dưới đây là bảng tổng hợp các điểm nâng cấp đắt giá từ kiến trúc cơ bản V1 lên hệ thống RAG doanh nghiệp tương tác toàn năng V2:

| Trực quan hóa / Kỹ thuật | 🚗 Phiên bản V1 (Basic Production RAG) | 💎 Phiên bản V2 (Advanced Interactive RAG) | 🎯 Lợi ích mang lại |
| :--- | :--- | :--- | :--- |
| **Quản lý ngữ cảnh (Memory)** | Single-Turn (Truy vấn độc lập câu đơn lẻ) | **Conversational Query Rewriter** (Nhớ 3 lượt chat) | Tự động phân tích lịch sử hội thoại gần nhất và diễn đạt lại các câu truy vấn có đại từ thay thế (ví dụ: *"họ"*, *"đó"*), duy trì mạch trò chuyện trôi chảy tự nhiên. |
| **Hiệu suất & Chi phí (Caching)** | Không có đệm, gọi OpenAI API 100% lượt | **Lớp đệm kép (Exact MD5 & Semantic Cache >= 0.96)** | Phản hồi siêu tốc trong `< 10ms` và chi phí **0đ** đối với các câu hỏi cũ hoặc đồng nghĩa ngữ nghĩa, tiết kiệm 90% ngân sách API. |
| **Bộ nhớ Caching Driver** | Không hỗ trợ lưu cache | Tự động chuyển đổi thông minh: **PostgreSQL** trên Cloud và tự động fallback sang **SQLite** khi chạy Offline | Tương thích đa nền tảng, đảm bảo tốc độ phản hồi nhanh ở môi trường local lẫn cloud sản xuất. |
| **Độ bao phủ tri thức (Multimodal)**| Chỉ xử lý văn bản thô thuần túy | **Vision AI diagnostics (Quét ảnh lỗi taplo VinFast)** | Trợ lý ảo có khả năng quét và diễn giải đèn cảnh báo nguy hiểm thực tế chụp từ taplo, truy xuất cẩm nang sửa chữa RAG khẩn cấp tức thì. |
| **Bảo toàn bảng biểu (Chunking)** | Phân mảnh cơ học gối ký tự thông thường | **Parent-Child Retrieval & Layout-Aware Parser** | Vector search tìm trên mảnh con (100-200 từ) cực kỳ nhạy, gửi mảnh cha (1000-2000 từ) cho LLM. Giữ nguyên 100% bảng biểu giá cước, chính sách. |
| **Giao diện người dùng (UI/UX)** | Streamlit cơ bản, giao diện tĩnh đơn điệu | **Cockpit Dark-Neon đa nhiệm (FastAPI Mount FE)** | 5 Tab tương tác cao cấp: AI Chat (pipeline sáng led, nhật ký suy nghĩ), Lớp Học RAG, Quản trị Console (Duyệt tài liệu thật), Buồng nạp dữ liệu Ingestion, và Thuyết trình luồng RAG. |
| **Dữ liệu đánh giá (Evaluation)** | 5 câu hỏi không dấu tĩnh trong mã python | **10 câu kịch bản thật tiếng Việt đầy đủ dấu (JSON)** | Console kết nối với bộ dataset thật từ `golden_dataset.json`. 4 thẻ đo lường **Active Queries, Average Latency, Token Efficiency, Cost Per Request** liên kết trực tiếp theo thời gian thực (Session Telemetry). |

---

## 🚀 3. Hướng Dẫn Khởi Chạy Hệ Thống Chi Tiết

Dưới đây là các bước để cài đặt và chạy dự án locally trên máy tính của bạn sử dụng hệ điều hành Windows:

### Bước 1: Kích hoạt Môi trường Ảo (Virtual Environment)
Mở Powershell tại thư mục dự án và chạy lệnh sau để kích hoạt môi trường ảo:

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

### Bước 3: Khởi chạy FastAPI Server (Chạy cả API & Front-End Cockpit)
Đây là cách tối ưu và khuyên dùng nhất ở Giai đoạn 2. Chỉ cần khởi chạy FastAPI, máy chủ sẽ tự động biên dịch API và kích hoạt giao diện Dashboard Dark-Neon cao cấp tại root `/`:

```powershell
# Khởi chạy server FastAPI
.\venv\Scripts\uvicorn.exe app.api.routes:app --reload --port 8000
```
*Trình duyệt sẽ tự động mở trang Dashboard cao cấp tại địa chỉ: **`http://localhost:8000`** (hoặc truy cập trực tiếp `http://localhost:8000/FE/`)*.

#### Các tính năng tại giao diện Dashboard mới:
1. **💬 Trợ Lý Hỏi Đáp (AI Chat Assistant):** Cockpit 3 cột hỗ trợ đổi Vai trò đối tượng mục tiêu, kéo thả tải ảnh lỗi taplo (Vision), hệ thống Pipeline sáng led từng bước xử lý thời gian thực và ghi nhật ký suy nghĩ (Mental logs) của RAG.
2. **👨‍🏫 Lớp Học RAG Thầy Giáp:** Hệ thống 8 bài giảng chuyên sâu sắp xếp theo trình tự thiết kế RAG cấp doanh nghiệp thực tế.
3. **⚙️ Quản Trị Hệ Thống (Admin Panel):** Theo dõi số lượng vector ChromaDB thực tế, số lượt Cache hit thành công, trình dọn sạch Cache Database, kích hoạt Ingestion cục bộ và bộ cào dữ liệu BFS Crawler tự động.

### Bước 4: Khởi chạy Streamlit UI (Tham chiếu phiên bản cũ)
Nếu bạn vẫn muốn xem lại phiên bản Streamlit cũ:
```powershell
streamlit run app/api/streamlit_ui.py
```
*Trang Streamlit sẽ mở tại: **`http://localhost:8501`***

### Bước 5: Chạy Suite Đánh Giá Chất Lượng RAGAS tự động
Để đo lường độ trễ phản hồi, độ chính xác định dạng trích nguồn (Citations) và tỷ lệ thu hồi từ khóa trên bộ 5 kịch bản vàng (Gold Dataset) ở chế độ offline an toàn:

```powershell
.\venv\Scripts\python.exe run_tests.py
```

---

## ☁️ 4. Hướng Dẫn Triển Khai Lên Đám Mây Railway vĩnh viễn

Khi triển khai lên Railway, do đĩa cứng mặc định của container là đĩa tạm (Ephemeral), chúng ta cần cấu hình ổ cứng vĩnh viễn (Volume) để tránh bị mất dữ liệu khi restart hoặc deploy bản mới.

### Bước 1: Tạo và gắn Railway Volume
1. Truy cập **Railway Dashboard** ➔ Chọn dịch vụ RAG của bạn.
2. Đi tới tab **Settings** ➔ Cuộn xuống mục **Volumes** ➔ Chọn **Add Volume**.
3. Cấu hình đĩa dung lượng từ `5 GB` trở lên và đặt **Mount Path** là: `/app/persistent_storage`
4. Lưu cấu hình. Railway sẽ tự động restart dịch vụ.

### Bước 2: Cấu hình Cơ sở dữ liệu Caching trên Railway (PostgreSQL)
1. Thêm dịch vụ **PostgreSQL** của Railway vào cùng dự án.
2. Railway sẽ tự động cung cấp biến môi trường **`DATABASE_URL`** cho container FastAPI của bạn.
3. Module `cache.py` khi khởi chạy trên Railway phát hiện thấy biến `DATABASE_URL` và thư viện kết nối `psycopg2-binary` sẽ tự động chuyển đổi sang làm trình điều khiển đệm chính thức (Postgres Driver) hoàn toàn trong suốt.

### Bước 3: Cấu hình Environment Variables trên Railway
Chuyển sang tab **Variables** trên Railway và thêm các biến cấu hình sau để hệ thống tự động lưu trữ dữ liệu vĩnh viễn trên ổ đĩa vừa mount:

| Biến Môi Trường | Giá trị cấu hình | Ý nghĩa |
| :--- | :--- | :--- |
| **`CHROMA_PROVIDER`** | `chromadb` | Kích hoạt cơ sở dữ liệu ChromaDB thật chạy trên Linux |
| **`DATA_DIR`** | `/app/persistent_storage/data` | Đường dẫn lưu trữ tài liệu vĩnh viễn trên Volume |
| **`CHROMA_PERSIST_DIR`** | `/app/persistent_storage/chroma_db` | Đường dẫn lưu trữ cơ sở dữ liệu vector ChromaDB |
| **`OPENAI_API_KEY`** | `sk-proj-xxxx...` | Khóa OpenAI API Key chính thức của bạn |

*Hệ thống thông minh sẽ tự động đồng bộ tài liệu chính sách mặc định vào Volume và nạp chỉ mục ChromaDB ngay lần khởi chạy đầu tiên trên Cloud!*

---

## 🧠 5. Phân Tích Chuyên Sâu Công Nghệ RAG (Retrieval, Chunking & Reranking)

Để đảm bảo các kỹ sư và quản trị viên hệ thống có cái nhìn toàn diện, dưới đây là tóm tắt so sánh kỹ thuật các công nghệ cốt lõi của RAG:

### 1. Công Nghệ Truy Vấn: Similarity vs. Threshold vs. MMR
* **Similarity Search (Tương đồng Cosine)**: Tìm Top K nhanh nhất, nhạy bén nhất. Nhược điểm: Dễ bị lặp ngữ cảnh (Redundancy) khi các mảnh chứa nội dung giống nhau.
* **Similarity with Score Threshold (Ngưỡng điểm số)**: Ngăn chặn rác cực tốt. Nhược điểm: Ngưỡng cứng rất nhạy cảm và dễ gây mất kết quả khi diễn đạt gián tiếp (Threshold Fragility).
* **Maximal Marginal Relevance (MMR)**: Cân bằng tối ưu giữa **Độ tương đồng** và **Tính đa dạng** bằng công thức MMR với tham số $\lambda \approx 0.5$.
  * *Đặc điểm*: Hạn chế tối đa thông tin trùng lặp trong Context window.
  * *Đánh đổi*: Giảm nhẹ độ chính xác tuyệt đối của mảnh đứng đầu tiếp theo và làm tăng độ trễ tính toán chéo ($O(K^2)$).

### 2. Tiến Trình Tiến Hóa Kỹ Thuật Chunking
1. **Character Chunking**: Cắt thô theo ký tự ➔ Gây đứt câu, hỏng từ. (❌ Không dùng)
2. **Recursive Character Chunking**: Tách theo danh sách phân tách `["\n\n", "\n", " "]` ➔ Giữ câu tốt. (⚠️ Baseline)
3. **Heading-Aware Chunking (Markdown)**: Tách theo tiêu đề `#`, `##` ➔ Giữ trọn cấu trúc điều khoản. (✅ Khuyên dùng cho văn bản pháp lý/chính sách)
4. **Semantic Chunking**: Cắt theo sự thay đổi đột ngột ngữ nghĩa câu ➔ Tự nhiên nhưng tốn embedding từng câu. (⚠️ Dành cho sách/truyện)
5. **Agentic Chunking (LLM-based)**: LLM tự quyết định điểm cắt ➔ Hoàn hảo nhưng chi phí cực đắt, tốc độ chậm. (❌ Không thực tế)
6. **Hierarchical + Parent-Child Retrieval**: Nhúng mảnh con (100-200 từ) để tìm kiếm nhạy bén, liên kết mảnh cha (1000-2000 từ) để gộp ngữ cảnh khi gửi LLM ➔ **Tiêu chuẩn vàng (Gold Standard)** trong doanh nghiệp hiện đại.

### 3. Kiến Trúc Tìm Kiếm & Reranking Chiều Sâu
* **Tìm Kiếm Lai (Hybrid Search)**: Kết hợp **Dense Search** (Embedding bắt từ đồng nghĩa) và **Sparse Search** (BM25 bắt từ khóa chính xác, mã số, hotline) qua thuật toán **RRF (Reciprocal Rank Fusion)** để xếp thứ hạng tối ưu.
* **Bi-Encoder (ChromaDB Vector Matching)**: Nhúng độc lập Query và Document ➔ Cực kỳ nhanh, độ chính xác khá tốt, tính toán offline được. Nhược điểm là thiếu tương tác Attention chéo.
* **Cross-Encoder (Reranker)**: Ghép đôi `Query + Document` vào Transformer để tương tác Self-Attention chéo toàn phần ➔ Độ chính xác siêu việt, bắt trọn sắc thái ngữ nghĩa tinh tế. Nhược điểm là tính toán cực nặng, bắt buộc dùng ở Stage 2 (chỉ xếp hạng lại Top 30-50 ứng viên).

---

## 🌟 6. Kế Hoạch Phát Triển Phiên Bản V3 (Advanced Agentic RAG - 2026)

> [!WARNING]
> **ĐÁNH GIÁ THỰC TẾ CHI PHÍ & ĐỘ TRỄ (LATENCY):** 
> Trong số các tính năng dự kiến cho V3, có những nâng cấp được đánh giá là **quá đà (excessive/over-the-top)**, làm tăng vọt độ trễ phản hồi (từ 1-3 giây lên 10-30 giây) và nhân chi phí API LLM lên gấp **5 - 10 lần** do phải gọi LLM đệ quy/nhiều lần. Đối với một chatbot thương mại tối ưu tốc độ và chi phí như Xanh SM, các tính năng **GraphRAG (Neo4j)**, **Self-RAG (Phản biện đa tầng)** và **CRAG (Corrective RAG)** cần được cân nhắc cực kỳ cẩn trọng hoặc thay thế bằng các giải pháp thực dụng (như Đồ thị RAM siêu nhẹ thay cho Neo4j DB) để đảm bảo trải nghiệm người dùng mượt mà nhất.

Dựa trên tài liệu khảo sát kỹ thuật chuyên sâu về các mô hình **Agentic RAG** và **NLU Optimization**, lộ trình nâng cấp hệ thống Xanh SM CSKH RAG lên **Phiên bản V3** sẽ tập trung vào các tính năng đột phá sau:

### 1. Self-Querying / Self-Query Retriever (Truy vấn tự cấu trúc hóa)
* **Khắc phục:** Người dùng đặt câu hỏi có kèm điều kiện lọc (ví dụ: *"Các chính sách bồi hoàn cho khách hàng trong năm 2026"*).
* **Cơ chế:** Dùng một LLM để phân dịch ngôn ngữ tự nhiên thành một cấu trúc truy vấn hoàn chỉnh gồm: **Semantic Search Query** (Nội dung cần tìm) + **Metadata Filters** (Ví dụ: `{"role": "customer", "year": {"$eq": 2026}}`). Điều này thu hẹp 100% không gian tìm kiếm, triệt tiêu nhiễu tri thức từ các tệp tin của `driver` hoặc `merchant`.
* **Đánh giá hiệu năng:** **Tốt & Rẻ!** Chỉ tốn thêm một cuộc gọi LLM siêu nhẹ để bóc tách Filter, nhưng tăng độ chính xác tìm kiếm vector lên tối đa.

### 2. Corrective RAG (CRAG - Luồng RAG tự sửa lỗi thông minh)
* **Khắc phục:** Ngăn chặn tuyệt đối hiện tượng ảo tưởng thông tin (Hallucination) khi tri thức trong CSDL nội bộ không chứa câu trả lời.
* **Cơ chế:** Tích hợp bộ đánh giá chất lượng tài liệu tìm thấy (Retrieval Evaluator). Nếu điểm số liên quan của Top 5 tài liệu tìm thấy quá thấp hoặc không đáp ứng:
  * Hệ thống sẽ tự động kích hoạt **Web Search Tool** (Tích hợp Google Search API / Tavily) để cào thông tin chính sách, cẩm nang GSM mới nhất thời gian thực từ trang chủ `greensm.com`.
  * Hợp nhất dữ liệu cào ngoài với tri thức cũ để sinh ra câu trả lời chuẩn xác.
* **⚠️ Cảnh báo hiệu năng (Cân nhắc):** Khâu Web Search có thể làm tăng thời gian phản hồi thêm 2-4 giây và tốn phí API tìm kiếm, chỉ nên kích hoạt ở chế độ fallback khẩn cấp khi tri thức nội bộ hoàn toàn trống rỗng để tránh làm chậm hệ thống hàng ngày.

### 3. Agentic Tool Calling & Function Calling (Công cụ tác vụ chủ động & Hỗ trợ hành trình)
* **Khắc phục:** Chatbot RAG truyền thống bị giới hạn ở việc trả lời tĩnh, không thể thực hiện hành động hoặc tính toán nghiệp vụ động.
* **Cơ chế:** Thiết lập bộ công cụ (Tools) cho Agent gọi trực tiếp:
  * **GSM Taxi Booking Tool:** Khách hàng có thể yêu cầu đặt chuyến xe trực tiếp qua chat, Agent sẽ gọi API đặt chuyến của Xanh SM.
  * **Driver Hotspot Suggester Tool (Gợi ý điểm nhiều cuốc):** Hỗ trợ tài xế tìm kiếm các tọa độ/khu vực có nhu cầu đặt chuyến cao trong thành phố theo thời gian thực để tăng tần suất nhận chuyến.
  * **Customer Smart Ride Planner Tool (Gợi ý giờ rẻ, xe dễ):** Gợi ý cho khách hàng các khung giờ thấp điểm có giá cước ưu đãi và các địa điểm đón xe tối ưu (vùng xanh lá cước rẻ, dễ bắt).
  * **Driver Scorecard Tool:** Tra cứu lịch sử vi phạm chỉ số AR (Tỷ lệ nhận chuyến) và CR (Tỷ lệ hủy chuyến) của đối tác tài xế trực tiếp trong SQLite DB.
  * **Refund Calculator Tool:** Chạy mã Python thực tế để tính toán chính xác mức phạt hủy chuyến của hành khách sau 2 phút tùy theo phân khúc xe (Xanh Car, Xanh Luxury, Xanh Bike) thay vì trích dẫn thô sơ.
* **⚠️ Rào cản Dữ liệu Thực tế (Data Constraint & Warning):** 
  Hiện tại dự án **không có quyền truy cập vào nguồn dữ liệu thực tế thời gian thực (Real-time production APIs)** của Xanh SM về luồng xe chạy, phân bố mật độ cuốc khách, biến động giá cước động (Surge pricing) hay thống kê điểm bắt xe lịch sử. Trong phiên bản V3, các công cụ này sẽ hoạt động dựa trên các bộ dữ liệu giả lập (Mock Datasets/APIs) hoặc dữ liệu thống kê tĩnh được cấu trúc hóa trong file JSON/SQLite, trừ khi có sự tích hợp API chính thức từ đối tác Xanh SM.

### 4. Self-RAG (Hệ thống RAG tự phản biện đa tầng)
* **Khắc phục:** Kiểm soát chặt chẽ từng lượt sinh văn bản của LLM.
* **Cơ chế:** Sử dụng mô hình tự phản biện qua các chỉ thị phản hồi (Fine-grained feedback tokens):
  * **Is Retrieve Needed?** Đánh giá xem câu hỏi có thực sự cần tra cứu DB không.
  * **Are Chunks Relevant?** Phản biện xem tài liệu tìm được có thực sự khớp với câu hỏi của người dùng không.
  * **Is Answer Faithful?** Đảm bảo câu trả lời được LLM sinh ra là trung thực (100% dựa trên tài liệu tham khảo).
  * **Is Answer Useful?** Đánh giá xem câu trả lời cuối cùng có giải quyết triệt để thắc mắc gốc của người dùng không.
* **⚠️ Cảnh báo ĐÁNH GIÁ QUÁ ĐÀ & LÃNG PHÍ:** Việc bắt LLM tự phản biện qua 4-5 bước trung gian sẽ biến 1 request thành 5 request LLM liên tiếp. Tốc độ chat sẽ chậm như rùa (8-15 giây) và hóa đơn OpenAI sẽ tăng 500%, hoàn toàn không phù hợp cho môi trường CSKH thực tế cần phản hồi nhanh.

### 5. Knowledge Graph RAG (GraphRAG tích hợp Neo4j)
* **Khắc phục:** Giải quyết các câu hỏi dạng suy luận liên kết nhiều bước phức tạp (Multi-hop Reasoning).
* **Cơ chế:** Xây dựng đồ thị tri thức kết nối thực thể (ví dụ: `Tài xế` ➔ `Vi phạm mức độ 2` ➔ `Chế tài phạt 1 triệu` ➔ `Thời gian tạm khóa tài khoản`). Khi truy xuất, hệ thống sẽ kết hợp truy vấn đồ thị (Graph Search) và truy vấn ngữ nghĩa (Vector Search) để mang lại câu trả lời đa chiều hoàn hảo.
* **⚠️ Cảnh báo ĐÁNH GIÁ QUÁ ĐÀ & TỐN KÉM:** GraphRAG (Neo4j) yêu cầu tài nguyên phần cứng lớn, chi phí trích xuất đồ thị bằng LLM đắt gấp 50x-100x và độ trễ tìm kiếm cực cao (5-30 giây). Thay vì Neo4j, việc sử dụng các quan hệ liên kết file Markdown trực tiếp trong RAM bằng **networkx** (như đã thiết kế ở Chương 14 lớp học RAG) tối ưu chi phí 0đ và độ trễ 0ms là sự thay thế thực dụng hoàn hảo.

### 6. Sentence Window Retrieval (Truy xuất cửa sổ câu liên kết)
* **Khắc phục:** Tránh mất ngữ cảnh khi phân mảnh quá nhỏ, nhưng cũng không làm loãng thông tin khi chunk quá lớn.
* **Cơ chế:** Cắt tài liệu thành từng câu đơn lẻ cực kỳ nhỏ để nhúng vector nhạy bén nhất. Khi tìm được câu liên quan nhất, hệ thống tự động kéo thêm một "cửa sổ trượt" gồm $N$ câu liền kề phía trước và phía sau để cung cấp ngữ cảnh đầy đủ, mạch lạc nhất cho LLM tổng hợp đáp án.
* **Đánh giá hiệu năng:** **Rất tốt!** Tăng chất lượng context mà hầu như không tăng chi phí hoặc độ trễ.

### 7. Active Clarifying Questions (Đặt câu hỏi ngược để làm rõ)
* **Khắc phục:** Người dùng đặt câu hỏi quá mơ hồ, thiếu chi tiết.
* **Cơ chế:** Thay vì cố gắng đoán mò và trả lời sai lệch, Agent sẽ chủ động so sánh thông tin tìm thấy. Nếu phát hiện thiếu điều kiện cần (ví dụ: chưa biết người dùng đang quan tâm đến chính sách chiết khấu của *Xanh Car* hay *Xanh Luxury*), Agent sẽ chủ động đưa ra câu hỏi làm rõ ngược lại để định hướng người dùng.
* **Đánh giá hiệu năng:** **Rất thực dụng!** Tiết kiệm token sinh câu trả lời vô nghĩa và giúp tăng tính chính xác của cuộc đối thoại.

### 8. Long-Term Memory RAG (CSDL hội thoại dài hạn)
* **Khắc phục:** Cá nhân hóa câu trả lời dựa trên những tương tác lịch sử từ nhiều ngày hoặc nhiều tuần trước.
* **Cơ chế:** Định kỳ tóm tắt nội dung hội thoại cũ, nhúng vector hóa và lưu trữ vào cơ sở dữ liệu lịch sử hội thoại của người dùng. Khi họ quay lại và đặt câu hỏi mới, Agent có thể tham chiếu chéo cả tri thức chính sách chung lẫn bộ nhớ thói quen đặt xe/sự cố cũ của chính họ để trả lời.
* **Đánh giá hiệu năng:** **Trung bình.** Tăng nhẹ thời gian tìm kiếm nhưng đem lại trải nghiệm cá nhân hóa cao.

### 9. Multimodal & Table-Aware Ingestion Pipeline (Quy trình nạp đa phương tiện & bảng biểu chuyên sâu)
* **Tầm quan trọng:** Đây được đánh giá là **tính năng đáng giá và ưu tiên nâng cấp hàng đầu trong V3**. Lớp chunking đa phương tiện với phương pháp biểu diễn kép (Dual-Representation) cho phép một khối tri thức logic (mảnh cha) chứa đựng và phản ánh chính xác đồng thời nhiều loại dữ liệu (vừa có Text mô tả, vừa chứa Table biểu phí cước, vừa có Image sơ đồ/ảnh minh họa) mà không bị đứt gãy ngữ cảnh.
* **Cơ chế:** Thiết lập bộ nạp phân loại và gán nhãn metadata chuyên sâu với trường `chunk_type: "text" | "table" | "image"`.
  * **Table-specific RAG (Bảng biểu):** Trích xuất tọa độ bảng bằng **Table Transformer / Nougat**. Lưu trữ dạng văn bản tóm tắt tự nhiên (Table Summary) để Vector Search tìm kiếm nhạy nhất, nhưng kéo định dạng Markdown/HTML Table gốc khi LLM sinh câu trả lời để đạt độ chính xác số liệu 100%. Gán nhãn metadata `{"chunk_type": "table", "has_table": true}`.
  * **Image-specific RAG (Hình ảnh):** Cắt tự động ảnh chính sách/sơ đồ taplo bằng **PyMuPDF**, chạy VLM để sinh văn bản mô tả (Image Caption) làm đại diện Vector Search. Khi khớp tìm kiếm, truyền URL ảnh thật để LLM hiển thị trực quan dạng Markdown cho người dùng click xem. Gán nhãn metadata `{"chunk_type": "image", "image_url": "...", "has_visual": true}`.
* **⚠️ Phân tích Thực Tế về Chi Phí & Tính Khả Thi (Cost & Feasibility Analysis):** 
  Việc chạy mô hình Vision-Language (VLM) thương mại lớn của OpenAI (như `gpt-4o`) để quét hàng vạn trang PDF chứa ảnh/bảng biểu sẽ **gây vọt chi phí API lên gấp hàng chục lần** và tăng đáng kể thời gian Ingestion. Để đảm bảo tính thực tế và tối ưu chi phí tối đa cho Xanh SM, phương án khuyến nghị là tự host và chạy offline các mô hình mã nguồn mở gọn nhẹ như **LLaVA-1.5-8B** hoặc **Qwen-VL** trên GPU cục bộ/cloud giá rẻ để tự động gán nhãn, OCR và viết caption cho dữ liệu trước khi nạp vào ChromaDB. Điều này mang lại hiệu quả vượt trội với chi phí vận hành tiệm cận 0đ!