# 🚗 Xanh SM Enterprise Production RAG System (Phase 5)

[![Live Demo](https://img.shields.io/badge/Demo-Live-00A651?style=for-the-badge&logo=vercel&logoColor=white)](https://rag-xanh-sm-v1.vercel.app/)

> [!NOTE]
> **🚀 CẬP NHẬT MỚI TẠI PHASE 5 (SCOPE EXPANSION & IMAGE SUPPORT):**
> *   **Mở rộng kho tri thức (Green SM Platform)**:
>     *   **Các dòng xe VinFast hỗ trợ**: Cập nhật thông số kỹ thuật chi tiết, giá bán, giá thuê và các tùy chọn mua/thuê của toàn bộ các dòng ô tô điện (**VF 6, VF 5, EC Van, Herio Green, Limo Green, Minio Green**) và xe máy điện (**Evo, Evo Grand, Feliz II, Viper**).
>     *   **Các chính sách mua/thuê xe & sạc pin**: Tích hợp các tài liệu PDF chính sách lớn (chương trình mua xe trực tiếp qua Green SM, chương trình "Mua xe 0 đồng", ưu đãi sạc pin miễn phí tại trạm V-Green, cơ chế thuê vận doanh và chia sẻ doanh số lên tới 90%).
>     *   **Tổng hợp tin tức & sự kiện**: Danh sách 12 bài viết tin tức mới nhất về các chiến dịch ra mắt xe mới, nâng cấp pin miễn phí, ngày hội thu cũ đổi mới và các chương trình khuyến mại.
> *   **Hiển thị hình ảnh trực quan trong Chat**: Trích xuất tự động thẻ ảnh từ chunks và hiển thị hình ảnh minh họa thực tế của dòng xe hoặc tin tức trực quan trong câu trả lời (bo góc tròn, zoom khi hover và mở tab mới khi click).
> *   **Hỗ trợ kết nối Docker Local**: Tự động nhận diện và kết nối trực tiếp đến Qdrant chạy local Docker (`localhost`/`127.0.0.1`) mà không yêu cầu API Key.


Hệ thống **Retrieval-Augmented Generation (RAG)** cấp doanh nghiệp (Production-Grade) được thiết kế và tối ưu hóa đặc biệt dành riêng cho **Xanh SM** nhằm hỗ trợ tra cứu tập trung và chính xác mọi thông tin chính sách cước phí, điều khoản dịch vụ, cơ chế tài chính cho khách hàng, đối tác tài xế, đối tác cửa hàng merchant và nhân viên CSKH.

Hệ thống này triển khai kiến trúc **NLU-Gateway RAG (Phase 5)** tiên tiến nhất hiện nay với tốc độ xử lý siêu tốc:
`Question ➔ Safety Guardrail ➔ Intent Classifier ➔ Slot Filling (Task/RAG) ➔ Memory Query Rewrite ➔ Hybrid Search (Qdrant Dense + BM25) ➔ Cohere Reranker ➔ Adjacent Context Expansion ➔ LLM Synthesizer ➔ Server-Sent Events (SSE) Stream ➔ Citation Validator`.

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
│   │   └── reranker.py       # Cohere Reranker xếp hạng lại Top 10 tài liệu
│   │
│   ├── rag/
│   │   ├── prompt.py         # Prompt hệ thống tối ưu hóa tác phong và trích nguồn
│   │   ├── gateway.py        # Conversation Gateway (Regex chặn từ cấm tức thì ~0ms)
│   │   ├── classifier.py     # Intent Classifier & Slot Filling (Xử lý Small-talk & Task-agent)
│   │   ├── chain.py          # Chuỗi RAG chính, xử lý SSE Stream
│   │   ├── pipeline.py       # Điều phối luồng xử lý RAG Pipeline tích hợp Guardrails & Cache
│   │   ├── guardrail.py      # Lớp bảo vệ an toàn (Guardrail) ngăn chặn Prompt Injection và từ cấm
│   │   └── cache.py          # Quản lý Semantic Cache tăng tốc độ phản hồi truy vấn lặp lại
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
│   │   └── logger.py         # Ghi log hợp nhất kết hợp xuất console (stdout/stderr) và lưu Database
│   │
│   └── db/                   # Quản lý Database PostgreSQL/SQLite
│       ├── database.py       # Khởi tạo kết nối SQLAlchemy Engine và Session Local
│       └── models.py         # Định nghĩa các bảng dữ liệu (Users, Conversations, Logs, Chunks...)
│
├── crawler/                  # Module crawl theo URL registry đã duyệt
│   ├── registry.py           # Bootstrap/đọc crawl_sources từ DB và urls.json
│   ├── sources.py            # Khai báo source profile main_site/platform/platform_pdf
│   ├── crawler.py            # Page Crawler thu thập HTML bằng requests
│   ├── run_crawler.py        # Deterministic crawler main_site/platform/platform_pdf -> Markdown
│   ├── agent_crawler.py      # Compatibility wrapper, no LLM/Agent API calls
│   ├── category_cleaners.py  # Rule-based cleaners for service/news/platform pages
│   ├── pdf_utils.py          # Extract PDF bằng pymupdf4llm/PyMuPDF
│   └── storage.py            # Lưu trữ tài liệu Markdown
│
├── data/                     # Thư mục chứa tài liệu Markdown thô (Crawler tạo ra)
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
├── requirements.txt          # Thư viện phụ thuộc (FastAPI, Qdrant-client, Cohere...)
└── README.md                 # Hướng dẫn khởi chạy và vận hành
```

---

## ⚡ 2. Luồng Xử Lý Phase 5 NLU-Gateway RAG (Tối Ưu Unification & Early Cache)

Hệ thống hoạt động qua các bước khép kín với các lớp bảo vệ và tối ưu hóa hiệu năng vượt trội:

```mermaid
graph TD
    A([User Input]) --> N[Normalize Input]
    N --> B{Input Gateway Safety}
    B -- "Prompt injection / secret leak / malicious defamation" --> Block[Refusal Response]
    B -- "Safe" --> C{Early Exact Cache}

    C -- "Cache Hit (~5ms)" --> Out([Stream Answer + Citations])
    C -- "Cache Miss" --> D{NLU Fast-path Eligible?}

    D -- "Yes: clear RAG query" --> D1[Rule-based RAG NLU + Rule Expansion]
    D -- "No: context rewrite needed" --> D2[Unified LLM NLU: intent + rewrite]
    D1 --> DV[Domain Vocabulary]
    D2 --> RuleExp[Rule-based Expansion]
    RuleExp --> DV
    DV --> E{Intent}
    E -- "small-talk" --> Stalk[LLM Persona Answer]
    E -- "sensitive" --> Block
    E -- "rag" --> F{Second Exact Cache}

    F -- "Cache Hit" --> Out
    F -- "Cache Miss" --> G[Hybrid Retrieval: Dense + Sparse + SQL keyword fallback]

    G --> H[Cohere Reranker]
    H --> I[Parent / Section Context Expansion]
    I --> K[LLM Synthesis & SSE Stream]
    K --> CacheSave[Save Semantic Cache]
    CacheSave --> Out
    Block --> Out
    Stalk --> Out

    style A fill:#00A651,stroke:#fff,color:#fff
    style Out fill:#00A651,stroke:#fff,color:#fff
    style Block fill:#ff4444,stroke:#fff,color:#fff
    style Stalk fill:#f59e0b,stroke:#fff,color:#fff
    style B fill:#f43f5e,stroke:#fff,color:#fff
```

### Chi tiết các công nghệ và thông số kỹ thuật:
Hệ thống RAG được cấu trúc thành một chuỗi tuần tự gồm 9 Node xử lý độc lập từ đầu vào đến đầu ra, kết hợp nhiều kỹ thuật nâng cao để tối ưu hóa độ trễ, tài nguyên và độ chính xác:

1. **NODE 1: API Gateway & Input Guardrail (Kiểm duyệt đầu vào)**
   - **Công nghệ áp dụng**: Thư viện biểu thức chính quy (`re` Python) kết hợp bộ quy tắc phân loại cục bộ.
   - **Logic xử lý**: Kiểm tra heuristic siêu tốc trên câu hỏi gốc của người dùng nhằm phát hiện sớm các tấn công Prompt Injection (tấn công thao túng chỉ thị), System Prompt Leakage (nỗ lực rò rỉ prompt hệ thống) và các từ khóa thô tục, nhạy cảm.
   - **Thông số kỹ thuật**: Độ trễ **< 1ms**. Nếu phát hiện vi phạm, hệ thống lập tức chặn và trả về thông điệp từ chối mà không cần chuyển tới các Node xử lý LLM/VectorDB, tiết kiệm 100% tài nguyên tính toán.

2. **NODE 2: Early Cache Lookup (Kiểm tra Cache sớm)**
   - **Công nghệ áp dụng**: Hệ quản trị cơ sở dữ liệu (PostgreSQL / SQLite) qua SQLAlchemy ORM.
   - **Logic xử lý**: Thực hiện đối sánh chuỗi chính xác (Exact Match) giữa câu hỏi thô của người dùng với cơ sở dữ liệu `SemanticCache`.
   - **Thông số kỹ thuật**: Độ trễ **~5-10ms**. Nếu xảy ra Cache Hit (đã có câu trả lời hợp lệ và còn hiệu lực TTL), hệ thống trả kết quả ngay lập tức về client, bỏ qua toàn bộ các bước RAG sau đó.

3. **NODE 3: NLU Gateway 3-in-1 + Domain Vocabulary (Xử lý ngôn ngữ tự nhiên tích hợp)**
   - **Công nghệ áp dụng**: OpenAI API `chat/completions` với mô hình `gpt-4o-mini` kết hợp Rule-based Pipeline.
   - **Logic xử lý**: Tích hợp gộp các tác vụ tiền RAG bằng kỹ thuật Few-Shot Prompting và Structured Outputs:
     - *Intent Classification (Phân loại ý định)*: Xác định câu hỏi thuộc nhóm `rag` (cần tra cứu tài liệu), `small-talk` (chào hỏi, LLM trả lời trực tiếp), hay `sensitive` (nhạy cảm).
     - *Query Rewrite (Viết lại câu hỏi)*: Khử tham chiếu, bổ sung ngữ cảnh từ lịch sử hội thoại gần nhất.
     - *Domain Vocabulary (Từ điển miền Xanh SM)*: Chuẩn hóa alias/sai chính tả.
     *(Lưu ý: Tính năng Query Expansion đã được tắt bỏ hoàn toàn để tối ưu hóa hiệu năng, giảm độ trễ và tránh quá tải cho backend/VectorDB).*
   - **Thông số kỹ thuật**: Gộp API calls giúp giảm độ trễ NLU từ **~1.5s xuống còn ~0.8s**. Vocabulary rule-based chạy cục bộ để tăng recall kể cả khi LLM rewrite chưa đủ tốt.

4. **NODE 4: Second Cache Lookup (Kiểm tra Cache lần 2)**
   - **Công nghệ áp dụng**: PostgreSQL / SQLite SQL Query.
   - **Logic xử lý**: Thực hiện đối sánh Cache lần 2 dựa trên câu hỏi đã được chuẩn hóa ở Node 3. Điều này giúp nâng cao đáng kể tỷ lệ trúng cache trong trường hợp câu hỏi thô của người dùng dài dòng hoặc viết sai chính tả nhưng có cùng bản chất ngữ nghĩa với câu hỏi đã lưu.
   - **Thông số kỹ thuật**: Độ trễ **~5-10ms**.

5. **NODE 5: Hybrid Search (Dense + Sparse + SQL Keyword Fallback + Metadata Boost)**
   - **Công nghệ áp dụng**: Qdrant Vector Database (`qdrant-client`) kết hợp Dense Vectors (mô hình `text-embedding-3-small` của OpenAI, 1536 chiều), Sparse Vectors (BM25/FastEmbed), và SQL fallback trên bảng `document_chunks`.
   - **Logic xử lý**: Chuyển đổi câu hỏi chuẩn hóa thành Dense/Sparse vectors (Query Expansion đã được tắt bỏ hoàn toàn để tránh quá tải hệ thống và giảm độ trễ). Qdrant dùng **RRF (Reciprocal Rank Fusion)** để hợp nhất kết quả, sau đó SQL fallback bắt các cụm literal quan trọng bị miss bởi vector search. Domain metadata hints sẽ boost tài liệu theo `category`, `document_type`, `service` và ưu tiên `data/overview/service_catalog.md` cho câu hỏi tổng quát.
   - **Thông số kỹ thuật**: Kích thước Dense Vector `dimensions = 1536`. Lấy ra **Top 25 tài liệu thô** (`limit = 25`) trước khi rerank.

6. **NODE 6: Cohere Reranker (Tái xếp hạng ngữ nghĩa chuyên sâu)**
   - **Công nghệ áp dụng**: API Cohere Rerank (thư viện client `cohere`) với mô hình `rerank-multilingual-v3.0`.
   - **Logic xử lý**: Đưa cặp câu hỏi chuẩn hóa và nội dung của 25 tài liệu thô vào API Cohere Rerank để tính toán điểm số tương thích ngữ nghĩa trực tiếp. Cohere Rerank sử dụng cơ chế Cross-Attention tự động tối ưu hóa cho tài liệu đa ngôn ngữ (đặc biệt là tiếng Việt), khắc phục hoàn toàn điểm yếu mất ngữ cảnh của Embedding Bi-Encoder thông thường.
   - **Thông số kỹ thuật**: Lọc lấy **Top 10 tài liệu tinh** khắt khe nhất (`top_n = 10`). Ngưỡng điểm relevance tối thiểu để kích hoạt mở rộng parent-child thích ứng là `relevance_score >= 0.7`.

7. **NODE 7: Adaptive Parent-Child Section Expansion (Mở rộng ngữ cảnh thích ứng)**
   - **Công nghệ áp dụng**: Bộ lọc truy vấn metadata Qdrant & PostgreSQL.
   - **Logic xử lý**: 
     - Với các chunk tinh có `relevance_score >= 0.7`, hệ thống truy quét VectorDB dựa trên `parent_chunk_id` để lấy thêm toàn bộ các chunk con khác thuộc cùng một chương/mục/bảng biểu lớn (tối đa 10 chunks). Kỹ thuật này giúp tái cấu trúc trọn vẹn ngữ cảnh gốc (như bảng biểu đầy đủ hoặc điều khoản luật nguyên vẹn) để LLM đọc hiểu.
     - Với các chunk có điểm `< 0.7`, giữ nguyên nội dung chunk gốc để tránh làm loãng prompt.
     - *Deduplication (Khử trùng lặp)*: Tự động loại bỏ tiêu đề trùng lặp ở đầu các chunk con thứ cấp (index > 0) và loại bỏ các chunk bị lồng nhau để tối ưu hóa kích thước context.
   - **Thông số kỹ thuật**: Ngưỡng điểm thích ứng `0.7`. Số lượng chunk con tối đa `max_parent_chunks = 10`.

8. **NODE 8: LLM Synthesis & Stream (Tổng hợp phản hồi dạng Stream)**
   - **Công nghệ áp dụng**: OpenAI API `chat/completions` với mô hình `gpt-4o-mini`.
   - **Logic xử lý**: Nhận prompt chứa toàn bộ ngữ cảnh đã qua giải nén parent-child, câu hỏi chuẩn hóa và lịch sử hội thoại gần nhất. LLM tổng hợp câu trả lời khách quan, trung thực dựa trên tài liệu được cung cấp và truyền dữ liệu từng chữ về client qua giao thức **Server-Sent Events (SSE)** kèm Metadata nguồn trích dẫn (`sources`).
   - **Thông số kỹ thuật**: Nhiệt độ `temperature = 0.2` (giảm thiểu tối đa ảo tưởng thông tin), `max_tokens = 2048`. Chỉ số độ trễ xử lý của máy chủ (`TTFT - Time To First Token`) được chốt ngay khi nhận ký tự đầu tiên từ OpenAI để phản ánh trung thực hiệu năng máy chủ.

9. **NODE 9: Semantic Cache Saving & Output (Lưu cache và trả kết quả)**
    - **Công nghệ áp dụng**: PostgreSQL / SQLite Cache Storage.
    - **Logic xử lý**: Sau khi sinh câu trả lời, hệ thống lưu câu trả lời hợp lệ vào `SemanticCache` cho cả hai khóa: câu hỏi thô ban đầu (Node 2) và câu hỏi đã được chuẩn hóa (Node 4) nhằm tối đa hóa cơ hội Cache Hit cho các lượt truy vấn tương lai. Các nỗ lực prompt injection, lộ system prompt/API key/cấu hình nội bộ và yêu cầu bôi nhọ không căn cứ được chặn sớm ở Input Gateway/NLU safety, giúp answer path không bị false-positive với câu trả lời hợp lệ.
---

## 🧱 2.1 Ghi Chú Thay Đổi Kiến Trúc Knowledge Builder

Các thay đổi mới nhất của pipeline dữ liệu:

- **URL Registry thay cho auto-discovery**: crawler production không tự mò URL bằng Playwright/Chromium. Admin quản lý danh sách crawl trong bảng `crawl_sources`; `crawler/urls.json` chỉ còn là seed/bootstrap khi DB rỗng.
- **Knowledge Builder**: tab admin mới gom CRUD URL, `Crawl Main Site -> Markdown`, `Crawl Platform/PDF -> Markdown`, `Clear ALL Knowledge`, và `Ingest ALL From data/`.
- **Pure-code crawler**: crawler production không gọi LLM/Agent. `news`, `vehicle` và nhóm `pdf` được tách cleaner/parser riêng; trang dịch vụ main-site vẫn dùng parser cũ đang ổn.
- **Clear/Ingest tách rời**: `Clear ALL Knowledge` chỉ xóa Postgres `document_chunks` và reset Qdrant. `Ingest ALL From data/` chỉ nạp snapshot trong `data/`, không clear ngầm.
- **PDF parser-first**: PDF platform đi qua `crawler/pdf_utils.py` với `pymupdf4llm`/PyMuPDF, log `bytes`, `page_count`, `raw_md_len`, `clean_md_len`, `table_count`; không còn dùng `pypdf` làm đường chính.
- **Markdown Quality Gate**: crawler và ingestion kiểm tra frontmatter, heading rỗng, CTA/form rác, text dính, và bảng Markdown trước khi đưa vào knowledge.
- **Overview Catalogs**: hệ thống sinh deterministic `data/overview/service_catalog.md`, `pricing_catalog.md`, `platform_vehicle_catalog.md`, `policy_catalog.md`, `news_catalog.md` để trả lời câu hỏi tổng quát.
- **Domain Vocabulary**: RAG có lớp vocabulary rule-based để map từ đời thường/sai chính tả sang thuật ngữ tài liệu, ví dụ `đền hàng` -> `bồi thường/bảo hiểm`, `ăn chia` -> `doanh thu/chiết khấu`, `green exress` -> `Green Express`.

Giải thích node mới trong Mermaid:

- `Domain Vocabulary`: node rule-based chạy sau NLU để bổ sung canonical query, chuẩn hóa từ vựng và metadata hints. (Lưu ý: Tính năng Query Expansion đã được tắt bỏ hoàn toàn để giảm thiểu độ trễ, tiết kiệm tài nguyên sinh token của LLM và concurrency cho VectorDB).
- `Hybrid Search: Dense + Sparse + SQL Fallback`: node truy xuất hợp nhất semantic vector, BM25 sparse vector và SQL keyword fallback. Metadata boost ưu tiên đúng category/document type, đặc biệt `overview` với câu hỏi tổng quát.

---

## 🛠️ 3. Kỹ Thuật Phân Đoạn Tài Liệu Nâng Cao (Table & Heading-Aware Chunking)

Hệ thống tích hợp một ingestion pipeline chuyên sâu với bộ phân đoạn tài liệu thông minh nhằm đảm bảo tính toàn vẹn ngữ nghĩa của cấu trúc tài liệu pháp lý và bảng biểu:

### 💎 A. Phân Đoạn Nhận Biết Tiêu Đề (Heading-Aware Splitting)
* **Logic hoạt động**: Sử dụng bộ thư viện `MarkdownHeaderTextSplitter` để bóc tách tài liệu theo phân cấp cấu trúc tiêu đề Markdown từ `#` đến `####`. Đường dẫn mục lục được ghi nhận thẳng vào metadata `"section"` (ví dụ: `Dịch vụ di chuyển > Xanh SM Taxi > Biểu phí Hà Nội`).
* **Đặc tính chống mất ngữ cảnh**: Đối với các chunk con thứ cấp (index > 0) thuộc cùng một chương/mục lớn, hệ thống tự động nhúng thêm tiêu đề ở đầu văn bản dưới dạng `### {meta['section']}

`. Điều này giúp mô hình Embedding ghi nhận đầy đủ ngữ cảnh của chủ đề mục lớn, tránh tình trạng chunk con bị cắt vụn rời rạc và mất thông tin nguồn gốc.

### 💎 B. Phân Đoạn Đệ Quy Mềm (Recursive Character Splitting)
* **Thông số kỹ thuật**: Sau khi chia nhỏ theo tiêu đề, hệ thống áp dụng `RecursiveCharacterTextSplitter` với kích thước `chunk_size = 400` ký tự và độ chồng lấn `chunk_overlap = 50` ký tự.
* **Logic xử lý**: Các ký tự phân tách được chọn ưu tiên theo thứ tự `["

", "
", ". ", " ", ""]`. Thuật toán đảm bảo văn bản được ngắt ở ranh giới đoạn văn hoặc dấu chấm câu phù hợp, không bị cắt đôi một câu hoặc một từ dở dang.

### 💎 C. Bảo Toàn Cấu Trúc Bảng Biểu (Table-Aware Parsing)
Hệ thống tích hợp bộ phát hiện và xử lý bảng biểu Markdown thông minh (Table-Aware Splitter) để đối phó với các bảng giá cước phức tạp của Xanh SM:
1. **Cô lập cấu trúc bảng (Table Isolation)**: Tự động tách biệt các khối bảng biểu Markdown. Đối với các bảng biểu vừa và nhỏ (dưới 1500 ký tự), hệ thống cô lập bảng đó thành một chunk độc lập hoàn chỉnh, tuyệt đối không cắt nhỏ, tránh việc trộn lẫn với văn bản mô tả xung quanh.
2. **Nhân bản tiêu đề dòng/cột (Header Replication)**: Đối với các bảng lớn (vượt quá 1500 ký tự), thuật toán tiến hành cắt bảng theo từng dòng nhưng **luôn tự động nhân bản hai dòng tiêu đề đầu tiên** (column headers) vào đầu mỗi chunk con thứ cấp. Nhờ đó, mô hình VectorDB tìm kiếm đúng bản ghi theo từng cột và LLM đọc hiểu chính xác giá trị tương ứng của từng dòng trong bảng biểu lớn.

### 💎 D. Khóa Định Danh Không Xung Đột (Collision-Free Unique UUID)
* **Logic xử lý**: Mỗi chunk được định danh bằng một chuỗi ASCII MD5 hash sạch (`chunk_id`) sinh ra từ metadata tọa độ: `hash(filename + section + chunk_index)`.
* **Mục đích**: Loại bỏ hoàn toàn nguy cơ lỗi/crash của PostgreSQL và Qdrant khi xử lý các ký tự Unicode tiếng Việt phức tạp trong tên file hoặc mục lục tiêu đề của tài liệu.

### 💎 E. Trình Đọc Tài Liệu Đồng Bộ (Unified Document Loader)
* **Công nghệ**: Sử dụng `pymupdf4llm` thay thế cho thư viện `pypdf` truyền thống để bóc tách các file PDF. Thư viện này hỗ trợ bóc tách PDF trực tiếp thành định dạng Markdown, giữ nguyên cấu trúc tiêu đề và các bảng số liệu phức tạp trước khi chuyển qua bộ cắt chunk.

### 💎 F. Table-First Retrieval Chunking
Chiến thuật chunking mới được tối ưu cho truy hồi, không chỉ cho ingestion:
* **HTML table giữ nguyên bản đầy đủ**: Mỗi bảng HTML được lưu thành một chunk `html_table_full` riêng để bảo toàn `rowspan`, `colspan` và toàn bộ cấu trúc gốc.
* **Sinh thêm chunk chỉ mục theo dòng**: Cùng một bảng HTML còn tạo thêm các chunk `table_row_index` gộp 1-3 dòng dữ liệu mỗi chunk để tăng recall khi người dùng hỏi chi tiết theo cột hoặc theo giá trị rời rạc.
* **Metadata bắt buộc cho bảng**: Mỗi chunk bảng mang các trường `chunk_type`, `table_id`, `table_title`, `row_start`, `row_end`, `derived_from`, `chunk_id`, `parent_chunk_id`.
* **Chunk ID ổn định**: `chunk_id` được tạo từ metadata ổn định + hash nội dung, tránh collision và giúp Qdrant/Postgres không bị lỗi khi tái ingest.
* **Retrieval-first expansion**: Khi reranker trả về chunk `table_row_index`, pipeline sẽ tự động truy ngược `derived_from` để lấy lại chunk `html_table_full` tương ứng. Nhờ vậy context trả cho LLM vẫn là bảng đầy đủ, nhưng retrieval ban đầu vẫn bám được các giá trị nhỏ trong bảng.
* **Qdrant payload indexes**: Hệ thống đã index sẵn các trường `metadata.chunk_type`, `metadata.table_id`, `metadata.derived_from`, `metadata.row_start`, `metadata.row_end`, `metadata.chunk_index` để truy vấn và mở rộng context nhanh hơn.

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
Copy file `.env.example` thành `.env` và điền key OpenAI & Cohere của bạn:
```env
OPENAI_API_KEY=sk-proj-xxxx...
COHERE_API_KEY=nzDrVpZ...
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4o-mini
NLU_MODEL=gpt-4o-mini
AI_JUDGE_MODEL=gpt-4o-mini
RERANKER_PROVIDER=cohere
RERANKER_MODEL=rerank-multilingual-v3.0

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

## ☁️ 5. Hướng Dẫn Triển Khai Lên Đám Mây (Deploy)

### 🖥️ A. Backend - Triển Khai Lên Railway
Hệ thống được thiết kế để dễ dàng đưa lên Production thông qua [Railway.app](https://railway.app).
1. Tạo một project mới trên Railway.
2. Thêm **PostgreSQL Database** plugin từ Railway.
3. Liên kết GitHub Repo của dự án vào Railway.
4. Chuyển sang tab **Variables** và cấu hình các thông số:
   - `OPENAI_API_KEY`: Key của bạn.
   - `COHERE_API_KEY`: Key của bạn.
   - `DATABASE_URL`: Sử dụng Connection URL nội bộ của PostgreSQL plugin (Railway tự cấp phát).
   - `QDRANT_URL`: URL cụm Qdrant Cloud của bạn (Nên tạo tài khoản trên Qdrant Cloud miễn phí).
   - `GOOGLE_CLIENT_ID`: Client ID Google Auth.
   - `AI_JUDGE_MODEL`: Mô hình AI chấm điểm đánh giá tự động (mặc định: `gpt-4o-mini`).
   - `PORT`: `8000`.
   - `HF_TOKEN`: (Tùy chọn nhưng khuyến nghị) Token Hugging Face của bạn để tải các mô hình FastEmbed nhanh hơn và tránh lỗi giới hạn lượt tải (rate limits).
5. Railway sẽ tự động detect Python (thông qua `requirements.txt`) và chạy lệnh `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

### 🌐 B. Frontend - Triển Khai Lên Vercel
Giao diện React/Vite được tối ưu để lưu trữ tĩnh và deploy siêu tốc lên [Vercel](https://vercel.com).
1. Đẩy mã nguồn của bạn lên GitHub.
2. Đăng nhập vào Vercel, chọn **Add New** -> **Project**.
3. Import GitHub repository của bạn.
4. Tại cấu hình dự án, thiết lập **Root Directory** là `frontend`.
5. Vercel sẽ tự động nhận diện khung làm việc (Framework Preset) là **Vite**.
6. Tại mục **Environment Variables**, thêm các biến sau:
   - `VITE_API_BASE`: Địa chỉ URL API của Backend sau khi deploy lên Railway (ví dụ: `https://ten-backend-cua-ban.up.railway.app`).
   - `VITE_GOOGLE_CLIENT_ID`: Client ID Google OAuth2 của bạn để nhúng vào nút đăng nhập Google.
7. Bấm **Deploy**. Dự án của bạn sẽ hoàn thành build trong vòng chưa đầy 1 phút!

---

### 🔑 Hướng Dẫn Cấu Hình Google OAuth & Client ID Khi Deploy

Khi deploy ứng dụng lên môi trường Production (như Vercel, Netlify hoặc tên miền riêng), bạn cần cấu hình trên Google Cloud Console để tránh lỗi **invalid_client (Lỗi 401)**:

1. **Cập nhật Authorized Origins trên Google Cloud Console:**
   * Truy cập [Google Cloud Console Credentials](https://console.cloud.google.com/apis/credentials).
   * Mở xem chi tiết **Client ID Web Application** của bạn.
   * Tại mục **Authorized JavaScript origins**, hãy bấm **+ Add URI** và điền đầy đủ:
     * Địa chỉ chạy local: `http://localhost:5173`
     * Địa chỉ chạy production của frontend: `https://ten-ung-dung-cua-ban.vercel.app` *(Lưu ý: Không viết dấu gạch chéo `/` ở cuối)*
   * Tại mục **Authorized redirect URIs**, bấm **+ Add URI** và điền tương tự:
     * `http://localhost:5173`
     * `https://ten-ung-dung-cua-ban.vercel.app`
   * Bấm **Save** ở chân trang. *(Thông thường thay đổi sẽ có hiệu lực sau 5-15 phút)*

2. **Cập nhật Biến Môi Trường (Environment Variables) trên hosting:**
   * **Tại Backend (Railway):** Thêm biến `GOOGLE_CLIENT_ID` trỏ về Client ID Google của bạn.
   * **Tại Frontend (Vercel):** Thêm biến `VITE_GOOGLE_CLIENT_ID` trỏ về cùng Client ID Google của bạn để Vite có thể nhúng và biên dịch nút đăng nhập lúc đóng gói.

---

## 🧪 6. Quy Trình Chạy Đánh Giá Chất Lượng RAG (Ragas Benchmark)

> Cập nhật kiến trúc gần nhất: pipeline hiện chuyển trách nhiệm chặn prompt-injection, yêu cầu lộ system prompt/API key/cấu hình nội bộ và yêu cầu bôi nhọ không căn cứ sang **Input Gateway/NLU safety**. NLU có thêm **fast-path rule-based** cho các câu RAG rõ ràng để bỏ qua OpenAI NLU call, giảm latency ở bước `NLU Gateway`; fast-path cũng được làm giàu bằng **Domain Vocabulary** để xử lý viết tắt/sai chính tả như `xsm`, `vgreen`, `dk`, `platfom`. Model NLU được tách qua `NLU_MODEL`, mặc định vẫn là `gpt-4o-mini`. Đường sinh câu trả lời không còn dùng Output Guardrail như một node chặn chính để tránh false-positive với câu trả lời hợp lệ như thông số xe EC Van. Benchmark cũng lưu snapshot vào bảng `evaluation_runs` để so sánh chất lượng giữa các lần chạy.

### Bảng lưu lịch sử benchmark

Mỗi lần chạy `evaluation/ragas_eval.py`, hệ thống ghi thêm một snapshot vào bảng `evaluation_runs` gồm:

| Cột | Ý nghĩa |
|---|---|
| `run_name` | Mã lần chạy dạng `run_YYYYMMDD_HHMMSS` |
| `dataset_name`, `total_cases`, `model_name` | Bộ dữ liệu, số case và model dùng khi chạy |
| `recall_5`, `recall_10`, `mrr`, `ndcg_5` | Retrieval metrics |
| `faithfulness`, `correctness`, `relevancy` | Generation metrics từ LLM-as-Judge |
| `average_latency_sec` | Latency trung bình mỗi case |
| `metrics_json`, `details_json` | Snapshot đầy đủ để audit/so sánh lại |

Admin UI đọc `/api/admin/eval/runs` để hiển thị recent runs và delta so với lần chạy trước, giúp theo dõi hệ thống đang cải thiện hay suy giảm.

Dự án được trang bị bộ benchmark chất lượng tìm kiếm & trả lời tự động bằng LLM-as-a-Judge kết hợp các chỉ số truyền thống (Recall, MRR, NDCG).

### Khởi chạy đánh giá tự động:
Chạy lệnh python từ thư mục gốc của dự án:
```bash
.\venv\Scripts\python.exe evaluation/ragas_eval.py
```

### Kết quả xuất bản:
* Kết quả tóm tắt điểm trung bình sẽ hiển thị trực tiếp trên Terminal sau khi chạy xong.
* Báo cáo đầy đủ cho từng câu hỏi kiểm thử được ghi nhận tự động vào [evaluation_report.json](file:///c:/Users/DUNG/Desktop/RAG_XANH_SM/evaluation_report.json).
* Để biết thêm chi tiết về cơ chế chấm điểm và cấu trúc bộ câu hỏi (Golden Dataset), tham khảo [EVALUATION.md](file:///c:/Users/DUNG/Desktop/RAG_XANH_SM/evaluation/EVALUATION.md).
