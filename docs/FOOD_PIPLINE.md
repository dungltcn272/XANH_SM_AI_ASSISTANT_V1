# Báo Cáo Kiến Trúc & Luồng Xử Lý Food Recommendation

Tài liệu này mô tả luồng hoạt động hiện tại của hệ thống Food Recommendation, cách thức đánh giá (ranking) các đề xuất món ăn, cũng như các điểm chờ (hooks) đã được thiết kế sẵn để nâng cấp lên các mô hình Machine Learning (ML) và Deep Learning (DL).

## 1. Luồng Hoạt Động Hiện Tại (Rule-based / Heuristics)

Hệ thống hiện tại chủ yếu vận hành dựa trên các quy tắc (Rule-based) và tìm kiếm từ khóa (Keyword Search) kết hợp với các công thức tính điểm (Heuristics) được định nghĩa sẵn.

Các bước trong luồng xử lý:

1. **NLU & Trích xuất thông tin (Slot Filling)**
   * Dữ liệu từ câu truy vấn (query) của người dùng được phân tích thông qua `FoodRecommendationChain`.
   * Hệ thống trích xuất các thông tin (slots) quan trọng như: `category` (loại món), `taste_tags` (khẩu vị), `budget_min/max` (ngân sách), `meal_time` (bữa ăn), và tọa độ `lat/lng` của người dùng.

2. **Truy xuất ứng viên (Retrieval Phase)**
   * **Lọc không gian (Geo-filtering):** Chỉ lấy các quán ăn nằm trong bán kính quy định so với vị trí người dùng.
   * **Truy xuất từ khóa (BM25Okapi):** Từ khóa truy vấn được đối chiếu với thông tin của món ăn (tên, mô tả, tag,...) thông qua thuật toán BM25 để tính điểm độ phủ (Recall Score).

3. **Xếp hạng & Đánh giá (Ranking Phase)**
   * Các ứng viên được chuyển tới `rank_catalog` (trong `ranker.py`) để tính tổng điểm (Score).
   * Điểm số được tổng hợp từ nhiều yếu tố với trọng số cố định:
     - `recall_score`: Điểm khớp từ khóa BM25 (15%)
     - `nearby_score`: Điểm khoảng cách (16%)
     - `delivery_fee_score`: Điểm phí giao hàng (10%)
     - `eta_score`: Thời gian dự kiến (8%)
     - `budget_score`: Độ phù hợp ngân sách (10%)
     - `personalization_score`: Lịch sử tương tác của người dùng (15%)
     - `category_score`: Mức độ khớp loại món ăn (Rất quan trọng, có áp dụng trừng phạt hàm mũ 1.5 nếu điểm này thấp).
   * **Lọc cứng (Hard Filter):** Các món ăn vượt quá ngân sách lớn, khoảng cách quá xa, hoặc nằm trong danh sách không thích (disliked_foods) sẽ bị loại bỏ hoàn toàn.

---

## 2. Tiềm Năng Kích Hoạt Mô Hình ML / DL

Kiến trúc hiện tại (trong thư mục `ranking/ml_ranker.py` và `search/retrieval.py`) đã được thiết kế mở (modular) để dễ dàng chuyển đổi sang các mô hình ML/DL thông qua các cơ chế sau:

### A. Mô Hình Học Máy: XGBoost (Learning-to-Rank)
Hệ thống đã có sẵn class `XGBoostFoodRanker`.
* **Cơ chế hoạt động:** Khi hệ thống khởi động, nó kiểm tra sự tồn tại của file mô hình tại `data/models/food_xgboost.json`. Nếu file này tồn tại, `xgb_ranker.is_loaded` sẽ chuyển thành `True`.
* **Tác dụng khi kích hoạt:** Điểm số (Score) dựa trên Rule-based sẽ bị ghi đè bởi xác suất click/mua hàng do XGBoost tính toán. Model sẽ tự động tìm ra trọng số tối ưu cho từng features thay vì gán cứng bằng tay.

### B. Deep Learning Retrieval: Vector Search (Two-Tower)
Hệ thống có sẵn hàm `vector_search` sử dụng VectorDB (Qdrant).
* **Cơ chế hoạt động:** Thay vì tìm kiếm bằng từ khóa BM25, query của người dùng và thông tin món ăn được biến đổi thành Dense Vectors. Hệ thống sẽ so sánh khoảng cách ngữ nghĩa giữa hai vector này.
* **Tác dụng khi kích hoạt:** Giúp hệ thống hiểu được ý nghĩa câu lệnh thay vì chỉ khớp từ vựng. Ví dụ: "món ăn giải nhiệt" có thể tự động đề xuất "chè", "sinh tố" hoặc "kem" mặc dù không có chữ "giải nhiệt" trong tên món.

### C. Neural Reranker: Cross-Encoder (Cohere/BGE)
* **Cơ chế hoạt động:** Có sẵn class `CohereCrossEncoder` trong `ranker.py` nhưng hiện đang bị comment.
* **Tác dụng khi kích hoạt:** Cải thiện độ chính xác xếp hạng cho Top 50 kết quả trả về từ Retrieval, bằng cách phân tích sự tương quan chéo (cross-attention) cực chi tiết giữa truy vấn ngữ cảnh người dùng và mô tả món ăn.

### D. Online Learning: Bandit Explorer
* **Trạng thái:** Đang được kích hoạt một phần ở cuối bước xếp hạng.
* **Cơ chế hoạt động:** Sử dụng thuật toán Epsilon-Greedy (`epsilon=0.1`). Với tỷ lệ 10%, hệ thống sẽ bốc ngẫu nhiên một món ăn ở xếp hạng thấp đưa lên đầu.
* **Tác dụng:** Giúp người dùng khám phá (Explore) các quán ăn mới, tránh việc chỉ hiển thị mãi các quán quen thuộc, đồng thời thu thập thêm dữ liệu tương tác để phục vụ cho việc huấn luyện lại mô hình XGBoost.

## 3. Tổng Kết
Kiến trúc Food Pipeline hiện tại được thiết kế rất tốt với tư duy **"Rule-based first, ML-ready"**. 
Bạn đang dùng Rule-based để đảm bảo hệ thống có thể chạy ngay (Cold Start). Khi thu thập đủ dữ liệu (User interactions, Click logs, Orders), bạn có thể ngay lập tức train và thả các file mô hình vào hệ thống, luồng ML/DL sẽ tự động "Take over" và tăng độ thông minh của hệ thống lên mức cá nhân hóa cao nhất.
