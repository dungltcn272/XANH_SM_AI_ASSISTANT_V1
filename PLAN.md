# Kế hoạch thêm User Review cho RAG Production

Mục tiêu là biến phản hồi của người dùng thành nguồn dữ liệu đánh giá liên tục cho production: biết câu nào trả lời tốt, câu nào sai, thiếu nguồn, latency khó chịu, hoặc retrieval/debug cần xem lại.

## 1. Mục tiêu sản phẩm

User Review cần trả lời được các câu hỏi vận hành:

- Người dùng có hài lòng với câu trả lời không?
- Câu trả lời sai vì thiếu tài liệu, retrieval sai, NLU rewrite sai, hay generation sai?
- Case nào nên đưa vào golden dataset/eval set?
- Phiên bản pipeline mới có cải thiện theo feedback thực tế không?
- Admin có đủ dữ liệu để debug lại một câu trả lời cụ thể không?

## 2. Backend

### 2.1. Bảng dữ liệu

Tạo bảng `user_reviews`:

- `id`: UUID/string primary key.
- `conversation_id`: id hội thoại nếu có.
- `message_id`: id message/câu trả lời được review.
- `user_id`: nullable, để hỗ trợ cả user chưa đăng nhập nếu cần.
- `query`: câu hỏi gốc.
- `answer`: câu trả lời đã hiển thị.
- `rating`: `up`, `down`, hoặc numeric `1-5`.
- `reason_tags`: JSON array, ví dụ `wrong_answer`, `missing_source`, `outdated`, `too_slow`, `unclear`, `unsafe`, `good_answer`.
- `comment`: text tự do của người dùng.
- `sources`: JSON citations đã trả về.
- `pipeline_metrics`: JSON gồm `nlu_fast_path`, `nlu_latency_ms`, `search_latency_ms`, `rerank_latency_ms`, `generation_latency_ms`, token/cost nếu có.
- `pipeline_trace`: JSON rút gọn gồm intent, rewritten_query, expanded_queries, top docs ids/sources.
- `status`: `new`, `triaged`, `added_to_eval`, `fixed`, `ignored`.
- `admin_note`: ghi chú nội bộ.
- `created_at`, `updated_at`.

Index cần có:

- `created_at`
- `rating`
- `status`
- `conversation_id`
- `message_id`

### 2.2. API public/user

Thêm endpoint:

- `POST /api/reviews`
  - Nhận `message_id`, `conversation_id`, `rating`, `reason_tags`, `comment`.
  - Backend tự lấy thêm query/answer/sources/metrics nếu message đã có trong DB.
  - Nếu FE gửi kèm snapshot thì validate và lưu fallback.

- `GET /api/reviews/mine`
  - Optional, dùng cho lịch sử feedback của user nếu cần.

### 2.3. API admin

Thêm endpoint:

- `GET /api/admin/reviews`
  - Filter theo `rating`, `status`, `reason_tag`, ngày, intent, fast-path, latency range.
  - Pagination.

- `GET /api/admin/reviews/{id}`
  - Xem chi tiết query, answer, sources, metrics, trace.

- `PATCH /api/admin/reviews/{id}`
  - Cập nhật `status`, `admin_note`.

- `POST /api/admin/reviews/{id}/promote-to-eval`
  - Chuyển feedback xấu hoặc case hay thành item trong golden dataset draft.
  - Không tự ghi thẳng vào golden dataset chính nếu chưa review.

### 2.4. Liên kết với pipeline/debug

Khi trả lời chat, response cần có `message_id` ổn định để FE gửi review đúng câu.

Mỗi answer nên lưu hoặc có thể truy hồi:

- `query`
- `rewritten_query`
- `expanded_queries`
- `intent`
- `nlu_fast_path`
- `sources`
- `latency breakdown`
- `top_docs` rút gọn

Điểm quan trọng: User Review không chỉ là like/dislike, mà là “bookmark debug” cho một lần pipeline chạy thật.

## 3. Frontend người dùng

### 3.1. Vị trí review

Ở cuối mỗi câu trả lời assistant:

- Nút thumbs up.
- Nút thumbs down.
- Nút mở form feedback chi tiết.

Sau khi bấm:

- Hiện trạng thái đã gửi.
- Cho phép sửa feedback trong vài phút hoặc trong session hiện tại.

### 3.2. Form feedback

Nếu thumbs down, mở nhanh các lý do:

- Sai thông tin.
- Thiếu nguồn.
- Nguồn không liên quan.
- Câu trả lời khó hiểu.
- Trả lời quá chậm.
- Câu hỏi của tôi bị hiểu sai.
- Nội dung không an toàn/không phù hợp.
- Khác.

Nếu thumbs up, có thể hỏi nhẹ:

- Hữu ích.
- Đúng trọng tâm.
- Có nguồn rõ.
- Dễ hiểu.

Comment tự do là optional, không bắt buộc để giảm friction.

## 4. Frontend admin

Thêm tab hoặc section `User Reviews`.

### 4.1. Dashboard tổng quan

Các chỉ số:

- Tổng review theo ngày.
- Tỷ lệ thumbs up/down.
- Top reason tags.
- Avg latency của các review xấu.
- Tỷ lệ review xấu theo `nlu_fast_path=true/false`.
- Top categories/intents có nhiều review xấu.

### 4.2. Bảng review

Columns:

- Time.
- Rating.
- Query.
- Answer preview.
- Reason tags.
- Intent.
- NLU fast-path.
- Latency.
- Sources count.
- Status.
- Action.

Filters:

- Rating.
- Status.
- Reason tag.
- Intent.
- NLU fast-path.
- Latency range.
- Date range.

### 4.3. Review detail dialog

Hiển thị:

- Query gốc.
- Rewritten query.
- Expanded queries.
- Answer đầy đủ.
- Sources/citations.
- Metrics breakdown.
- Top docs.
- User comment.
- Admin note.

Actions:

- Mark triaged.
- Mark fixed.
- Add to eval draft.
- Copy debug payload.

## 5. Eval loop

Quy trình cải thiện:

1. User gửi feedback xấu.
2. Admin triage và xác định lỗi: NLU, retrieval, rerank, context, prompt, data missing.
3. Nếu case có giá trị, promote vào eval draft.
4. Chuẩn hóa expected answer/keywords/sources.
5. Chạy eval trước/sau fix.
6. Đánh dấu review là `fixed` nếu case đã qua kiểm thử.

Không nên đưa tất cả feedback vào golden dataset. Chỉ đưa các case đại diện, khó, hoặc từng gây lỗi thật.

## 6. Privacy và an toàn dữ liệu

- Không lưu secret/token trong review.
- Nếu query có PII nhạy cảm, cân nhắc masking trước khi hiển thị admin rộng.
- Admin export phải loại bỏ thông tin cá nhân nếu dùng cho báo cáo.
- Review comment có thể chứa nội dung độc hại, nên hiển thị dạng text escaped.

## 7. Thứ tự triển khai đề xuất

### Phase 1: Review cơ bản

- Tạo model/table `user_reviews`.
- API `POST /api/reviews`.
- FE thumbs up/down + reason tags.
- Admin list đơn giản.

### Phase 2: Debug tốt hơn

- Lưu pipeline metrics/trace.
- Review detail dialog.
- Filter theo latency, intent, NLU fast-path.
- Action status/admin note.

### Phase 3: Eval integration

- Promote review to eval draft.
- So sánh review xấu trước/sau fix.
- Thêm dashboard trend theo ngày/tuần.

## 8. Tiêu chí thành công

- Mỗi câu trả lời có thể được review trong 1 click.
- Admin xem được review xấu kèm đủ trace để debug.
- Feedback tốt/xấu đo được theo thời gian.
- Có đường đưa case thực tế vào eval set.
- Sau mỗi release, có thể biết production đang tốt lên hay xấu đi dựa trên review thật.

---

# Kế Hoạch Refactor Toàn Bộ RAG Pipeline Sang Async/Await

Việc chuyển đổi toàn bộ kiến trúc từ Đồng bộ (Synchronous) sang Bất đồng bộ (Asynchronous) là một giải pháp tối ưu cho High Concurrency (hàng vạn CCU). Tuy nhiên, đây là một thay đổi lớn, toàn diện mã nguồn Backend do tính chất lan truyền của Async/Await trong Python.

## 1. Đánh giá độ khó & Rủi ro
- **Độ khó**: 🔴 Khó và Mất nhiều thời gian (Massive Refactoring).
- **Rủi ro**: Khi thay đổi một hàm bên dưới thành `async` (như truy cập DB, gọi API LLM), tất cả các hàm gọi nó (Retriever, Pipeline, API Endpoint) đều bắt buộc phải chuyển sang `async/await`. Do đó, streaming thông qua Langchain và FastAPI cũng cần thay đổi đồng bộ để tránh lỗi block Event Loop.

## 2. Các Hạng Mục Cần Triển Khai

### 2.1. Vector Database Layer (`app/vectordb/qdrant_client.py`)
- Thay thế `QdrantClient` đồng bộ bằng `AsyncQdrantClient`.
- Đổi hàm `hybrid_search` thành `async def hybrid_search`.
- Tích hợp `AsyncOpenAI` để sinh Dense Vector không chặn luồng (Non-blocking I/O).

### 2.2. Retrieval Layer (`app/retrieval/hybrid_search.py` & `retriever.py`)
- Lớp `XanhSMHybridSearch` đổi logic gọi DB thành `await self.db.hybrid_search(...)`.
- Các Pipeline tích hợp Langchain phải chuyển từ dùng class `Retriever` đồng bộ sang `AsyncRetriever` (hoặc kế thừa `BaseRetriever` bất đồng bộ).

### 2.3. NLU & Classifier Layer (`app/rag/classifier.py`)
- Đổi hàm `unified_nlu` (đang gọi LLM phân tích Intent) sang sử dụng `AsyncOpenAI` và dùng `await client.chat.completions.create(...)`.
- Hàm này sẽ trở thành `async def unified_nlu`.

### 2.4. RAG Pipeline Core (`app/rag/chain.py` & `pipeline.py`)
- Toàn bộ Langchain `chain.stream()` phải được đổi sang `async for chunk in chain.astream()`.
- Hàm `stream_chat_pipeline` trong `pipeline.py` phải biến thành một `AsyncGenerator` (`async def stream_chat_pipeline`).

### 2.5. API Layer (`app/api/chat.py`)
- Xóa bỏ cơ chế bọc luồng hiện tại (`_run_stream_in_thread`).
- Truyền trực tiếp `stream_chat_pipeline` vào `StreamingResponse` của FastAPI, để FastAPI tự động quản lý luồng bằng Asyncio.

### 2.6. Database Logging & Sync IO
- Chuyển các thao tác ghi Log hoặc lịch sử chat vào SQLite/PostgreSQL sang bất đồng bộ, hoặc bọc các hàm đồng bộ bằng `asyncio.to_thread` để tránh block luồng chính.

## 3. Kế hoạch Kiểm Thử (Verification Plan)
1. Tiến hành refactor theo thứ tự từ dưới lên (Database client -> Retriever -> NLU Classifier -> Chain -> API Controller).
2. Kiểm thử độc lập API Endpoint `/chat` với Postman/cURL để xác nhận SSE Streaming hoạt động mượt mà.
3. Chạy Load Test (mô phỏng CCU cao) để so sánh tài nguyên CPU/Memory sử dụng so với phiên bản dùng Global ThreadPool hiện tại.

---

# Kế Hoạch Tích Hợp Đa Tầng Memory & Context Builder

Việc tối ưu hóa "trí nhớ" cho AI Assistant (Context Window) là yếu tố quyết định để tạo ra trải nghiệm cá nhân hóa, đặc biệt trong các kịch bản Food Recommendation (nhớ sở thích, vị trí) và hỏi đáp nối tiếp (hiểu các đại từ "nó", "ở đó"). Thay vì gửi toàn bộ lịch sử thô vào Prompt gây tốn token và tăng độ trễ (latency), hệ thống sẽ sử dụng **Context Engineering + Memory Retrieval**.

## 1. Kiến Trúc 4 Tầng Bộ Nhớ (Memory Tiers)

Cốt lõi của hệ thống là chia nhỏ "trí nhớ" thành các tầng có vòng đời và mục đích khác nhau:

### 1.1. Working Memory (Bộ nhớ ngắn hạn)
- **Mục đích:** Giữ mạch hội thoại hiện tại, hiểu các câu hỏi nối tiếp và giải quyết hiện tượng đồng tham chiếu (Co-reference resolution). 
- **Ví dụ:** User hỏi "Thông tin VF3", sau đó hỏi "nó bao tiền?". Working memory giúp NLU Gateway hiểu "nó" chính là "VF3" ngay trước khi gọi RAG.
- **Lưu trữ:** Chỉ giữ 5–10 tin nhắn gần nhất trong bộ nhớ tạm (Redis hoặc DB session).

### 1.2. Conversation Summary (Tóm tắt phiên)
- **Mục đích:** Nén một đoạn chat dài thành các insight có cấu trúc khi phiên chat vượt quá giới hạn Working Memory.
- **Định dạng lưu trữ (JSON):** Chứa `current_goal`, `decisions`, và `open_questions`.

### 1.3. Long-term User Memory (Bộ nhớ dài hạn)
- **Mục đích:** Lưu trữ vĩnh viễn các thông tin (facts) cốt lõi về User để cá nhân hóa gợi ý (ví dụ: Vị trí làm việc, món ăn bị dị ứng, thói quen ăn uống). Tránh việc AI phải hỏi lại nhiều lần.
- **Trích xuất:** Dùng một Agent (Memory Extractor) chạy ngầm để trích xuất các "facts" từ hội thoại và cập nhật vào User Memory DB.

### 1.4. Episodic Memory (Bộ nhớ sự kiện)
- **Mục đích:** Ghi nhớ các sự kiện quan trọng theo mốc thời gian để tránh gợi ý lặp lại gây nhàm chán (Ví dụ: Hôm qua đã gợi ý bún chả, hôm nay sẽ đề xuất phở).

## 2. Context Builder & Prompt Caching

Khi User đặt câu hỏi mới, **Context Builder** sẽ đóng vai trò như một nhạc trưởng:
1. **Lấy Working Memory** hiện tại.
2. **Query Retrieval Memory** để lấy đúng mảng kiến thức RAG và các phần tử liên quan trong Long-term User Memory.
3. **Lắp ráp** thành một Prompt động, tinh gọn.

```text
SYSTEM: Bạn là AI Assistant của Xanh SM...
STATIC RULES: ...
USER PROFILE: {retrieved_user_memory}
SESSION SUMMARY: {conversation_summary}
RELEVANT KNOWLEDGE: {rag_chunks}
RECENT MESSAGES: {last_5_messages}
USER QUESTION: {current_question}
```

### Tối ưu Prompt Caching (OpenAI API)
- Đặt phần `SYSTEM` và `STATIC RULES` lên đầu prompt để LLM tự động áp dụng Cache Hit, giúp giảm mạnh độ trễ và chi phí input token. Phần Dynamic (như User Memory và Working Memory) đặt ở cuối.

## 3. Lộ Trình Triển Khai (Roadmap)

1. **Phase 1: Working Memory & Context Builder Core**
   - Áp dụng kỹ thuật nén 5-10 lượt chat gần nhất.
   - Thử nghiệm độ chính xác của NLU trong việc phân giải đại từ ("nó bao tiền").
2. **Phase 2: Long-term User Memory (Dành riêng cho Food Recommendation)**
   - Xây dựng bảng DB lưu trữ Facts người dùng (Vị trí, sở thích).
   - Prompt Engineering cho Memory Extractor (chạy async sau mỗi lượt chat).
3. **Phase 3: Prompt Caching & Episodic Retrieval**
   - Sắp xếp lại cấu trúc Prompt để tận dụng OpenAI Prompt Caching.
   - Xây dựng multi-index memory để retrieval cả RAG document lẫn Episodic Memory.
