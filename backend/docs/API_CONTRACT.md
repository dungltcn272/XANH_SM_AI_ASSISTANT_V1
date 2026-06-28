# Xanh SM Modular API Contract

Base URL:

```text
http://127.0.0.1:8000/api/v1
```

All JSON endpoints return UTF-8 JSON. Chat uses Server-Sent Events.

## Auth

### POST `/auth/guest`

Create an anonymous guest actor.

Response:

```json
{
  "access_token": "jwt",
  "token_type": "bearer",
  "guest_id": "actor_xxx",
  "type": "guest"
}
```

### POST `/auth/admin-login`

Request:

```json
{
  "username": "admin",
  "password": "admin"
}
```

Response:

```json
{
  "access_token": "jwt",
  "token_type": "bearer",
  "user_id": "actor_xxx",
  "email": "admin@system.admin",
  "name": "System Admin",
  "role": "admin",
  "type": "user"
}
```

### POST `/auth/google`

Status: `501` until the Google verification client is moved into `integrations/`.

## Personas

### GET `/personas`

Response:

```json
[
  {
    "id": "customer",
    "display_name": "Customer AI Assistant",
    "prompt_key": "customer_persona",
    "allowed_tools": ["rag", "food", "ride", "travel", "commerce", "payment_stub"],
    "memory_scopes": ["general", "food", "ride", "travel"],
    "data_scopes": ["public", "customer"],
    "requires_auth": false
  }
]
```

## Chat

### POST `/chat`

Content type: `application/json`

Request:

```json
{
  "query": "Tôi đói quá, gợi ý món gần tôi",
  "display_query": "Tôi đói quá, gợi ý món gần tôi",
  "conversation_id": null,
  "image_base64": null,
  "deep_search": false,
  "persona": "customer",
  "lat": 10.7769,
  "lng": 106.7009,
  "address": null,
  "budget_vnd": 70000
}
```

Response: `text/event-stream`

SSE events:

```text
data: {"conversation_id":"conv_xxx","run_id":"run_xxx","persona":"customer"}

data: {"step":"intent","intent":"food_recommendation","persona":"customer"}

data: Kết quả demo...

data: {"metrics":{"total_latency_ms":12.3},"tool_results":[...]}

data: [DONE]
```

Frontend rules:

- Treat JSON `data:` payloads as metadata when they contain `conversation_id`, `step`, `metrics`, or `tool_results`.
- Treat non-JSON `data:` payloads as assistant text chunks.
- Stop reading after `[DONE]`.

## Conversations

### GET `/conversations`

Response:

```json
[
  {
    "id": "conv_xxx",
    "title": null,
    "persona_id": "customer",
    "channel": "web",
    "status": "active",
    "updated_at": "2026-06-28T10:00:00+07:00"
  }
]
```

### GET `/conversations/{conversation_id}/messages`

Response:

```json
[
  {
    "id": "msg_xxx",
    "role": "assistant",
    "content": "Xin chào",
    "content_type": "text",
    "metadata": {
      "persona": "customer"
    },
    "pipeline_trace": "{\"persona\":\"customer\"}",
    "created_at": "2026-06-28T10:00:00+07:00"
  }
]
```

## Domain Endpoints

### GET `/rag/answer?q=...`

Runs the RAG pipeline against ingested policy/knowledge documents.

Query params:

```text
q=chính sách hủy chuyến là gì
top_k=25
```

Response:

```json
{
  "answer": "Câu trả lời dựa trên tài liệu...",
  "sources": [
    {
      "chunk_id": "chunk_xxx",
      "section": "Chính sách hủy chuyến",
      "document_id": "doc_xxx",
      "score": 0.91,
      "retrieval_source": "sql_bm25"
    }
  ],
  "retrieved_count": 12,
  "reranked_count": 8
}
```

### GET `/rag/answer/stream?q=...`

Streams the same RAG answer as Server-Sent Events. Use this when the UI needs token-by-token rendering.

SSE events:

```text
event: sources
data: {"sources":[...],"retrieved_count":12,"reranked_count":8}

event: token
data: Nội dung

event: token
data:  đang

event: answer
data: {"answer":"Nội dung đang...","sources":[...],"retrieved_count":12,"reranked_count":8}

event: done
data: [DONE]
```

### POST `/rag/ingest`

Ingests markdown, local markdown file path, website URL, or PDF URL. The backend performs heading-aware and table-aware chunking, then optionally upserts vectors to Qdrant.

Request with markdown:

```json
{
  "title": "Chính sách hủy chuyến",
  "markdown": "# Chính sách hủy chuyến\n\nNội dung...",
  "uri": "manual://cancel-policy",
  "category": "policy",
  "access_scope": "public",
  "document_type": "policy",
  "upsert_vectors": true
}
```

Request with URL/file:

```json
{
  "uri": "https://example.com/policy.pdf",
  "category": "policy",
  "access_scope": "public",
  "document_type": "policy",
  "upsert_vectors": true
}
```

Response:

```json
{
  "status": "ingested",
  "source_id": "ksrc_xxx",
  "document_id": "doc_xxx",
  "chunks": 24,
  "vectors": 24
}
```

### GET `/food/recommendations?q=...`

Runs food recommendation using DB `merchant_menu_items` first, with `data/food_catalog/shopeefood_catalog.jsonl` as fallback. Ranking uses keyword/BM25 match, distance, rating, review count, and budget.

Query params:

```text
q=cơm gà
lat=10.7769
lng=106.7009
address=Quận 1, TP.HCM
budget_vnd=70000
limit=8
```

Response:

```json
{
  "answer": "Mình gợi ý...",
  "items": [
    {
      "name": "Cơm gà",
      "merchant_name": "Quán A",
      "final_price": 55000,
      "distance_km": 1.2,
      "merchant_rating": 4.6,
      "score": 0.82
    }
  ],
  "context": {
    "lat": 10.7769,
    "lng": 106.7009,
    "budget_vnd": 70000
  },
  "source": "merchant_menu_items_or_jsonl"
}
```

### GET `/driver/status`

Returns driver demo status.

### GET `/driver/charging-stations`

Returns nearby charging station demo data.

### GET `/driver/demand-heatmap`

Returns demo hot zones.

### GET `/merchant/analytics`

Returns merchant revenue snapshot.

### GET `/merchant/menu-optimization`

Returns menu suggestions.

### GET `/merchant/review-sentiment`

Returns sentiment snapshot.

### GET `/operator/metrics`

Returns fleet/revenue/fraud/incident snapshot.

### GET `/executive/insights`

Returns BI, voucher simulation, churn, and expansion snapshot.

### POST `/booking`

Request:

```json
{
  "pickup": "Vinhomes Central Park",
  "dropoff": "Sân bay Tân Sơn Nhất",
  "service_type": "xanh_car",
  "confirm": true
}
```

Response:

```json
{
  "answer": "Mình đã tạo yêu cầu đặt xe...",
  "status": "requested",
  "service_type": "xanh_car",
  "trip_id": "trip_xxx",
  "route": {
    "pickup": {"label": "Vinhomes Central Park", "lat": 10.7949, "lng": 106.7219},
    "dropoff": {"label": "Sân bay Tân Sơn Nhất", "lat": 10.8188, "lng": 106.652},
    "distance_km": 10.35,
    "eta_minutes": 37.1,
    "polyline": [[10.7949, 106.7219], [10.8188, 106.652]],
    "steps": [],
    "routing_provider": "osrm"
  },
  "fare": {
    "estimated_fare_vnd": 195000,
    "currency": "VND"
  },
  "driver_match": {
    "status": "matched",
    "driver": {"name": "Nguyễn Minh", "eta_minutes": 8.8}
  }
}
```

### POST `/booking/estimate`

Request:

```json
{
  "pickup": {"address": "Vinhomes Central Park"},
  "dropoff": {"address": "Sân bay Tân Sơn Nhất"},
  "service_type": "xanh_car"
}
```

Returns the same route/fare/driver preview without changing status to `requested`.

### GET `/booking/preview?pickup=...&dropoff=...&service_type=xanh_car`

Convenience GET endpoint for quick UI previews.

### GET `/booking/fare-estimate?distance_km=5.2`

Returns estimated fare.

## Voice

### POST `/voice/session`

Request:

```json
{
  "persona": "customer",
  "language": "vi-VN"
}
```

Response:

```json
{
  "session_id": "voice_xxx",
  "persona": "customer",
  "language": "vi-VN",
  "status": "created"
}
```

## Admin

### GET `/admin/health`

Response:

```json
{
  "status": "ok",
  "service": "xanhsm-backend",
  "version": "modular-v1"
}
```
