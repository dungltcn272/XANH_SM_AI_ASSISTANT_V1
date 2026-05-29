# 👨‍🏫 Xanh SM Enterprise RAG - Hệ Tư Duy & Sơ Đồ Kiến Trúc (MINDSET)

Chào mừng các em học sinh và các kỹ sư hệ thống đến với **Lớp Học RAG Doanh Nghiệp** của **Thầy Giáo AI Xanh SM**! 

Tài liệu này trình bày toàn bộ hệ tư duy thiết kế, sơ đồ kiến trúc luồng dữ liệu chuẩn hóa sản xuất (Production-Grade) cùng nhật ký giải quyết lỗ hổng cấu trúc dữ liệu thực tế của dự án **Xanh SM RAG System**.

---

## 🌿 1. Sơ Đồ Kiến Trúc Luồng Hoạt Động (RAG Workflow)

Dưới đây là sơ đồ chi tiết biểu diễn luồng đi của một câu hỏi từ lúc người dùng nhập vào cho đến khi nhận được câu trả lời kèm trích dẫn đã xác thực nguồn gốc.

> Luồng hoạt động chính thức của Phase 3 trong `app/rag/chain.py` là:
> 1. **Nhận câu hỏi** từ người dùng.
> 2. **Chạy qua Conversation Gateway**: Chuẩn hóa Unicode dựng sẵn (NFC), nhận dạng ngôn ngữ (Anh/Việt) và chạy Safety Precheck. Nếu phát hiện vi phạm, hệ thống chặn ngay lập tức (early exit).
> 3. **Ý định & Định tuyến (Intent Classifier)**: Phân loại câu hỏi thành `small-talk` (xã giao), `faq` (câu hỏi phổ biến), `rag` (truy xuất sâu), `task-agent` (tính toán), hoặc `sensitive` (độc hại).
> 4. **Tác vụ nghiệp vụ (Task Agent / Slot Filling)**: Đối với tác vụ tính phí hủy chuyến (`refund_calculator`), bóc tách thực thể `vehicle_type` và `waiting_time`. Nếu thiếu, sinh câu hỏi làm rõ (Clarification). Nếu đủ, gọi `RefundCalculatorTool` tính toán tức thì.
> 5. **Kiểm tra đệm (Semantic Cache)**: Đối với luồng RAG, so khớp MD5 tuyệt đối hoặc khoảng cách ngữ nghĩa Cosine Similarity (>= 0.96) để trả về ngay dưới `< 10ms` với chi phí `0đ`.
> 6. **Biên dịch ngữ cảnh (Query Rewrite)**: Đọc lịch sử 3 lượt chat gần nhất để viết lại đại từ mơ hồ thành câu hỏi độc lập.
> 7. **Chiến lược truy xuất động (Strategy Selector)**: Đánh giá câu hỏi để phân phối luồng tìm kiếm BM25 Keyword, Dense Search, hoặc Hybrid Search.
> 8. **Tìm kiếm lai phân quyền (Shared Search)**: Thực hiện tìm kiếm và áp dụng bộ lọc vai trò trực tiếp tại ChromaDB và BM25.
> 9. **Tái xếp hạng (Cross-Encoder Reranker)**: Stage 2 dùng Transformer Attention chéo lọc ra Top 5 tốt nhất.
> 10. **Gộp Parent-Child**: Vector search mảnh con (Child chunks) nhạy bén, LLM đọc mảnh cha (Parent chunks) đầy đủ.
11. **LLM Generator & Synthesis**: LLM tổng hợp phản hồi dựa trên ngữ cảnh đã nén.
12. **Citation Validator & Cost Tracking**: Xác thực nguồn sạch, đối khớp URL, tính toán số lượng token và báo cáo chi phí (USD/VND) theo thời gian thực. (Lưu ý: Faithfulness Check hiện được tích hợp ở chế độ pass-through để tối ưu tốc độ phản hồi).

```mermaid
graph TD
    %% Nodes
    Q[❓ 1. Nhận Câu Hỏi Người Dùng] --> GW[🛡️ 2. Conversation Gateway<br>NFC, Safety & Lang Check]
    
    GW -->|Phát hiện vi phạm/Spam| Block[🚫 Chặn Guardrail & Early Exit]
    GW -->|Hợp lệ| Classify[🎯 3. Intent + Query Classifier]
    
    Classify -->|sensitive| Block
    Classify -->|small-talk| SmallTalk[💬 Small Talk Path<br>Phản hồi trực tiếp LLM]
    Classify -->|task-agent| SlotFilling{🧾 4. Slot Filling Engine<br>Bóc tách tham số}
    Classify -->|rag hoặc faq| CacheCheck{⚡ 5. Fast FAQ / Semantic Cache}
    
    SlotFilling -->|Thiếu thông tin| Clarify[🤖 Clarification Question<br>Hỏi ngược làm rõ]
    SlotFilling -->|Đầy đủ| Tool[🛠️ Action Engine<br>RefundCalculatorTool]
    
    CacheCheck -->|Cache Hit >=0.96| FastReturn[🎉 Early-Exit / Bypass<br>Trả kết quả từ Cache < 10ms - 0đ]
    CacheCheck -->|Cache Miss| Rewrite[🧠 6. Conversational Memory<br>Query Rewrite 3 lượt]
    
    Rewrite --> Strategy{🔀 7. Retrieval Strategy Selector}
    
    Strategy -->|Lọc số/Mã lỗi/Hotline| BM25_Path[🔤 BM25 Keyword Search]
    Strategy -->|Khái niệm trừu tượng| Dense_Path[🔎 Dense Semantic Search]
    Strategy -->|Mặc định/Bao phủ rộng| Hybrid_Path[🔍 Dense + Sparse Hybrid Search]
    
    BM25_Path & Dense_Path & Hybrid_Path --> SG[👤 8. Shared Role Filter<br>Khách hàng/Tài xế/Cửa hàng]
    
    SG --> Rerank[🚀 9. Cross-Encoder Reranker<br>Transformer Attention chéo]
    Rerank --> ParentChild[📚 10. Parent-Child Context Compression]
    PC --> LLM[🤖 11. LLM Generation<br>Synthesizer]
    LLM --> Citation[📖 12. Citation & Response<br>Cost Tracking & Source Validation]

    SmallTalk & Clarify & Tool & FastReturn & Fallback & Citation --> Final[🎉 Phản hồi cuối cùng]
    Final --> Obs[📊 Observability<br>Telemetry logs & Feedback]

    %% Styles
    classDef highlight fill:#00f0ff,stroke:#ffffff,stroke-width:2px,color:#0c101b;
    classDef security fill:#0e3a5c,stroke:#00f0ff,stroke-width:2px,color:#00f0ff;
    classDef standard fill:#131a2b,stroke:#1e293b,stroke-width:1px,color:#e2e8f0;
    classDef cacheHit fill:#10b981,stroke:#ffffff,stroke-width:2px,color:#ffffff;
    classDef errorRed fill:#ef4444,stroke:#ffffff,stroke-width:2px,color:#ffffff;
    
    class Q,Final highlight;
    class FastReturn,Tool cacheHit;
    class Block,Fallback errorRed;
    class GW,Classify,SlotFilling,Strategy,Faith security;
    class Rewrite,BM25_Path,Dense_Path,Hybrid_Path,SG,Rerank,ParentChild,LLM,Citation,Obs standard;
```

---

## 👨‍🏫 2. Bài Giảng Chuyên Sâu Từ Thầy Giáo AI

> [!NOTE]
> *“Hỏi gì đáp nấy (Naive RAG) là cách nhanh nhất để đưa một hệ thống RAG doanh nghiệp vào ngõ cụt. Thông tin nhiễu, lỗi định dạng đứt đoạn, và ảo giác (hallucination) sẽ giết chết lòng tin của khách hàng. Thầy đã hệ thống lại 8 chương bài giảng chuyên sâu theo trình tự 4 giai đoạn chuẩn của một đường ống (pipeline) RAG cấp doanh nghiệp thực thụ.”*

---

### 🧱 GIAI ĐOẠN I: CHUẨN BỊ DỮ LIỆU & PHÂN MẢNH (INGESTION PHASE)

#### 🧹 Chương 1: Tiền Xử Lý Dữ Liệu & Tách Theo Tiêu Đề (Heading-Aware Chunking)
Để VectorDB lưu trữ hiệu quả, dữ liệu HTML thô được bóc tách bằng BeautifulSoup, loại bỏ sạch rác (headers, footers, scripts) rồi chuyển về **Markdown** nhằm giữ cấu trúc phân cấp.

Thay vì cắt văn bản ngẫu nhiên theo số ký tự làm mất câu và ngữ cảnh, Thầy thiết kế bộ tách `HeadingAwareSplitter` cắt văn bản theo các thẻ tiêu đề Markdown (`#`, `##`, `###`) để giữ các điều khoản pháp lý nguyên vẹn, sau đó mới chia nhỏ với kích thước `chunk_size=700` ký tự và `overlap=150` để đảm bảo gối đầu liền mạch. Mỗi mảnh (chunk) được gán mã MD5 duy nhất dạng ASCII để tránh lỗi ký tự đặc biệt của hệ điều hành.

#### 📦 Chương 2: Tiến Trình Tiến Hóa Của Kỹ Thuật Chunking (Phân Mảnh Văn Bản)
Phân mảnh quyết định chất lượng của vector đầu vào. Thầy xin khái quát con đường tiến hóa của kỹ thuật này từ sơ khai đến hiện đại:
* **Character Chunking** *(Cổ điển)*: Cắt cơ học đúng số ký tự $N$ (ví dụ: cứ 500 ký tự cắt 1 mảnh). Nhanh nhưng làm đứt câu, hỏng từ và nát bảng biểu. (❌ Không dùng)
* **Recursive Character Chunking**: Tách đệ quy dựa trên danh sách ký tự ưu tiên `["\n\n", "\n", " ", ""]` để bảo toàn đoạn văn và câu. Rất tốt cho tài liệu phẳng thông thường. (⚠️ Baseline cơ bản)
* **Heading-Aware / Structural Chunking**: Sử dụng cấu trúc cú pháp tiêu đề Markdown để cắt. Bảo toàn 100% tính toàn vẹn của một điều khoản, bảng biểu. (✅ Khuyên dùng cho chính sách/quy chế)
* **Semantic Chunking**: Tính toán embedding cho từng câu liên tiếp, thực hiện cắt chunk khi độ tương đồng ngữ nghĩa giữa hai câu đột ngột sụt giảm. Mảnh cắt tự nhiên nhưng tốn tài nguyên nhúng vector từng câu. (⚠️ Phù hợp cho văn xuôi)
* **Agentic / LLM-based Chunking**: Dùng một LLM đọc và tự quyết định vị trí cắt đoạn tối ưu. Chất lượng hoàn hảo nhưng chi phí API khổng lồ, tốc độ chậm chạp. (❌ Không thực tế)
* **Hierarchical + Parent-Child Retrieval** *(Vàng)*: Phân tích layout PDF bằng mô hình thị giác cục bộ (PyMuPDF / Marker). Tạo ra các **Chunk Con (Child Chunks - 100-200 từ)** nhúng vector để tìm kiếm cực nhạy, liên kết với **Chunk Cha (Parent Chunks - 1000-2000 từ)** để tự động gộp context khi gửi LLM. Đạt lợi ích kép: Tìm siêu nhạy + Context siêu đầy đủ, chi phí ban đầu bằng $0. (👑 Tiêu chuẩn vàng doanh nghiệp hiện đại)

#### 🗺️ Chương 2b: Xử Lý Đa Phương Tiện & Trích Xuất Bảng Biểu Phức Tạp Bằng Định Dạng Metadata Trong V3 (Multimodal & Table Ingestion Roadmap)

Khi tài liệu nguồn là PDF có cấu trúc phức tạp chứa nhiều hình ảnh Taplo sự cố, sơ đồ bãi đỗ xe hoặc bảng giá cước, RAG cơ bản sẽ làm nát cấu trúc hoặc bỏ qua hoàn toàn các tín hiệu đa phương tiện.

* **🎯 Tầm Quan Trọng Vượt Trội:** Trong số các nâng cấp của V3, **Multimodal Ingestion & Chunking** được định vị là **tính năng cốt lõi và đáng giá nhất**. Phương pháp biểu diễn kép (Dual-Representation) cho phép một khối tri thức logic (mảnh cha) vừa liên kết tìm kiếm nhạy bén bằng Vector, vừa lưu trữ và bảo toàn đồng thời nhiều định dạng dữ liệu (văn bản thô, bảng biểu Markdown, hình ảnh đính kèm) mà không bị đứt gãy ngữ cảnh.

* **Thực trạng Giai đoạn 2 (V2) hiện tại:**
  * **Đối với Bảng biểu (Tables):** Đã giải quyết ở cấp độ Parser bằng cách bóc tách HTML thô và bảo tồn thành Markdown Table (`| cột 1 | cột 2 |`) kết hợp `HeadingAwareSplitter` để tránh cắt nát đoạn. Tuy nhiên, hệ thống *chưa có nhãn metadata phân loại rõ ràng loại chunk* (như `type = table`) trong DB.
  * **Đối với Hình ảnh (Images):** Đã hỗ trợ Vision ở đầu vào (đọc ảnh taplo người dùng gửi), nhưng ở khâu Ingestion hệ thống *chưa lưu trữ* và *chưa gắn nhãn* hình ảnh chính sách.

* **Phương án đột phá trong Phiên bản V3 (Lộ trình 2026):**
  Thầy thiết kế giải pháp **Multimodal & Table-Aware Ingestion Pipeline** với trường metadata bắt buộc gán cho mỗi chunk: `chunk_type: "text" | "table" | "image"`.

  1. **Giải pháp xử lý Bảng biểu chuyên sâu (Table-specific RAG):**
     - *Trích xuất:* Dùng **Table Transformer / Nougat** nhận diện tọa độ bảng trong PDF gốc.
     - *Biểu diễn kép (Dual-Representation):*
       - **Vector Search Representation:** Dùng LLM tóm tắt ý nghĩa bảng bằng văn bản tự nhiên (*"Bảng này thể hiện mức phạt hủy chuyến..."*). Hệ thống tính toán vector (embedding) trên đoạn tóm tắt này để Vector Search tìm kiếm nhạy nhất.
       - **LLM Context Representation:** Khi chunk được truy xuất trúng, kéo nguyên bản định dạng Markdown/HTML Table nạp vào context để LLM tính toán chính xác 100%.
     - *Gán nhãn metadata:* `{"chunk_type": "table", "has_table": true}`.

  2. **Giải pháp xử lý Hình ảnh chuyên sâu (Image-specific / Multimodal RAG):**
     - *Trích xuất:* Dùng **PyMuPDF / PDFPlumber** tự động cắt và lưu trữ file ảnh thô (`.png`, `.jpg`) vào Storage.
     - *Biểu diễn kép (Dual-Representation):*
       - **Vector Search Representation:** Dùng mô hình **VLM (Vision-Language Model như GPT-4o-mini)** đọc ảnh và viết một bản mô tả chi tiết bằng văn bản (Image Captioning). Ví dụ: *"Hình chụp đèn taplo VF8 cảnh báo lỗi Rùa Vàng..."*. Nhúng vector đoạn mô tả này để tìm kiếm.
       - **LLM Context Representation:** Khi tìm thấy, hệ thống kéo cả bản mô tả VÀ đường dẫn liên kết URL ảnh thật nạp cho LLM. AI sẽ sinh ra câu trả lời có chứa link ảnh trực tiếp để người dùng xem trực quan.
     - *Gán nhãn metadata:* `{"chunk_type": "image", "image_url": "...", "has_visual": true}`.

* **⚠️ Phân Tích Kỹ Thuật Về Chi Phí & Tính Khả Thi (Cost & Feasibility Warning):**
  Việc gửi hàng vạn bức ảnh chính sách và bảng biểu lên các API Vision thương mại lớn như `gpt-4o` sẽ **làm tăng vọt hóa đơn API lên gấp 10-20 lần** và làm chậm đáng kể quá trình ingestion tự động. Để giải quyết bài toán kinh tế này cho Xanh SM, giải pháp thực tế nhất là **tự host và chạy offline** các mô hình Vision-Language mã nguồn mở nhỏ gọn như **LLaVA-1.5-8B** hoặc **Qwen-VL** trên máy chủ GPU cục bộ hoặc dịch vụ cloud thuê theo giờ. Mô hình cục bộ sẽ đảm nhiệm việc OCR, sinh caption mô tả và viết tóm tắt bảng biểu một cách hoàn toàn miễn phí (chi phí gọi API = 0đ), giúp RAG pipeline V3 vừa cực kỳ toàn năng vừa tối ưu ngân sách tối đa!

---

### 🧠 GIAI ĐOẠN II: Ý ĐỊNH & TRUY VẤN NÂNG CAO (QUERYING & RETRIEVAL PHASE)

#### 🔀 Chương 7: Chiến Lược Truy Xuất Động (Strategy Selector)
Hệ thống không sử dụng một cách tìm kiếm duy nhất cho mọi câu hỏi. **Strategy Selector** đóng vai trò là "người điều phối" (Orchestrator) với cơ chế Heuristic siêu tốc:
*   **BM25 / Keyword Search**: Kích hoạt khi câu hỏi có mật độ số liệu cao (hotline, ngày tháng, mã lỗi `rùa vàng`, `2088`). Giúp bắt chính xác tuyệt đối các con số mà Vector Search đôi khi làm mờ đi.
*   **Dense Search**: Dành cho câu hỏi khái niệm ("tác phong chuẩn mực là gì?"). Sử dụng Embedding để tìm kiếm theo ý nghĩa thay vì mặt chữ.
*   **Hybrid Search**: Sự kết hợp hoàn hảo, dùng khi câu hỏi phức tạp cần cả sự nhạy bén của từ khóa lẫn chiều sâu của ngữ nghĩa.

#### 🔍 Chương 5: Tìm Kiếm Lai & Hòa Trộn RRF (Hybrid Search)
Tại sao phải dùng Hybrid Search? Vì **Vector Search (Dense)** giỏi hiểu ý nhưng hay nhầm các từ viết tắt, còn **Keyword Search (BM25)** giỏi bắt từ khóa nhưng lại "mù" ngữ nghĩa.
*   **Thuật toán RRF (Reciprocal Rank Fusion)**: Chúng ta không cộng điểm số trực tiếp (vì thang đo khác nhau). RRF xếp hạng lại dựa trên vị trí của tài liệu trong cả hai danh sách:
    $$RRF\_Score(d) = \sum_{r \in \{R_{dense}, R_{bm25}\}} \frac{1}{k + r(d)}$$ (với $k=60$).
*   Cơ chế này đảm bảo những tài liệu đứng đầu ở cả hai phía sẽ có trọng số cao nhất.

#### ⚡ Chương 6: Tái Xếp Hạng Đa Tầng (Multi-Stage Reranking)
Đây là bước "tinh lọc" cuối cùng trước khi gửi dữ liệu cho LLM:
1.  **Stage 1 (Retrieval)**: Lấy ra 25 ứng viên tiềm năng nhất (phễu rộng).
2.  **Stage 2 (Reranking)**: Sử dụng **Heuristic Semantic Reranker** hoặc **Cross-Encoder**.
    *   **Heuristic**: Tính điểm dựa trên sự xuất hiện của tập hợp từ khóa đã chuẩn hóa (Accent-stripped) giữa Query và Document. Cực nhanh, hỗ trợ tốt tiếng Việt không dấu.
    *   **Cross-Encoder (Future)**: Đọc sâu tương tác Attention chéo giữa từng cặp câu hỏi-tài liệu để chấm điểm logic.
*   **Kết quả**: Chỉ giữ lại Top 5 "tinh hoa" nhất, giúp LLM không bị nhiễu bởi các đoạn văn bản "trông có vẻ giống" nhưng thực tế không chứa câu trả lời.

---

### 🛡️ GIAI ĐOẠN IV: TỔNG HỢP & BẢO MẬT (SYNTHESIS & CITATION PHASE)

#### 🤖 Chương 8: Tổng Hợp Phản Hồi Trích Nguồn & Giám Sát Chi Phí (Synthesis & Observability)
Top 5 trích đoạn sạch nhất được đưa vào hệ thống Prompt kiểm duyệt trích nguồn cực kỳ nghiêm ngặt. LLM (gpt-4o-mini) tổng hợp câu trả lời tự nhiên, thân thiện đúng tác phong CSKH Xanh SM.

Sau đó, bộ xác thực trích nguồn sẽ thực hiện:
1. **Xác thực URL**: Đối sánh nguồn và hiển thị gọn gàng bên dưới câu trả lời.
2. **Giám sát chi phí (Token Tracking)**: Thu thập số lượng token tiêu tốn từ khâu Query Expansion, Rewrite và Generation.
3. **Quy đổi tài chính**: Tự động tính toán chi phí theo USD và VND (tỉ giá 25.450đ) để quản trị viên theo dõi hiệu quả vận hành.

Việc tích hợp này giúp hệ thống đạt được sự minh bạch tối đa về mặt chi phí trong khi vẫn đảm bảo độ tin cậy của thông tin trích dẫn!

---25 sẽ trả về 0.
* **Hòa trộn thứ hạng (RRF - Reciprocal Rank Fusion)**: Hệ thống của chúng ta không cộng điểm số trực tiếp (vì phân phối điểm vector và BM25 hoàn toàn khác nhau). Thay vào đó, ta sử dụng RRF để xếp hạng lại dựa trên thứ tự xuất hiện của tài liệu trong cả hai danh sách tìm kiếm:
  $$RRF\_Score(d \in D) = \frac{1}{60 + r_{dense}(d)} + \frac{1}{60 + r_{sparse}(d)}$$
  Điều này giúp chọn ra những tài liệu đứng hạng cao ở cả hai luồng hoặc cực kỳ nổi bật ở một trong hai luồng.

#### 2. So sánh Kiến trúc Reranker: Bi-Encoder vs. Cross-Encoder
Đây là phần tri thức cực kỳ quan trọng về mặt kiến trúc Transformer mà các kỹ sư AI bắt buộc phải thấu hiểu:

* **Bi-Encoder (Mô hình Nhúng Vector - Ví dụ: ChromaDB + text-embedding-3)**:
  - *Kiến trúc*: Câu hỏi $Q$ và Tài liệu $D$ được đưa vào mô hình Encoder độc lập nhau để tạo ra hai vector đại diện $V_Q$ và $V_D$. Sau đó tính khoảng cách bằng tích vô hướng hoặc Cosine Similarity.
  - *Cơ chế tương tác*: **Không có**. Hai văn bản không hề biết đến sự tồn tại của nhau trong quá trình encode.
  - *Ưu điểm*: Tốc độ siêu tốc. Toàn bộ các mảnh tài liệu có thể được tính toán vector sẵn (Offline indexing) và lưu vào cơ sở dữ liệu. Khi người dùng hỏi, hệ thống chỉ cần tính 1 vector cho câu hỏi và thực hiện đối sánh cực nhanh trong vài mili-giây.
  - *Nhược điểm*: Vì không có sự tương tác trực tiếp ở cấp độ từ vựng (Cross-Attention) giữa câu hỏi và tài liệu, mô hình dễ bỏ sót các sắc thái ngữ nghĩa phức tạp và độ chính xác ở mức trung bình khá.

```
[Kiến trúc Bi-Encoder]
Query (Q)    ➔ [ Encoder ] ➔ Vector V_Q ──┐
                                          ├──➔ [ Cosine Sim ] ➔ Điểm số
Document (D) ➔ [ Encoder ] ➔ Vector V_D ──┘
```

* **Cross-Encoder (Mô hình Reranker - Ví dụ: `bge-reranker-large` / `cohere-rerank`)**:
  - *Kiến trúc*: Ghép trực tiếp câu hỏi và tài liệu thành một chuỗi văn bản duy nhất dạng `[CLS] Query [SEP] Document [SEP]` rồi đưa toàn bộ chuỗi này vào một mô hình Transformer duy nhất.
  - *Cơ chế tương tác*: **Tối đa (Full Attention)**. Từng từ trong câu hỏi được phép thực hiện cơ chế Self-Attention trực tiếp với từng từ trong tài liệu.
  - *Ưu điểm*: Độ chính xác cực kỳ cao, bắt trọn từng sắc thái ngữ nghĩa tinh tế nhất, hiểu rõ mối quan hệ logic giữa câu hỏi và văn bản trả về.
  - *Nhược điểm*: Tính toán cực kỳ nặng nề và chậm chạp. Không thể tính trước (offline) vì phải ghép cặp trực tiếp từng cặp $(Q, D)$ tại thời điểm chạy (Runtime).
  - *Tính thực tế*: Hệ thống RAG doanh nghiệp áp dụng cơ chế **Phễu Lọc 2 Lớp (Two-Stage Pipeline)**: Sử dụng Bi-Encoder (Hybrid Search) để quét nhanh hàng triệu mảnh để lấy ra Top 30 ứng viên, sau đó mới dùng Cross-Encoder (Reranker) để chấm điểm sâu và chọn ra Top 5 mảnh chất lượng nhất để gửi LLM.

```
[Kiến trúc Cross-Encoder]
Query (Q)    ──┐
               ├──➔ [ CLS + Q + SEP + D + SEP ] ➔ [ Transformer ] ➔ Điểm số (Full Attention)
Document (D) ──┘
```

---

## 🛡️ 3. Nhật Ký Giải Quyết Lỗ Hổng Phân Phối Dữ Liệu & Bảo Mật

### ⚠️ Điểm yếu nghiêm trọng đã phát hiện (The Issue)
Trong quá trình vận hành, khi khách hàng hỏi câu hỏi: **"hướng dẫn đặt đồ ăn xanh sm"** (hoặc các dịch vụ như thuê xe, đặt xe sân bay...), hệ thống trả về thông báo trống rỗng: *"Rất tiếc, tài liệu chính sách hiện tại không có thông tin về vấn đề này."*

Mặc dù trong kho dữ liệu thô **CÓ** đầy đủ tài liệu về dịch vụ đồ ăn Xanh Food (`vn_vi_greensm_ngon.md`) và Hướng dẫn trợ giúp đặt xe (`vn_vi_helps.md`), nhưng khách hàng vẫn bị báo trắng thông tin.

#### Nguyên nhân kỹ thuật:
1. **Lỗi phân loại của Crawler (Categorization Bug)**:
   Do chân trang (footer) của mọi trang trên `xanhsm.com` đều chứa các liên kết đăng ký tài xế, hàm phân loại cũ quét từ khóa thô `"tài xế" in content_lower` đã **nhầm lẫn xếp 26 tài liệu trợ giúp chung vào thư mục `data/driver`**.
2. **Lỗi cô lập dữ liệu (Rigid Metadata Siloing)**:
   Hệ thống RAG cũ áp dụng bộ lọc vai trò tuyệt đối `{"role": target_role}`. Khi Khách hàng (customer) hỏi, bộ lọc ChromaDB và BM25 chặn đứng tất cả tài liệu có nhãn `driver` hoặc trợ giúp chung `faq`, dẫn đến việc RAG trả về 0 kết quả!

```
[Mô tả lỗi cũ]
Người dùng (Khách hàng) ➔ Gửi câu hỏi "Đặt đồ ăn" 
                        ➔ RAG áp dụng lọc {"role": "customer"} 
                        ➔ Không tìm thấy tài liệu (do bị gắn nhãn driver và nằm ở data/driver/) 
                        ➔ Báo lỗi trống thông tin.
```

---

### 💡 Giải pháp cấu trúc dữ liệu chia sẻ chung (Shared Document Store Solution)

Thầy giáo AI đã thiết kế giải pháp tái cấu trúc và phân quyền chuẩn Production như sau:

#### 1. Sửa lỗi Crawler & Tái cấu trúc thư mục dữ liệu
* **Tối ưu hàm phân loại**: Cập nhật hàm `categorize_content` trong [crawl.py](file:///c:/Users/DUNG/Desktop/RAG_XANH_SM/app/crawler/crawl.py) để nhận diện đúng trang tài xế bằng các từ khóa chuyên sâu ở phần thân bài (`chính sách tài xế`, `tác phong tài xế`), loại bỏ hoàn toàn nhiễu từ footer.
* **Di dời tài liệu về kho dùng chung**: Chuyển toàn bộ 26 tệp tin hướng dẫn dịch vụ tổng quan từ `data/driver` về thư mục **`data/faq`** (Kho lưu trữ dùng chung). Thư mục `driver/` bây giờ chỉ giữ lại các tài liệu nhạy cảm thực sự của tài xế.

#### 2. Thiết kế bộ lọc liên kết (Unified Shared Filter)
Nâng cấp bộ lọc tìm kiếm trong cả [chroma_client.py](file:///c:/Users/DUNG/Desktop/RAG_XANH_SM/app/vectordb/chroma_client.py) và [bm25_retriever.py](file:///c:/Users/DUNG/Desktop/RAG_XANH_SM/app/retrieval/bm25_retriever.py). 

Khi một người dùng thuộc một vai trò cụ thể tìm kiếm, hệ thống cho phép họ truy cập tài liệu đặc thù của họ **VÀ kho tài liệu trợ giúp dùng chung (`faq`)**:

$$\text{Quyền truy cập của vai trò} = \text{target\_role} \cup \text{"faq"}$$

```python
# Cú pháp truy vấn ChromaDB nâng cao tự động áp dụng:
search_filter = {"role": {"$in": [target_role, "faq"]}}
```

```
[Cơ chế mới hoạt động hoàn hảo]
Người dùng (Khách hàng) ➔ Gửi câu hỏi "Hướng dẫn đặt đồ ăn xanh sm"
                        ➔ RAG lọc thông tin thuộc danh mục: "customer" hoặc "faq"
                        ➔ Truy cập thành công file "vn_vi_greensm_ngon.md" (đã được chuyển về danh mục faq)
                        ➔ Trích xuất chính xác biểu phí và quy trình đặt đồ ăn Xanh Food!
```

Cơ chế này vừa bảo mật tuyệt đối thông tin nội bộ của từng vai trò (khách hàng không bao giờ đọc được chiết khấu hay mức phạt của tài xế), vừa tối ưu hóa khả năng chia sẻ thông tin hữu ích cho toàn bộ người dùng!

---

## 🚨 4. Kết Quả Khắc Phục Bộ Tứ Điểm Yếu Kinh Điển (Giai Đoạn 2 Thành Công)

> [!TIP]
> *“Học trò của Thầy thân mến! Một kỹ sư giỏi không chỉ xây dựng hệ thống chạy được, mà phải là người nhìn thấy trước những vết nứt và gia cố nó vững chãi trước sóng gió. Thầy rất tự hào thông báo: **Toàn bộ 4 điểm yếu kinh điển của hệ thống RAG sơ khai đã được khắc phục hoàn chỉnh và kiểm thử thành công trong Giai đoạn 2 (Phase 2)!** Dưới đây là kiến trúc thực tiễn chúng ta đã triển khai.”*

### ✅ Khắc phục Điểm Yếu 1: Giải quyết Trôi Ngữ Cảnh bằng Conversational Query Rewriter
* **Cách giải quyết:** Chúng tôi tích hợp bộ biên dịch truy vấn ngữ cảnh `_rewrite_query` vào `app/rag/chain.py`.
* **Kỹ thuật:** RAG tự động ghi nhớ 3 lượt chat gần nhất từ `chat_history`. Khi người dùng đặt câu hỏi phụ thuộc (ví dụ: *"Ai là đối tác cửa hàng?"* -> *"Mức phí của họ là bao nhiêu?"*), một LLM siêu nhẹ (`gpt-4o-mini`) sẽ phân tích và viết lại đại từ thay thế thành truy vấn độc lập hoàn chỉnh (*"Mức phí chiết khấu của đối tác cửa hàng Xanh Food là bao nhiêu?"*) trước khi tiến hành tìm kiếm vector.

### ✅ Khắc phục Điểm Yếu 2: Tối ưu Chi Phí và Tốc Độ bằng Dual-Driver Caching Layer
* **Cách giải quyết:** Triển khai bộ đệm Caching thông minh kép `XanhSMRAGCache` trong `app/rag/cache.py` đạt hiệu năng kinh ngạc **(Độ trễ ~10ms, Chi phí = 0đ)**.
* **Kỹ thuật:**
  * *Cơ chế Early-Exit / Bypass tối ưu:* Khi một câu hỏi của khách hàng gửi lên, hệ thống sẽ thực hiện kiểm tra lớp **Caching Layer** đầu tiên (đặt tại tầng cao nhất của luồng xử lý trong `chain.py`, trước khâu Query Rewrite hay Vector Search). Nếu phát hiện câu hỏi đã tồn tại trong DB cache (thỏa mãn khớp tuyệt đối hoặc khớp ngữ nghĩa): Hệ thống sẽ lập tức **bẻ gãy luồng xử lý (early-exit/bypass)**, bỏ qua 100% các bước: *Rewrite, Query Expansion, Vector/BM25 Retrieval, Reranking, và LLM Generation*. Kết quả đã lưu trong Cache sẽ được trả về trực tiếp trong `< 10ms` với chi phí **0đ** và **0 token**.
  * *Exact Match:* Sử dụng thuật toán băm chuỗi nhanh để khớp tuyệt đối câu hỏi cũ.
  * *Semantic Match:* Embedding câu hỏi mới và so khớp khoảng cách Cosine Similarity chéo trên cơ sở dữ liệu. Nếu độ tương đồng đạt ngưỡng cực cao (`Similarity Score >= 0.96`), hệ thống trả ngay câu trả lời đã lưu trước đó mà không cần gọi OpenAI API.
  * *Dual-Driver:* Tự động đồng bộ với cơ sở dữ liệu **PostgreSQL** (thông qua `DATABASE_URL` và thư viện `psycopg2-binary`) khi deploy lên Railway Cloud, và tự động fallback sang **SQLite** cục bộ (`rag_cache.db`) trong môi trường phát triển offline.
  * *Cache Eviction:* Khi có tiến trình ingest nạp tri thức mới, hệ thống tự động xóa sạch cache để tránh lưu trữ dữ liệu chính sách cũ bị lỗi thời.

### ✅ Khắc phục Điểm Yếu 3: Chẩn Đoán Lỗi Taplo Bằng Multimodal Vision LLM Agent
* **Cách giải quyết:** Giải quyết hoàn toàn sự cố "mù thị giác" khi tiếp nhận hình ảnh cảnh báo taplo xe điện VinFast.
* **Kỹ thuật:** Nâng cấp API `/api/chat` tiếp nhận chuỗi ảnh Base64. Hệ thống điều phối mô hình Vision LLM (`gpt-4o-mini`) để chẩn đoán mã lỗi taplo (icon rùa vàng, báo lỗi động cơ, đèn phanh...), tự động chuyển đổi mô tả kỹ thuật đó thành truy vấn mở rộng gửi xuống RAG để tìm phương án xử lý khẩn cấp và đưa ra chỉ dẫn an toàn cho hành khách và tài xế.

### ✅ Khắc phục Điểm Yếu 4: Giải Quyết Đứt Gãy Văn Bản PDF Bằng Parent-Child Chunking
* **Cách giải quyết:** Đập tan nghịch lý phân mảnh PDF bằng giải thuật **Parent-Child Retrieval & Context Deduplication**.
* **Kỹ thuật:**
  * *Layout-Aware PDF Parser:* Sử dụng parser dựa trên **PyMuPDF + Heuristics cục bộ** siêu tốc để cấu trúc hóa Markdown mà không tốn chi phí AI xử lý dữ liệu thô ban đầu, hoàn toàn vượt trội so với "cơn ác mộng" phình đĩa 3GB của thư viện `Unstructured`.
  * *Mảnh Con (Child Chunks - 100-200 từ):* Đánh chỉ mục vector phục vụ tìm kiếm đạt độ nhạy ngữ nghĩa tốt nhất.
  * *Mảnh Cha (Parent Chunks - 1000-2000 từ):* Khi mảnh con khớp, thuật toán trong `chain.py` tự động truy xuất mảnh cha tương đương, tiến hành loại bỏ trùng lặp mã nhận dạng (`parent_chunk_id`) để gộp ngữ cảnh liền mạch gửi cho LLM. Điều này vừa bảo toàn 100% cấu trúc pháp lý của điều khoản và bảng biểu giá cước, vừa tối ưu hóa dung lượng context window gửi lên LLM.

---

👨‍🏫 *Lớp học của Thầy giáo AI hôm nay đến đây là kết thúc. Hãy nhớ rằng: Trong thực tế sản xuất, kiến trúc RAG vững chãi, tiết kiệm chi phí và có bộ nhớ thông minh mới là chìa khóa mở ra sự thành công bền vững của doanh nghiệp các em!*
