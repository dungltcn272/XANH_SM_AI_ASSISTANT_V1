# Xanh SM AI - Frontend

Đây là thư mục chứa mã nguồn giao diện cho Hệ thống Trợ lý Ảo RAG (Retrieval-Augmented Generation) của Xanh SM, được xây dựng trên React + Vite.

## Cấu trúc Hệ thống và Chiến thuật AI
Toàn bộ sơ đồ kiến trúc hệ thống (Gateway, Intent Classification, Strategy Search) và các lý giải về chiến thuật RAG nâng cao đã được dời ra tài liệu chung của dự án. 

Vui lòng tham khảo tài liệu chi tiết tại: **[`PIPELINE.md`](../PIPELINE.md)**

## Cài đặt và Chạy cục bộ

```bash
npm install
npm run dev
```

## Các Màn Hình Chính trong Giao Diện Admin
- **Pipeline Manager:** Xem kiến trúc hệ thống dưới dạng sơ đồ Mermaid.
- **RAG History:** Lịch sử trò chuyện và quá trình truy xuất dữ liệu của người dùng.
- **Crawl & Ingest:** Giao diện trực tiếp kích hoạt tiến trình cào dữ liệu (Crawler) và nạp dữ liệu (Chunking & Embedding) vào Qdrant với tính năng truyền log thời gian thực.
- **AI Evaluation Lab:** Kiểm thử RAGAS Benchmark (Metrics: MRR, NDCG, Recall, Faithfulness, etc.)
- **Raw Database:** Quản lý xem và xoá hàng loạt các dòng trong Database.
