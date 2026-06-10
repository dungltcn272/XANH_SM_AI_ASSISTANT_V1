# 🚀 Lộ trình Tối ưu hóa RAG Xanh SM (Go-Live Readiness Plan)

Dựa trên báo cáo đánh giá `evaluation_report.json`, hệ thống đã đạt độ chính xác (Correctness) 87% và độ trung thực (Faithfulness) 99%. Tuy nhiên, để đạt chuẩn Production cao cấp, chúng ta cần xử lý 3 nhược điểm chính: **Latency cao (>10s)**, **Xử lý câu hỏi mơ hồ**, và **Độ phủ ở các Case khó**.

---

## 🛠️ Giai đoạn 1: Tối ưu hóa hiệu năng (Latency Reduction)
**Mục tiêu:** Giảm thời gian phản hồi trung bình từ 10.2s xuống < 6s thông qua xử lý song song.

- [ ] **1.1. Tối ưu hóa Bất đồng bộ (Full Async & Parallelization):** 
    - Thực hiện truy vấn đồng thời Vector DB (Qdrant) và BM25 thay vì tuần tự.
    - Gọi API Reranker (Cohere) và các bước xử lý NLU bằng `asyncio.gather` để giảm "blocking time".
- [ ] **1.2. Tinh chỉnh Reranker & Retrieval:**
    - Giảm `RETRIEVAL_CANDIDATE_LIMIT` từ 25 xuống 15 để giảm khối lượng tính toán cho Reranker.
    - Tối ưu hóa số lượng chunk truyền vào LLM (`RERANK_TOP_N`) để giảm thời gian Inference của GPT-4o-mini.
- [ ] **1.3. Cơ chế Exact Cache (Duy trì hiện tại):**
    - Giữ nguyên cơ chế Exact Match hiện có để đảm bảo an toàn tuyệt đối cho Production. Tạm hoãn (Delay) việc nâng cấp Semantic Cache để nghiên cứu thêm về vấn đề phủ định (negation).

## 🧠 Giai đoạn 2: Nâng cao trí tuệ & Độ chính xác (Quality Boost)
**Mục tiêu:** Nâng Correctness cho Hard cases từ 86% lên > 92%.

- [ ] **2.1. Layout-aware Chunking (PDF):**
    - Cải thiện việc đọc bảng biểu trong các file chính sách tài xế/mua xe để không bị mất ngữ cảnh hàng/cột.
- [ ] **2.2. Query Expansion (Multi-Query):**
    - Nâng cấp khả năng diễn giải Query để tìm được nhiều tài liệu liên quan hơn cho các câu hỏi phức tạp.
- [ ] **2.3. Xử lý Ambiguity (Gateway):**
    - Thêm bước phân loại: Nếu câu hỏi quá mơ hồ, AI sẽ hỏi lại thay vì trả lời sai.

## 🛡️ Giai đoạn 3: Guardrail & Multimedia (UX & Safety)
**Mục tiêu:** Hiển thị trực quan và bảo mật dữ liệu.

- [ ] **3.1. Multimedia Mapping (Images):**
    - Hoàn thiện module `domain_vocabulary.py` để mapping chuẩn xác ảnh xe/banner theo từ khóa.
- [ ] **3.2. Prompt Engineering:**
    - Ép định dạng Markdown Table và Bullet points cho câu trả lời để dễ đọc trên UI.
    - Củng cố Guardrail ngăn chặn Prompt Injection.

---

## 📊 Kế hoạch kiểm thử (Validation)
Sau mỗi thay đổi, cần chạy lại pipeline đánh giá:
1. `python evaluation/ragas_eval.py`
2. Kiểm tra `evaluation_report.json`:
    - `average_latency_sec` < 6.0
    - `hard_avg_recall_5` > 0.85
    - `ambiguity_correctness` > 0.80

---
*Ngày lập kế hoạch: 10/06/2026*
*Trạng thái: Đang thực hiện*
