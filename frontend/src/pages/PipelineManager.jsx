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
    output: {
      title: "9. Output Response (Stream SSE)",
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
              className={`glow-card cursor-pointer p-4 rounded-xl border bg-white/5 w-72 text-center relative ${activeNode === 'user_input' ? 'border-[#00c897] bg-white/10 ring-1 ring-[#00c897]/50' : 'border-white/10'}`}
              onMouseEnter={() => setActiveNode('user_input')}
              onMouseLeave={() => setActiveNode(null)}
            >
              <div className="font-bold text-[#00c897] flex items-center justify-center gap-2">
                <PlayCircle size={18} />
                <span>User Input</span>
              </div>
              <p className="text-xs text-white/50 mt-1">Nhận câu hỏi truy vấn</p>
            </div>

            {/* Link 1 -> 2 */}
            <svg className="w-16 h-10" viewBox="0 0 64 40">
              <path d="M32 0 V40" stroke="#00c897" strokeWidth="2.5" className="flow-line" />
              <path d="M28 32 L32 40 L36 32" stroke="#00c897" strokeWidth="2" fill="none" />
            </svg>

            {/* Node 2: Gateway */}
            <div 
              className={`glow-card cursor-pointer p-4 rounded-xl border bg-white/5 w-72 text-center ${activeNode === 'gateway' ? 'border-blue-500 bg-white/10 ring-1 ring-blue-500/50' : 'border-white/10'}`}
              onMouseEnter={() => setActiveNode('gateway')}
              onMouseLeave={() => setActiveNode(null)}
            >
              <div className="font-bold text-blue-400 flex items-center justify-center gap-2">
                <Shield size={18} />
                <span>API Gateway & Guardrails</span>
              </div>
              <p className="text-xs text-white/50 mt-1">Kiểm tra bảo mật & An toàn</p>
            </div>

            {/* Link 2 -> Split (Block vs Intent) */}
            <div className="w-full flex justify-center h-12 relative">
              <svg className="w-[360px] h-12" viewBox="0 0 360 48" preserveAspectRatio="none">
                {/* Line down and left to Block */}
                <path d="M180 0 V16 H80 V48" stroke="#ef4444" strokeWidth="2.5" className="flow-line" />
                <path d="M76 40 L80 48 L84 40" stroke="#ef4444" strokeWidth="2" fill="none" />
                
                {/* Line down and right to NLU */}
                <path d="M180 0 V16 H280 V48" stroke="#3b82f6" strokeWidth="2.5" className="flow-line" />
                <path d="M276 40 L280 48 L284 40" stroke="#3b82f6" strokeWidth="2" fill="none" />
                
                <text x="110" y="12" fill="#ef4444" className="text-[10px] font-bold" textAnchor="middle">Từ chối (Vi phạm)</text>
                <text x="250" y="12" fill="#3b82f6" className="text-[10px] font-bold" textAnchor="middle">Hợp lệ</text>
              </svg>
            </div>

            {/* Row 3: Block vs Intent */}
            <div className="flex justify-between w-full max-w-[640px] gap-6">
              {/* Left Column: Block */}
              <div 
                className={`glow-card cursor-pointer p-4 rounded-xl border bg-red-950/10 w-64 text-center ${activeNode === 'block_violation' ? 'border-red-500 bg-red-950/20 ring-1 ring-red-500/50' : 'border-red-900/30'}`}
                onMouseEnter={() => setActiveNode('block_violation')}
                onMouseLeave={() => setActiveNode(null)}
              >
                <div className="font-bold text-red-400 flex items-center justify-center gap-2">
                  <AlertTriangle size={18} />
                  <span>Chặn nội dung vi phạm</span>
                </div>
                <p className="text-xs text-red-400/50 mt-1">Dừng pipeline & cảnh báo</p>
              </div>

              {/* Right Column: Intent Classifier */}
              <div 
                className={`glow-card cursor-pointer p-4 rounded-xl border bg-white/5 w-64 text-center ${activeNode === 'nlu_intent' ? 'border-indigo-500 bg-white/10 ring-1 ring-indigo-500/50' : 'border-white/10'}`}
                onMouseEnter={() => setActiveNode('nlu_intent')}
                onMouseLeave={() => setActiveNode(null)}
              >
                <div className="font-bold text-indigo-400 flex items-center justify-center gap-2">
                  <Brain size={18} />
                  <span>Intent Classifier & Slots</span>
                </div>
                <p className="text-xs text-white/50 mt-1">Phân tích ý định & Thực thể</p>
              </div>
            </div>

            {/* Link 3 Right -> Split (Task Agent vs Query Expansion) */}
            <div className="w-full flex justify-center h-12 relative">
              {/* Invisible spacer on the left to align with Right Column */}
              <div className="w-64"></div>
              <div className="w-[320px] flex justify-center relative">
                <svg className="w-[280px] h-12" viewBox="0 0 280 48" preserveAspectRatio="none">
                  {/* Down and left to Task Agent */}
                  <path d="M140 0 V16 H50 V48" stroke="#f59e0b" strokeWidth="2.5" className="flow-line" />
                  <path d="M46 40 L50 48 L54 40" stroke="#f59e0b" strokeWidth="2" fill="none" />
                  
                  {/* Down and right to Query Expansion */}
                  <path d="M140 0 V16 H230 V48" stroke="#a855f7" strokeWidth="2.5" className="flow-line" />
                  <path d="M226 40 L230 48 L234 40" stroke="#a855f7" strokeWidth="2" fill="none" />
                  
                  <text x="75" y="12" fill="#f59e0b" className="text-[9px] font-bold" textAnchor="middle">Small-talk/Cước đơn</text>
                  <text x="205" y="12" fill="#a855f7" className="text-[9px] font-bold" textAnchor="middle">Hỏi đáp nghiệp vụ</text>
                </svg>
              </div>
            </div>

            {/* Row 4: Task Agent vs Query Expansion */}
            <div className="flex justify-end w-full max-w-[640px] gap-6">
              {/* Task Agent */}
              <div 
                className={`glow-card cursor-pointer p-4 rounded-xl border bg-white/5 w-60 text-center ${activeNode === 'task_agent' ? 'border-amber-500 bg-white/10 ring-1 ring-amber-500/50' : 'border-white/10'}`}
                onMouseEnter={() => setActiveNode('task_agent')}
                onMouseLeave={() => setActiveNode(null)}
              >
                <div className="font-bold text-amber-400 flex items-center justify-center gap-2">
                  <Zap size={18} />
                  <span>Task Agent (Fast Path)</span>
                </div>
                <p className="text-xs text-white/50 mt-1">Trả lời nhanh cước/smalltalk</p>
              </div>

              {/* Query Expansion */}
              <div 
                className={`glow-card cursor-pointer p-4 rounded-xl border bg-white/5 w-60 text-center ${activeNode === 'query_expansion' ? 'border-purple-500 bg-white/10 ring-1 ring-purple-500/50' : 'border-white/10'}`}
                onMouseEnter={() => setActiveNode('query_expansion')}
                onMouseLeave={() => setActiveNode(null)}
              >
                <div className="font-bold text-purple-400 flex items-center justify-center gap-2">
                  <Cpu size={18} />
                  <span>Query Expansion & Rewrite</span>
                </div>
                <p className="text-xs text-white/50 mt-1">Tối ưu hóa câu hỏi</p>
              </div>
            </div>

            {/* RAG Main Stream starting from Query Expansion */}
            <div className="w-full flex justify-end w-full max-w-[640px]">
              <div className="w-60 flex flex-col items-center">
                
                {/* Link Query Expansion -> Hybrid Search */}
                <svg className="w-16 h-10" viewBox="0 0 64 40">
                  <path d="M32 0 V40" stroke="#a855f7" strokeWidth="2.5" className="flow-line" />
                  <path d="M28 32 L32 40 L36 32" stroke="#a855f7" strokeWidth="2" fill="none" />
                </svg>

                {/* Node 5: Hybrid Search */}
                <div 
                  className={`glow-card cursor-pointer p-4 rounded-xl border bg-white/5 w-60 text-center ${activeNode === 'hybrid_search' ? 'border-cyan-500 bg-white/10 ring-1 ring-cyan-500/50' : 'border-white/10'}`}
                  onMouseEnter={() => setActiveNode('hybrid_search')}
                  onMouseLeave={() => setActiveNode(null)}
                >
                  <div className="font-bold text-cyan-400 flex items-center justify-center gap-2">
                    <Search size={18} />
                    <span>Hybrid Search (Qdrant & BM25)</span>
                  </div>
                  <p className="text-xs text-white/50 mt-1">Truy vấn vector & từ khóa</p>
                </div>

                {/* Link Hybrid Search -> Reranker */}
                <svg className="w-16 h-10" viewBox="0 0 64 40">
                  <path d="M32 0 V40" stroke="#06b6d4" strokeWidth="2.5" className="flow-line" />
                  <path d="M28 32 L32 40 L36 32" stroke="#06b6d4" strokeWidth="2" fill="none" />
                </svg>

                {/* Node 6: Reranker */}
                <div 
                  className={`glow-card cursor-pointer p-4 rounded-xl border bg-white/5 w-60 text-center ${activeNode === 'reranker' ? 'border-pink-500 bg-white/10 ring-1 ring-pink-500/50' : 'border-white/10'}`}
                  onMouseEnter={() => setActiveNode('reranker')}
                  onMouseLeave={() => setActiveNode(null)}
                >
                  <div className="font-bold text-pink-400 flex items-center justify-center gap-2">
                    <Layers size={18} />
                    <span>Cohere Reranker</span>
                  </div>
                  <p className="text-xs text-white/50 mt-1">Sắp xếp mức độ liên quan</p>
                </div>

                {/* Link Reranker -> Parent-Child Expansion */}
                <svg className="w-16 h-10" viewBox="0 0 64 40">
                  <path d="M32 0 V40" stroke="#ec4799" strokeWidth="2.5" className="flow-line" />
                  <path d="M28 32 L32 40 L36 32" stroke="#ec4799" strokeWidth="2" fill="none" />
                </svg>

                {/* Node 7: Parent-Child Expansion */}
                <div 
                  className={`glow-card cursor-pointer p-4 rounded-xl border bg-white/5 w-60 text-center ${activeNode === 'context_expansion' ? 'border-teal-500 bg-white/10 ring-1 ring-teal-500/50' : 'border-white/10'}`}
                  onMouseEnter={() => setActiveNode('context_expansion')}
                  onMouseLeave={() => setActiveNode(null)}
                >
                  <div className="font-bold text-teal-400 flex items-center justify-center gap-2">
                    <Layers size={18} />
                    <span>Parent-Child Expansion</span>
                  </div>
                  <p className="text-xs text-white/50 mt-1">Mở rộng ngữ cảnh & gộp chunk</p>
                </div>

                {/* Link Context Expansion -> LLM */}
                <svg className="w-16 h-10" viewBox="0 0 64 40">
                  <path d="M32 0 V40" stroke="#14b8a6" strokeWidth="2.5" className="flow-line" />
                  <path d="M28 32 L32 40 L36 32" stroke="#14b8a6" strokeWidth="2" fill="none" />
                </svg>

                {/* Node 8: LLM */}
                <div 
                  className={`glow-card cursor-pointer p-4 rounded-xl border bg-white/5 w-60 text-center ${activeNode === 'llm_gen' ? 'border-violet-500 bg-white/10 ring-1 ring-violet-500/50' : 'border-white/10'}`}
                  onMouseEnter={() => setActiveNode('llm_gen')}
                  onMouseLeave={() => setActiveNode(null)}
                >
                  <div className="font-bold text-violet-400 flex items-center justify-center gap-2">
                    <Sparkles size={18} />
                    <span>LLM Generation (Gemini)</span>
                  </div>
                  <p className="text-xs text-white/50 mt-1">Tổng hợp & sinh câu trả lời</p>
                </div>

              </div>
            </div>

            {/* Merge Links back to Output */}
            <div className="w-full flex justify-center h-16 relative">
              <svg className="w-[500px] h-16" viewBox="0 0 500 64" preserveAspectRatio="none">
                {/* Flow from Task Agent down & right to Output */}
                <path d="M125 0 V24 H250 V64" stroke="#f59e0b" strokeWidth="2" className="flow-line" fill="none" />
                <path d="M246 56 L250 64 L254 56" stroke="#f59e0b" strokeWidth="2" fill="none" />

                {/* Flow from LLM (centered at right col, which is approx at x=375) down & left to Output */}
                <path d="M375 0 V24 H250 V64" stroke="#8b5cf6" strokeWidth="2" className="flow-line" fill="none" />
                <path d="M246 56 L250 64 L254 56" stroke="#8b5cf6" strokeWidth="2" fill="none" />
              </svg>
            </div>

            {/* Node 9: Output */}
            <div 
              className={`glow-card cursor-pointer p-4 rounded-xl border bg-white/5 w-72 text-center ${activeNode === 'output' ? 'border-[#00c897] bg-white/10 ring-1 ring-[#00c897]/50' : 'border-white/10'}`}
              onMouseEnter={() => setActiveNode('output')}
              onMouseLeave={() => setActiveNode(null)}
            >
              <div className="font-bold text-[#00c897] flex items-center justify-center gap-2">
                <MessageSquare size={18} />
                <span>Output Response (SSE)</span>
              </div>
              <p className="text-xs text-white/50 mt-1">Truyền phát câu trả lời thời gian thực</p>
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
