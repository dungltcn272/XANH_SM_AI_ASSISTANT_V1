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
