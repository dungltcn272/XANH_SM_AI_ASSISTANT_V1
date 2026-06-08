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
