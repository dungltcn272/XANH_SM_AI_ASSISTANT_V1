# RAG Xanh SM - Frontend UI/UX Documentation (for AI Stitch)

Tài liệu này đóng vai trò làm bản đặc tả kỹ thuật (Specification) dành cho công cụ sinh UI (AI Stitch).
Hệ thống là một ứng dụng Web Full-stack (React/Vite) giao tiếp với Backend FastAPI qua REST API và SSE (Server-Sent Events).

## 1. Thiết Kế Chung (Design System)
- **Màu chủ đạo (Primary):** Xanh lá cây nhạt/Cyan đặc trưng của Xanh SM (`#00A651` hoặc tương đương).
- **Màu nền (Background):** Hỗ trợ Dark Mode (nền đen xám `#121212`) và Light Mode (nền trắng `#FFFFFF`).
- **Typography:** Font hiện đại (Inter, Roboto hoặc hệ thống).
- **Trạng thái:** Các nút ấn cần có loading indicator (spinner) khi đợi API.
- **Layout:** Hai cột chính: Sidebar (trái, cố định) và Main Content (phải, cuộn được).

---

## 2. Các Vai Trò Người Dùng (Roles)
Hệ thống phân quyền UI dựa theo đối tượng:
1. **GUEST (Khách):** Không yêu cầu đăng nhập. Chỉ có màn hình Chatbot. Không có Sidebar Lịch sử Chat.
2. **USER (Người dùng đăng nhập):** Có Sidebar bên trái hiển thị danh sách "Lịch sử Chat" tương tự ChatGPT. Có thể ấn vào để xem lại phiên chat cũ.
3. **ADMIN (Quản trị viên):** Truy cập vào Admin Dashboard với hàng loạt tab/chức năng quản trị nâng cao.

---

## 3. Chi Tiết Các Màn Hình (Screens)

### 3.1. Màn Hình Đăng Nhập (Login)
- Cửa sổ form giữa màn hình: Input Email, Password, Nút "Đăng nhập".
- Link "Tiếp tục dưới dạng Khách (Guest)".

### 3.2. Màn Hình User Chat (GUEST / USER)
- **Sidebar (Chỉ hiện cho USER):**
  - Header: Logo Xanh SM RAG, Tên User.
  - Nút "Đoạn chat mới" (New Chat) nổi bật.
  - Danh sách Lịch sử Chat (hiển thị tiêu đề tự sinh).
  - Góc dưới: Nút đổi Dark/Light mode, Đăng xuất.
- **Main Area (Khu vực Chat):**
  - Khung hiển thị các tin nhắn (User bên phải, AI bên trái).
  - **Tính năng Source Citations:** Dưới mỗi câu trả lời của AI, nếu có trích dẫn nguồn, hiển thị danh sách các thẻ nhỏ (tags) chứa tên file (VD: `🔗 chinh-sach.md`). Các thẻ này là thẻ `<a>` có thể click mở tab mới.
  - **Tính năng Realtime Status:** Khi AI đang suy nghĩ, không chỉ hiện "Loading..." mà hiển thị trạng thái động (VD: "Đang truy xuất dữ liệu...", "Đang chấm điểm...", "Đang tổng hợp...").
  - Khung nhập liệu ở dưới cùng (Textarea) có nút Gửi (Icon Send). Nút Gửi bị vô hiệu hóa khi đang loading.

### 3.3. Màn Hình Quản Trị (ADMIN DASHBOARD)
- **Sidebar Admin:**
  - Chuyển đổi giữa các menu: Thống kê (Dashboard), Quản lý File (Crawler/Ingestion), Lịch sử RAG (Logs), Quản lý Chunks, Chấm điểm Ragas.
- **Main Area (Tương ứng với Menu được chọn):**

#### A. Tab "Thống Kê (Dashboard)"
- Hiển thị các khối Card (KPIs): Tổng số User, Tổng số Request, Số truy vấn bị chặn (Guardrail), Thời gian phản hồi trung bình.
- Bảng hiển thị một số log chat mới nhất.

#### B. Tab "Lịch Sử RAG & Đánh Giá Request"
- Bảng Grid/Table liệt kê các Request:
  - Cột: Thời gian, User/Guest, Câu hỏi gốc, Câu hỏi viết lại, Câu trả lời, Trạng thái (Safe/Blocked).
  - **Nút Hành Động:** Nút "Chấm Điểm Request Này" (Manual Eval).
  - Khi ấn nút, hệ thống gọi API để chạy Ragas cho câu hỏi đó và cập nhật điểm số (Faithfulness, Relevancy...) lên UI dạng Badge (Màu xanh nếu >0.8, vàng nếu >0.5, đỏ nếu <0.5).

#### C. Tab "Quản Lý Tài Liệu (Crawler & Ingestion)"
> [!IMPORTANT]
> Cần phân biệt rõ hai khái niệm trên UI:
> - **Crawler:** Script lấy dữ liệu từ Web/Nguồn ngoài và lưu thành file tĩnh (`.md`, `.pdf`).
> - **Ingestion:** Quá trình đọc các file tĩnh đó, băm nhỏ (chunking) và đẩy vào Database (Qdrant & PostgreSQL).

- **Khu vực Crawler:**
  - Input: Nhập URL hoặc chọn nguồn.
  - Checkbox: "Ghi đè file nếu đã tồn tại".
  - Nút: "Bắt đầu Crawl".
  - Một khung Terminal giả lập để nhận SSE Realtime hiện tiến độ Crawl (VD: "Đang tải trang 1...", "Lưu file A thành công").
- **Khu vực Ingestion:**
  - Nút: "Bắt đầu Ingestion (Chunking & Nạp DB)".
  - Có khung Terminal giả lập báo cáo tiến độ (VD: "Xóa chunk cũ...", "Nạp 50 chunks file chính sách...").

#### D. Tab "Quản Lý Document Chunks"
- Để Admin kiểm tra quá trình băm (chunking) có bị mất chữ/vỡ dòng hay không.
- Giao diện Table:
  - Cột: Nguồn (Source/URL), Tiêu đề phần (Section), Nội dung Chunk (Text dài, có thể cắt bớt và thêm nút "Xem thêm"), Thời gian nạp.
- Chức năng: Lọc theo Source, Tìm kiếm trong Chunk.

#### E. Tab "Đánh Giá Toàn Hệ Thống (Benchmark / RAGAS)"
- Màn hình dành riêng để chạy đánh giá tổng thể dựa trên `golden_dataset.json`.
- Nút to: "Chạy Đánh Giá Toàn Bộ (Benchmark)".
- **Realtime Status:** Khung màn hình đen (Console) ở dưới, nhận luồng SSE từ API `/api/admin/evaluate` báo cáo log của script `evaluation/ragas_eval.py`.
- **Kết quả:** Khi hoàn tất, render ra biểu đồ hoặc bảng điểm NDCG, MMR, Faithfulness, Context Precision trung bình toàn hệ thống.

---

## 4. Đặc tả kỹ thuật cho Component Chat (Tham khảo)
- **Parse SSE (Server-Sent Events):** Phải dùng `TextDecoder` và lưu `buffer` để tránh đứt gãy JSON khi stream trả về chuỗi dài.
- **Render Source:** Nằm trong object `msg.sources`, format mẫu: `[{source: "policy.md", url: "https..."}]`. Render bằng Flexbox dưới text chính.
- **Trạng thái Step:** Nằm trong field `msg.pipelineStep`, render với chữ in nghiêng màu phụ.
