# 🚗 Xanh SM AI Assistant - Frontend

Mã nguồn giao diện người dùng cho **Xanh SM AI Assistant** – Hệ thống Trợ lý Ảo toàn diện của Xanh SM, được xây dựng trên nền tảng **React + Vite**.

---

## 🌟 Các Tính Năng Giao Diện (Từ Pitch Deck W4)

Trải nghiệm người dùng được thiết kế hiện đại, mượt mà và trực quan với các phân hệ chính:

* **🔍 Knowledge Search**: Giao diện tra cứu tri thức, chính sách và tài liệu vận hành nội bộ.
* **🔬 Deep Research**: Tính năng tổng hợp thông tin chuyên sâu từ nhiều nguồn dữ liệu, hiển thị rõ ràng trích dẫn (`sources`).
* **⚡ Vehicle Expert**: Tra cứu thông tin, thông số kỹ thuật và hệ sinh thái các dòng xe điện của Xanh SM.
* **💰 Pricing Assistant**: Giao diện phân tích, tính toán và giải thích giá cước, ưu đãi theo từng tình huống di chuyển thực tế.
* **📰 News Digest**: Tóm tắt và cập nhật các tin tức sự kiện nóng nhất liên quan đến Xanh SM.
* **🍜 Food Recommendation**: Giao diện gợi ý món ăn/quán ăn thông minh, tích hợp form bản đồ GPS động và hiển thị chi tiết độ phù hợp (Breakdown Score).
* **🛡️ Policy & Support**: Phân hệ hỗ trợ khách hàng, giải đáp điều khoản và giải quyết khiếu nại.
* **📊 Data Analytics**: Hệ thống dashboard theo dõi chất lượng cuộc hội thoại, phản hồi của người dùng và các chỉ số đo lường.

---

## 🖥️ Các Màn Hình Quản Trị Hệ Thống (Admin Control Center)

Dành cho quản trị viên và kỹ sư AI vận hành hệ thống:

1. **Command Center**: Dashboard tổng quan hiển thị các chỉ số hoạt động hệ thống thời gian thực.
2. **Food Trace Dashboard**: Giao diện theo dõi và phân tích chi tiết các log suy luận gợi ý món ăn (giúp tinh chỉnh thuật toán Ranking).
3. **Crawl & Ingest Manager**: Giao diện trực quan kích hoạt tiến trình cào dữ liệu nguồn và nạp (chunking, embedding) vào Qdrant Vector DB.
4. **AI Evaluation Lab**: Giao diện chạy và so sánh lịch sử các đợt đánh giá RAGAS Benchmark (Recall, MRR, Faithfulness...).
5. **Database Manager**: Trình duyệt quản lý, tìm kiếm và thao tác trực tiếp với các bảng cơ sở dữ liệu.

---

## 🛠️ Hướng Dẫn Cài Đặt và Khởi Chạy Cục Bộ

1. Cài đặt các thư viện phụ thuộc:
```bash
npm install
```

2. Khởi chạy máy chủ phát triển (Development Server):
```bash
npm run dev
```

Truy cập ứng dụng tại: **[http://localhost:5173](http://localhost:5173)**
