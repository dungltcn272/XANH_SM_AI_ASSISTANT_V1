# PLAN: Agent Crawl, Clean Markdown, Clear All, Ingest All, and General-Question RAG

## Kế hoạch T2-T6, 08/06/2026 - 12/06/2026

Mục tiêu tuần này là khắc phục các điểm yếu của pipeline tri thức ở phạm vi production: tài liệu crawl còn nhiễu, metadata chưa ổn định, PDF chưa được xử lý đồng nhất, và RAG đôi khi bỏ lỡ ý định người dùng khi từ khóa truy vấn không khớp trực tiếp với tài liệu.

### T2 - 08/06: Khắc phục rủi ro vận hành dữ liệu

- Chuẩn hóa luồng crawl chỉ tạo tài liệu trong `data/`, không tự clear hoặc ingest.
- Tách rõ thao tác `Clear ALL Knowledge` và `Ingest ALL From data/` để tránh mất dữ liệu do bấm nhầm.
- Chuyển sang cơ chế URL registry do admin kiểm soát, giảm rủi ro crawler tự lấy nhầm link hoặc crawl thiếu link quan trọng.

### T3 - 09/06: Khắc phục vấn đề phân loại nguồn

- Chuẩn hóa nhóm dữ liệu theo nghiệp vụ thay vì theo tên website, ví dụ `vehicle`, `news`, `pdf`, `term-policies`.
- Bổ sung cơ chế infer metadata cho URL: `source_profile`, `source_type`, `category`, `document_type`.
- Với PDF, dùng parser PDF riêng thay vì xử lý như HTML thông thường.

### T4 - 10/06: Khắc phục chất lượng Markdown

- Giữ parser cũ cho các trang có cấu trúc tốt.
- Bổ sung cleaner thuần code cho các loại trang dễ nhiễu như trang xe, trang tin tức, trang overview và PDF.
- Tập trung loại bỏ nhiễu UI như menu, CTA, sidebar, nội dung lặp; đồng thời giữ lại bảng, tiêu đề, mô tả, giá, chính sách và thông tin quan trọng cho chunking.

### T5 - 11/06: Khắc phục điểm yếu truy xuất của RAG

- Bổ sung vocabulary nghiệp vụ để xử lý từ đồng nghĩa, sai chính tả và cách hỏi đời thường.
- Tạo các catalog tổng quan từ tài liệu đã crawl để hỗ trợ câu hỏi dạng tổng hợp.
- Tăng recall bằng hybrid search, metadata boost và keyword fallback khi vector search chưa bắt đúng ngữ cảnh.

### T6 - 12/06: Kiểm tra độ sẵn sàng production

- Gom thao tác quản trị tri thức vào Knowledge Builder để admin dễ kiểm soát nguồn dữ liệu.
- Kiểm tra build frontend, entrypoint crawler, lint rule và các luồng crawl/clear/ingest chính.
- Cập nhật tài liệu dự án để phản ánh đúng kiến trúc production hiện tại: crawler thuần code, không dùng agent mặc định.

### Điểm yếu còn lại và hướng khắc phục

- Chất lượng Markdown vẫn phụ thuộc HTML gốc; cần audit output sau mỗi lần crawl nhóm nguồn mới.
- Một số PDF có thể nằm sau viewer hoặc redirect; cần admin bổ sung URL PDF trực tiếp nếu parser không lấy được nội dung.
- Registry cũ có thể còn metadata sai sau khi đổi nhóm dữ liệu; cần sửa qua UI hoặc bootstrap lại trên môi trường sạch.
- RAG vẫn có thể miss với câu hỏi quá tổng quát hoặc từ khóa quá xa tài liệu; hướng xử lý là tăng chất lượng catalog, metadata và vocabulary nghiệp vụ.
- Không đưa agent vào crawler production mặc định; ưu tiên parser, rule-based cleaner và các bước kiểm định có thể kiểm soát được.

## 0. Decision Update: Pure-Code Crawler, No LLM/Agent For Crawling

Quyết định mới: không dùng LLM/Agent trong crawler production. Admin kiểm soát URL qua `crawl_sources` và `crawler/urls.json`; crawler chỉ fetch đúng URL đã duyệt rồi dùng parser/cleaner theo loại trang.

- [x] Giữ crawler cũ cho nhóm đang chạy tốt: `user`, `driver`, `merchant`, `helps`, `green-care`, `term-policies`.
- [x] Tách cleaner riêng cho `news` để crawl số lượng lớn mà không tốn LLM.
- [x] Tách cleaner riêng cho `platform` vì layout/card/spec bất quy tắc nhưng vẫn xử lý bằng rule-based parser.
- [x] Giữ `platform_pdf` theo hướng parser-first bằng `pymupdf4llm`/PyMuPDF, không đưa PDF vào LLM.
- [x] Refactor `crawler/run_crawler.py` nhận `--sources main_site,platform,platform_pdf` và không auto-discovery URL.
- [x] Biến `crawler/agent_crawler.py` thành wrapper tương thích, không import/call OpenAI.
- [x] Cập nhật README ghi rõ crawler production là pure-code.

Ghi chú: endpoint/FE cũ có thể vẫn gọi tên `runAgentCrawler` hoặc `/crawl/agent` để tránh phá tương thích, nhưng tiến trình phía sau không còn là AI Agent.

## Mục tiêu

Xây dựng lại luồng crawl -> làm sạch dữ liệu -> ingestion -> RAG theo hướng:

1. Chấp nhận dùng **Agent Crawl** để làm sạch dữ liệu cho các nguồn có cấu trúc khác nhau.
2. Dữ liệu sau crawl phải có **format Markdown chuẩn, đẹp, giàu cấu trúc** để chunking ổn định.
3. Tách rõ **Clear ALL Knowledge** và **Ingest ALL From `data/`** thành hai thao tác riêng.
4. RAG trả lời tốt cả câu hỏi chi tiết và câu hỏi tổng quát, ví dụ:
   - "Green SM gồm những danh mục nào?"
   - "Green SM cung cấp những dịch vụ gì?"
   - "Các loại phí liên quan đến Green Express?"
5. Gom Crawler, Agent Crawler và Ingestion vào một tab quản trị rõ ràng.

## Nhận định quan trọng

Việc clear trước khi ingest là hợp lý vì:

- Tránh duplicate chunks qua nhiều lần ingest.
- Tránh Qdrant giữ vector cũ khi nội dung source đã thay đổi.
- Đảm bảo Postgres `document_chunks` và Qdrant phản ánh snapshot mới nhất.

Vấn đề không phải là "có clear hay không", mà là **không nên để nút ingest tự clear ngầm**.

Quyết định vận hành mới:

1. Crawler chỉ sinh tài liệu Markdown/PDF-extracted Markdown trong `data/`.
2. `Clear ALL Knowledge` là một nút riêng, chỉ xóa knowledge trong Postgres/Qdrant.
3. `Ingest ALL From data/` là một nút riêng, chỉ đọc toàn bộ `data/` và nạp lại.
4. Không còn mode ingest tự clear theo category/source ở phase đầu.
5. Luồng đúng để tránh trùng lặp:
   - Crawl/Agent Crawl để cập nhật file Markdown.
   - Kiểm tra file trong `data/`.
   - Clear ALL Knowledge.
   - Ingest ALL From `data/`.

## Quyết định kiến trúc sau khi đọc dữ liệu hiện có

Không nên dùng một pipeline crawl/LLM duy nhất cho cả hai website theo nghĩa "mọi trang đều đưa vào Agent cùng một prompt". Hai nguồn có bản chất khác nhau:

1. `https://www.greensm.com/vn-vi/`
   - Dữ liệu trong `data/user`, `data/merchant`, `data/driver`, `data/green-care`, `data/helps`, `data/term-policies`.
   - Nhiều trang đã là văn bản dài, có heading khá rõ và có bảng biểu.
   - Ví dụ `data/helps/helps.md` rất dài, nếu đưa cả trang vào một Agent call sẽ tốn token, dễ bị tóm tắt mất chi tiết và dễ làm hỏng FAQ.
   - Phù hợp hơn với deterministic cleaner + section-aware splitting; Agent chỉ nên dùng cho bước tạo metadata/overview hoặc làm sạch cục bộ theo section nhỏ.

2. `https://platform.greensm.com/VN-vi`
   - Dữ liệu trong `data/platform`.
   - Trang xe/news/platform thường ngắn hơn nhưng cấu trúc DOM/card/form không giống văn bản tự nhiên.
   - Ví dụ trang xe có ảnh, giá, specs, CTA; cần Agent để tái cấu trúc thành Markdown sạch.
   - Phù hợp với Agent cleaner theo prompt chuyên biệt.

3. PDF platform
   - Các PDF thật nằm ở **4 link đầu tiên trong tab "Chính sách" của Platform**.
   - Trong dữ liệu hiện tại tương ứng với các file:
     - `data/platform/public_document_Chuong_trinh_mua_xe_oto_dien_vinfast_truc_tiep_qua_green_smpdf.md`
     - `data/platform/public_document_Chuong_trinh_thue_van_hanh_thuong_van_doanh_xe_o_to_dien_vinfastpdf.md`
     - `data/platform/public_document_Chuong_trinh_cho_thue_xe_o_to_dien_gsm_rentalpdf.md`
     - `data/platform/public_document_Chinh_sach_ban_xe_may_dien_vinfastpdf.md`
   - Các link chính sách còn lại trên Platform là web pages, không phải PDF thật.
   - Các link policy của `crawler/urls.json` thuộc website chính `www.greensm.com`, ví dụ `terms-policies/general`, `privacy-notice`, `service-agreement`; đây là một nhóm khác, có thể overlap chủ đề nhưng không nên gom lẫn với PDF platform.

Vì vậy quyết định là:

- **Hợp nhất ở tầng vận hành**: một tab `Knowledge Builder`, một CLI, một manifest, một schema Markdown, hai thao tác knowledge rõ ràng: clear all và ingest all.
- **Tách riêng ở tầng extraction/cleaning**:
  - `main_site_cleaner`
  - `platform_agent_cleaner`
  - `platform_pdf_extractor`
  - `overview_generator`

Nói ngắn gọn: chung "khung pipeline", riêng "chiến lược xử lý nội dung".

## Quyết định URL registry: bỏ auto-discovery trong production

Không dùng chế độ backend tự mò URL làm luồng chính nữa.

Lý do:

- Auto-discovery bằng Playwright/Chromium làm backend image nặng.
- DOM/menu/news pagination dễ đổi, dễ thiếu URL.
- Admin sẵn sàng tự kiểm soát URL nên dữ liệu sẽ chuẩn hơn, ít rác hơn.
- Tool nên tập trung crawl/extract/clean Markdown từ danh sách URL đã duyệt.

Quyết định:

1. `urls.json` vẫn tồn tại nhưng chỉ đóng vai trò **seed/bootstrap**.
2. Thêm bảng DB quản lý URL crawl.
3. Khi app deploy mới hoặc DB rỗng, backend có thể import `crawler/urls.json` vào bảng DB.
4. FE Admin có màn thêm/sửa/xóa/bật/tắt URL cần crawl.
5. Crawler production chỉ đọc URL từ DB registry, không tự mò link bằng Playwright.
6. Không triển khai chế độ `Suggest URLs`/auto-discovery trong phase này; admin kiểm soát danh sách URL.

Schema DB đề xuất:

```text
crawl_sources
- id
- url
- title
- source_profile        main_site | platform | platform_pdf
- source_type           web | pdf
- category              user | merchant | driver | green-care | helps | term-policies | platform | overview
- document_type         service | pricing | policy | faq | news | vehicle | policy_pdf | overview
- output_dir            data/user | data/platform | ...
- enabled
- priority
- notes
- last_crawled_at
- last_status
- last_error
- created_at
- updated_at
```

Luồng bootstrap:

1. App/admin kiểm tra bảng `crawl_sources`.
2. Nếu rỗng, đọc `crawler/urls.json`.
3. Convert từng URL thành row:
   - key JSON -> `category`
   - URL chứa `(pdf)` hoặc `.pdf` -> `source_type=pdf`
   - URL `platform-static*/public/document/*.pdf` -> `source_profile=platform_pdf`
   - URL `platform.greensm.com` -> `source_profile=platform`
   - URL `www.greensm.com` -> `source_profile=main_site`
4. Lưu vào DB với `enabled=true`.
5. Admin có thể chỉnh lại category/document_type/output_dir trên FE.

Luồng crawl production:

1. Admin mở `Knowledge Builder`.
2. Chọn URL hoặc nhóm URL enabled trong DB.
3. Bấm crawl.
4. Backend lấy danh sách URL từ DB.
5. Crawl/extract/clean Markdown.
6. Ghi output vào `data/<category>/...`.
7. Không tự discover URL mới.

## Root-cause candidates: news thiếu và PDF thiếu nội dung

Sau khi đọc `crawler/agent_crawler.py`, `crawler/run_crawler.py`, `crawler/markdown_converter.py` và các file mẫu trong `data/`, các lỗi cũ nhiều khả năng nằm ở các điểm sau.

### A. News crawl bị thiếu

1. Discovery news đang chỉ quét tối đa 3 trang mỗi tag.
   - Trong `AgentCrawler.discover_urls()`, đoạn news dùng:
     - tags: `Tất cả`, `Báo chí`, `Chính sách`, `Sự kiện`
     - `for page_num in range(1, 4)`
   - Nếu Platform có nhiều hơn 3 trang/tags, chắc chắn thiếu.

2. Discovery phụ thuộc click UI và text tiếng Việt bị encoding mojibake trong source.
   - Code đang tìm các text dạng mojibake như `Táº¥t cáº£`, `BÃ¡o chÃ­`.
   - Nếu runtime/source/page text không khớp encoding, click tag có thể fail hoặc chỉ crawl tab mặc định.

3. Có nguy cơ chỉ crawl listing page, không crawl đủ detail page.
   - File `data/platform/VN_vi_news_all_page_1.md` là listing page, chứa preview có dấu `[…]`.
   - Listing page không đủ nội dung bài viết.
   - Cần đảm bảo mọi URL detail `/news/<slug>` cần dùng được lưu trong registry và crawl thành file riêng.

4. `max_urls` có thể cắt mất news detail.
   - Backend đang gọi agent crawler với `--max-urls 45`.
   - `discover_urls()` trả `sorted(list(filtered_discovered))`, sau đó mới `urls_to_crawl[:self.max_urls]`.
   - Nếu số URL discover > 45, một số news detail/PDF có thể bị cắt tùy thứ tự sort.
   - Đây là lỗi rất dễ gây cảm giác "crawl tin tức rất thiếu".

5. Pagination selector có thể không đúng hoặc chưa đợi render đủ.
   - Code dùng `.ant-pagination-next`.
   - Nếu nút next bị lazy render, bị disabled theo class nhưng `is_enabled()` vẫn không phản ánh đúng, hoặc page cần scroll xuống, crawler sẽ dừng sớm.

6. Agent filtering có thể skip news.
   - Sau crawl, content được đưa qua `analyze_content_with_llm()`.
   - Nếu Agent chấm `knowledge_score < 50`, page bị skip.
   - News ngắn hoặc listing/detail ít text có thể bị đánh giá thấp.

### B. PDF crawl/extract bị thiếu

1. Agent crawler đang dùng `pypdf.PdfReader.extract_text()`.
   - `pypdf.extract_text()` thường mất bảng, mất layout, mất text trong ảnh, hoặc đọc sai thứ tự cột.
   - Trong khi ingestion/chunking lại có `pymupdf4llm.to_markdown()` tốt hơn cho PDF.
   - Đây là ứng viên lỗi lớn nhất với PDF thiếu nội dung/bảng.

2. PDF được bọc thành HTML rồi đưa qua `markdownify` và LLM.
   - `crawl_page()` tạo:
     - `<html><body><h1>...</h1><div>{full_text}</div></body></html>`
   - Sau đó `markdownify` xử lý lại và toàn bộ PDF text đi vào `analyze_content_with_llm()`.
   - Nếu PDF dài, LLM có thể:
     - bị quá context,
     - tóm tắt mất chi tiết,
     - bỏ phụ lục/bảng cuối,
     - output JSON ngắn hơn nội dung gốc.

3. Prompt Agent yêu cầu "clean/restructure", không yêu cầu bảo toàn 100% PDF.
   - Với policy/PDF, yêu cầu đúng phải là "preserve all clauses, tables, numbers".
   - Prompt hiện tại phù hợp trang xe/news hơn là policy PDF dài.

4. 4 PDF Platform có nguồn khác domain và có staging/static lẫn nhau.
   - Seed hiện hardcode:
     - `platform-static-staging...`
     - `platform-static...`
   - Nếu file đổi URL, redirect, hoặc một link cần signed/static mới, `requests.get()` có thể tải bản lỗi/ngắn/HTML fallback mà vẫn không được validate bằng content-type.
   - Cần check `Content-Type: application/pdf` và size trước khi parse.

5. Standard crawler xử lý `(pdf)` của main site không phải PDF extraction thật.
   - Trong `crawler/run_crawler.py`, nếu URL trong `urls.json` có `(pdf)`, code lại dùng `PDFGenerator.extract_images_and_save_pdf()` từ HTML.
   - Đây là tạo PDF từ ảnh HTML, không phải tải và parse tài liệu PDF gốc.
   - Với main site `terms-policies/regulations (pdf)`, nếu muốn nội dung text thì cần xử lý riêng, không dùng `pdf_generator` làm nguồn tri thức.

### C. Hướng sửa ưu tiên

1. News:
   - Bỏ news auto-discovery khỏi luồng production.
   - Admin nhập URL detail `/news/<slug>` vào URL registry.
   - Crawl detail `/news/<slug>` là nguồn chính; listing chỉ để admin tham khảo hoặc sinh catalog nếu đã có danh sách URL.
   - Không để `max_urls` global cắt mất PDF/news; crawler chạy theo danh sách URL enabled trong DB.
   - Không triển khai tool phụ tự tìm news trong phase này; admin tự bổ sung URL vào registry.

2. PDF:
   - Tạo `crawler/pdf_utils.py`.
   - Dùng `pymupdf4llm.to_markdown()` hoặc PyMuPDF trước, không dùng `pypdf.extract_text()` làm đường chính.
   - Validate download:
     - status code 200,
     - content-type PDF,
     - byte size tối thiểu,
     - số page.
   - Không đưa toàn bộ PDF qua một LLM call.
   - Với PDF, LLM chỉ normalize theo page/section nếu thật cần; output phải bảo toàn điều khoản, bảng, số liệu.

3. Agent prompts:
   - Tách prompt:
     - `PLATFORM_NEWS_PROMPT`
     - `PLATFORM_VEHICLE_PROMPT`
     - `PLATFORM_POLICY_PAGE_PROMPT`
     - `PLATFORM_PDF_PROMPT`
   - PDF prompt cấm tóm tắt thay thế nội dung gốc.

4. Tests:
   - So sánh số news URL trong registry với số file detail đã sinh ra.
   - Với mỗi PDF, log:
     - URL,
     - bytes,
     - page_count,
     - markdown length,
     - table count,
     - output md length.
   - Fail nếu markdown output ngắn bất thường so với raw extracted text.

### D. Nguyên tắc xử lý PDF mới

PDF không cần Agent "hiểu" hay viết lại nhiều. PDF trong bài toán này về bản chất là tài liệu văn bản có thể có bảng, điều khoản và phụ lục. Mục tiêu chính là **crawl/extract đủ nội dung**.

Quy tắc:

1. PDF extraction phải là parser-first, không phải LLM-first.
2. Dùng `pymupdf4llm` hoặc PyMuPDF để giữ cấu trúc text/table tốt nhất có thể.
3. Không dùng `pypdf.extract_text()` làm đường chính vì dễ mất bảng và sai layout.
4. Không đưa toàn bộ PDF vào một LLM call.
5. Không cho LLM tóm tắt thay thế nội dung PDF.
6. Nếu cần Agent thì chỉ dùng để:
   - đặt lại heading rõ hơn,
   - sửa bảng Markdown nhẹ,
   - xóa header/footer lặp theo trang,
   - giữ nguyên toàn bộ số liệu, điều khoản, phụ lục.
7. PDF output phải có log/audit:
   - số byte tải về,
   - content-type,
   - số trang,
   - độ dài markdown raw,
   - độ dài markdown clean,
   - số bảng phát hiện.
8. Nếu PDF có 7 trang như `Chuong_trinh_mua_xe_oto_dien_vinfast_truc_tiep_qua_green_sm.pdf`, output Markdown phải phản ánh đủ 7 trang, không chỉ 1-2 trang đầu.

## 1. Source Profiles

Tạo khái niệm `SourceProfile` để mỗi nguồn có luật crawl, clean, output và ingest riêng.

### 1.1 Main Website

Nguồn:

- `https://www.greensm.com/vn-vi/`

Đặc điểm:

- Cấu trúc khá rõ ràng.
- Có tiêu đề, section, nội dung, bảng biểu.
- Có các trang dịch vụ như Green Car, Green Limo, Green Bike, Green Express, Green Van...
- Có các trang hỗ trợ, chính sách, bảo hiểm, merchant, driver.

Chiến lược:

- Không đưa nguyên trang dài vào một LLM call mặc định.
- Dùng deterministic cleaner trước:
  - loại nav/footer/script/form rác,
  - giữ heading,
  - giữ FAQ theo từng `### question`,
  - giữ bảng Markdown.
- Nếu cần Agent thì chỉ dùng theo section nhỏ hoặc dùng để sinh metadata/summary, không được tóm tắt thay thế nội dung chính.
- Ưu tiên bảo toàn heading, bảng, link ảnh, FAQ.
- Output phân thư mục theo category hiện có:
  - `data/user`
  - `data/merchant`
  - `data/driver`
  - `data/green-care`
  - `data/helps`
  - `data/term-policies`

### 1.2 Platform Website

Nguồn:

- `https://platform.greensm.com/VN-vi`

Đặc điểm:

- Cấu trúc bất quy tắc hơn.
- Có trang xe, hình ảnh, thông số, giá bán/thuê, tin tức.
- Có các PDF chính sách/điều khoản phức tạp.

Chiến lược:

- Dùng Agent Crawl mạnh hơn để:
  - loại header/footer/form rác,
  - gom thông tin xe thành block chuẩn,
  - giữ ảnh sản phẩm/spec nếu có,
  - chuẩn hóa bảng giá/thông số,
  - tạo metadata rõ.
- Output chính:
  - `data/platform`
- Các trang policy web trong tab Chính sách nhưng không phải PDF vẫn đi qua `platform_agent_cleaner`.
- News listing page chỉ nên dùng để catalog/audit; URL detail cần crawl phải được admin lưu trong registry.

### 1.3 PDF Documents

Nguồn:

- 4 PDF URL đầu tiên trong tab Chính sách của Platform.
- PDF local nếu có trong `data/`.

Đặc điểm:

- Văn bản dài.
- Có bảng biểu.
- Có điều khoản/chính sách phức tạp.

Chiến lược:

- Tách PDF extraction thành helper riêng.
- Dùng parser giữ layout/bảng tốt nhất hiện có (`pymupdf4llm` trong chunking đang dùng được).
- Sau khi extract, Agent chỉ làm sạch/chuẩn hóa nhẹ:
  - chuẩn hóa heading,
  - giữ bảng Markdown,
  - không tóm tắt mất số liệu,
  - không bỏ điều khoản/phụ phí/giá.
- Không gọi Agent trên PDF quá dài theo một request duy nhất; nếu cần thì chia theo page/section.

## 2. Chuẩn Markdown Đầu Ra Cho Agent Crawl

Mục tiêu lớn nhất: output markdown phải "chunking-friendly".

### 2.0 Vấn đề từ crawler cũ

Các file sinh bởi crawler cũ cho thấy dữ liệu khá trung thực nhưng còn nhiều rác UI, làm chunking bị vấp:

- CTA/nút bấm:
  - `ĐĂNG KÝ`
  - `ĐĂNG KÝ NGAY`
  - `Ứng tuyển ngay`
  - `Chỉ đường`
  - `Khám phá`
- Form field:
  - `Họ và tên *`
  - `Email`
  - `Số điện thoại *`
  - `Tỉnh/ Thành phố đang sinh sống * Chọn`
  - `Nội dung cần tư vấn thêm`
- Text UI/tab:
  - `Lựa chọn tỉnh/ thành phố`
  - `Đăng ký trực tiếp`
  - `Đăng ký Online`
  - `Tải ngay App...`
- Text bị dính do DOM/card:
  - `Chia sẻ doanh thuHưởng mức...`
  - `Hỗ trợ gói vayGói vay...`
  - `ĐẶC QUYỀNTài xế Green SM Platform...`
- Ảnh icon không có giá trị tri thức:
  - `driver-discover-icon-*`
  - icon service/card/navigation.
- Heading rỗng hoặc heading nhiễu:
  - `##`
  - title lặp 2-3 lần ngay đầu file.

Crawler code có ưu điểm là ít bịa nội dung, nhưng nếu giữ nguyên rác này, `HeadingAwareSplitter` sẽ tạo chunk chứa nhiều token không liên quan, làm retrieval/rerank kém chính xác.

### 2.0.1 Ràng buộc với thuật toán chunking hiện tại

`HeadingAwareSplitter` hiện hoạt động theo logic:

1. Split theo heading Markdown `#`, `##`, `###`, `####`.
2. Với mỗi section, split tiếp bằng block/table-aware splitter.
3. Bảng Markdown hợp lệ được giữ nguyên nếu dưới 1500 ký tự.
4. Các chunk sau trong cùng section được prepend lại semantic header path.

Vì vậy Markdown đầu ra cần:

- Heading rõ và không rỗng.
- Mỗi heading chứa đúng một chủ đề.
- Không để CTA/form/menu nằm chung section với nội dung chính.
- Bảng phải là Markdown table hợp lệ.
- FAQ phải có từng câu hỏi là `###`.
- Các step/hướng dẫn nên là numbered list chuẩn `1.`, `2.`, `3.`.
- Các card tính năng nên chuyển thành bullet list có nhãn rõ, không để text dính.

Ví dụ tốt:

```markdown
## Quyền lợi dành cho tài xế Green SM Platform

- **Chia sẻ doanh thu:** Hưởng mức chia sẻ lên tới 87% doanh thu chuyến xe.
- **Hỗ trợ gói vay:** Gói vay mua xe tới 70% cùng nhiều chính sách ưu đãi.
- **Chủ động công việc:** Tự do vận doanh và linh hoạt thời gian làm việc.
- **Tiên phong chuyển đổi:** Dẫn dắt xu hướng giao thông xanh, tiện lợi và bền vững.
```

Ví dụ xấu cần tránh:

```markdown
Chia sẻ doanh thuHưởng mức chia sẻ lên tới 87% doanh thu chuyến xe

ĐĂNG KÝ NGAY

Họ và tên *
Email
Số điện thoại *
```

### 2.1 Frontmatter bắt buộc

Mỗi file `.md` sau crawl cần có:

```yaml
---
url: "https://..."
canonical_url: "https://..."
source_profile: "main_site|platform|platform_pdf"
source_type: "web|pdf"
category: "user|merchant|driver|green-care|helps|term-policies|platform|overview"
title: "..."
service_name: "Green Express"
service_group: "delivery"
document_type: "service|pricing|policy|faq|news|vehicle|pdf|overview"
crawl_date: "YYYY-MM-DD"
content_hash: "..."
---
```

Các field có thể null/rỗng nếu không áp dụng, nhưng key nên ổn định.

### 2.2 Cấu trúc heading chuẩn

Format đề xuất:

```markdown
# Tên trang / tên dịch vụ / tên tài liệu

## Tóm tắt
...

## Danh mục / Dịch vụ liên quan
...

## Nội dung chính
...

## Bảng giá / Cước phí / Phụ phí
...

## Điều kiện áp dụng
...

## Câu hỏi thường gặp
...

## Nguồn
- URL: ...
```

Không bắt buộc file nào cũng có đủ mọi section, nhưng nếu có dữ liệu tương ứng thì nên đưa đúng heading chuẩn.

### 2.3 Quy tắc bảng biểu

Agent phải giữ bảng dưới dạng Markdown table:

```markdown
| Hạng mục | Giá trị | Ghi chú |
|---|---:|---|
| 2 km đầu | 15.000 VNĐ | Hà Nội |
| Km tiếp theo | 5.700 VNĐ/km | Hà Nội |
```

Quy tắc:

- Không chuyển bảng thành đoạn văn nếu bảng có giá/số liệu.
- Không bỏ đơn vị tiền tệ.
- Không đổi tên cột thành `Giá trị 2`, `Giá trị 3` nếu có thể suy ra tên cột rõ hơn.
- Nếu bảng gốc thiếu header rõ, Agent được đặt header mô tả như `Khu vực`, `Dịch vụ`, `Mức giá`, `Ghi chú`.

### 2.4 Quy tắc ảnh

Với platform và trang xe:

- Giữ ảnh có giá trị nhận diện sản phẩm/spec:
  - ảnh xe,
  - ảnh màu xe,
  - bảng thông số,
  - ảnh mô tả chương trình.
- Bỏ ảnh icon/navigation/footer.
- Format:

```markdown
![Green SM Limo - ngoại thất](https://...)
```

### 2.5 Quy tắc trang tin tức

Trang news cần output:

```markdown
# Tiêu đề tin

## Tóm tắt
...

## Nội dung chính
...

## Thông tin liên quan
- Ngày đăng:
- Chủ đề:
- URL:
```

Tin tức không được lẫn vào overview dịch vụ trừ khi có liên quan trực tiếp đến dịch vụ/giá/chính sách.

### 2.6 Bộ lọc rác UI bắt buộc

Cleaner phải loại các nhóm sau trước khi lưu Markdown:

1. Navigation/header/footer:
   - menu đầu trang,
   - footer,
   - language selector,
   - app download block,
   - hotline floating widget,
   - Zalo chat.
2. CTA/button text không mang tri thức:
   - `Đăng ký`
   - `Đăng ký ngay`
   - `Ứng tuyển ngay`
   - `Xem thêm`
   - `Khám phá`
   - `Chỉ đường`
   - `Tải ngay`
3. Form/input labels:
   - `Họ và tên`
   - `Email`
   - `Số điện thoại`
   - `Chọn`
   - `Nội dung cần tư vấn`
   - checkbox consent text, trừ khi là điều khoản pháp lý có nội dung thật.
4. Icon/image decorative:
   - ảnh có alt chứa `icon`, `logo`, `Service` nếu URL thuộc static icon,
   - ảnh dùng cho form/banner không mang thông tin sản phẩm/chính sách.
5. Heading rỗng/lặp:
   - xóa heading `##` rỗng,
   - gộp title lặp liên tiếp,
   - không lặp lại H1 ngay dưới H1.

### 2.7 Quality gate cho Markdown trước khi ingest

Trước khi lưu hoặc trước khi ingest, chạy validator nhẹ:

- Không có heading rỗng: regex `^#{1,4}\s*$`.
- Không có quá 3 dòng CTA liên tiếp.
- Tỷ lệ dòng form/CTA không vượt ngưỡng, ví dụ 5% tổng dòng.
- Không có text dính phổ biến:
  - chữ thường/hoa dính sau từ kết thúc không dấu câu,
  - pattern như `doanh thuHưởng`, `vayGói`, `việcTự`.
- File phải có ít nhất:
  - 1 H1,
  - 1 H2 có nội dung thật,
  - frontmatter `url`, `category`, `title`.
- Nếu file có bảng giá/quyền lợi, bảng phải có separator row `|---|`.

Nếu fail:

- ghi cảnh báo vào crawl manifest,
- vẫn có thể lưu raw converted file để debug,
- không đưa file fail vào `data/clean` hoặc không ingest nếu chọn strict mode.

### 2.8 Đề xuất thư mục output sạch

Để tránh nhầm giữa raw và clean:

- `data/raw/`: JSON/HTML thô.
- `data/raw_converted/`: Markdown convert thô để debug.
- `data/<category>/`: Markdown sạch, được phép ingest.

Crawler/Agent chỉ nên ghi bản cuối vào `data/<category>/` khi đã qua cleaner + quality gate.

## 3. Overview Documents Cho Câu Hỏi Tổng Quát

Đây là phần quan trọng để trả lời tốt câu kiểu:

- "Green SM gồm những danh mục nào?"
- "Green SM cung cấp những dịch vụ gì?"
- "Các dịch vụ người dùng của Green SM là gì?"
- "Platform Green SM có những dòng xe nào?"

### 3.1 Tạo `service_catalog.md`

Sau crawl, hệ thống cần sinh file tổng quan:

Path đề xuất:

- `data/overview/service_catalog.md`

Nội dung mẫu:

```markdown
---
url: "internal://overview/service-catalog"
source_profile: "generated"
source_type: "overview"
category: "overview"
title: "Danh mục dịch vụ Green SM"
document_type: "overview"
---

# Danh mục dịch vụ Green SM

## Tổng quan
Green SM cung cấp các nhóm dịch vụ chính cho người dùng, tài xế, đối tác doanh nghiệp và nền tảng mua/thuê xe điện.

## Dịch vụ dành cho người dùng
| Danh mục | Tên dịch vụ | Mô tả ngắn | URL |
|---|---|---|---|
| Di chuyển | Green SM Car | Dịch vụ taxi ô tô điện | ... |
| Di chuyển | Green SM Limo | Dịch vụ limousine | ... |
| Giao hàng | Green Express | Dịch vụ giao hàng | ... |
| Giao đồ ăn | Green SM Food | Dịch vụ giao đồ ăn | ... |

## Dịch vụ dành cho tài xế
...

## Dịch vụ dành cho đối tác/merchant
...

## Nền tảng mua/thuê xe điện
...
```

Nguồn sinh catalog:

- `crawler/urls.json` cho danh mục main site.
- Frontmatter của các file đã crawl.
- Heuristic theo URL path:
  - `/greensm-car` -> Green SM Car
  - `/greensm-limo` -> Green SM Limo
  - `/green-express` -> Green Express
  - `/greensm-bike` -> Green SM Bike
  - `/green-van` -> Green Van
- Platform overview hiện có như `data/platform/VN_vi_overview.md`, `car_overview.md`, `bike_overview.md`.

Không nên bắt LLM đọc toàn bộ `helps.md` hoặc toàn bộ main site để trả lời catalog. Catalog nên được sinh deterministic từ URL/category/frontmatter, sau đó LLM chỉ dùng khi cần viết mô tả ngắn.

### 3.2 Tạo overview theo nhóm

Các file generated nên có:

- `data/overview/service_catalog.md`
- `data/overview/pricing_catalog.md`
- `data/overview/platform_vehicle_catalog.md`
- `data/overview/policy_catalog.md`
- `data/overview/news_catalog.md`

Vai trò:

- `service_catalog.md`: trả lời danh mục/dịch vụ tổng quát.
- `pricing_catalog.md`: gom các trang có giá/cước/phụ phí.
- `platform_vehicle_catalog.md`: gom xe platform, hình thức mua/thuê, giá, specs chính.
- `policy_catalog.md`: gom chính sách/điều khoản.
- `news_catalog.md`: gom tin tức.

### 3.3 Metadata cho overview

Overview documents phải có:

- `document_type: overview`
- `category: overview`
- `source_profile: generated`

Ingestion cần ingest overview như một category riêng để retrieval có context tổng quát.

## 4. Agent Crawl Unified Pipeline

### 4.1 Không hợp nhất logic crawl một cách cưỡng ép

Tên `Agent Crawl Unified Pipeline` không có nghĩa là mọi nguồn đều dùng LLM như nhau.

Pipeline thống nhất gồm các bước:

1. Load URL/file từ DB registry.
2. Fetch raw content.
3. Chọn cleaner theo `source_profile`.
4. Xuất Markdown theo schema chung.
5. Sinh overview/catalog.
6. Ghi manifest snapshot.
7. Dừng tại file Markdown/manifest; không đụng Postgres/Qdrant.

Cleaner được chọn theo nguồn:

| Source profile | Fetcher | Cleaner | LLM usage |
|---|---|---|---|
| `main_site` | requests/httpx | deterministic + section-aware | optional, theo section nhỏ |
| `platform` | requests/httpx + parsed Next data/static HTML | Agent cleaner | yes, vì DOM/card bất quy tắc |
| `platform_pdf` | PDF downloader/parser | PDF structure normalizer | optional, theo page/section |
| `overview` | generated from manifest/frontmatter | deterministic generator | optional |

Ghi chú: không thêm Playwright/Chromium vào backend image trong phase này.

### 4.2 Refactor `crawler/agent_crawler.py`

Thêm CLI:

```bash
python crawler/agent_crawler.py --sources main_site,platform,platform_pdf --max-urls 100
```

Options:

- `--sources main_site,platform,platform_pdf`
- `--max-urls`
- `--output-root data`
- `--include-pdfs`
- `--generate-overviews`
- `--mode crawl|extract|all`

### 4.3 SourceProfile config

Tạo `crawler/sources.py`:

```python
SOURCE_PROFILES = {
    "main_site": {
        "base_url": "https://www.greensm.com/vn-vi/",
        "registry": "db:crawl_sources",
        "seed_file": "crawler/urls.json",
        "output_strategy": "by_url_category",
    },
    "platform": {
        "base_url": "https://platform.greensm.com/VN-vi",
        "output_dir": "data/platform",
        "registry": "db:crawl_sources",
    },
    "platform_pdf": {
        "source_type": "pdf",
        "output_dir": "data/platform",
        "seed_kind": "platform_policy_first_4",
    },
}
```

### 4.4 Platform policy/PDF registry rule

Với Platform tab `Chính sách`, admin nhập/duyệt các URL vào DB registry:

- 4 item đầu tiên là PDF thật.
- Các item còn lại là web pages/chính sách dạng page.
- Crawler cần lưu metadata khác nhau:

```yaml
source_profile: platform_pdf
source_type: pdf
category: platform
document_type: policy_pdf
```

hoặc:

```yaml
source_profile: platform
source_type: web
category: platform
document_type: policy_page
```

Không dựa vào text hiển thị duy nhất để đoán PDF; khi admin lưu URL hoặc backend crawl, nên inspect href/content-type:

- URL kết thúc `.pdf`, hoặc
- HTTP `Content-Type: application/pdf`, hoặc
- link thuộc `platform-static*.car-trading.gsm-api.net/public/document/`.

### 4.5 Agent prompt theo từng nguồn

Agent prompt không nên dùng một prompt chung cho mọi nguồn.

Tạo prompt profile:

- `MAIN_SITE_CLEANING_PROMPT`
  - giữ heading/table/FAQ,
  - ít tái cấu trúc.
  - không tóm tắt trang dài thành bản ngắn.
  - nếu trang dài, xử lý theo section/chunk.
- `PLATFORM_CLEANING_PROMPT`
  - gom specs/price/images,
  - loại form/contact/modal,
  - chuẩn hóa trang xe.
- `PDF_CLEANING_PROMPT`
  - bảo toàn điều khoản, bảng, số liệu,
  - không tóm tắt mất chi tiết.

### 4.6 Crawl manifest

Mỗi lần crawl sinh một manifest:

```json
{
  "crawl_run_id": "crawl_...",
  "started_at": "...",
  "sources": ["main_site", "platform", "platform_pdf"],
  "documents": [
    {
      "url": "https://...",
      "canonical_url": "https://...",
      "source_profile": "platform_pdf",
      "source_type": "pdf",
      "category": "platform",
      "document_type": "policy_pdf",
      "output_path": "data/platform/public_document_....md",
      "content_hash": "..."
    }
  ]
}
```

Manifest dùng để audit crawl output, sinh overview/catalog, và debug thiếu URL. Phase đầu không dùng manifest để clear theo scope.

### 4.7 Output filename

Filename deterministic:

- Dựa trên canonical URL/path.
- Nếu trùng path nhưng khác query/source, thêm hash ngắn.
- Cùng URL crawl lại thì overwrite đúng file cũ.

## 5. Clear ALL + Ingest ALL

### 5.1 Nguyên tắc mới

Phase đầu không chia vùng clear để tránh logic phức tạp và dễ lỗi.

Tách knowledge operations thành 2 nút riêng:

1. `Clear ALL Knowledge`
   - Xóa toàn bộ Postgres `document_chunks`.
   - Recreate hoặc clear toàn bộ Qdrant collection.
   - Không ingest.
   - Không đọc `data/`.

2. `Ingest ALL From data/`
   - Đọc toàn bộ `.md` và `.pdf` hợp lệ trong `data/`.
   - Chunk, embed, upsert vào Postgres và Qdrant.
   - Không clear ngầm.

### 5.2 Luồng vận hành chuẩn

1. Chạy crawler/agent crawler để sinh hoặc cập nhật Markdown trong `data/`.
2. Kiểm tra nhanh output Markdown/PDF-extracted Markdown.
3. Bấm `Clear ALL Knowledge`.
4. Bấm `Ingest ALL From data/`.
5. Test RAG/debug pipeline.

### 5.3 Vì sao tách hai nút

- Tránh chuyện bấm ingest mà hệ thống âm thầm xóa dữ liệu.
- Tránh bug clear sai category/source.
- Dễ hiểu với người vận hành: `data/` là snapshot tri thức, knowledge DB là bản index của snapshot đó.
- Nếu ingest lỗi sau khi clear, lỗi nằm ở bước ingest, không lẫn với logic clear scope.

### 5.4 Cảnh báo UI cho Clear ALL

`Clear ALL Knowledge` là thao tác nguy hiểm:

- UI phải yêu cầu nhập `CLEAR`.
- Text cảnh báo:
  - "Thao tác này xóa toàn bộ knowledge đã index trong Postgres document_chunks và Qdrant. Các file Markdown trong data/ không bị xóa."
- Sau khi clear xong, hệ thống có thể tạm thời không trả lời được RAG cho đến khi ingest lại.

### 5.5 Backend behavior

Endpoint đề xuất:

- `POST /api/admin/knowledge/clear`
- `POST /api/admin/knowledge/ingest-all`

`clear` làm:

1. Delete toàn bộ `DocumentChunk`.
2. Recreate Qdrant collection hoặc delete toàn bộ points.
3. Return summary:
   - chunks_deleted
   - qdrant_collection_reset

`ingest-all` làm:

1. Gọi ingestion trên toàn bộ `settings.DATA_DIR` hoặc `./data`.
2. Không gọi `setup_qdrant()` theo kiểu recreate collection nữa.
3. Upsert toàn bộ chunks.
4. Return summary:
   - files_processed
   - chunks_inserted
   - qdrant_points_upserted
   - failed_files

## 5.6 URL Registry Backend

Thêm model/bảng `crawl_sources` để lưu các URL admin muốn crawl.

Endpoint đề xuất:

- `GET /api/admin/crawl-sources`
- `POST /api/admin/crawl-sources`
- `PUT /api/admin/crawl-sources/{id}`
- `DELETE /api/admin/crawl-sources/{id}`
- `POST /api/admin/crawl-sources/bootstrap`

`bootstrap` làm:

1. Nếu bảng `crawl_sources` rỗng, đọc `crawler/urls.json`.
2. Import mỗi URL thành một row.
3. Nếu bảng đã có data, không tự ghi đè; chỉ return summary.

Crawler production:

1. Query `crawl_sources` với `enabled=true`.
2. Có thể filter theo `source_profile`, `category`, `document_type`.
3. Crawl đúng danh sách URL này.
4. Không gọi auto-discovery.

## 6. Knowledge Builder Tab

Gom `Crawl & Ingest` và `Agent Crawler` vào một tab.

Tên đề xuất:

- `Knowledge Builder`

### 6.1 Layout

Màn hình gồm 4 vùng:

1. Source Selection
   - Website chính
   - Platform
   - Platform PDF policies
   - Overview generated docs

2. Crawl & Clean
   - `Crawl Main Site -> Markdown`
   - `Agent Crawl Platform/PDF -> Markdown`
   - Chọn source crawl
   - Include Platform PDF policies
   - Generate overview docs
   - Chỉ ghi/cập nhật file trong `data/`, không đụng Postgres/Qdrant

3. Knowledge Operations
   - `Clear ALL Knowledge`
   - `Ingest ALL From data/`
   - Hai nút độc lập, không gọi lẫn nhau

4. Logs & Summary
   - URL crawled from registry
   - Documents saved
   - Overview docs generated
   - Chunks deleted/inserted
   - Qdrant points deleted/upserted

### 6.2 UX quan trọng

Hai nút crawl:

- `Crawl Main Site -> Markdown`
- `Agent Crawl Platform/PDF -> Markdown`

Text giải thích:

- "Crawler chỉ sinh tài liệu Markdown trong data/. Crawler không clear và không ingest knowledge."

Hai nút knowledge:

- `Clear ALL Knowledge`
- `Ingest ALL From data/`

Text giải thích:

- `Clear ALL Knowledge`: "Xóa toàn bộ knowledge đã index trong Postgres/Qdrant. Không xóa file trong data/."
- `Ingest ALL From data/`: "Nạp toàn bộ file hiện có trong data/ vào Postgres/Qdrant. Không clear ngầm."

Luồng khuyến nghị hiển thị trên UI:

1. Crawl để cập nhật Markdown.
2. Clear ALL Knowledge.
3. Ingest ALL From data/.

## 7. RAG Fix Cho Follow-up Và Tổng Quát

Vấn đề Green Express chỉ là một ví dụ. Gốc lỗi rộng hơn là **semantic mismatch** giữa câu hỏi đời thường và ngôn ngữ trong tài liệu:

- Người dùng hỏi bằng từ ngắn, sai chính tả, hoặc từ quen miệng: `green exress`, `phí`, `mất bao nhiêu`, `đền bù`, `hủy đơn`, `đăng ký chạy`.
- Tài liệu lại dùng từ chính thức/pháp lý/marketing: `Green Express`, `giá cước`, `phụ phí`, `bồi hoàn`, `chính sách bồi thường`, `đối tác tài xế`, `thưởng vận doanh`.
- NLU hiện chưa đủ mạnh để rewrite mọi câu hỏi thành truy vấn canonical.
- Retrieval keyword/BM25 có thể bỏ lỡ vì token không khớp, trong khi dense search có thể tìm được nhưng score không đủ tự tin.
- Prompt trả lời có xu hướng "không dám trả lời" nếu context không chứa đúng từ khóa người dùng hỏi, dù có đoạn tương đương về nghĩa.

Kết luận: không nên chỉ thêm synonym cho `phí/giá/cước`; cần một lớp **domain vocabulary + query understanding** cho toàn bộ miền Green SM.

Mục tiêu sửa:

1. Chuẩn hóa entity/service:
   - `green exress`, `xanh express`, `gsm express` -> `Green Express`.
   - `limo`, `green limo`, `greensm limo` -> `Green SM Limo`.
   - `ngon`, `food`, `giao đồ ăn` -> `Green SM Ngon/Green Food`.
2. Chuẩn hóa intent:
   - `bao nhiêu tiền`, `mất bao nhiêu`, `cước`, `phí`, `giá` -> `pricing_fee`.
   - `đền`, `bồi thường`, `bảo hiểm`, `mất hàng`, `hỏng hàng` -> `insurance_compensation`.
   - `hủy`, `cancel`, `không nhận chuyến`, `hủy đơn` -> `cancellation_policy`.
   - `đăng ký`, `tham gia`, `làm tài xế`, `chạy xe` -> `registration_onboarding`.
   - `thưởng`, `doanh thu`, `ăn chia`, `chiết khấu` -> `revenue_bonus_commission`.
3. Query expansion không chỉ thêm từ đồng nghĩa, mà thêm cả cụm canonical:
   - `phí giao hàng Green Express` -> `giá cước Green Express`, `phụ phí Green Express`, `bảng giá Green Express`.
   - `đền hàng Green Express` -> `bảo hiểm hàng hóa Xanh Express`, `bồi thường hàng hóa`, `chính sách bồi hoàn`.
4. Retrieval nên phối hợp:
   - dense semantic search,
   - BM25/sparse,
   - SQL keyword fallback,
   - metadata boost theo service/entity/intent.
5. Prompt trả lời cần phân biệt:
   - "không có thông tin" khi thật sự không có context liên quan,
   - "tài liệu không dùng đúng từ bạn hỏi, nhưng có mục tương đương..." khi context có liên quan về nghĩa.

### 7.1 Fix follow-up Green Express

Thêm normalizer:

- `green exress` -> `Green Express`
- `greensm express` -> `Green Express`
- `green sm express` -> `Green Express`
- `limo` trong ngữ cảnh Green SM -> `Green SM Limo`

Sửa NLU prompt:

- Nếu query dạng `X thì sao`, kế thừa chủ đề từ lượt trước.
- Nếu lượt trước hỏi `các loại phí liên quan đến Green Limo`, query mới `green exress thì sao` phải rewrite thành:

```text
Các loại phí, phụ phí và giá cước liên quan đến Green Express là gì?
```

### 7.2 Synonym nhóm phí

Trong query expansion:

- `phí`
- `phụ phí`
- `cước phí`
- `giá cước`
- `bảng giá`

phải được xem là cụm liên quan.

### 7.3 Retrieval cho câu hỏi tổng quát

Khi query có intent tổng quát:

- `Green SM gồm những gì`
- `danh mục Green SM`
- `Green SM cung cấp dịch vụ gì`
- `các dịch vụ của Green SM`

Retrieval nên ưu tiên:

- `document_type: overview`
- `category: overview`
- `service_catalog.md`

Có thể làm bằng:

1. Query expansion thêm:
   - `danh mục dịch vụ Green SM`
   - `service catalog Green SM`
2. Qdrant payload filter/boost nếu metadata có `document_type=overview`.
3. SQL keyword fallback ưu tiên source chứa `service_catalog`.

## 8. Tests / Debug Cases

### 8.1 Crawl output checks

Kiểm tra markdown sau Agent Crawl:

- Có frontmatter đầy đủ.
- Có đúng `#`, `##`.
- Bảng giá vẫn là Markdown table.
- Ảnh quan trọng còn giữ.
- Không còn header/footer/form rác.

### 8.2 Overview checks

Các câu cần trả lời được:

- `Green SM gồm những danh mục nào?`
- `Green SM cung cấp những dịch vụ gì?`
- `Các dịch vụ dành cho người dùng của Green SM là gì?`
- `Platform Green SM có những dòng xe nào?`

Kỳ vọng:

- Trả lời bằng danh sách/bảng.
- Có Green Car, Green SM Limo, Green Express, Green SM Bike, Green SM Food, Green Van nếu dữ liệu có.

### 8.3 Ingestion checks

1. `Clear ALL Knowledge`:
   - Xóa toàn bộ `document_chunks`.
   - Reset/clear toàn bộ Qdrant collection.
   - Không xóa bất kỳ file nào trong `data/`.
   - Chỉ chạy khi UI confirm bằng `CLEAR`.
2. `Ingest ALL From data/`:
   - Không tự clear.
   - Đọc toàn bộ file hợp lệ trong `data/`.
   - Insert chunks vào Postgres và upsert points vào Qdrant.
   - Báo số file/chunk/point và failed files.
3. Flow đầy đủ:
   - Crawl -> sinh Markdown.
   - Clear ALL.
   - Ingest ALL.
   - RAG debug query trả lời được.

### 8.4 RAG regression

Đoạn hội thoại:

1. `các loại phí liên quan đến green limo`
2. `green exress thì sao`
3. `giá cước express`

Kỳ vọng:

- Câu 2 không còn trả lời "chưa có thông tin".
- Câu 2 kéo được context Green Express pricing/fares.
- Câu 3 vẫn trả lời được bảng giá.

## 9. Thứ Tự Triển Khai

1. Tạo URL registry DB `crawl_sources` và bootstrap từ `crawler/urls.json` khi DB rỗng.
2. Cập nhật Agent Crawl output schema và prompts theo source profile.
3. Refactor crawler đọc URL từ registry, nhận `--sources main_site,platform,platform_pdf`, không tự discover.
4. Sinh overview docs, đặc biệt `service_catalog.md`.
5. Tách backend thành 2 endpoint: `clear knowledge` và `ingest all`.
6. Gom UI thành tab `Knowledge Builder` với CRUD URL registry, 2 nút crawl và 2 nút knowledge.
7. Sửa RAG normalizer, NLU follow-up và query expansion.
8. Chạy crawl thử main site + platform + platform PDF policies từ danh sách URL đã bật.
9. Clear ALL Knowledge rồi Ingest ALL From data/.
10. Test các câu tổng quát và case Green Express.

## 10. Checklist Triển Khai

### 10.1 Chuẩn hóa kiến trúc crawler

- [x] Tạo `crawler/sources.py` khai báo `main_site`, `platform`, `platform_pdf`, `overview`.
- [x] Refactor `crawler/agent_crawler.py` nhận `--sources main_site,platform,platform_pdf`.
- [x] Tách fetcher/cleaner theo source profile, không dùng một prompt chung cho mọi nguồn.
- [x] Đảm bảo hai nút crawl chỉ sinh/cập nhật file trong `data/`, không gọi clear và không gọi ingest.
- [x] Sinh crawl manifest cho mỗi lần crawl để audit URL, output path, content hash, lỗi và cảnh báo.

### 10.2 Main site cleaner

- [x] Giữ pipeline deterministic cho `https://www.greensm.com/vn-vi/`.
- [x] Loại header/nav/footer/hotline/Zalo/app download.
- [x] Loại CTA/form fields như `Đăng ký`, `Ứng tuyển ngay`, `Họ và tên`, `Email`, `Số điện thoại`, `Chọn`.
- [x] Sửa text dính trong card, ví dụ `Chia sẻ doanh thuHưởng...`.
- [x] Chuẩn hóa card/tính năng thành bullet list có nhãn rõ.
- [x] Giữ FAQ theo format `### Câu hỏi`.
- [x] Giữ bảng Markdown hợp lệ.
- [x] Không đưa cả trang dài như `helps.md` vào một LLM call.

### 10.3 Platform cleaner

- [x] Giữ Agent cleaner cho platform web pages vì DOM/card/spec/news bất quy tắc.
- [x] Tách prompt cho vehicle, news, policy page.
- [x] Với trang xe, giữ giá, specs, ảnh sản phẩm/spec quan trọng.
- [x] Loại form đăng ký tư vấn, CTA, modal, floating widget.
- [x] News listing chỉ dùng để catalog/audit, không xem là nguồn nội dung chính.
- [x] Crawl news detail `/news/<slug>` thành file riêng khi URL detail đã có trong registry.

### 10.4 URL registry và quản lý URL crawl

- [x] Xóa chế độ tự mò URL khỏi luồng production crawler.
- [x] Tạo model/bảng `crawl_sources` lưu URL, source type, category/output_dir, title, enabled, crawl strategy và metadata.
- [x] Giữ `crawler/urls.json` làm seed/bootstrap mặc định.
- [x] Thêm bootstrap: nếu DB rỗng hoặc deploy mới, import `crawler/urls.json` vào `crawl_sources`.
- [x] Bootstrap không overwrite DB đã có dữ liệu; chỉ báo summary số URL đã nạp/bỏ qua.
- [x] Thêm endpoint `GET /api/admin/crawl-sources`.
- [x] Thêm endpoint `POST /api/admin/crawl-sources`.
- [x] Thêm endpoint `PUT /api/admin/crawl-sources/{id}`.
- [x] Thêm endpoint `DELETE /api/admin/crawl-sources/{id}` hoặc soft delete bằng `enabled=false`.
- [x] Thêm endpoint `POST /api/admin/crawl-sources/bootstrap`.
- [x] Crawler chỉ đọc URL từ `crawl_sources` với `enabled=true`.
- [x] Admin tự thêm URL detail news `/news/<slug>`, URL xe, URL policy và URL PDF cần crawl.
- [x] Không để `max_urls` global cắt mất URL theo từng nhóm; dùng filter/limit theo source type nếu cần.
- [x] Manifest phải ghi rõ URL nào được lấy từ DB registry, output path, trạng thái và lỗi nếu có.

### 10.5 PDF extraction

- [x] Tạo `crawler/pdf_utils.py`.
- [x] Download PDF với validation: status 200, content-type PDF, byte size tối thiểu.
- [x] Log số page của từng PDF.
- [x] Dùng `pymupdf4llm` hoặc PyMuPDF làm parser chính.
- [x] Không dùng `pypdf.extract_text()` làm đường chính.
- [x] Extract đủ toàn bộ trang, ví dụ PDF 7 trang phải có output phản ánh đủ 7 trang.
- [x] Giữ bảng dưới dạng Markdown table nếu parser nhận được.
- [x] Nếu bảng parser chưa tốt, giữ text theo page/section, không bỏ dòng.
- [x] Không đưa toàn bộ PDF vào một LLM call.
- [x] Nếu dùng Agent cho PDF, chỉ normalize nhẹ và cấm tóm tắt mất số liệu/điều khoản.
- [x] Ghi audit cho từng PDF: bytes, page_count, raw_md_len, clean_md_len, table_count.

### 10.6 Markdown quality gate

- [x] Tạo validator kiểm tra heading rỗng `^#{1,4}\s*$`.
- [x] Check tỷ lệ CTA/form lines không vượt ngưỡng.
- [x] Check text dính phổ biến như `doanh thuHưởng`, `vayGói`.
- [x] Check frontmatter bắt buộc: `url`, `category`, `title`.
- [x] Check có ít nhất 1 H1 và 1 H2 thật.
- [x] Check bảng Markdown có separator row.
- [x] File fail validator phải được ghi cảnh báo vào manifest.
- [x] Chỉ file sạch mới được đưa vào thư mục ingest chính.

### 10.7 Overview/catalog generation

- [x] Sinh `data/overview/service_catalog.md`.
- [x] Sinh `data/overview/pricing_catalog.md`.
- [x] Sinh `data/overview/platform_vehicle_catalog.md`.
- [x] Sinh `data/overview/policy_catalog.md`.
- [x] Sinh `data/overview/news_catalog.md`.
- [x] Catalog sinh deterministic từ `urls.json`, frontmatter và manifest; không bắt LLM đọc toàn bộ site.
- [x] Đảm bảo câu "Green SM gồm những danh mục nào?" có context từ `service_catalog.md`.

### 10.8 Clear ALL và Ingest ALL

- [x] Thêm backend endpoint `POST /api/admin/knowledge/clear`.
- [x] Endpoint clear xóa toàn bộ `DocumentChunk`.
- [x] Endpoint clear reset/clear toàn bộ Qdrant collection.
- [x] Endpoint clear không xóa file trong `data/`.
- [x] Thêm backend endpoint `POST /api/admin/knowledge/ingest-all`.
- [x] Endpoint ingest-all đọc toàn bộ file hợp lệ trong `data/`.
- [x] Endpoint ingest-all không tự clear.
- [x] Return summary: files processed, chunks inserted, Qdrant points upserted, failed files.

### 10.9 Knowledge Builder UI

- [x] Gom `Crawl & Ingest` và `Agent Crawler` vào một tab `Knowledge Builder`.
- [x] Thêm bảng quản lý URL crawl: thêm/sửa/xóa/bật tắt/search.
- [x] Cho admin chọn `source_type`, `category`, `output_dir`, `crawl_strategy` khi thêm URL.
- [x] Thêm nút bootstrap từ `crawler/urls.json` khi DB rỗng hoặc admin muốn nạp seed.
- [x] Thêm nút `Crawl Main Site -> Markdown`.
- [x] Thêm nút `Agent Crawl Platform/PDF -> Markdown`.
- [x] Thêm nút `Clear ALL Knowledge`, bắt nhập `CLEAR`.
- [x] Thêm nút `Ingest ALL From data/`.
- [x] UI ghi rõ crawler không clear và không ingest.
- [x] UI ghi rõ ingest không clear ngầm.
- [x] Hiển thị logs và summary cho crawl, clear, ingest.

### 10.10 RAG retrieval fixes

- [x] Thêm normalizer alias/typo: `green exress` -> `Green Express`.
- [x] Sửa NLU prompt để follow-up kiểu `X thì sao` kế thừa chủ đề trước.
- [x] Tạo domain vocabulary cho toàn bộ Green SM, không chỉ nhóm phí/giá/cước.
- [x] Chuẩn hóa service/entity aliases: Green Express, Green SM Limo, Green SM Ngon/Food, Green Van, Green Care, Driver, Merchant, Platform.
- [x] Chuẩn hóa intent aliases: pricing_fee, insurance_compensation, cancellation_policy, registration_onboarding, revenue_bonus_commission, operating_policy, document_requirement.
- [x] Thêm synonym nhóm phí: `phí`, `phụ phí`, `cước phí`, `giá cước`, `bảng giá`.
- [x] Thêm synonym nhóm bồi thường/bảo hiểm: `đền`, `bồi thường`, `bồi hoàn`, `bảo hiểm`, `mất hàng`, `hỏng hàng`, `đổ vỡ`.
- [x] Thêm synonym nhóm đăng ký/onboarding: `đăng ký`, `tham gia`, `làm tài xế`, `chạy xe`, `đối tác`, `hồ sơ`, `giấy tờ`.
- [x] Thêm synonym nhóm vận doanh/doanh thu: `thưởng`, `doanh thu`, `ăn chia`, `chiết khấu`, `hoa hồng`, `vận doanh`.
- [x] Query rewrite phải sinh canonical query + expanded queries + metadata hints `{service, intent, category, document_type}`.
- [x] Retrieval boost theo metadata hints, ví dụ intent `insurance_compensation` ưu tiên `green-care`, `policy`, `faq`.
- [x] SQL keyword fallback nhận expanded keywords thay vì chỉ dùng nguyên query người dùng.
- [x] Prompt trả lời cho phép nói "tài liệu gọi nội dung này là ..." khi từ khóa người dùng không khớp nhưng context tương đương.
- [x] Chỉ trả lời "chưa có thông tin" khi không có context liên quan sau cả dense, sparse, SQL fallback và expanded query.
- [x] Boost/ưu tiên overview docs cho câu hỏi tổng quát.
- [x] Nâng SQL keyword fallback theo service term + pricing term.

### 10.10.1 Crawler cleanup sau refactor registry

- [x] Audit import/runtime usage của toàn bộ file trong `crawler/`.
- [x] Xác nhận file nào vẫn dùng trong production: `run_crawler.py`, `agent_crawler.py`, `registry.py`, `sources.py`, `pdf_utils.py`, `crawler.py`, `markdown_converter.py`, `storage.py`, `urls.json`.
- [x] Đánh dấu hoặc xóa file crawler cũ không còn dùng sau khi bỏ auto-discovery/Playwright, ví dụ `discovery.py` nếu không còn import.
- [x] Xóa `pdf_generator.py` nếu không còn dùng cho knowledge source, vì PDF tri thức đã đi qua `pdf_utils.py`.
- [x] Xóa `classifier.py` nếu pipeline mới không còn gọi classifier riêng hoặc chuyển logic còn dùng vào cleaner/metadata generator.
- [x] Dọn `__pycache__` trong `crawler/` khỏi repo/workspace nếu xuất hiện do compile.
- [x] Cập nhật README/PLAN nếu có file bị xóa để người sau không gọi nhầm crawler cũ.
- [x] Chạy lại `python -m py_compile` và smoke test hai nút crawl sau khi xóa file.

### 10.11 Test regression

- [x] Test crawl main site sinh Markdown không còn CTA/form rác trong các file driver/green-care.
- [x] Test bootstrap `crawler/urls.json` vào DB khi `crawl_sources` rỗng.
- [ ] Test thêm/sửa/xóa/bật tắt URL crawl trên FE admin.
- [x] Test crawler không tự discover URL mới trong production.
- [ ] Test platform news detail được crawl đủ khi URL detail đã có trong registry.
- [x] Test 4 PDF platform extract đủ page count.
- [ ] Test PDF output giữ bảng và số liệu.
- [ ] Clear ALL rồi Ingest ALL thành công.
- [ ] Query: `Green SM gồm những danh mục nào?`
- [ ] Query: `các loại phí liên quan đến green limo` -> `green exress thì sao`.
- [ ] Query: `giá cước express`.
