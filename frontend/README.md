# Xanh SM AI - Frontend

Đây là thư mục chứa mã nguồn giao diện cho Hệ thống Trợ lý Ảo RAG (Retrieval-Augmented Generation) của Xanh SM, được xây dựng trên React + Vite.

## Cấu trúc Hệ thống và Chiến thuật AI
Toàn bộ sơ đồ kiến trúc hệ thống (Gateway, Intent Classification, Strategy Search) và các lý giải về chiến thuật RAG nâng cao đã được dời ra tài liệu chung của dự án.

Vui lòng tham khảo tài liệu chi tiết tại: **[`PIPELINE.md`](../docs/PIPELINE.md)**

Sơ đồ luồng xử lý tổng quát (đã cập nhật bước nạp User Context):

```mermaid
graph TD
    A([User Input]) --> N[Normalize Input]
    N --> B{Input Gateway Safety}
    B -- "Prompt injection / secret leak" --> Block[Refusal Response]
    B -- "Safe" --> C{Early Exact Cache}

    C -- "Cache Hit (~5ms)" --> Out([Stream Answer + Citations])
    C -- "Cache Miss" --> LC[Load User Context: Memory & Profile]
    LC --> D[Unified LLM NLU Orchestrator]
    
    D --> E{Intent Classification}
    E -- "small-talk" --> Stalk[Return NLU suggested_answer]
    E -- "sensitive" --> Sen[Return NLU suggested_answer]
    E -- "missing_info" --> Miss[Ask clarification from NLU suggested_answer]
    E -- "rag" --> F{Second Exact Cache}
    E -- "food_recommendation" --> M{Missing info?}

    %% Luồng Food Recommendation
    M -- yes --> FORM[Answer + ui_form/map payload]
    M -- no --> FR1[Geocode & Target Coordinates]
    FR1 --> FR2[Geo-BM25 Hybrid Retrieval]
    FR2 --> FR3[ML-Ready Candidate Ranker]
    FR3 --> FR4[Food Answer LLM]
    FR4 --> CARD[Food cards UI + advice]
    CARD --> LOG[Interaction + trace log]
    LOG --> Out

    %% Luồng RAG
    F -- "Cache Hit" --> Out
    F -- "Cache Miss" --> G[Hybrid Retrieval: Dense + Sparse]
    G --> H[Cohere Reranker]
    H --> I[Parent / Section Context Expansion]
    I --> K[LLM Synthesis & SSE Stream]
    K --> CacheSave[Save Semantic Cache]
    CacheSave --> Out

    Block --> Out
    Stalk --> Out
    Sen --> Out
    Miss --> Out
    FORM --> Out

    style A fill:#00A651,stroke:#fff,color:#fff
    style Out fill:#00A651,stroke:#fff,color:#fff
    style Block fill:#ff4444,stroke:#fff,color:#fff
    style Stalk fill:#f59e0b,stroke:#fff,color:#fff
    style Sen fill:#f43f5e,stroke:#fff,color:#fff
    style Miss fill:#f59e0b,stroke:#fff,color:#fff
    style B fill:#f43f5e,stroke:#fff,color:#fff
    style FR1 fill:#0ea5e9,stroke:#fff,color:#fff
    style FR2 fill:#0ea5e9,stroke:#fff,color:#fff
    style FR3 fill:#0ea5e9,stroke:#fff,color:#fff
    style FR4 fill:#0ea5e9,stroke:#fff,color:#fff
    style CARD fill:#0ea5e9,stroke:#fff,color:#fff
    style LC fill:#a855f7,stroke:#fff,color:#fff
```

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
