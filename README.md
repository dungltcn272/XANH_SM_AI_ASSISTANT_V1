# 🚗 Xanh SM AI Assistant (Phase 9)

**Xanh SM AI Assistant** là hệ thống trợ lý ảo hội thoại toàn diện cấp doanh nghiệp (Production-Grade) được thiết kế và phát triển dành riêng cho hệ sinh thái **Xanh SM**. Trợ lý ảo tích hợp nhiều phân hệ động từ hỏi đáp tri thức (RAG) đến gợi ý dịch vụ ăn uống (Food Recommendation) nhằm phục vụ đắc lực cho khách hàng, đối tác tài xế, đối tác cửa hàng merchant và đội ngũ CSKH.

---

## 🔗 Trải Nghiệm Live Demo

> [!TIP]
> ### 🌐 Truy Cập Trực Tuyến
> Trải nghiệm giao diện và các tính năng thông minh của trợ lý ảo tại:
> 
> **[👉 Ấn vào đây để truy cập Live Demo 👈](https://rag-xanh-sm-v1.vercel.app/)**
>
> *Hệ thống hỗ trợ đầy đủ Google OAuth, lịch sử chat cá nhân và bảng điều khiển quản trị thời gian thực.*

---

## 🌟 Các Năng Lực Cốt Lõi (Theo Pitch Deck W4)

Hệ thống gom nhiều năng lực nghiệp vụ vào một trải nghiệm hội thoại duy nhất:

* **🔍 Knowledge Search**: Tra cứu nhanh chóng mọi tài liệu nội bộ, chính sách cước phí và điều khoản vận hành.
* **🔬 Deep Research**: Chế độ tìm kiếm chuyên sâu tự động tổng hợp nhiều nguồn tài liệu, bỏ qua cache và hiển thị nguồn trích dẫn (`sources`) chi tiết.
* **⚡ Vehicle Expert**: Hỏi đáp thông tin kỹ thuật, tính năng và trải nghiệm di chuyển các dòng xe điện VinFast.
* **💰 Pricing Assistant**: Tính toán và giải thích chi tiết các cơ chế giá cước, ưu đãi và điều kiện áp dụng.
* **📰 News Digest**: Tóm tắt và cập nhật các tin tức biến động thị trường liên quan đến Xanh SM.
* **🍜 Food Recommendation**: Gợi ý món ăn thông minh dựa trên vị trí (tọa độ GPS), ngân sách, thời gian (ETA) và khẩu vị người dùng.
* **🛡️ Policy & Support**: Hỗ trợ CSKH giải quyết khiếu nại, hướng dẫn thủ tục theo đúng văn phong chuẩn.
* **📊 Data Analytics**: Giám sát và ghi vết mọi suy luận (Trace Logs), đo lường hiệu năng và khảo sát ý kiến người dùng.

---

## 🚀 Các Nâng Cấp Nổi Bật & Bộ Nhớ Đa Tầng

> [!IMPORTANT]
> ### 💎 Cập Nhật Mới Tại Phase 9 (ML-Ready, Giải Thích Gợi Ý & Trí Nhớ Đa Tầng)
> * **Giải thích lý do gợi ý món ăn (Explainable Recommendation)**: Hệ thống tự động lý giải chi tiết "Vì sao tôi được gợi ý món ăn này?" dựa trên sự kết hợp giữa:
>   - **Heuristics định lượng**: Tính toán và hiển thị rõ ràng độ khớp khoảng cách địa lý (km), thời gian giao hàng (ETA), khoảng giá ngân sách, tín hiệu đánh giá tốt (rating/reviews) và các chương trình khuyến mãi giảm giá.
>   - **LLM-Synthesized Advice**: Mô hình Food Answer LLM phân tích các đặc trưng quán ăn để sinh lời khuyên tư vấn ngữ cảnh cá nhân hóa (advice) hiển thị trực quan dưới từng Card món ăn.
> * **Trí nhớ hội thoại ngắn hạn (Short-term Working Memory)**: Lưu giữ 5-10 lượt chat gần nhất giúp NLU Orchestrator giải quyết các truy vấn mang tính tham chiếu liên kết:
>   - *Hội thoại ngữ cảnh*: Khi người dùng hỏi "Xe VF6 có đặc điểm gì?" và tiếp tục hỏi "Ưu điểm của nó là gì?", hệ thống tự động nhận diện "nó" là VF6.
>   - *Lựa chọn theo danh sách*: Khi AI đưa ra danh sách các món ăn hoặc dòng xe, người dùng chỉ cần gõ "Chọn số 1", "Lấy cái thứ hai" hoặc "Quán phở đầu tiên", hệ thống tự động đối chiếu lịch sử để xử lý chính xác ý định.
> * **Trí nhớ dài hạn & Hồ sơ người dùng (Long-term Profile Memory)**: Tự động ghi nhớ lâu dài vị trí (địa chỉ nhà riêng, cơ quan), sở thích ẩm thực (khẩu vị cay, ăn chay, thích đồ ngọt) và thói quen chi tiêu của người dùng trong bảng `user_profiles` để phục vụ cá nhân hóa không cần hỏi lại.
> * **ML-Ready Architecture (Ranker & Explorer)**: Sẵn sàng cho MLOps với module `XGBoostFoodRanker`, `CohereCrossEncoder`, và `BanditExplorer` kết hợp ghi trace log suy luận chi tiết lên Admin Dashboard.

> [!NOTE]
> ### 💎 Cập Nhật Mới Tại Phase 8 (Parallel NLU Routing & Optimization)
> * **Kiến trúc Multi-threading NLU**: "Đập bỏ" God Prompt nguyên khối, tách thành 3 System Prompts chuyên biệt (Intent, Food, Memory) và gọi LLM song song (Parallel execution) qua ThreadPoolExecutor. 
> * **Cost & Latency Optimization**: Giảm 50% số lượng Input/Output Tokens, tiết kiệm chi phí và tăng tốc độ xử lý (Latency < 600ms cho phân loại Intent).
> * **Food Recommendation Service V2**: Sử dụng LLM song song tự động xác định ngữ cảnh vị trí, nếu thiếu thông tin sẽ trả UI Form bản đồ. Hỗ trợ ranking dựa trên khoảng cách, ETA, giá cả, và tạo câu trả lời tự nhiên qua Food Answer LLM.

## Kiến Trúc Hệ Thống Tổng Quan

Hệ thống triển khai kiến trúc **NLU-Gateway RAG (Phase 8)** tiên tiến nhất hiện nay với tốc độ xử lý siêu tốc nhờ chia nhỏ luồng LLM, tự động nhận biết intent để rẽ nhánh sang luồng RAG hoặc Food Recommendation:

```mermaid
graph TD
    A([User Input]) --> N[Normalize Input]
    N --> B{Input Gateway Safety}
    B -- "Prompt injection / secret leak" --> Block[Refusal Response]
    B -- "Safe" --> C{Early Exact Cache}

    C -- "Cache Hit (~5ms)" --> Out([Stream Answer + Citations])
    C -- "Cache Miss" --> LC[Memory Signal Extraction]
    LC --> D[Parallel NLU Orchestrator]
    
    D --> E{NLU Intent Classification}
    E -- "small-talk" --> Stalk[Return NLU suggested_answer]
    E -- "sensitive" --> Sen[Return NLU suggested_answer]
    E -- "missing_info" --> Miss[Ask clarification from NLU suggested_answer]
    E -- "rag" --> F{Second Exact Cache}
    E -- "food_recommendation" --> M{Missing info?}

    %% Luồng Food Recommendation
    M -- yes --> FORM[Answer + ui_form/map payload]
    M -- no --> FR1[Geocode & Target Coordinates]
    FR1 --> FR2[Geo-BM25 Hybrid Retrieval]
    FR2 --> FR3[ML-Ready Candidate Ranker]
    FR3 --> FR4[Food Answer LLM]
    FR4 --> CARD[Food cards UI + advice]
    CARD --> LOG[Interaction + trace log]
    LOG --> Out

    %% Luồng RAG
    F -- "Cache Hit" --> Out
    F -- "Cache Miss" --> G[Hybrid Retrieval: Dense + Sparse]
    G --> H[Cohere Reranker]
    H --> I[Parent / Section Context Expansion]
    I --> K[LLM Synthesis & SSE Stream]
    K --> CacheSave[Save Semantic Cache]
    CacheSave --> Out

    Block --> Out
    Stalk --> Out
    Sen --> Out
    Miss --> Out
    FORM --> Out

    style A fill:#00A651,stroke:#fff,color:#fff
    style Out fill:#00A651,stroke:#fff,color:#fff
    style Block fill:#ff4444,stroke:#fff,color:#fff
    style Stalk fill:#f59e0b,stroke:#fff,color:#fff
    style Sen fill:#f43f5e,stroke:#fff,color:#fff
    style Miss fill:#f59e0b,stroke:#fff,color:#fff
    style B fill:#f43f5e,stroke:#fff,color:#fff
    style FR1 fill:#0ea5e9,stroke:#fff,color:#fff
    style FR2 fill:#0ea5e9,stroke:#fff,color:#fff
    style FR3 fill:#0ea5e9,stroke:#fff,color:#fff
    style FR4 fill:#0ea5e9,stroke:#fff,color:#fff
    style CARD fill:#0ea5e9,stroke:#fff,color:#fff
    style LC fill:#a855f7,stroke:#fff,color:#fff
```

* Chi tiết cấu trúc thư mục dự án xem tại: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
* Chi tiết nguyên lý hoạt động và chi tiết từng Node xử lý xem tại: [`docs/PIPELINE.md`](docs/PIPELINE.md)
* Chi tiết luồng xử lý Food Recommendation và thiết kế ML-Ready xem tại: [`docs/FOOD_PIPLINE.md`](docs/FOOD_PIPLINE.md)
* Database diagram, class diagram và giải thích chi tiết từng bảng xem tại: [`docs/DATABASE_SCHEMA.md`](docs/DATABASE_SCHEMA.md)
* Quy trình thay đổi schema database bằng Alembic xem tại: [`docs/DATABASE_MIGRATIONS.md`](docs/DATABASE_MIGRATIONS.md)

---

## 🛠️ Hướng Dẫn Khởi Chạy Cục Bộ (Local)

### 📦 A. Yêu Cầu Môi Trường
- **Python 3.10+**
- **Node.js 18+**
- **Docker & Docker Compose** (Chạy Qdrant và PostgreSQL)

### 📦 B. Khởi Động Databases Bằng Docker
*(Hãy chắc chắn đã bật Docker Desktop trước khi chạy lệnh)*
```bash
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
Sao chép file `.env.example` thành `.env` và điền key OpenAI & Cohere:
```env
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
COHERE_API_KEY=YOUR_COHERE_API_KEY
DATABASE_URL=postgresql://postgres:password@localhost:5432/greensm_db
QDRANT_URL=http://localhost:6333
```

3. **Chạy Server FastAPI:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Khi chạy backend local sau khi đổi schema, chạy `alembic upgrade head` trước. Khi deploy Docker, lệnh này được chạy tự động trước khi start API.

### 📦 D. Cài Đặt & Khởi Chạy Frontend
Mở một Terminal mới:
```bash
cd frontend
npm install
npm run dev
```
Truy cập ứng dụng tại: **[http://localhost:5173](http://localhost:5173)**

### 📦 E. Khởi Động Ứng Dụng Mobile (React Native / Expo)
```bash
cd mobile
npm install
npm start
```

---

## ☁️ Hướng Dẫn Triển Khai Lên Đám Mây (Deploy)

### 🖥️ A. Backend - Triển Khai Lên Railway
1. Thêm **PostgreSQL Database** plugin trên Railway.
2. Liên kết GitHub Repo của dự án.
3. Cấu hình các biến môi trường thiết yếu: `OPENAI_API_KEY`, `COHERE_API_KEY`, `DATABASE_URL` (lấy từ Railway), `QDRANT_URL` (Qdrant Cloud), `PORT=8000`.

### 🌐 B. Frontend - Triển Khai Lên Vercel
1. Thiết lập **Root Directory** là `frontend`.
2. Cấu hình biến môi trường:
   - `VITE_API_BASE`: Link Backend trên Railway.
   - `VITE_GOOGLE_CLIENT_ID`: Client ID Google OAuth2.

---

## 🧪 Quy Trình Chạy Đánh Giá Chất Lượng RAG (Ragas Benchmark)

Dự án tích hợp bộ công cụ đánh giá tự động lưu lịch sử chạy vào bảng `evaluation_runs`.

Chạy lệnh python từ thư mục gốc của dự án:
```bash
.\venv\Scripts\python.exe evaluation/ragas_eval.py
```
* Kết quả tóm tắt điểm trung bình sẽ hiển thị trực tiếp trên Terminal sau khi chạy xong.
* Báo cáo chi tiết được ghi nhận vào [`evaluation_report.json`](evaluation_report.json).
* Chi tiết cơ chế chấm điểm và bộ Golden Dataset tham khảo thêm tại [`EVALUATION.md`](evaluation/EVALUATION.md).
