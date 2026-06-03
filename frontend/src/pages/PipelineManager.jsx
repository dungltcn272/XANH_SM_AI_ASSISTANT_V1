import { useState } from 'react';
import { 
  ArrowDown, Shield, Brain, Search, Zap, Layers, Cpu, Sparkles, MessageSquare, AlertTriangle, PlayCircle
} from 'lucide-react';

export default function PipelineManager() {
  const [activeNode, setActiveNode] = useState(null);

  const NODES = {
    user_input: {
      title: "1. User Input (Yêu cầu đầu vào)",
      desc: "Người dùng gửi câu hỏi truy vấn đến trợ lý ảo Xanh SM. Hệ thống tiếp nhận câu hỏi dưới dạng văn bản thô qua API.",
      details: "Hỗ trợ các câu hỏi đơn, câu hỏi ghép, câu hỏi có ý đồ xấu hoặc câu hỏi thông tin thông thường.",
      icon: PlayCircle,
      color: "border-[#00c897] text-[#00c897] shadow-[0_0_15px_rgba(0,200,151,0.15)]",
      status: "Đang hoạt động"
    },
    gateway: {
      title: "2. API Gateway & Guardrails",
      desc: "Chốt chặn bảo mật đầu tiên. Kiểm tra quyền truy cập (Token), giới hạn tần suất (Rate Limiter) và quét Guardrails an toàn nội dung.",
      details: "Tự động phát hiện và ngăn chặn các hành vi tấn công Prompt Injection, Jailbreak hoặc ngôn từ vi phạm quy tắc ứng xử.",
      icon: Shield,
      color: "border-blue-500 text-blue-400 shadow-[0_0_15px_rgba(59,130,246,0.15)]",
      status: "Đang hoạt động"
    },
    block_violation: {
      title: "Chặn nội dung vi phạm",
      desc: "Nếu Guardrail phát hiện câu hỏi vi phạm chính sách an toàn, hệ thống sẽ dừng pipeline ngay lập tức và đưa ra phản hồi cảnh báo.",
      details: "Từ chối trả lời trực tiếp: 'Yêu cầu của bạn không thể xử lý do vi phạm chính sách an toàn...'",
      icon: AlertTriangle,
      color: "border-red-500 text-red-400 shadow-[0_0_15px_rgba(239,68,68,0.15)]",
      status: "Chặn dòng"
    },
    nlu_intent: {
      title: "3. Intent Classifier & Slot Filling",
      desc: "Bộ phân loại ý định sử dụng NLU. Xác định câu hỏi thuộc nhóm: Small-talk, Hỏi đáp cước phí cơ bản, hay Câu hỏi nghiệp vụ phức tạp.",
      details: "Tự động trích xuất các Slots quan trọng (ví dụ: tỉnh thành = 'Nam Định', dịch vụ = 'Limo Green') phục vụ định tuyến và tìm kiếm.",
      icon: Brain,
      color: "border-indigo-500 text-indigo-400 shadow-[0_0_15px_rgba(99,102,241,0.15)]",
      status: "Đang hoạt động"
    },
    task_agent: {
      title: "Task Agent (Phản hồi nhanh)",
      desc: "Định tuyến phản hồi siêu tốc đối với các câu hỏi Small-talk hoặc cước phí/dịch vụ đơn giản đã được định nghĩa sẵn.",
      details: "Trả về câu trả lời trực tiếp mà không cần đi qua quy trình RAG truy vấn cơ sở dữ liệu. Độ trễ cực thấp (< 0.3s).",
      icon: Zap,
      color: "border-amber-500 text-amber-400 shadow-[0_0_15px_rgba(245,158,11,0.15)]",
      status: "Đang hoạt động"
    },
    query_expansion: {
      title: "4. Query Expansion & Rewrite",
      desc: "Cải tiến câu hỏi nghiệp vụ. Sửa lỗi chính tả, chuẩn hóa từ viết tắt và viết lại câu hỏi rõ ràng hơn. Tách câu ghép thành các truy vấn đơn.",
      details: "Giúp tối ưu hóa độ khớp (Recall) khi truy vấn trên Cơ sở dữ liệu tri thức bằng cách tạo ra các truy vấn bổ sung phù hợp.",
      icon: Cpu,
      color: "border-purple-500 text-purple-400 shadow-[0_0_15px_rgba(168,85,247,0.15)]",
      status: "Đang hoạt động"
    },
    hybrid_search: {
      title: "5. Hybrid Search & Retrieval",
      desc: "Tìm kiếm tài liệu kép. Thực hiện truy vấn song song trên Qdrant Vector Search (Dense) và BM25 Search (Sparse).",
      details: "Kết hợp kết quả tìm kiếm thông qua thuật toán RRF (Reciprocal Rank Fusion) để có được top 10 tài liệu có độ tương đồng cao nhất.",
      icon: Search,
      color: "border-cyan-500 text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.15)]",
      status: "Đang hoạt động"
    },
    reranker: {
      title: "6. Cohere Reranker",
      desc: "Tái xếp hạng tài liệu. Sử dụng mô hình Cross-Encoder để đánh giá chính xác mức độ liên quan thực tế giữa câu hỏi và các tài liệu.",
      details: "Lọc bỏ tài liệu nhiễu và đẩy các tài liệu chứa câu trả lời chuẩn xác nhất lên hàng đầu.",
      icon: Layers,
      color: "border-pink-500 text-pink-400 shadow-[0_0_15px_rgba(236,72,153,0.15)]",
      status: "Đang hoạt động"
    },
    context_expansion: {
      title: "7. Parent-Child Expansion",
      desc: "Mở rộng ngữ cảnh thông minh. Nếu một tài liệu đạt điểm Rerank >= 0.7, hệ thống tự động tải thêm các chunk lân cận cùng Parent ID.",
      details: "Gộp các chunk con lại thành ngữ cảnh lớn hoàn chỉnh, giúp LLM có đầy đủ thông tin mạch lạc để trả lời các câu hỏi phức tạp.",
      icon: Layers,
      color: "border-teal-500 text-teal-400 shadow-[0_0_15px_rgba(20,184,166,0.15)]",
      status: "Đang hoạt động"
    },
    llm_gen: {
      title: "8. LLM Generation (Gemini)",
      desc: "Mô hình ngôn ngữ lớn (Gemini) tổng hợp câu trả lời dựa trên prompt tối ưu và ngữ cảnh mở rộng đã được cung cấp.",
      details: "Tuân thủ nghiêm ngặt System Prompt: Tuyệt đối trung thực, không bịa đặt thông tin, từ chối trả lời nếu ngữ cảnh không chứa đáp án.",
      icon: Sparkles,
      color: "border-violet-500 text-violet-400 shadow-[0_0_15px_rgba(139,92,246,0.15)]",
      status: "Đang hoạt động"
    },
    output_guardrail: {
      title: "9. Output Guardrails (Kiểm duyệt đầu ra)",
      desc: "Chốt chặn bảo mật cuối cùng. Kiểm tra câu trả lời đầu ra trước khi trả về cho khách hàng để ngăn chặn rò rỉ prompt, thông tin nhạy cảm (PII) hoặc ngôn từ không phù hợp.",
      details: "Tự động thay thế câu trả lời bằng cảnh báo nếu phát hiện vi phạm chính sách an toàn thông tin của doanh nghiệp.",
      icon: Shield,
      color: "border-rose-500 text-rose-400 shadow-[0_0_15px_rgba(244,63,94,0.15)]",
      status: "Đang hoạt động"
    },
    output: {
      title: "10. Output Response (Stream SSE)",
      desc: "Truyền phát câu trả lời dạng stream thời gian thực (SSE) trực tiếp lên UI cho người dùng.",
      details: "Ghi nhận log telemetry (độ trễ, số chunk, độ dài ngữ cảnh) để cập nhật và giám sát chất lượng hệ thống RAG.",
      icon: MessageSquare,
      color: "border-[#00c897] text-[#00c897] shadow-[0_0_15px_rgba(0,200,151,0.15)]",
      status: "Đang hoạt động"
    }
  };

  const getActiveDetails = () => {
    if (!activeNode || !NODES[activeNode]) {
      return {
        title: "Tổng quan Luồng xử lý RAG Pipeline",
        desc: "Hệ thống sử dụng mô hình NLU Gateway nâng cao kết hợp RAG thông minh (Parent-Child Expansion & Reranker) và Guardrails an toàn.",
        details: "Di chuột qua bất kỳ hộp quy trình nào trong sơ đồ để xem mô tả chi tiết, chức năng và cơ chế hoạt động của từng công đoạn.",
        icon: Brain,
        color: "border-primary text-primary",
        status: "Online"
      };
    }
    return NODES[activeNode];
  };

  const activeInfo = getActiveDetails();
  const ActiveIcon = activeInfo.icon;

  return (
    <div className="max-w-[1600px] mx-auto w-full pb-12 flex flex-col p-4 md:p-8">
      {/* CSS Animation styles inside the component */}
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes stroke-flow {
          to {
            stroke-dashoffset: -20;
          }
        }
        .flow-line {
          stroke-dasharray: 6, 4;
          animation: stroke-flow 1.2s linear infinite;
        }
        .glow-card {
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .glow-card:hover {
          transform: translateY(-2px) scale(1.02);
        }
      `}} />

      {/* Header */}
      <div className="mb-8 flex justify-between items-end shrink-0">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="inline-block w-3 h-3 rounded-full bg-primary animate-pulse shadow-[0_0_10px_#00c897]"></span>
            <span className="text-primary text-xs font-bold tracking-widest uppercase">System Telemetry & Architecture</span>
          </div>
          <h2 className="text-3xl md:text-4xl font-bold text-on-surface">Interactive Pipeline Manager</h2>
          <p className="text-lg text-on-surface-variant mt-2 max-w-2xl">
            Sơ đồ luồng xử lý RAG nâng cao thời gian thực của hệ thống Xanh SM AI.
          </p>
        </div>
      </div>

      {/* Main Container */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start">
        
        {/* Left Column: Sơ đồ Pipeline Động (8 cols) */}
        <div className="xl:col-span-8 rounded-3xl border border-outline-variant/20 dark:border-white/10 overflow-hidden flex flex-col bg-[#0b121e] p-6 md:p-8 shadow-2xl">
          <div className="flex flex-col items-center w-full space-y-0">

            {/* Node 1: User Input */}
            <div 
              className={`glow-card cursor-pointer p-2.5 rounded-lg border bg-white/5 w-48 text-center relative ${activeNode === 'user_input' ? 'border-[#00c897] bg-white/10 ring-1 ring-[#00c897]/50' : 'border-white/10'}`}
              onMouseEnter={() => setActiveNode('user_input')}
              onMouseLeave={() => setActiveNode(null)}
            >
              <div className="font-bold text-[#00c897] text-[13px] flex items-center justify-center gap-1.5">
                <PlayCircle size={14} />
                <span>User Input</span>
              </div>
              <p className="text-[10px] text-white/50 mt-0.5">Nhận câu hỏi truy vấn</p>
            </div>

            {/* Link 1 -> 2 */}
            <svg className="w-16 h-6" viewBox="0 0 64 24">
              <line x1="32" y1="0" x2="32" y2="24" stroke="#00c897" strokeWidth="2.5" className="flow-line" />
              <path d="M28 18 L32 24 L36 18" stroke="#00c897" strokeWidth="2" fill="none" />
            </svg>

            {/* Node 2: Gateway */}
            <div 
              className={`glow-card cursor-pointer p-2.5 rounded-lg border bg-white/5 w-48 text-center ${activeNode === 'gateway' ? 'border-blue-500 bg-white/10 ring-1 ring-blue-500/50' : 'border-white/10'}`}
              onMouseEnter={() => setActiveNode('gateway')}
              onMouseLeave={() => setActiveNode(null)}
            >
              <div className="font-bold text-blue-400 text-[13px] flex items-center justify-center gap-1.5">
                <Shield size={14} />
                <span>API Gateway & Guardrails</span>
              </div>
              <p className="text-[10px] text-white/50 mt-0.5">Kiểm tra bảo mật & An toàn</p>
            </div>

            {/* Link 2 -> Split (Block vs Intent) */}
            <div className="w-full flex justify-center h-8 relative max-w-[520px]">
              <svg className="w-[520px] h-8" viewBox="0 0 520 32" preserveAspectRatio="none">
                {/* Line down and left to Block */}
                <path d="M260 0 V12 H80 V32" stroke="#ef4444" strokeWidth="2.5" className="flow-line" fill="none" />
                <path d="M76 26 L80 32 L84 26" stroke="#ef4444" strokeWidth="2" fill="none" />
                
                {/* Line down and right to NLU */}
                <path d="M260 0 V12 H440 V32" stroke="#3b82f6" strokeWidth="2.5" className="flow-line" fill="none" />
                <path d="M436 26 L440 32 L444 26" stroke="#3b82f6" strokeWidth="2" fill="none" />
                
                <text x="170" y="10" fill="#ef4444" className="text-[8px] font-bold" textAnchor="middle">Từ chối (Vi phạm)</text>
                <text x="350" y="10" fill="#3b82f6" className="text-[8px] font-bold" textAnchor="middle">Hợp lệ</text>
              </svg>
            </div>

            {/* Row 3: Block vs Intent */}
            <div className="flex justify-between w-full max-w-[520px] gap-4">
              {/* Left Column: Block */}
              <div 
                className={`glow-card cursor-pointer p-2.5 rounded-lg border bg-red-950/10 w-40 text-center ${activeNode === 'block_violation' ? 'border-red-500 bg-red-950/20 ring-1 ring-red-500/50' : 'border-red-900/30'}`}
                onMouseEnter={() => setActiveNode('block_violation')}
                onMouseLeave={() => setActiveNode(null)}
              >
                <div className="font-bold text-red-400 text-[13px] flex items-center justify-center gap-1.5">
                  <AlertTriangle size={14} />
                  <span>Chặn nội dung vi phạm</span>
                </div>
                <p className="text-[10px] text-red-400/50 mt-0.5">Dừng pipeline & cảnh báo</p>
              </div>

              {/* Right Column: Intent Classifier */}
              <div 
                className={`glow-card cursor-pointer p-2.5 rounded-lg border bg-white/5 w-40 text-center ${activeNode === 'nlu_intent' ? 'border-indigo-500 bg-white/10 ring-1 ring-indigo-500/50' : 'border-white/10'}`}
                onMouseEnter={() => setActiveNode('nlu_intent')}
                onMouseLeave={() => setActiveNode(null)}
              >
                <div className="font-bold text-indigo-400 text-[13px] flex items-center justify-center gap-1.5">
                  <Brain size={14} />
                  <span>Intent Classifier & Slots</span>
                </div>
                <p className="text-[10px] text-white/50 mt-0.5">Phân tích ý định & Thực thể</p>
              </div>
            </div>

            {/* Link 3 Right -> Split (Task Agent vs Query Expansion) */}
            <div className="w-full flex justify-between w-full max-w-[520px] gap-4 relative">
              {/* Left Column: Red flow line */}
              <div className="w-40 flex justify-center">
                <svg className="w-16 h-8" viewBox="0 0 64 100" preserveAspectRatio="none">
                  <line x1="32" y1="0" x2="32" y2="100" stroke="#ef4444" strokeWidth="2.5" strokeDasharray="4 4" className="flow-line" />
                </svg>
              </div>
              {/* Right Column: Split line */}
              <div className="w-[336px] flex justify-center relative">
                <svg className="w-[336px] h-8" viewBox="0 0 336 32" preserveAspectRatio="none">
                  {/* Down and left to Task Agent */}
                  <path d="M168 0 V12 H72 V32" stroke="#f59e0b" strokeWidth="2.5" className="flow-line" fill="none" />
                  <path d="M68 26 L72 32 L76 26" stroke="#f59e0b" strokeWidth="2" fill="none" />
                  
                  {/* Down and right to Query Expansion */}
                  <path d="M168 0 V12 H264 V32" stroke="#a855f7" strokeWidth="2.5" className="flow-line" fill="none" />
                  <path d="M260 26 L264 32 L268 26" stroke="#a855f7" strokeWidth="2" fill="none" />
                  
                  <text x="110" y="10" fill="#f59e0b" className="text-[7.5px] font-bold" textAnchor="middle">Small-talk/Cước đơn</text>
                  <text x="226" y="10" fill="#a855f7" className="text-[7.5px] font-bold" textAnchor="middle">Hỏi đáp nghiệp vụ</text>
                </svg>
              </div>
            </div>

            {/* Row 4: Task Agent vs Query Expansion */}
            <div className="flex justify-between w-full max-w-[520px] gap-4">
              {/* Left Column: Red flow line */}
              <div className="w-40 flex justify-center items-center h-[60px]">
                <svg className="w-16 h-full" viewBox="0 0 64 100" preserveAspectRatio="none">
                  <line x1="32" y1="0" x2="32" y2="100" stroke="#ef4444" strokeWidth="2.5" strokeDasharray="4 4" className="flow-line" />
                </svg>
              </div>
              
              {/* Right Column: Task Agent & Query Expansion */}
              <div className="flex gap-4 w-[336px]">
                {/* Task Agent */}
                <div 
                  className={`glow-card cursor-pointer p-2.5 rounded-lg border bg-white/5 w-36 text-center ${activeNode === 'task_agent' ? 'border-amber-500 bg-white/10 ring-1 ring-amber-500/50' : 'border-white/10'}`}
                  onMouseEnter={() => setActiveNode('task_agent')}
                  onMouseLeave={() => setActiveNode(null)}
                >
                  <div className="font-bold text-amber-400 text-[13px] flex items-center justify-center gap-1.5">
                    <Zap size={14} />
                    <span>Task Agent (Fast Path)</span>
                  </div>
                  <p className="text-[10px] text-white/50 mt-0.5">Trả lời nhanh cước/smalltalk</p>
                </div>

                {/* Query Expansion */}
                <div 
                  className={`glow-card cursor-pointer p-2.5 rounded-lg border bg-white/5 w-36 text-center ${activeNode === 'query_expansion' ? 'border-purple-500 bg-white/10 ring-1 ring-purple-500/50' : 'border-white/10'}`}
                  onMouseEnter={() => setActiveNode('query_expansion')}
                  onMouseLeave={() => setActiveNode(null)}
                >
                  <div className="font-bold text-purple-400 text-[13px] flex items-center justify-center gap-1.5">
                    <Cpu size={14} />
                    <span>Query Expansion & Rewrite</span>
                  </div>
                  <p className="text-[10px] text-white/50 mt-0.5">Tối ưu hóa câu hỏi</p>
                </div>
              </div>
            </div>

            {/* RAG Main Stream starting from Query Expansion */}
            <div className="w-full flex justify-between w-full max-w-[520px] gap-4">
              {/* Left Column: Red flow line */}
              <div className="w-40 flex justify-center">
                <svg className="w-16 h-full min-h-[300px]" viewBox="0 0 64 100" preserveAspectRatio="none">
                  <line x1="32" y1="0" x2="32" y2="100" stroke="#ef4444" strokeWidth="2.5" strokeDasharray="4 4" className="flow-line" />
                </svg>
              </div>

              {/* Right Column: RAG Main Stream */}
              <div className="w-[336px] flex justify-between">
                {/* Yellow flow line under Task Agent */}
                <div className="w-36 flex justify-center">
                  <svg className="w-16 h-full min-h-[300px]" viewBox="0 0 64 100" preserveAspectRatio="none">
                    <line x1="32" y1="0" x2="32" y2="100" stroke="#f59e0b" strokeWidth="2.5" strokeDasharray="6 4" className="flow-line" />
                  </svg>
                </div>

                {/* RAG Main Stream */}
                <div className="w-36 flex flex-col items-center">
                  
                  {/* Link Query Expansion -> Hybrid Search */}
                  <svg className="w-16 h-8" viewBox="0 0 64 32">
                    <line x1="32" y1="0" x2="32" y2="32" stroke="#a855f7" strokeWidth="2.5" className="flow-line" />
                    <path d="M28 26 L32 32 L36 26" stroke="#a855f7" strokeWidth="2" fill="none" />
                  </svg>

                  {/* Node 5: Hybrid Search */}
                  <div 
                    className={`glow-card cursor-pointer p-2.5 rounded-lg border bg-white/5 w-36 text-center ${activeNode === 'hybrid_search' ? 'border-cyan-500 bg-white/10 ring-1 ring-cyan-500/50' : 'border-white/10'}`}
                    onMouseEnter={() => setActiveNode('hybrid_search')}
                    onMouseLeave={() => setActiveNode(null)}
                  >
                    <div className="font-bold text-cyan-400 text-[13px] flex items-center justify-center gap-1.5">
                      <Search size={14} />
                      <span>Hybrid Search</span>
                    </div>
                    <p className="text-[10px] text-white/50 mt-0.5">Truy vấn vector & từ khóa</p>
                  </div>

                  {/* Link Hybrid Search -> Reranker */}
                  <svg className="w-16 h-8" viewBox="0 0 64 32">
                    <line x1="32" y1="0" x2="32" y2="32" stroke="#06b6d4" strokeWidth="2.5" className="flow-line" />
                    <path d="M28 26 L32 32 L36 26" stroke="#06b6d4" strokeWidth="2" fill="none" />
                  </svg>

                  {/* Node 6: Reranker */}
                  <div 
                    className={`glow-card cursor-pointer p-2.5 rounded-lg border bg-white/5 w-36 text-center ${activeNode === 'reranker' ? 'border-pink-500 bg-white/10 ring-1 ring-pink-500/50' : 'border-white/10'}`}
                    onMouseEnter={() => setActiveNode('reranker')}
                    onMouseLeave={() => setActiveNode(null)}
                  >
                    <div className="font-bold text-pink-400 text-[13px] flex items-center justify-center gap-1.5">
                      <Layers size={14} />
                      <span>Cohere Reranker</span>
                    </div>
                    <p className="text-[10px] text-white/50 mt-0.5">Sắp xếp liên quan</p>
                  </div>

                  {/* Link Reranker -> Parent-Child Expansion */}
                  <svg className="w-16 h-8" viewBox="0 0 64 32">
                    <line x1="32" y1="0" x2="32" y2="32" stroke="#ec4799" strokeWidth="2.5" className="flow-line" />
                    <path d="M28 26 L32 32 L36 26" stroke="#ec4799" strokeWidth="2" fill="none" />
                  </svg>

                  {/* Node 7: Parent-Child Expansion */}
                  <div 
                    className={`glow-card cursor-pointer p-2.5 rounded-lg border bg-white/5 w-36 text-center ${activeNode === 'context_expansion' ? 'border-teal-500 bg-white/10 ring-1 ring-teal-500/50' : 'border-white/10'}`}
                    onMouseEnter={() => setActiveNode('context_expansion')}
                    onMouseLeave={() => setActiveNode(null)}
                  >
                    <div className="font-bold text-teal-400 text-[13px] flex items-center justify-center gap-1.5">
                      <Layers size={14} />
                      <span>Parent-Child Expansion</span>
                    </div>
                    <p className="text-[10px] text-white/50 mt-0.5">Mở rộng ngữ cảnh</p>
                  </div>

                  {/* Link Context Expansion -> LLM */}
                  <svg className="w-16 h-8" viewBox="0 0 64 32">
                    <line x1="32" y1="0" x2="32" y2="32" stroke="#14b8a6" strokeWidth="2.5" className="flow-line" />
                    <path d="M28 26 L32 32 L36 26" stroke="#14b8a6" strokeWidth="2" fill="none" />
                  </svg>

                  {/* Node 8: LLM */}
                  <div 
                    className={`glow-card cursor-pointer p-2.5 rounded-lg border bg-white/5 w-36 text-center ${activeNode === 'llm_gen' ? 'border-violet-500 bg-white/10 ring-1 ring-violet-500/50' : 'border-white/10'}`}
                    onMouseEnter={() => setActiveNode('llm_gen')}
                    onMouseLeave={() => setActiveNode(null)}
                  >
                    <div className="font-bold text-violet-400 text-[13px] flex items-center justify-center gap-1.5">
                      <Sparkles size={14} />
                      <span>LLM (Gemini)</span>
                    </div>
                    <p className="text-[10px] text-white/50 mt-0.5">Sinh câu trả lời</p>
                  </div>

                </div>
              </div>
            </div>

            {/* Merge Links back to Output */}
            <div className="w-full flex justify-center h-12 relative max-w-[520px]">
              <svg className="w-[520px] h-12" viewBox="0 0 520 48" preserveAspectRatio="none">
                {/* Flow from Block Violation (red) */}
                <path d="M80 0 V16 H260 V48" stroke="#ef4444" strokeWidth="2" strokeDasharray="4 4" className="flow-line" fill="none" />
                <path d="M256 42 L260 48 L264 42" stroke="#ef4444" strokeWidth="2" fill="none" />

                {/* Flow from Task Agent (orange) */}
                <path d="M256 0 V16 H260 V48" stroke="#f59e0b" strokeWidth="2" className="flow-line" fill="none" />
                <path d="M256 42 L260 48 L264 42" stroke="#f59e0b" strokeWidth="2" fill="none" />

                {/* Flow from LLM (purple) */}
                <path d="M448 0 V16 H260 V48" stroke="#8b5cf6" strokeWidth="2" className="flow-line" fill="none" />
                <path d="M256 42 L260 48 L264 42" stroke="#8b5cf6" strokeWidth="2" fill="none" />
              </svg>
            </div>

            {/* Node 8.5: Output Guardrail */}
            <div 
              className={`glow-card cursor-pointer p-2.5 rounded-lg border bg-white/5 w-48 text-center ${activeNode === 'output_guardrail' ? 'border-rose-500 bg-white/10 ring-1 ring-rose-500/50' : 'border-white/10'}`}
              onMouseEnter={() => setActiveNode('output_guardrail')}
              onMouseLeave={() => setActiveNode(null)}
            >
              <div className="font-bold text-rose-400 text-[13px] flex items-center justify-center gap-1.5">
                <Shield size={14} />
                <span>Output Guardrails</span>
              </div>
              <p className="text-[10px] text-white/50 mt-0.5">Kiểm duyệt an toàn đầu ra</p>
            </div>

            {/* Link 8.5 -> 9 */}
            <svg className="w-16 h-6" viewBox="0 0 64 24">
              <line x1="32" y1="0" x2="32" y2="24" stroke="#00c897" strokeWidth="2.5" className="flow-line" />
              <path d="M28 18 L32 24 L36 18" stroke="#00c897" strokeWidth="2" fill="none" />
            </svg>

            {/* Node 9: Output */}
            <div 
              className={`glow-card cursor-pointer p-2.5 rounded-lg border bg-white/5 w-48 text-center ${activeNode === 'output' ? 'border-[#00c897] bg-white/10 ring-1 ring-[#00c897]/50' : 'border-white/10'}`}
              onMouseEnter={() => setActiveNode('output')}
              onMouseLeave={() => setActiveNode(null)}
            >
              <div className="font-bold text-[#00c897] text-[13px] flex items-center justify-center gap-1.5">
                <MessageSquare size={14} />
                <span>Output Response (SSE)</span>
              </div>
              <p className="text-[10px] text-white/50 mt-0.5">Truyền phát thời gian thực</p>
            </div>

          </div>
        </div>

        {/* Right Column: Bảng Chi Tiết Quy Trình (4 cols) */}
        <div className="xl:col-span-4 sticky top-6">
          <div className="rounded-3xl border border-outline-variant/20 dark:border-white/10 bg-[#0d1527] p-6 min-h-[500px] flex flex-col justify-between shadow-2xl">
            <div>
              <div className="flex items-center gap-3 pb-4 border-b border-white/10 mb-6">
                <div className={`p-2 rounded-lg bg-white/5 ${activeInfo.color.split(' ')[1]}`}>
                  <ActiveIcon size={24} />
                </div>
                <div>
                  <span className="text-[10px] font-bold text-white/40 uppercase tracking-widest">Trạng thái: {activeInfo.status}</span>
                  <h3 className="font-bold text-white text-lg leading-tight mt-0.5">{activeInfo.title}</h3>
                </div>
              </div>
              
              <div className="space-y-4">
                <div>
                  <h4 className="text-xs font-bold text-primary uppercase tracking-widest mb-1.5">Mô tả công việc</h4>
                  <p className="text-sm text-white/80 leading-relaxed font-medium">{activeInfo.desc}</p>
                </div>

                <div>
                  <h4 className="text-xs font-bold text-secondary uppercase tracking-widest mb-1.5">Chi tiết triển khai</h4>
                  <p className="text-sm text-white/70 leading-relaxed font-normal bg-white/5 p-4 rounded-xl border border-white/5">
                    {activeInfo.details}
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-8 pt-4 border-t border-white/10 flex items-center justify-between text-xs text-white/40">
              <span>Hệ thống NLU-Gateway v1.2</span>
              <span>Xanh SM AI Lab</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
