# Kiến Trúc Code Xanh SM Assistant

Tài liệu này là bản đồ hiện tại của codebase sau đợt dọn cấu trúc đầu tiên.
README chỉ nên giữ phần giới thiệu và cách chạy; còn phân lớp, trách nhiệm
module và hướng refactor nên xem tại file này.

## Trạng Thái Dọn Code

Đã xử lý được các điểm rối lớn:

- Tách NLU khỏi `app/rag`: classifier thật hiện nằm ở `app/nlu/classifier.py`.
- Giữ `app/rag/classifier.py` như wrapper tương thích để import cũ không gãy.
- Tách memory heuristic khỏi classifier sang `app/nlu/memory_extractor.py`.
- Tách parser/card food inline khỏi `ChatLayout.jsx` sang `frontend/src/components/chat/`.
- Tách bong bóng chat `MessageBubble.jsx` và các component vị trí bản đồ `FoodLocationPrompt.jsx` khỏi `ChatLayout.jsx`.
- Cập nhật README trỏ về tài liệu kiến trúc này.

Chưa sạch hoàn toàn, nhưng đã có đường đi rõ:

- `frontend/src/components/ChatLayout.jsx` vẫn còn: chat shell, SSE, input/mic bar và logic điều hướng chính.
- `app/api/admin/database.py` vẫn là file lớn: vừa serialize log, vừa thống kê, vừa database manager.
- `app/api/admin/knowledge.py` cũng lớn và nên tách sau.
- `app/food_recommendation/chain.py` đang là orchestrator chính của food, vẫn có thể tách nhỏ thêm khi có test/smoke ổn định.

Nguyên tắc hiện tại: không big-bang refactor. Mỗi lần chỉ tách một trách nhiệm,
giữ wrapper/import tương thích, chạy build/compile ngay.

## Cấu Trúc Tổng Quan

```text
RAG_XANH_SM/
  app/          Backend FastAPI
  crawler/      Bộ crawl dữ liệu từ nguồn đã duyệt
  data/         Dữ liệu local, gồm food catalog và tài liệu crawl
  docs/         Tài liệu kỹ thuật nội bộ
  evaluation/   Bộ test/evaluation cho RAG
  frontend/     Web app React + Vite
  mobile/       App mobile Expo / React Native
```

## Luồng Chạy Chính

```text
User gửi chat
  -> app/api/chat.py
  -> app/assistant/pipeline.py
  -> app/assistant/orchestrator.py
  -> gateway safety + cache lookup
  -> app/nlu/classifier.py
  -> rẽ nhánh theo intent
       small-talk / sensitive / missing_info -> trả lời trực tiếp
       rag -> app/rag/chain.py
       food_recommendation -> app/food_recommendation/chain.py
  -> app/memory/memory_service.py lưu message + memory candidate
  -> system logs / request logs phục vụ debug admin
```

## Backend: Từng Thư Mục Và File Chính

### `app/main.py`

Entry point FastAPI. Gắn router, CORS, static/config cơ bản và khởi động app.

### `app/api/`

Tầng HTTP boundary. Các file ở đây nên validate input, gọi service/chain, rồi
trả response. Không nên nhét business logic dài vào API.

- `chat.py`: endpoint chat/SSE chính.
- `auth.py`: đăng nhập, guest token, user auth.
- `food.py`: endpoint phụ trợ food như geocode/profile/location.
- `conversations.py`: quản lý hội thoại.
- `reviews.py`: ghi nhận đánh giá người dùng.

### `app/api/admin/`

Các endpoint cho dashboard quản trị.

- `database.py`: dashboard database/logs/stats/table browser. File này đang lớn,
  nên tách tiếp thành `serializers.py`, `logs.py`, `stats.py`, `table_browser.py`
  khi có thời gian.
- `knowledge.py`: quản lý knowledge/crawl/test retrieval. Cũng đang hơi lớn.
- `eval.py`: chạy/đọc kết quả evaluation.
- `food.py`: admin endpoint riêng cho food.
- `ml_control.py`: điều khiển thử nghiệm ML/ranker.
- `reviews.py`: admin review logs.
- `__init__.py`: gom router admin.

### `app/assistant/`

Điều phối hội thoại cấp cao.

- `orchestrator.py`: quyết định flow: safety, cache, NLU, route sang RAG/Food/direct answer.
- `pipeline.py`: nối API chat với memory service và orchestrator, lưu message sau stream.
- `events.py`: helper tạo SSE events và stream text thường.
- `system_log.py`: ghi system log từng node để debug demo.
- `trace_store.py`: helper lưu trace cấp assistant nếu cần.

Quy tắc: `assistant` chỉ điều phối, không nên biết chi tiết ranking food hay retrieval RAG.

### `app/nlu/`

Tầng hiểu ngôn ngữ trước khi rẽ nhánh.

- `classifier.py`: gọi LLM NLU, normalize JSON, quyết định intent cuối, rewrite query,
  pass-through food slots, áp memory correction trước khi trả kết quả.
- `memory_extractor.py`: rule/local heuristic cho memory: nhận diện “hãy nhớ”,
  “tôi tên là…”, thói quen, sở thích, câu hỏi recall, merge memory candidates.
- `__init__.py`: export `XanhSMClassifier` và `MemorySignalExtractor`.

Ghi chú tương thích: `app/rag/classifier.py` vẫn tồn tại như wrapper, nhưng code
mới nên import từ `app.nlu.classifier`.

### `app/rag/`

Tầng hỏi đáp tri thức Xanh SM.

- `chain.py`: luồng RAG chính: retrieval, rerank, context expansion, LLM answer, SSE.
- `gateway.py`: normalize input, safety precheck, greeting/thanks local rules.
- `cache.py`: semantic cache.
- `hybrid_search.py`: tìm kiếm dense/sparse/metadata.
- `multi_query.py`: mở rộng query.
- `reranker.py`: rerank kết quả.
- `guardrail.py`: guardrail output/logic bảo vệ.
- `trace_store.py`: lưu request log RAG.
- `domain_vocabulary.py`: từ vựng/domain hints.
- `pipeline.py`: wrapper/eval pipeline cũ nếu còn dùng.
- `classifier.py`: wrapper tương thích trỏ sang `app.nlu.classifier`.

Quy tắc: `rag` không chứa memory extraction và không chứa logic food.

### `app/food_recommendation/`

Tầng gợi ý món ăn/quán ăn.

- `chain.py`: orchestrator chính của food: nhận slot/context, resolve location,
  gọi retrieval/ranker, stream answer, ghi trace. Đây vẫn là file lớn cần tách
  sau thành location resolver / trace builder / missing-info handler.
- `answer_llm.py`: gọi Food Answer LLM và stream text thô. Backend không parse
  card cho frontend; LLM có thể nhả `[[FOOD_CARD {...}]]`.
- `schemas.py`: request/response/dataclass/schema food.
- `retrieval.py`: lấy candidate food theo catalog/query/location.
- `ranker.py`: xếp hạng candidate, category inference, fallback matching.
- `ml_ranker.py`: hook ML ranker/bandit thử nghiệm.
- `features.py`: trích feature cho ranker.
- `catalog.py`: load/normalize food catalog local.
- `geocode.py`: đổi địa chỉ sang tọa độ.
- `nlu.py`: helper chuyển NLU slots thành food slots.
- `payloads.py`: build payload/log/card fields.
- `profile.py`: normalize text/profile helper cho food.
- `profile_store.py`: đọc/ghi `UserFoodProfile`, lưu location quen thuộc.
- `trace_store.py`: lưu `FoodRequestLog`.
- `tool.py`: public tool `recommend_food()`.
- `__init__.py`: export API nội bộ.

Quy tắc card: BE stream chữ + marker `[[FOOD_CARD {...}]]`; FE chịu trách nhiệm
ẩn marker đang dở, hiện shimmer, và render card inline.

### `app/memory/`

Tầng nhớ người dùng/hội thoại.

- `memory_service.py`: lưu message, lấy recent window, extract/save memory,
  refresh `UserProfile`, sync location memory sang food profile.
- `context_builder.py`: build prompt messages cho NLU/RAG/Food từ history,
  food context và assistant memory context.
- `__init__.py`: package marker.

Quy tắc dữ liệu: `UserMemory` là nguồn sự thật. `UserProfile` chỉ là cache dẫn
xuất để prompt/debug dễ đọc hơn.

### `app/db/`

Tầng database.

- `models.py`: SQLAlchemy models: user, conversation, memories, profiles, logs,
  food logs, system logs, cache...
- `database.py`: engine/session/base.
- `migrations.py`: auto migration nhẹ cho SQLite/Postgres trong demo.

### `app/core/`

Tiện ích nền.

- `config.py`: settings/env.
- `llm.py`: chọn client/model LLM.
- `logger.py`: log console/db helper.
- `security.py`: JWT/password/auth helper.

### `app/ingestion/`

Nạp tri thức vào vector/db.

- `chunking.py`: chia chunk.
- `embedding.py`: tạo embedding.
- `ingest.py`: pipeline ingest.
- `process_images.py`: xử lý ảnh trong tài liệu nếu có.

### `app/vectordb/`

- `qdrant_client.py`: kết nối và thao tác Qdrant collection.

### `app/prompts/`

- `system_prompts.py`: prompt NLU/RAG/Food. Đây là nơi cần cực kỳ cẩn thận vì
  thay đổi prompt có thể đổi behavior demo.
- `__init__.py`: export prompt.

### `app/scripts/`

- `train_food_ranker.py`: script thử nghiệm/train ranker food.

## Frontend: Từng Phần Chính

### `frontend/src/components/ChatLayout.jsx`

Chat UI chính. Hiện vẫn lớn, đang giữ:

- layout chat;
- đọc SSE;
- render message;
- xử lý input/mic/image;
- food location prompt/map;
- gọi các component card đã tách.

Đã tách khỏi file này:

- parser food marker;
- food inline card;
- food shimmer;
- food explanation modal;
- fallback food recommendation list.

### `frontend/src/components/chat/`

Module UI nhỏ cho chat.

- `FoodInlineParts.js`: parse `[[FOOD_CARD {...}]]`, tách text/card/loading,
  tạo `foodInlineText()` và `foodInlineRecommendations()`.
- `FoodInlineCards.jsx`: `FoodRecommendationRow`, `FoodCardShimmer`,
  `FoodExplanationModal`, `FoodRecommendationList`.

Nên tách tiếp:

- `MessageBubble.jsx`: render từng bubble assistant/user.
- `FoodLocationPrompt.jsx`: form/map chọn vị trí.
- `ChatInputBar.jsx`: input, mic, image, quick actions.

### `frontend/src/api.js`

Wrapper gọi REST/SSE backend.

### `frontend/src/AuthContext.jsx`

Auth state, token, guest/user identity. Guest ổn định theo localStorage; nếu
xóa localStorage/incognito/browser khác thì sẽ sinh guest mới.

### `frontend/src/pages/`

Các trang admin/demo:

- `DatabaseManager.jsx`: xem bảng DB.
- `BasicLogView.jsx`, `RagLogView.jsx`, `FoodLogView.jsx`: xem log.
- `FoodTraceDashboard.jsx`: dashboard trace food.
- `AIEvalLab.jsx`: evaluation lab.
- `KnowledgeBuilder.jsx`, `IngestionManager.jsx`, `AgentCrawler.jsx`: quản lý knowledge/crawl.
- `CommandCenter.jsx`, `HistoryDashboard.jsx`, `MLControlCenter.jsx`: dashboard vận hành.
- `LandingPage.jsx`, `PresentationFlow/`: trang demo/presentation.

## Crawler Và Data

### `crawler/`

- `registry.py`: đọc/khởi tạo source crawl.
- `sources.py`: định nghĩa source profile.
- `crawler.py`: crawl HTML.
- `run_crawler.py`: chạy crawl deterministic.
- `agent_crawler.py`: wrapper tương thích.
- `category_cleaners.py`: clean theo loại trang.
- `pdf_utils.py`: xử lý PDF.
- `markdown_converter.py`, `markdown_quality.py`, `overview_generator.py`: chuẩn hóa markdown.
- `storage.py`: lưu dữ liệu crawl.
- `urls.json`: danh sách URL seed.

### `data/`

- `food_catalog/shopeefood_catalog.jsonl`: catalog food local.
- `food_catalog/shopeefood_crawl_metadata.json`: metadata crawl food.

### `evaluation/`

- `golden_dataset.py`, `golden_dataset.json`: bộ câu hỏi/ground truth.
- `ragas_eval.py`: script evaluation.
- `EVALUATION.md`: ghi chú evaluation.

## Quy Tắc Refactor

1. Mỗi lần chỉ tách một trách nhiệm rõ ràng.
2. Giữ import path cũ bằng wrapper nếu module từng được dùng rộng.
3. Không đổi payload API/SSE nếu không sửa FE cùng lúc.
4. Sau đổi backend chạy `python -m compileall app`.
5. Sau đổi frontend chạy `npm run build`.
6. Không trộn refactor với thay đổi behavior, trừ khi đang sửa bug đã xác định.

## Thứ Tự Dọn Tiếp

1. Tách `app/api/admin/database.py` thành serializers/logs/stats/table browser.
2. Tách `app/food_recommendation/chain.py` theo node: location, retrieval, answer, trace.
3. Chỉ cân nhắc rename `food_recommendation` sau khi có smoke test ổn định, vì
   package này đang demo-critical và có nhiều import trực tiếp.
