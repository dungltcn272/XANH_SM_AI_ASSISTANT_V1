# PLAN: Production Knowledge Pipeline

## Trạng thái đã chốt

- Crawler production dùng hướng thuần code, không dùng agent mặc định.
- Admin quản lý URL qua `crawler/urls.json` và DB `crawl_sources`.
- `Sync urls.json` dùng để đồng bộ metadata từ file vào DB.
- Crawler chỉ sinh Markdown/PDF-Markdown trong `data/`.
- `Clear ALL Knowledge` và `Ingest ALL From data/` là hai thao tác riêng.
- Nhóm dữ liệu hiện tại:
  - `user`, `merchant`, `driver`, `green-care`, `helps`, `term-policies`
  - `vehicle`
  - `news`
  - `pdf`
  - `overview`

## Việc còn cần xử lý

### 1. Audit Markdown sau crawl

- Crawl thử từng nhóm nhỏ: `vehicle`, `news`, `pdf`.
- Kiểm tra file Markdown có còn CTA/sidebar/menu/text lặp không.
- Kiểm tra trang xe có giữ được giá, thông số, ảnh chính và điều kiện mua/thuê không.
- Kiểm tra news detail có giữ đủ nội dung bài và bỏ được phần bài viết gần đây/sidebar không.
- Kiểm tra PDF có đủ số trang, bảng và điều khoản quan trọng.

### 2. Bổ sung OCR hybrid cho ảnh/PDF dạng slide

Vấn đề: nhiều bài news và PDF có bảng/chính sách nằm trong ảnh. Parser HTML/PDF text hiện tại có thể bỏ sót.

Hướng xử lý:

- Thêm `image_extractor.py` để lấy ảnh từ HTML/PDF.
- Thêm `image_classifier.py` để lọc ảnh đáng OCR:
  - ảnh lớn trong nội dung bài viết,
  - ảnh có alt/title chứa chính sách, thưởng, phí, cước, bảng giá, thu nhập,
  - bài viết ít text nhưng nhiều ảnh,
  - PDF page ít text nhưng nhiều image.
- Thêm `image_ocr.py` dùng OCR local trước, ví dụ PaddleOCR hoặc EasyOCR.
- Thêm `vision_parser.py` chỉ dùng khi ảnh quan trọng, nhiều bảng/cột, hoặc OCR confidence thấp.
- Thêm `document_merger.py` để gộp OCR Markdown vào tài liệu gốc.

Markdown OCR nên có dạng:

```markdown
## Nội dung trích xuất từ ảnh

### Ảnh: <alt hoặc tên ảnh>

Nguồn ảnh: <image_url>

<nội dung OCR/vision đã chuẩn hóa>
```

Metadata OCR nên lưu kèm chunk:

```json
{
  "source_type": "image_ocr",
  "page_url": "...",
  "image_url": "...",
  "content_type": "policy_table",
  "ocr_engine": "local|vision",
  "ocr_confidence": 0.0
}
```

### 3. Quality gate trước ingestion

- Cảnh báo tài liệu có nhiều ảnh nhưng không có OCR text.
- Cảnh báo PDF page nhiều image nhưng ít text.
- Cảnh báo Markdown quá ngắn so với số ảnh/PDF page.
- Cảnh báo bảng Markdown lỗi format.
- Chỉ ingest sau khi audit output đạt yêu cầu.

### 4. Tối ưu RAG sau khi dữ liệu sạch hơn

- Ưu tiên `data/overview/*_catalog.md` cho câu hỏi tổng quan.
- Duy trì domain vocabulary cho từ đồng nghĩa/sai chính tả.
- Tiếp tục dùng hybrid search + SQL keyword fallback khi vector search miss.
- Boost theo metadata `category`, `document_type`, `source_type`.
- Kiểm thử lại các câu hỏi:
  - danh mục Green SM gồm gì,
  - phí/cước/phụ phí,
  - chính sách thu nhập/thưởng,
  - điều kiện mua/thuê xe,
  - bảo hiểm/bồi thường.

### 5. Retrieval-first metadata strategy cho Qdrant/PostgreSQL

Mục tiêu: metadata không chỉ để mô tả tài liệu, mà phải đóng vai trò `retrieval control plane` để filter, boost, expand context và trace citation.

Nguyên tắc:

- Chỉ thêm/index field có tác dụng trực tiếp cho retrieval.
- Qdrant payload lưu metadata đầy đủ hơn PostgreSQL.
- PostgreSQL `document_chunks` cần đủ metadata tối thiểu để SQL keyword fallback không mất ngữ cảnh.
- HTML table full chunk và row-index chunk phải cùng tồn tại:
  - `html_table_full`: giữ nguyên `<table>` với `rowspan`/`colspan`.
  - `table_row_index`: chunk nhỏ theo 1-3 dòng bảng để rank tốt hơn khi hỏi chi tiết.
  - `text`: nội dung văn bản thường.

Metadata nên có trên mỗi chunk:

```json
{
  "url": "...",
  "source": "Chinh_sach_ban_xe_may_dien_vinfast.md",
  "title": "...",
  "category": "pdf",
  "document_type": "policy_pdf",
  "source_type": "pdf",
  "section": "...",
  "parent_chunk_id": "...",
  "chunk_id": "...",
  "chunk_index": 12,
  "chunk_type": "text | html_table_full | table_row_index",
  "table_id": "table_001",
  "table_title": "2.1 Chinh sach ban hang cua VinFast",
  "row_start": 3,
  "row_end": 5,
  "derived_from": "chunk_id_of_full_table",
  "page_range": "1-3"
}
```

Qdrant payload indexes nên có:

```text
metadata.url
metadata.parent_chunk_id
metadata.chunk_index
metadata.chunk_type
metadata.category
metadata.document_type
metadata.source_type
metadata.table_id
metadata.derived_from
```

Không nhất thiết index các field như `title`, `section`, `table_title` nếu chỉ dùng để hiển thị/boost text. Vẫn nên lưu trong payload.

Retrieval policy:

- Search trên tất cả chunks.
- Nếu hit `table_row_index`, dùng `derived_from` hoặc `table_id` để kéo thêm full HTML table.
- Nếu hit `html_table_full`, giữ làm context đầy đủ, nhưng không phụ thuộc duy nhất vào vector của chunk lớn.
- Boost nhẹ:
  - `table_row_index` cho câu hỏi chi tiết về giá, chính sách, dòng xe, điều kiện.
  - `html_table_full` cho câu hỏi "liệt kê", "so sánh", "bảng", "tất cả".
  - `text` cho câu hỏi điều kiện/diễn giải.
- Parent-child expansion vẫn dựa vào `parent_chunk_id` và sắp xếp bằng `chunk_index`.

Rủi ro cần xử lý:

- Nếu PostgreSQL chỉ lưu `source`, `section`, `content`, SQL keyword fallback sẽ mất `chunk_type`, `table_id`, `parent_chunk_id`.
- `chunk_id` hiện hash theo `filename_section_idx`, có thể đổi nếu chunk order thay đổi.
- Row-index chunk cần có `derived_from` để trace về full table và citation đúng.

## Rủi ro còn lại

- DB `crawl_sources` có thể còn metadata cũ nếu chưa bấm `Sync urls.json`.
- Một số URL PDF có thể là viewer/redirect, cần admin thay bằng URL file thật.
- OCR local có thể sai với ảnh nhiều cột hoặc chữ nhỏ.
- Vision fallback tốn chi phí, chỉ nên bật có điều kiện.
- Markdown OCR nếu không qua quality gate có thể làm vector DB nhiễu.

## Luồng vận hành khuyến nghị

1. Cập nhật `urls.json`.
2. Bấm `Sync urls.json`.
3. Crawl theo nhóm nhỏ.
4. Audit Markdown.
5. Nếu đạt: `Clear ALL Knowledge`.
6. `Ingest ALL From data/`.
7. Test RAG bằng bộ câu hỏi nghiệp vụ.
