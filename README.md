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

---

## 🚨 5. Điểm Yếu Hệ Thống & Kế Hoạch Nâng Cấp Giai Đoạn Tiếp Theo

> [!CAUTION]
> **ĐIỂM YẾU 1: THIẾU BỘ NHỚ HỘI THOẠI (CHAT HISTORY & CONTEXTUAL MEMORY)**
> - **Mô tả:** Hệ thống đang hoạt động theo cơ chế **Single-Turn (Hỏi-Đáp độc lập)**. Khi người dùng hỏi một chuỗi ngữ cảnh liên tiếp (ví dụ: *"Xanh SM có bao nhiêu nhân viên?"*, sau đó hỏi tiếp *"Doanh thu của **họ** là bao nhiêu?"*), RAG sẽ truy xuất sai lệch tài liệu hoặc trả về kết quả trống rỗng.
> - **Nguyên nhân:** Đại từ thay thế **"họ"** không thể giải nghĩa ngữ cảnh nếu gửi trực tiếp vào VectorDB/BM25 (vì CSDL Vector không có khái niệm lịch sử hội thoại trước đó).
>
> **ĐIỂM YẾU 2: LÃNG PHÍ CHI PHÍ & TĂNG ĐỘ TRỄ KHI HỎI LẠI CÂU HỎI CŨ (REDUNDANT LLM CALLS)**
> - **Mô tả:** Nhiều người dùng khác nhau thường xuyên hỏi cùng một câu hỏi hoặc các câu hỏi đồng nghĩa ngữ nghĩa (ví dụ: *"Phí hủy chuyến Bike sau 5 phút là gì?"* và *"Hủy xe Xanh Bike chờ trên 5 phút mất bao nhiêu tiền?"*). Hệ thống hiện tại phải gọi lại OpenAI API liên tục cho mỗi lượt truy cập, tạo ra **lãng phí chi phí API lớn** và **tăng độ trễ phản hồi không đáng có (~1s - 2s)**.
> - **Nguyên nhân:** Thiếu lớp đệm lưu trữ (Caching layer) để nhận diện và trả về kết quả tức thì đối với các câu hỏi cũ đã được LLM trả lời và xác thực trước đó.
>
> **ĐIỂM YẾU 3: CHƯA HỖ TRỢ ĐẦU VÀO ĐA PHƯƠNG TIỆN (MULTIMODAL RAG - IMAGE INPUTS)**
> - **Mô tả:** Hệ thống hiện tại bị mù thông tin thị giác (Text-only pipeline). Trong tương lai khi nâng cấp lên hệ thống toàn năng giải đáp các thắc mắc về lỗi kỹ thuật xe điện Xanh SM (EV), hành khách hoặc tài xế sẽ chụp ảnh đèn cảnh báo báo lỗi trên mặt taplo (ví dụ: lỗi icon rùa vàng, báo lỗi hệ thống phanh, lỗi động cơ...). Hệ thống hiện tại không thể tiếp nhận và phân tích hình ảnh này để truy xuất tài liệu sửa chữa tương ứng.
> - **Nguyên nhân:** Đường ống xử lý và bộ trích xuất vector hiện tại chỉ xử lý ký tự thuần túy và mô hình LLM/Embedding chưa kích hoạt chế độ Vision (Thị giác máy tính).
>
> **ĐIỂM YẾU 4: NGHỊCH LÝ PHÂN MẢNH VĂN BẢN TRÊN PDF PHỨC TẠP (THE CHUNKING PARADOX IN COMPLEX DOCUMENTS)**
> - **Mô tả:** Các phương pháp phân mảnh truyền thống (như `RecursiveCharacterSplitter` hoặc `Semantic Chunking` dựa trên Embedding) hoạt động hoàn toàn cơ học, dễ làm đứt gãy bảng dữ liệu, danh sách lồng hoặc cấu trúc nhiều cột của PDF. Ngược lại, việc sử dụng AI (LLM-based document chunking) để tiền xử lý và cắt mảnh thông minh lại cực kỳ đắt đỏ, doanh nghiệp chắc chắn không sẵn lòng trả số tiền lớn chỉ để xử lý dữ liệu thô ban đầu. Với những tệp PDF có bố cục phức tạp, ngay cả mắt thường cũng rất khó chia mảnh tối ưu mà không làm mất tính liền mạch ngữ cảnh.
> - **Nguyên nhân:** Quá trình phân mảnh bị cô lập, thiếu khả năng nhận diện bố cục thị giác (Layout-Aware) của tài liệu và thiếu tính liên kết phân cấp ngữ cảnh (Hierarchical parent-child relationships).

### 🎯 Giải pháp & Tính năng phát triển trong Giai đoạn 2:

Để đưa hệ thống RAG Xanh SM đạt tiêu chuẩn vận hành tối ưu chi phí và trải nghiệm người dùng cao nhất, các tính năng sau sẽ được tích hợp:

#### 1. Luồng Giải Nghĩa Hội Thoại (Conversational Query Rewriter)
* **Lưu trữ lịch sử hội thoại**: Ghi nhớ 3-5 lượt chat gần nhất bằng cơ chế Redis/SQLite Cache.
* **LLM Query Rewriter**: Trước khi tìm kiếm Vector, sử dụng một LLM siêu nhẹ nhận ngữ cảnh hội thoại cũ + câu hỏi mới để tự động biên dịch lại thành câu hỏi độc lập (Self-Contained Query).
  - *Ví dụ:* `[Lịch sử: Xanh SM có bao nhiêu nhân viên?]` + `[Câu hỏi mới: Doanh thu của họ là bao nhiêu?]` ➔ `[Câu hỏi biên dịch: Doanh thu của Xanh SM là bao nhiêu?]`.

#### 2. Lớp Đệm Caching Thông Minh (Exact & Semantic Cache)
Triển khai bộ thư viện **GPTCache** hoặc tích hợp **Redis Semantic Cache** với 2 cơ chế bảo vệ chi phí:
* **Deterministic Cache (Exact Match)**: Sử dụng thuật toán băm (MD5/SHA256) chuỗi ký tự câu hỏi. Nếu có câu hỏi khớp 100% trong đệm và phiên bản tài liệu gốc chưa thay đổi, trả ngay câu trả lời đã lưu **(Độ trễ < 5ms, Chi phí = $0)**.
* **Semantic Cache (Ý nghĩa tương đồng)**: Embedding câu hỏi mới nhập và thực hiện tìm kiếm khoảng cách vector (Cosine Similarity) trên CSDL các câu hỏi lịch sử. Nếu độ tương đồng vượt ngưỡng cực cao (ví dụ: **`Similarity Score > 0.96`**), trả trực tiếp câu trả lời của câu hỏi tương đương đã lưu trước đó **(Độ trễ < 20ms, Chi phí = $0)**.

#### 3. Bộ Nhận Diện Lỗi Kỹ Thuật Đa Phương Tiện (Multimodal RAG & EV Diagnostics)
* **CSDL Vector Đa Phương Tiện (Multimodal VectorDB)**: Sử dụng mô hình CLIP hoặc ColPali để nhúng đồng thời cả hình ảnh cảnh báo và hướng dẫn dạng chữ từ Sách Hướng dẫn kỹ thuật GSM (EV Manuals) vào chung một không gian vector.
* **Vision LLM Agent**: Tích hợp GPT-4o Vision hoặc Claude 3.5 Sonnet tiếp nhận hình ảnh taplo lỗi thực tế của khách hàng chụp ➔ Trực quan hóa mã lỗi cảnh báo ➔ Truy xuất RAG tài liệu sửa chữa tương ứng ➔ Đưa ra chỉ dẫn an toàn khẩn cấp tức thì.

#### 4. Cơ chế Tách đoạn Phân cấp & Nhận diện Bố cục (Hierarchical Layout-Aware Parsing & Parent-Child Retrieval)
* **Layout-Aware PDF Parser**: Sử dụng mô hình thị giác máy tính cục bộ gọn nhẹ, miễn phí (như LayoutLMv3, Marker, hoặc PyMuPDF/fitz) để phân tích bố cục PDF, trích xuất chính xác cấu trúc bảng biểu, biểu phí nhiều cột và cấu trúc Header-DOM mà không cần gọi LLM đắt đỏ.
* **Parent-Child Retrieval (Truy xuất tự động gộp Cha-Con)**:
  - *Mảnh Con (Child Chunks - nhỏ, 100-200 từ)*: Phục vụ tìm kiếm vector để đạt độ chính xác ngữ nghĩa cao nhất.
  - *Mảnh Cha (Parent Chunks - lớn, 1000-2000 từ hoặc toàn bộ chương)*: Khi mảnh con được tìm thấy, RAG sẽ tự động truy xuất và gửi toàn bộ ngữ cảnh cha tương ứng vào LLM. Điều này vừa giúp bảo toàn ngữ cảnh hoàn hảo cho các tài liệu cực kỳ phức tạp, vừa tối ưu chi phí tiền xử lý bằng $0!

---

## 🧠 6. Phân Tích Chuyên Sâu Công Nghệ RAG (Retrieval, Chunking & Reranking)

Để đảm bảo các kỹ sư và quản trị viên hệ thống có cái nhìn toàn diện, dưới đây là tóm tắt so sánh kỹ thuật các công nghệ cốt lõi của RAG:

### 1. Công Nghệ Truy Vấn: Similarity vs. Threshold vs. MMR
* **Similarity Search (Tương đồng Cosine)**: Tìm Top K nhanh nhất, nhạy bén nhất. Nhược điểm: Dễ bị lặp ngữ cảnh (Redundancy) khi các mảnh chứa nội dung giống nhau.
* **Similarity with Score Threshold (Ngưỡng điểm số)**: Ngăn chặn rác cực tốt. Nhược điểm: Ngưỡng cứng rất nhạy cảm và dễ gây mất kết quả khi diễn đạt gián tiếp (Threshold Fragility).
* **Maximal Marginal Relevance (MMR)**: Cân bằng tối ưu giữa **Độ tương đồng** và **Tính đa dạng** bằng công thức MMR với tham số $\lambda \approx 0.5$.
  - *Đặc điểm*: Hạn chế tối đa thông tin trùng lặp trong Context window.
  - *Đánh đổi*: Giảm nhẹ độ chính xác tuyệt đối của mảnh đứng đầu tiếp theo và làm tăng độ trễ tính toán chéo ($O(K^2)$).

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