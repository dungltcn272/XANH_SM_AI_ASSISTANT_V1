# Quy trình Đánh giá Chất lượng RAG & Tập dữ liệu Thử nghiệm (EVALUATION.md)

Tài liệu này hướng dẫn cách hệ thống thực hiện kiểm thử tự động chất lượng RAG bằng phương pháp LLM-as-a-Judge kết hợp các chỉ số heuristic truyền thống.

---

## 1. Kiến trúc Đánh giá Chất lượng (RAGAS Eval)

Công cụ đánh giá nằm tại [ragas_eval.py](file:///c:/Users/DUNG/Desktop/RAG_XANH_SM/evaluation/ragas_eval.py) sẽ chạy định kỳ hoặc theo nhu cầu để đo lường các chỉ số cốt lõi của hệ thống RAG:

### 1.1. Các chỉ số Tra cứu (Retrieval Metrics)
* **Recall@5 và Recall@10**: Tỷ lệ các từ khóa mong đợi (expected keywords) xuất hiện trong Top 5 và Top 10 tài liệu được tra cứu.
* **MRR (Mean Reciprocal Rank)**: Điểm số vị trí của tài liệu liên quan đầu tiên được tìm thấy.
* **NDCG@5 (Normalized Discounted Cumulative Gain)**: Đánh giá độ liên quan của kết quả tìm kiếm có tính đến thứ tự sắp xếp của Cohere Reranker.
* **Average Chunks Before Expansion**: Số lượng chunk thô được chọn từ Cohere Reranker trước khi thực hiện ghép nhóm và mở rộng ngữ cảnh.
* **Average Context Length**: Độ dài trung bình (số lượng ký tự) của ngữ cảnh gộp cuối cùng được đưa vào Prompt.

### 1.2. Các chỉ số Tổng hợp (Generation Metrics - LLM Judge)
Sử dụng mô hình `gpt-4o-mini` đóng vai trò là Trọng tài chất lượng (Judge) để chấm điểm từ `0.0` đến `1.0`:
1. **Faithfulness**: Đo lường tính trung thực tuyệt đối. Câu trả lời của trợ lý có hoàn toàn dựa vào ngữ cảnh (Context) hay có lỗi ảo giác tự bịa đặt (Hallucination).
2. **Correctness**: Đánh giá câu trả lời có phản hồi trực diện câu hỏi và chứa đầy đủ thông tin/từ khóa mong đợi (`expected_keywords`).
3. **Relevancy**: Câu trả lời có ngắn gọn, đúng trọng tâm và không bị lan man hay thừa thông tin không cần thiết.

---

## 2. Thiết kế Bộ câu hỏi Đánh giá (Golden Dataset)

Bộ câu hỏi thử nghiệm nằm trong [golden_dataset.json](file:///c:/Users/DUNG/Desktop/RAG_XANH_SM/evaluation/golden_dataset.json) gồm đúng **20 câu hỏi**, phân bổ đều thành 5 nhóm đại diện cho toàn bộ các tình huống thực tế của hệ thống:

| Nhóm câu hỏi | Số lượng | File dữ liệu đối chiếu chính | Mục tiêu kiểm soát |
|---|---|---|---|
| **1. Long Policy (Trả lời dài)** | 4 | `driver_bike.md`, `greensm_merchant.md`, `green_express.md`, `driver_platform.md` | Đảm bảo khả năng tổng hợp thông tin dài, trình bày rõ ràng bằng danh sách (Bullet/Numbered) chuẩn Markdown. |
| **2. Cước giá (Pricing/Fares)** | 4 | `green_lien_tinh.md`, `greensm_limo.md`, `greensm_bike.md` | Kiểm tra độ chính xác của bảng giá dịch vụ, phụ phí lưu đêm, phí hủy chuyến và khả năng xử lý câu hỏi so sánh/câu hỏi kép về giá. |
| **3. Policy chung (General Policy)** | 4 | `driver_bike.md`, `driver_car.md`, `green_gift_card.md`, `green_subscription.md` | Đối chiếu các điều kiện ràng buộc cụ thể (độ tuổi ứng tuyển, chất ma túy xét nghiệm, mệnh giá thẻ, quyền lợi gói subscription). |
| **4. Động chạm Guardrail (An toàn)** | 4 | `helps.md`, `bao_hiem_hang_hoa_xanh_express.md` | Xác minh khả năng cung cấp giải pháp khẩn cấp (tai nạn, quấy rối, lái xe nguy hiểm) và trích xuất đúng thông tin bồi thường bảo hiểm. |
| **5. Tấn công hệ thống (Security)** | 4 | Không có (Bị chặn bởi Gateway / Classifier) | Đảm bảo hệ thống phát hiện chính xác các câu hỏi Jailbreak, System Prompt Injection, đòi xem file nội bộ để từ chối an toàn. |

---

## 3. Cách thức vận hành Kiểm thử

### 3.1. Lệnh thực hiện
Để khởi chạy suite đánh giá tự động:
```powershell
.\venv\Scripts\python.exe evaluation/ragas_eval.py
```

### 3.2. Kết quả xuất bản
Sau khi hoàn thành, hệ thống sẽ:
1. In bảng tóm tắt chỉ số trung bình (Latency, Recall, Faithfulness, Correctness, Chunks, Context Length) lên terminal.
2. Xuất báo cáo chi tiết cho từng câu hỏi ra file [evaluation_report.json](file:///c:/Users/DUNG/Desktop/RAG_XANH_SM/evaluation_report.json).
