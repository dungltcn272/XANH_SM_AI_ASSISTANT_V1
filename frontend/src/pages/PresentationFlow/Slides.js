export const PRESENTATION_SLIDES = [
  {
    id: "intro",
    title: "Kiến trúc RAG Thông minh",
    subtitle: "Tối ưu Độ Trễ - Chính Xác - An Toàn",
    strategy: "Hệ thống RAG Xanh SM không chỉ là một công cụ Search cơ bản. Nó được xây dựng với tư duy phân lớp (Multi-layer) để loại bỏ những điểm nghẽn của LLM truyền thống, ưu tiên Fast-path và Cache để đảm bảo phản hồi dưới 1 giây.",
    tech: "React Flow, Qdrant VectorDB, OpenAI Embeddings, Cohere Rerank, FastEmbed BM25.",
    benefits: "Trải nghiệm mượt mà, phản hồi lập tức. Tiết kiệm tới 80% chi phí gọi LLM.",
    focusNodes: ['user', 'normalize', 'gateway', 'cache1', 'nlu_check', 'rule_nlu', 'llm_nlu', 'vocab', 'intent', 'cache2', 'hybrid', 'rerank', 'context', 'llm', 'cachesave', 'out', 'persona', 'block', 'block2'],
    activeEdges: [],
    animatedNodes: []
  },
  {
    id: "safety",
    title: "1. Bảo Mật & Tiền Xử Lý",
    subtitle: "Input Gateway & Guardrail",
    strategy: "Trước khi query đến với NLU hay Vector DB, nó cần được 'làm sạch' và kiểm duyệt khắt khe. Chúng ta áp dụng Rule-based Guardrail ngay tại Gateway để chặn đứng mọi cuộc tấn công.",
    tech: "Normalization Regex, Keyword matching, Prompt Injection Detection.",
    benefits: "Đảm bảo an toàn tuyệt đối, hệ thống không bao giờ bị 'hack' để sinh nội dung bậy bạ. Độ trễ xác thực gần như 0ms.",
    focusNodes: ['user', 'normalize', 'gateway', 'block'],
    activeEdges: ['e-user-norm', 'e-norm-gate', 'e-gate-block', 'e-block-out'],
    animatedNodes: ['gateway', 'block']
  },
  {
    id: "early_cache",
    title: "2. Exact Cache (Lớp 1)",
    subtitle: "Bỏ qua mọi tính toán",
    strategy: "Các câu hỏi thường gặp (FAQ) được lưu tại bộ nhớ tạm. Nếu phát hiện Hit Cache ngay sau khi chuẩn hóa, hệ thống sẽ trả về đáp án ngay lập tức mà không cần đi qua mạng neural.",
    tech: "In-memory LRU Cache / Redis, Hashing câu hỏi đã chuẩn hóa.",
    benefits: "Latency giảm từ ~2s xuống còn <10ms. Chịu tải hàng ngàn truy vấn cùng lúc mà không tốn chi phí OpenAI.",
    focusNodes: ['gateway', 'cache1', 'out'],
    activeEdges: ['e-gate-cache1', 'e-cache1-out'],
    animatedNodes: ['cache1']
  },
  {
    id: "nlu_fast_path",
    title: "3. NLU Fast-Path",
    subtitle: "Tư duy Định tuyến Thông minh",
    strategy: "Thay vì dùng LLM tốn kém để phân tích ý định cho MỌI câu hỏi, chúng ta dùng bộ quy tắc (Regex/Rules) siêu nhẹ để nhận diện các câu hỏi tra cứu chính sách rõ ràng.",
    tech: "Rule-based Intent Classifier, Regex Pattern Matching.",
    benefits: "Với các luồng Fast-path, tiết kiệm hoàn toàn độ trễ 1-2s của LLM NLU, đồng thời độ chính xác phân loại đạt 100%.",
    focusNodes: ['cache1', 'nlu_check', 'rule_nlu', 'llm_nlu', 'vocab'],
    activeEdges: ['e-cache1-nlucheck', 'e-nlucheck-rulenlu', 'e-rulenlu-vocab'],
    animatedNodes: ['nlu_check', 'rule_nlu']
  },
  {
    id: "semantic_cache",
    title: "4. Semantic Cache (Lớp 2)",
    subtitle: "Bắt lỗi sai chính tả",
    strategy: "Nếu người dùng gõ sai ngữ pháp, NLU sẽ viết lại câu. Cấu trúc câu mới được tra vào bộ nhớ Cache lớp 2. Tránh việc gọi Database vô ích.",
    tech: "Bộ từ điển nội bộ (Domain Vocabulary), Tra cứu Cache dựa trên Canonical Query.",
    benefits: "Tăng tỷ lệ trúng Cache thêm 30%, xử lý linh hoạt mọi kiểu ngôn ngữ chat của tài xế.",
    focusNodes: ['vocab', 'intent', 'cache2', 'out'],
    activeEdges: ['e-vocab-intent', 'e-intent-cache2', 'e-cache2-out'],
    animatedNodes: ['cache2']
  },
  {
    id: "hybrid_search",
    title: "5. Cốt Lõi: Hybrid Search",
    subtitle: "Dense + Sparse RRF",
    strategy: "Vector Search truyền thống dễ bỏ sót các mã số (VD: VF8). BM25 truyền thống lại không hiểu ngữ nghĩa. Chúng ta kết hợp cả 2 và hợp nhất bằng điểm số RRF, chạy song song để đạt tốc độ tối đa.",
    tech: "Qdrant Native Hybrid Search, OpenAI text-embedding-3-small (Dense), FastEmbed (Sparse BM25), RRF Fusion.",
    benefits: "Mang lại kết quả tìm kiếm với độ phủ (Recall) cực cao, không bỏ sót bất cứ tài liệu chính sách hay mã xe nào.",
    focusNodes: ['cache2', 'hybrid', 'rerank'],
    activeEdges: ['e-cache2-hybrid', 'e-hybrid-rerank'],
    animatedNodes: ['hybrid']
  },
  {
    id: "rerank_context",
    title: "6. Tái Xếp Hạng & Mở Rộng",
    subtitle: "Tối ưu Context LLM",
    strategy: "25 kết quả từ Hybrid là quá nhiều nhiễu. Cohere sẽ chấm điểm lại (Rerank) để lấy ra Top 10 tinh túy nhất. Sau đó, thuật toán Parent-Child tự động ghép nối các chunk lân cận để giữ nguyên văn bản gốc.",
    tech: "Cohere Cross-Encoder Reranker, Qdrant Scroll API (Parent-Child Expansion).",
    benefits: "Cung cấp cho LLM bức tranh toàn cảnh (không bị cắt vụn), giúp LLM tổng hợp đáp án chính xác tuyệt đối, giảm ảo giác (Hallucination).",
    focusNodes: ['rerank', 'context', 'llm'],
    activeEdges: ['e-rerank-context', 'e-context-llm'],
    animatedNodes: ['rerank', 'context']
  },
  {
    id: "llm_synthesis",
    title: "7. Tổng Hợp & Streaming",
    subtitle: "Tốc Độ Phản Hồi Tức Thì",
    strategy: "Sử dụng LLM thế hệ mới để tổng hợp thông tin, định dạng đẹp mắt theo Markdown và truyền trực tiếp từng ký tự về UI (Streaming).",
    tech: "Server-Sent Events (SSE), Prompt Engineering, LLM JSON/Markdown Synthesis.",
    benefits: "Người dùng không phải chờ đợi 5-10s để có đáp án hoàn chỉnh. Trải nghiệm mượt mà như đang chat với người thật.",
    focusNodes: ['context', 'llm', 'cachesave', 'out'],
    activeEdges: ['e-context-llm', 'e-llm-cachesave', 'e-cachesave-out'],
    animatedNodes: ['llm', 'out']
  }
];
