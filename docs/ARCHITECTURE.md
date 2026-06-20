# Xanh SM Assistant Architecture

This document reflects the current backend/frontend layout after the first
folder-structure cleanup. It is the source of truth for code ownership; the
root README should stay shorter and link here.

## Current Top-Level Layout

```text
RAG_XANH_SM/
  app/                  FastAPI backend
  crawler/              Deterministic crawlers and source registry
  data/                 Local data assets, including food catalog files
  docs/                 Internal technical documentation
  evaluation/           RAG evaluation datasets and scripts
  frontend/             React + Vite web client
  mobile/               React Native / Expo client
```

## Backend Layout

```text
app/
  api/                  HTTP/SSE routes
  assistant/            Cross-capability chat orchestration
  core/                 Config, LLM clients, logging, security
  db/                   SQLAlchemy models, database session, migrations
  food_recommendation/  Food recommendation capability
  ingestion/            Document chunking, embedding, ingestion
  memory/               Conversation memory and user profile cache
  nlu/                  Intent classification, rewrite, memory candidates
  prompts/              System prompts shared by NLU/RAG/Food
  rag/                  RAG retrieval, rerank, answer synthesis, cache
  scripts/              Operational/training scripts
  vectordb/             Qdrant client
```

## Runtime Flow

```text
Chat API
  -> assistant.pipeline
  -> assistant.orchestrator
  -> gateway safety + cache check
  -> nlu.classifier
  -> route by intent
       small-talk / sensitive / missing_info -> direct streamed answer
       rag -> rag.chain
       food_recommendation -> food_recommendation.chain
  -> memory_service saves messages and memory candidates
  -> logs/traces are persisted for admin debugging
```

## Package Ownership

### `app/assistant`

Owns the conversation-level flow only:

- SSE step events and plain answer streaming.
- Gateway/cache/NLU/route order.
- Passing context to capability chains.
- System logs for major node transitions.

It should not own RAG retrieval details, food ranking details, or database
profile derivation rules.

### `app/nlu`

Owns language understanding before routing:

- Intent classification.
- Query rewriting.
- Missing information decisions.
- Food slot extraction pass-through from the NLU result.
- Memory candidate extraction and memory-recall fast paths.

`app.rag.classifier` remains as a compatibility wrapper, but new code should
import `XanhSMClassifier` from `app.nlu.classifier`.

Key files:

- `classifier.py`: LLM NLU call, result normalization, final routing-safe corrections.
- `memory_extractor.py`: local memory write/recall signals, candidate extraction,
  and memory recall answer synthesis.

### `app/rag`

Owns Xanh SM knowledge retrieval and answer generation:

- Vector/keyword retrieval.
- Query expansion helpers.
- Reranking.
- RAG answer streaming.
- RAG card parsing/sanitization.
- Semantic cache implementation.
- RAG request trace persistence.

It should not contain user memory extraction or food business logic.

### `app/food_recommendation`

Owns the food capability:

- Food slot normalization.
- Location/geocode handling.
- Candidate retrieval from the food catalog.
- Ranking and fallback behavior.
- Food answer LLM prompt and raw text streaming.
- Food trace persistence.

The backend streams normal text plus `[[FOOD_CARD {...}]]` markers. The
frontend owns parsing those markers and rendering inline loading/card states.

### `app/memory`

Owns user and conversation memory:

- Recent message window.
- Long-term memory persistence.
- Derived `UserProfile` cache.
- Syncing saved location candidates into the food profile when metadata has
  coordinates.

`UserMemory` is the source of truth. `UserProfile` is a derived cache to make
context prompts and debug views faster and easier to read.

### `app/api`

Owns HTTP boundaries:

- `chat.py`: chat stream endpoint.
- `auth.py`: user/guest auth.
- `food.py`: food profile/location helper endpoints.
- `conversations.py`: conversation CRUD.
- `admin/`: admin dashboards, logs, evaluation, knowledge tools.

Routes should validate inputs and call services/chains; they should not grow
large business rules.

### `frontend/src/components/ChatLayout.jsx`

Currently owns too many concerns:

- Chat shell.
- SSE reading.
- Food location UI.
- Inline food card marker parsing.
- Message rendering.

The next safe frontend cleanup is to extract pure helpers/components without
changing behavior:

```text
frontend/src/components/chat/
  FoodInlineParts.js       FOOD_CARD marker parser and derived text/items
  FoodInlineCards.jsx      Inline food row, explanation modal, shimmer, fallback list
  MessageBubble.jsx        Next extraction target
  LocationPrompt.jsx       Next extraction target
```

## Compatibility Rules During Refactor

1. Move one responsibility at a time.
2. Keep old import paths as wrappers until all callers are migrated.
3. Run backend compile checks after every backend move.
4. Run frontend build after every frontend extraction.
5. Keep API payloads and SSE event names stable unless the frontend is changed
   in the same step.
6. Do not mix folder moves with behavior changes unless a test catches a real
   bug.

## Next Cleanup Order

1. Keep `app/nlu` as the home of the classifier and memory-candidate extractor.
2. Extract message bubble rendering from `ChatLayout.jsx`.
3. Extract food location prompt/map UI after message rendering is isolated.
4. Split admin database/log serializers if the admin router keeps growing.
5. Consider renaming `food_recommendation` only after wrappers and tests are
   in place, because it has many direct imports and is demo-critical.
