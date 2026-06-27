# Milestones Tái Cấu Trúc Modular AI Assistant Platform

## M0. Clean Reset Foundation

Trạng thái: in progress

- [x] Chốt `PLAN.md` cho kiến trúc Modular AI Assistant Platform.
- [x] Chốt `NEW_DB_SCHEMA.md` cho database mới.
- [x] Tạo migration clean reset schema mới.
- [x] Tạo migration seed persona/FAQ nền.
- [x] Tạo persona registry nền.
- [x] Tạo curated FAQ semantic cache skeleton.
- [x] Chạy `alembic upgrade head` trên PostgreSQL dev/demo.
- [x] Verify DB có đủ bảng mới và seed đủ 5 persona.
- [x] Cập nhật SQLAlchemy models theo schema mới.
- [x] Tách `app/db/models.py` thành package `app/db/models/` theo domain trong `PLAN.md`.

Acceptance:

- `.\venv\Scripts\alembic.exe heads` trả về revision mới nhất.
- `.\venv\Scripts\alembic.exe upgrade head` chạy pass khi PostgreSQL sẵn sàng.
- `python -m compileall app` pass.

## M1. Identity, Auth, Conversation Compatibility

Mục tiêu: runtime cũ vẫn chạy được trên schema mới.

- [ ] Thay `users`/`guest_sessions` bằng `actors`/`actor_identities`.
- [x] Refactor `/api/auth/guest`, `/api/auth/google`, `/api/auth/admin-login`.
- [x] Refactor `get_current_entity()` trả về actor thay vì legacy user/guest.
- [x] Refactor `conversations` dùng `actor_id`, `persona_id`, `channel`, `status`.
- [ ] Refactor `messages` dùng `content_type`, `metadata_json`.
- [ ] Giữ response shape cũ cho frontend trong giai đoạn chuyển tiếp.

Acceptance:

- Guest login tạo actor type `guest`.
- Google/admin login tạo actor type `customer` hoặc `admin`.
- Chat tạo conversation mới với persona mặc định `customer`.
- Sidebar history vẫn đọc được hội thoại mới.

## M2. AI Brain Runtime

Mục tiêu: chuyển từ orchestrator tuyến tính sang AI Brain có persona context.

- [ ] Tạo `assistant/orchestrator/graph_runtime.py`.
- [ ] Tạo `assistant/orchestrator/intent_router.py`.
- [ ] Tạo `assistant/orchestrator/tool_executor.py`.
- [ ] Tạo `assistant/orchestrator/response_composer.py`.
- [ ] Chuẩn hóa `AssistantState`.
- [ ] Ghi `assistant_runs`, `tool_calls`, `ai_trace_events`.
- [ ] Giữ SSE response tương thích frontend.

Acceptance:

- Mỗi chat request tạo một `assistant_runs`.
- Mỗi tool call ghi `tool_calls`.
- Mỗi node quan trọng ghi `ai_trace_events`.
- Persona được truyền xuyên suốt pipeline.

## M3. Curated Semantic FAQ Cache

Mục tiêu: bỏ cache prompt user trực tiếp, chuyển sang FAQ curated hybrid cache.

- [x] Tạo `faq_candidate_analyzer.py`.
- [x] Tạo `hybrid_cache_matcher.py`.
- [x] Tạo `faq_cache.py`.
- [x] Tạo `faq_repository.py`.
- [ ] Tích hợp FAQ cache vào RAG gateway trước khi gọi full pipeline.
- [ ] Tạo `faq_candidates` sau assistant run nếu câu hỏi đủ chuẩn.
- [ ] Không cache câu hỏi realtime hoặc câu hỏi chứa dữ liệu cá nhân.
- [ ] Thêm admin/eval flow để publish FAQ.

Acceptance:

- Chỉ `faq_entries.status = published` được dùng để trả cache.
- Cache hit phải đúng persona/scope/intent/freshness.
- Prompt user không tự động vào cache.

## M4. User Context & Memory

Mục tiêu: memory chuẩn theo actor/persona/scope.

- [x] Refactor `MemoryService` dùng `memories`.
- [ ] Tạo `assistant/memory/context_builder.py`.
- [ ] Tạo `behavioral_memory.py`.
- [ ] Tạo profile snapshot refresh sang `profile_snapshots`.
- [ ] Hỗ trợ memory lifecycle: `active`, `superseded`, `deleted`, `expired`.
- [ ] Hỗ trợ lệnh quên/sửa memory.

Acceptance:

- Context builder lấy đúng recent turns + summary + scoped memories.
- Memory persona này không leak sang persona khác.
- Behavioral memory có confidence/evidence, không dùng như fact tuyệt đối.

## M5. Domain Modules & Tools

Mục tiêu: tách logic nghiệp vụ khỏi API và orchestrator.

- [ ] Tạo `domains/rag`.
- [ ] Tạo `domains/food`.
- [ ] Tạo `domains/ride`.
- [ ] Tạo `domains/driver_copilot`.
- [ ] Tạo `domains/merchant_copilot`.
- [ ] Tạo `domains/operator_copilot`.
- [ ] Tạo `domains/executive_copilot`.
- [ ] Tạo `tools/registry.py`.
- [ ] Tạo tool specs typed bằng Pydantic.

Acceptance:

- API route không chứa business logic dài.
- Persona chỉ gọi tool trong whitelist.
- Tool input/output có schema rõ.

## M6. Persona Demo Capabilities

Mục tiêu: có demo end-to-end cho 5 persona.

- [ ] Customer: RAG + food recommendation + trip/travel stub.
- [ ] Driver: trip status + charging station + demand heatmap demo.
- [ ] Merchant: revenue analysis + menu optimization + review sentiment.
- [ ] Operator: online drivers + revenue diagnostics + fraud signals.
- [ ] Executive: BI insight + voucher simulation + churn/expansion stub.

Acceptance:

- Mỗi persona có ít nhất 3 câu hỏi demo chạy được.
- Số liệu demo phải lấy từ snapshot/tool, không bịa trong prompt.

## M7. Frontend Persona Experience

Mục tiêu: frontend có trải nghiệm multi-persona rõ.

- [ ] Thêm persona switcher trong chat.
- [ ] Hiển thị persona hiện tại trong chat header.
- [ ] Tạo panels cho driver/merchant/operator/executive.
- [ ] Dùng Leaflet cho map driver/operator/customer location.
- [ ] Dùng Recharts cho KPI merchant/operator/executive.

Acceptance:

- `npm run build` pass.
- Mobile không overlap chat, map, dashboard panel.
- Persona đổi không làm mất conversation hiện tại.

## M8. Cleanup & Hardening

Mục tiêu: dọn legacy và ổn định production-like.

- [x] Xóa hoặc cô lập bảng/model legacy không còn dùng.
- [x] Tách file lớn trên 300 dòng.
- [x] Chuẩn hóa Alembic naming cho migration mới.
- [ ] Thêm smoke tests cho auth/chat/cache/memory.
- [ ] Cập nhật README/docs architecture.

Acceptance:

- `python -m compileall app` pass.
- `alembic upgrade head` pass trên DB sạch.
- `alembic downgrade -1` pass cho migration gần nhất nếu không destructive.
- Admin/demo flows quan trọng không lỗi import.
