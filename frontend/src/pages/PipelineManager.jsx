import { useState } from 'react';
import { Shield, Brain, Search, Zap, Layers, Cpu, Sparkles, MessageSquare, AlertTriangle, 
  PlayCircle, Play, ArrowRight, ArrowLeft, RotateCcw, X, Code, ExternalLink, Info, CheckCircle
} from 'lucide-react';
import { api } from '../api';

export default function PipelineManager() {
  const [activeNode, setActiveNode] = useState(null);

  // States for debugger
  const [testQuery, setTestQuery] = useState("");
  const [isDebugMode, setIsDebugMode] = useState(false);
  const [debugData, setDebugData] = useState(null);
  const [debugStepIndex, setDebugStepIndex] = useState(0);
  const [loadingDebug, setLoadingDebug] = useState(false);
  const [debugError, setDebugError] = useState("");
  const [selectedModalNode, setSelectedModalNode] = useState(null);

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

  // Determine dynamic steps based on API debugData
  const getDebugSteps = () => {
    if (!debugData) return [];
    
    // Gateway security check
    const isGatewaySafe = debugData.gateway_checked && debugData.safety_res && debugData.safety_res.safe !== false;
    const gatewayBlocked = debugData.answer && debugData.answer.includes("Cảnh báo bảo mật");
    
    if (!isGatewaySafe || gatewayBlocked) {
      return ['user_input', 'gateway', 'block_violation'];
    }
    
    const intent = debugData.intent || "rag";
    
    if (intent === 'sensitive') {
      return ['user_input', 'gateway', 'nlu_intent', 'block_violation'];
    }
    
    if (intent === 'small-talk') {
      return ['user_input', 'gateway', 'nlu_intent', 'task_agent', 'output_guardrail', 'output'];
    }
    
    // Default RAG Path
    return [
      'user_input',
      'gateway',
      'nlu_intent',
      'query_expansion',
      'hybrid_search',
      'reranker',
      'context_expansion',
      'llm_gen',
      'output_guardrail',
      'output'
    ];
  };

  const debugSteps = getDebugSteps();
  const activeDebugNode = isDebugMode && debugSteps.length > 0 ? debugSteps[debugStepIndex] : null;
  const effectiveActiveNode = activeNode || activeDebugNode;

  const getActiveDetails = () => {
    const nodeKey = effectiveActiveNode;
    if (!nodeKey || !NODES[nodeKey]) {
      return {
        title: "Tổng quan Luồng xử lý RAG Pipeline",
        desc: "Hệ thống sử dụng mô hình NLU Gateway nâng cao kết hợp RAG thông minh (Parent-Child Expansion & Reranker) và Guardrails an toàn.",
        details: "Di chuột qua bất kỳ hộp quy trình nào trong sơ đồ để xem mô tả chi tiết, chức năng và cơ chế hoạt động của từng công đoạn.",
        icon: Brain,
        color: "border-[#00c897] text-[#00c897]",
        status: "Online"
      };
    }
    return NODES[nodeKey];
  };

  const activeInfo = getActiveDetails();
  const ActiveIcon = activeInfo.icon;

  // Debug control actions
  const handleStartDebug = async (e) => {
    e.preventDefault();
    if (!testQuery.trim()) return;
    
    setLoadingDebug(true);
    setDebugError("");
    try {
      const data = await api.testPipeline(testQuery);
      setDebugData(data);
      setIsDebugMode(true);
      setDebugStepIndex(0); // Start at user_input
    } catch (err) {
      console.error(err);
      setDebugError("Không thể thực hiện chạy thử nghiệm. Vui lòng kiểm tra lại backend server.");
    } finally {
      setLoadingDebug(false);
    }
  };

  const handleNextStep = () => {
    if (debugStepIndex < debugSteps.length - 1) {
      setDebugStepIndex(prev => prev + 1);
    }
  };

  const handlePrevStep = () => {
    if (debugStepIndex > 0) {
      setDebugStepIndex(prev => prev - 1);
    }
  };

  const handleResetDebug = () => {
    setIsDebugMode(false);
    setDebugData(null);
    setDebugStepIndex(0);
    setTestQuery("");
    setDebugError("");
    setSelectedModalNode(null);
  };

  // Node classes generator
  const getNodeClass = (nodeKey, activeColorClass, baseColor) => {
    const isInspected = activeNode === nodeKey;
    const isCurrentDebug = isDebugMode && activeDebugNode === nodeKey;
    const isExecuted = isDebugMode && debugSteps.includes(nodeKey);
    const hasActiveState = isInspected || isCurrentDebug;
    
    if (isDebugMode && !isExecuted) {
      return "opacity-40 pointer-events-none border-white/5 bg-white/1 scale-95 transition-all duration-300";
    }
    
    let borderClass = "border-white/10";
    let bgClass = "bg-white/5 text-white/90";
    let shadowClass = "";
    let scaleClass = "transition-all duration-300";
    
    if (hasActiveState) {
      borderClass = activeColorClass;
      bgClass = "bg-white/10 text-white";
      scaleClass = "scale-[1.03] translate-y-[-2px] transition-all duration-300";
      
      if (baseColor === 'green') {
        shadowClass = "shadow-[0_0_20px_rgba(0,200,151,0.45)] ring-2 ring-[#00c897]/50";
      } else if (baseColor === 'blue') {
        shadowClass = "shadow-[0_0_20px_rgba(59,130,246,0.45)] ring-2 ring-blue-500/50";
      } else if (baseColor === 'red') {
        shadowClass = "shadow-[0_0_20px_rgba(239,68,68,0.45)] ring-2 ring-red-500/50";
      } else if (baseColor === 'indigo') {
        shadowClass = "shadow-[0_0_20px_rgba(99,102,241,0.45)] ring-2 ring-indigo-500/50";
      } else if (baseColor === 'amber') {
        shadowClass = "shadow-[0_0_20px_rgba(245,158,11,0.45)] ring-2 ring-amber-500/50";
      } else if (baseColor === 'purple') {
        shadowClass = "shadow-[0_0_20px_rgba(168,85,247,0.45)] ring-2 ring-purple-500/50";
      } else if (baseColor === 'cyan') {
        shadowClass = "shadow-[0_0_20px_rgba(6,182,212,0.45)] ring-2 ring-cyan-500/50";
      } else if (baseColor === 'pink') {
        shadowClass = "shadow-[0_0_20px_rgba(236,72,153,0.45)] ring-2 ring-pink-500/50";
      } else if (baseColor === 'teal') {
        shadowClass = "shadow-[0_0_20px_rgba(20,184,166,0.45)] ring-2 ring-teal-500/50";
      } else if (baseColor === 'violet') {
        shadowClass = "shadow-[0_0_20px_rgba(139,92,246,0.45)] ring-2 ring-violet-500/50";
      } else if (baseColor === 'rose') {
        shadowClass = "shadow-[0_0_20px_rgba(244,63,94,0.45)] ring-2 ring-rose-500/50";
      }
    } else if (isExecuted) {
      borderClass = activeColorClass.split(' ')[0] + "/30";
      bgClass = "bg-white/5 text-white/90";
    }
    
    return `glow-card cursor-pointer p-2.5 rounded-lg border ${borderClass} ${bgClass} ${shadowClass} ${scaleClass}`;
  };

  // Flow line opacity generator
  const getLineStyle = (relatedNodes) => {
    if (!isDebugMode) return { opacity: 1, transition: 'opacity 0.3s ease' };
    const isTraversed = relatedNodes.every(n => debugSteps.includes(n));
    return {
      opacity: isTraversed ? 1 : 0.15,
      transition: 'opacity 0.3s ease'
    };
  };

  const handleNodeClick = (nodeKey) => {
    if (!isDebugMode) {
      setSelectedModalNode(nodeKey);
    } else {
      if (debugSteps.includes(nodeKey)) {
        setSelectedModalNode(nodeKey);
      }
    }
  };

  // Node runtime details inside the modal
  const renderNodeRuntimeData = (nodeKey) => {
    if (!debugData) return null;
    
    const blockStyle = "bg-black/40 border border-white/10 rounded-xl p-4 text-sm font-mono text-white/90 overflow-x-auto whitespace-pre-wrap max-h-64 font-sans leading-relaxed";
    
    switch (nodeKey) {
      case 'user_input':
        return (
          <div className="space-y-4">
            <div>
              <span className="text-xs font-bold text-[#00c897] uppercase tracking-wider block mb-1">Dữ liệu thô nhận được từ người dùng (Query)</span>
              <div className={blockStyle}>{debugData.query}</div>
            </div>
          </div>
        );
      case 'gateway': {
        const safe = debugData.gateway_checked && (!debugData.safety_res || debugData.safety_res.safe !== false);
        return (
          <div className="space-y-4">
            <div>
              <span className="text-xs font-bold text-blue-400 uppercase tracking-wider block mb-1">Trạng thái Kiểm duyệt an toàn (Safety Status)</span>
              <div className="flex items-center gap-3">
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold ${safe ? 'bg-[#00c897]/20 text-[#00c897] border border-[#00c897]/30' : 'bg-red-500/20 text-red-400 border border-red-500/30'}`}>
                  {safe ? 'HỢP LỆ (SAFE)' : 'VI PHẠM (BLOCKED)'}
                </span>
                <span className="text-xs text-white/75">Cơ chế: Prompt Injection & Jailbreak Filter</span>
              </div>
            </div>
            <div>
              <span className="text-xs font-bold text-blue-400 uppercase tracking-wider block mb-1">Kết quả phân tích chi tiết</span>
              <div className={blockStyle}>
                {safe ? "Không phát hiện nguy cơ bảo mật. Cho phép tiếp tục xử lý." : `Phát hiện nguy hại: ${debugData.safety_res?.reason || 'Bị chặn bởi bộ lọc Gateway'}`}
              </div>
            </div>
          </div>
        );
      }
      case 'block_violation':
        return (
          <div className="space-y-4">
            <div>
              <span className="text-xs font-bold text-red-400 uppercase tracking-wider block mb-1">Câu hỏi đầu vào</span>
              <div className={blockStyle}>{debugData.query}</div>
            </div>
            <div>
              <span className="text-xs font-bold text-red-400 uppercase tracking-wider block mb-1">Thông điệp từ chối xử lý từ hệ thống</span>
              <div className="bg-red-950/20 border border-red-500/20 rounded-xl p-4 text-sm text-red-400 font-medium leading-relaxed font-sans">
                {debugData.answer}
              </div>
            </div>
          </div>
        );
      case 'nlu_intent':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider block mb-1">Phân loại Ý định (Intent)</span>
                <div className="bg-indigo-500/10 border border-indigo-500/20 rounded-xl p-3.5 text-sm text-indigo-300 font-bold capitalize">
                  {debugData.intent || 'RAG (Truy vấn nghiệp vụ)'}
                </div>
              </div>
              <div>
                <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider block mb-1">Đường truyền định tuyến</span>
                <div className="bg-white/5 border border-white/10 rounded-xl p-3.5 text-sm text-white/95 font-mono">
                  {debugData.intent === 'small-talk' ? 'Bypass RAG (Task Agent)' : 'RAG Mainstream'}
                </div>
              </div>
            </div>
            <div>
              <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider block mb-1">Lượng token tiêu thụ NLU</span>
              <div className="bg-white/5 border border-white/10 rounded-xl p-4 text-sm text-white/90">
                Prompt Tokens: <span className="text-white font-bold">{debugData.token_usage?.unified_nlu?.prompt_tokens || 0}</span> | 
                Completion Tokens: <span className="text-white font-bold">{debugData.token_usage?.unified_nlu?.completion_tokens || 0}</span>
              </div>
            </div>
          </div>
        );
      case 'task_agent':
        return (
          <div className="space-y-4">
            <div>
              <span className="text-xs font-bold text-amber-400 uppercase tracking-wider block mb-1">Câu hỏi nhận được</span>
              <div className={blockStyle}>{debugData.rewritten_query || debugData.query}</div>
            </div>
            <div>
              <span className="text-xs font-bold text-amber-400 uppercase tracking-wider block mb-1">Câu trả lời định nghĩa sẵn (Bypass RAG)</span>
              <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 text-sm text-amber-200 font-medium leading-relaxed font-sans">
                {debugData.answer}
              </div>
            </div>
          </div>
        );
      case 'query_expansion':
        return (
          <div className="space-y-4">
            <div>
              <span className="text-xs font-bold text-purple-400 uppercase tracking-wider block mb-1">Câu hỏi viết lại (Query Rewrite)</span>
              <div className={blockStyle}>{debugData.rewritten_query}</div>
            </div>
            <div>
              <span className="text-xs font-bold text-purple-400 uppercase tracking-wider block mb-2.5">Các câu hỏi mở rộng (Multi-Query Expansion)</span>
              <div className="space-y-2">
                {debugData.expanded_queries && debugData.expanded_queries.map((q, idx) => (
                  <div key={idx} className="flex gap-3 items-center bg-white/5 border border-white/5 px-4 py-3 rounded-xl text-sm text-white/80">
                    <span className="w-5 h-5 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center text-xs font-bold font-mono">{idx + 1}</span>
                    <span className="font-medium font-sans">{q}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );
      case 'hybrid_search':
        return (
          <div className="space-y-4 font-sans">
            <div className="flex justify-between items-center bg-white/5 border border-white/10 p-4 rounded-xl">
              <div>
                <span className="text-xs font-bold text-cyan-400 uppercase tracking-wider block">Chiến lược tìm kiếm được chọn</span>
                <span className="text-sm text-white font-bold">{debugData.strategy_selected || 'Hybrid Search'}</span>
              </div>
              <div>
                <span className="text-xs font-bold text-cyan-400 uppercase tracking-wider block text-right">Số lượng chunk thô đã lấy</span>
                <span className="text-sm text-white font-bold text-right block">25 candidate chunks (Dense + Sparse)</span>
              </div>
            </div>
            
            <div>
              <span className="text-xs font-bold text-cyan-400 uppercase tracking-wider block mb-2">Danh sách chunk thô ban đầu (Trước Rerank)</span>
              <div className="overflow-x-auto border border-white/10 rounded-xl max-h-72 overflow-y-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-white/10 text-white font-bold uppercase tracking-wider border-b border-white/10">
                      <th className="p-3 w-10 text-center">STT</th>
                      <th className="p-3 w-36">Nguồn File</th>
                      <th className="p-3 w-40">Phần / Điều</th>
                      <th className="p-3 w-20 text-center">Điểm RRF</th>
                      <th className="p-3">Nội dung</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 text-white/90 font-sans">
                    {debugData.raw_candidates && debugData.raw_candidates.map((c, idx) => (
                      <tr key={idx} className="hover:bg-white/5 transition-colors">
                        <td className="p-3 text-center font-bold text-cyan-400">{idx + 1}</td>
                        <td className="p-3 font-mono truncate max-w-[110px]" title={c.source}>{c.source}</td>
                        <td className="p-3 font-medium truncate max-w-[130px]" title={c.section}>{c.section}</td>
                        <td className="p-3 text-center font-mono text-cyan-300 font-bold">{(c.score || 0.0).toFixed(4)}</td>
                        <td className="p-3 max-w-[320px] truncate" title={c.content}>{c.content}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        );
      case 'reranker':
        return (
          <div className="space-y-4 font-sans">
            <div className="bg-white/5 border border-white/10 p-4 rounded-xl">
              <span className="text-xs font-bold text-pink-400 uppercase tracking-wider block mb-1">Mô hình Cohere Rerank sử dụng</span>
              <span className="text-sm text-white font-bold block">cohere-rerank-multilingual-v3.0 (Cross-Encoder)</span>
              <span className="text-xs text-white/75 mt-1 block">Tái sắp xếp độ tương đồng giữa câu hỏi và 25 chunks thô để chọn ra top 10 chunks liên quan tốt nhất.</span>
            </div>

            <div>
              <span className="text-xs font-bold text-pink-400 uppercase tracking-wider block mb-2">Top 10 Chunks sau khi Rerank</span>
              <div className="overflow-x-auto border border-white/10 rounded-xl max-h-72 overflow-y-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-white/10 text-white font-bold uppercase tracking-wider border-b border-white/10">
                      <th className="p-3 w-10 text-center">STT</th>
                      <th className="p-3 w-36">Nguồn File</th>
                      <th className="p-3 w-40">Phần / Điều</th>
                      <th className="p-3 w-20 text-center">Điểm Rerank</th>
                      <th className="p-3">Nội dung</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 text-white/90 font-sans">
                    {debugData.reranked_docs && debugData.reranked_docs.map((c, idx) => {
                      const isHigh = c.score >= 0.7;
                      return (
                        <tr key={idx} className="hover:bg-white/5 transition-colors">
                          <td className="p-3 text-center font-bold text-pink-400">{idx + 1}</td>
                          <td className="p-3 font-mono truncate max-w-[110px]" title={c.source}>{c.source}</td>
                          <td className="p-3 font-medium truncate max-w-[130px]" title={c.section}>{c.section}</td>
                          <td className={`p-3 text-center font-mono font-bold ${isHigh ? 'text-[#00c897]' : 'text-yellow-400'}`}>
                            {(c.score || 0.0).toFixed(4)}
                          </td>
                          <td className="p-3 max-w-[320px] truncate" title={c.content}>{c.content}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        );
      case 'context_expansion':
        return (
          <div className="space-y-4 font-sans">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white/5 border border-white/10 p-4 rounded-xl">
                <span className="text-xs font-bold text-teal-400 uppercase tracking-wider block">Ngưỡng điểm để Expand Parent</span>
                <span className="text-sm text-[#00c897] font-bold block mt-1">{"Score >= 0.70"}</span>
              </div>
              <div className="bg-white/5 border border-white/10 p-4 rounded-xl">
                <span className="text-xs font-bold text-teal-400 uppercase tracking-wider block">Độ dài ngữ cảnh đã nén</span>
                <span className="text-sm text-white font-bold block mt-1">{debugData.compressed_context_len || 0} ký tự</span>
              </div>
            </div>

            <div>
              <span className="text-xs font-bold text-teal-400 uppercase tracking-wider block mb-2">Danh sách Context sau khi mở rộng Parent-Child</span>
              <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
                {debugData.expanded_docs && debugData.expanded_docs.map((doc, idx) => {
                  const hasParent = !!doc.parent_chunk_id;
                  return (
                    <div key={idx} className="bg-white/5 border border-white/5 p-4 rounded-xl">
                      <div className="flex justify-between items-center mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-teal-400">Context #{idx + 1}</span>
                          <span className="text-[10px] text-white/60">| {doc.source} - {doc.section}</span>
                        </div>
                        {hasParent && (
                          <span className="px-2 py-0.5 bg-teal-500/10 border border-teal-500/20 text-teal-400 text-[9px] font-bold rounded-md font-sans">
                            Parent Expanded
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-white/90 whitespace-pre-wrap bg-black/20 p-2.5 rounded-lg border border-white/5 max-h-24 overflow-y-auto leading-relaxed">
                        {doc.content}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        );
      case 'llm_gen':
        return (
          <div className="space-y-4 font-sans">
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-white/5 border border-white/10 p-3 rounded-xl text-center">
                <span className="text-xs font-bold text-violet-400 uppercase tracking-wider block">Model</span>
                <span className="text-sm text-white font-bold block mt-0.5">GPT-4o-mini</span>
              </div>
              <div className="bg-white/5 border border-white/10 p-3 rounded-xl text-center">
                <span className="text-xs font-bold text-violet-400 uppercase tracking-wider block">Token Tiêu Thụ</span>
                <span className="text-sm text-white font-bold block mt-0.5">
                  {(debugData.token_usage?.generation?.prompt_tokens || 0) + (debugData.token_usage?.generation?.completion_tokens || 0)}
                </span>
              </div>
              <div className="bg-white/5 border border-white/10 p-3 rounded-xl text-center">
                <span className="text-xs font-bold text-violet-400 uppercase tracking-wider block">Chi phí API</span>
                <span className="text-sm text-[#00c897] font-bold block mt-0.5">
                  {debugData.llm_cost_usd ? `${debugData.llm_cost_usd.toFixed(5)} USD` : '0.00 USD'}
                  <span className="text-white/60 text-[10px] font-normal block mt-0.5">
                    (~{Math.round(debugData.llm_cost_vnd || 0)} VNĐ)
                  </span>
                </span>
              </div>
            </div>

            <div>
              <span className="text-xs font-bold text-violet-400 uppercase tracking-wider block mb-1">Nội dung câu trả lời do LLM sinh ra</span>
              <div className="bg-violet-950/10 border border-violet-500/20 rounded-xl p-4 text-sm text-white font-medium leading-relaxed max-h-52 overflow-y-auto whitespace-pre-wrap font-sans">
                {debugData.answer}
              </div>
            </div>
            
            <div>
              <span className="text-xs font-bold text-violet-400 uppercase tracking-wider block mb-1">Token Phân Tích</span>
              <div className="text-xs text-white/75 bg-white/5 border border-white/5 p-3 rounded-xl flex justify-around">
                <span>Prompt Tokens: <strong className="text-white">{debugData.token_usage?.generation?.prompt_tokens || 0}</strong></span>
                <span>Completion Tokens: <strong className="text-white">{debugData.token_usage?.generation?.completion_tokens || 0}</strong></span>
              </div>
            </div>
          </div>
        );
      case 'output_guardrail': {
        const guardrailPassed = debugData.output_guardrail_passed !== false;
        return (
          <div className="space-y-4 font-sans">
            <div>
              <span className="text-xs font-bold text-rose-400 uppercase tracking-wider block mb-1">Trạng thái Kiểm duyệt đầu ra (Output Guardrail)</span>
              <div className="flex items-center gap-3">
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold ${guardrailPassed ? 'bg-[#00c897]/20 text-[#00c897] border border-[#00c897]/30' : 'bg-red-500/20 text-red-400 border border-red-500/30'}`}>
                  {guardrailPassed ? 'ĐẠT (PASSED)' : 'BỊ CHẶN (BLOCKED)'}
                </span>
                <span className="text-xs text-white/75">Cơ chế: Kiểm tra PII, rò rỉ prompt & ngôn từ nhạy cảm</span>
              </div>
            </div>
            <div>
              <span className="text-xs font-bold text-rose-400 uppercase tracking-wider block mb-1">Câu trả lời sau kiểm duyệt</span>
              <div className={blockStyle}>
                {guardrailPassed ? debugData.answer : "Nội dung vi phạm chính sách an toàn đầu ra của Xanh SM."}
              </div>
            </div>
          </div>
        );
      }
      case 'output':
        return (
          <div className="space-y-4 font-sans">
            <div>
              <span className="text-xs font-bold text-[#00c897] uppercase tracking-wider block mb-1">Câu trả lời truyền về Chatbox (SSE stream)</span>
              <div className="bg-[#00c897]/5 border border-[#00c897]/20 rounded-xl p-4 text-sm text-white font-medium leading-relaxed max-h-48 overflow-y-auto whitespace-pre-wrap font-sans">
                {debugData.answer}
              </div>
            </div>

            <div>
              <span className="text-xs font-bold text-[#00c897] uppercase tracking-wider block mb-2">Các tài liệu trích dẫn nguồn (Citations)</span>
              <div className="space-y-2 max-h-44 overflow-y-auto pr-1">
                {debugData.citations && debugData.citations.length > 0 ? (
                  debugData.citations.map((c, idx) => (
                    <div key={idx} className="bg-white/5 border border-white/5 p-3 rounded-xl flex justify-between items-center text-xs">
                      <div>
                        <div className="font-bold text-white flex items-center gap-1.5">
                          <span>{c.source}</span>
                          <span className="text-[10px] text-white/60 font-normal">| {c.section}</span>
                        </div>
                        {c.url && (
                          <a href={c.url} target="_blank" rel="noreferrer" className="text-primary hover:underline flex items-center gap-1 mt-1 text-[10px] inline-flex items-center">
                            Xem tài liệu gốc <ExternalLink size={10} />
                          </a>
                        )}
                      </div>
                      <div className="text-right">
                        <span className="text-[10px] text-white/60 block">Độ tương đồng</span>
                        <span className="font-bold text-[#00c897] font-mono">{(c.relevance_score || 0.0).toFixed(4)}</span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-white/60 text-xs text-center py-4 bg-white/5 border border-dashed border-white/10 rounded-xl">
                    Không có nguồn trích dẫn.
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

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
      <div className="mb-6 flex justify-between items-end shrink-0">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="inline-block w-3 h-3 rounded-full bg-primary animate-pulse shadow-[0_0_10px_#00c897]"></span>
            <span className="text-primary text-xs font-bold tracking-widest uppercase">System Telemetry & Architecture</span>
          </div>
          <h2 className="text-3xl md:text-4xl font-bold text-on-surface">Interactive Pipeline Manager</h2>
          <p className="text-base text-on-surface-variant mt-2 max-w-2xl">
            Sơ đồ luồng xử lý nâng cao và hệ thống chạy debug kiểm thử từng bước (Node Debugger) của Xanh SM AI.
          </p>
        </div>
      </div>

      {/* RAG Pipeline Debugger Panel */}
      <div className="bg-[#070c18] border border-white/10 rounded-3xl p-6 mb-8 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-blue-500/5 rounded-full blur-3xl pointer-events-none"></div>
        
        <form onSubmit={handleStartDebug} className="flex flex-col md:flex-row gap-4 items-end relative z-10">
          <div className="flex-1 w-full">
            <label className="block text-xs font-bold text-[#00c897] uppercase tracking-wider mb-2">Nhập câu hỏi thử nghiệm</label>
            <input 
              type="text" 
              value={testQuery}
              onChange={(e) => setTestQuery(e.target.value)}
              disabled={loadingDebug}
              placeholder="Ví dụ: Phí hủy chuyến xe VF 8 là bao nhiêu? / xin chào chatbot..."
              className="w-full bg-white/10 border border-white/20 focus:border-[#00c897]/50 text-white placeholder-white/40 rounded-xl px-4 py-3 text-sm focus:outline-none transition-all"
            />
          </div>
          
          <button 
            type="submit"
            disabled={loadingDebug || !testQuery.trim()}
            className={`w-full md:w-auto flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-bold text-sm transition-all duration-300 ${
              loadingDebug 
                ? 'bg-white/10 text-white/75 cursor-not-allowed'
                : 'bg-[#00c897] hover:bg-[#00b084] text-[#090e17] shadow-[0_0_15px_rgba(0,200,151,0.25)] hover:shadow-[0_0_20px_rgba(0,200,151,0.4)] hover:scale-[1.02]'
            }`}
          >
            {loadingDebug ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                <span>Đang xử lý RAG...</span>
              </>
            ) : (
              <>
                <Play size={15} fill="currentColor" />
                <span>Chạy từng bước</span>
              </>
            )}
          </button>
        </form>

        {debugError && (
          <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl text-xs flex items-center gap-2">
            <AlertTriangle size={14} />
            <span>{debugError}</span>
          </div>
        )}

        {/* Debug stepping controls */}
        {isDebugMode && debugData && (
          <div className="mt-6 pt-6 border-t border-white/10 flex flex-col sm:flex-row justify-between items-center gap-4 relative z-10">
            <div className="flex items-center gap-3">
              <span className="px-3 py-1 bg-[#00c897]/20 border border-[#00c897]/30 text-[#00c897] text-xs font-bold rounded-full">
                Debug Session Active
              </span>
              <span className="text-xs text-white/90 font-sans">
                Bước <strong className="text-white font-mono">{debugStepIndex + 1}/{debugSteps.length}</strong>:{" "}
                <span className="font-bold text-[#00c897] font-sans">{NODES[debugSteps[debugStepIndex]]?.title.replace(/^\d+\.\s*/, '')}</span>
              </span>
            </div>
            
            <div className="flex items-center gap-2.5">
              <button 
                onClick={handlePrevStep}
                disabled={debugStepIndex === 0}
                className="flex items-center gap-1.5 px-3 py-2 bg-white/5 hover:bg-white/10 disabled:opacity-40 disabled:hover:bg-white/5 border border-white/10 rounded-lg text-xs font-bold text-white transition-colors"
              >
                <ArrowLeft size={13} />
                <span>Quay lại</span>
              </button>
              
              <button 
                onClick={handleNextStep}
                disabled={debugStepIndex === debugSteps.length - 1}
                className="flex items-center gap-1.5 px-3 py-2 bg-[#00c897] text-[#090e17] hover:bg-[#00b084] disabled:bg-white/10 disabled:text-white/60 border border-white/5 rounded-lg text-xs font-bold transition-colors"
              >
                <span>Tiếp theo</span>
                <ArrowRight size={13} />
              </button>

              <button 
                onClick={handleResetDebug}
                className="flex items-center gap-1.5 px-3 py-2 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 rounded-lg text-xs font-bold text-red-400 transition-colors"
              >
                <RotateCcw size={13} />
                <span>Đặt lại</span>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Main Container */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start">
        
        {/* Left Column: Sơ đồ Pipeline Động (8 cols) */}
        <div className="xl:col-span-8 rounded-3xl border border-outline-variant/20 dark:border-white/10 overflow-hidden flex flex-col bg-[#0b121e] p-6 md:p-8 shadow-2xl relative">
          
          {isDebugMode && (
            <div className="absolute top-4 right-4 flex items-center gap-1.5 text-[10px] text-[#00c897] bg-[#00c897]/5 border border-[#00c897]/20 px-2.5 py-1 rounded-md font-sans">
              <Info size={10} />
              <span>Click vào node được kích hoạt để xem chi tiết Runtime dữ liệu</span>
            </div>
          )}

          <div className="flex flex-col items-center w-full space-y-0">

            {/* Node 1: User Input */}
            <div 
              onClick={() => handleNodeClick('user_input')}
              className={getNodeClass('user_input', 'border-[#00c897] bg-white/10', 'green') + " w-48 text-center"}
              onMouseEnter={() => !isDebugMode && setActiveNode('user_input')}
              onMouseLeave={() => !isDebugMode && setActiveNode(null)}
            >
              <div className="font-bold text-[#00c897] text-[13px] flex items-center justify-center gap-1.5">
                <PlayCircle size={14} />
                <span>User Input</span>
              </div>
              <p className="text-[10px] text-white/75 mt-0.5">Nhận câu hỏi truy vấn</p>
            </div>

            {/* Link 1 -> 2 */}
            <svg className="w-16 h-6" viewBox="0 0 64 24" style={getLineStyle(['user_input', 'gateway'])}>
              <line x1="32" y1="0" x2="32" y2="24" stroke="#00c897" strokeWidth="2.5" className="flow-line" />
              <path d="M28 18 L32 24 L36 18" stroke="#00c897" strokeWidth="2" fill="none" />
            </svg>

            {/* Node 2: Gateway */}
            <div 
              onClick={() => handleNodeClick('gateway')}
              className={getNodeClass('gateway', 'border-blue-500 bg-white/10', 'blue') + " w-48 text-center"}
              onMouseEnter={() => !isDebugMode && setActiveNode('gateway')}
              onMouseLeave={() => !isDebugMode && setActiveNode(null)}
            >
              <div className="font-bold text-blue-400 text-[13px] flex items-center justify-center gap-1.5">
                <Shield size={14} />
                <span>API Gateway & Guardrails</span>
              </div>
              <p className="text-[10px] text-white/75 mt-0.5">Kiểm tra bảo mật & An toàn</p>
            </div>

            {/* Link 2 -> Split (Block vs Intent) */}
            <div className="w-full flex justify-center h-8 relative max-w-[520px]">
              <svg className="w-[520px] h-8" viewBox="0 0 520 32" preserveAspectRatio="none">
                {/* Line down and left to Block */}
                <path 
                  d="M260 0 V12 H80 V32" 
                  stroke="#ef4444" 
                  strokeWidth="2.5" 
                  className="flow-line" 
                  fill="none" 
                  style={getLineStyle(['gateway', 'block_violation'])}
                />
                <path 
                  d="M76 26 L80 32 L84 26" 
                  stroke="#ef4444" 
                  strokeWidth="2" 
                  fill="none" 
                  style={getLineStyle(['gateway', 'block_violation'])}
                />
                
                {/* Line down and right to NLU */}
                <path 
                  d="M260 0 V12 H440 V32" 
                  stroke="#3b82f6" 
                  strokeWidth="2.5" 
                  className="flow-line" 
                  fill="none" 
                  style={getLineStyle(['gateway', 'nlu_intent'])}
                />
                <path 
                  d="M436 26 L440 32 L444 26" 
                  stroke="#3b82f6" 
                  strokeWidth="2" 
                  fill="none" 
                  style={getLineStyle(['gateway', 'nlu_intent'])}
                />
                
                <text x="170" y="10" fill="#ef4444" className="text-[8px] font-bold" textAnchor="middle" style={getLineStyle(['gateway', 'block_violation'])}>Từ chối (Vi phạm)</text>
                <text x="350" y="10" fill="#3b82f6" className="text-[8px] font-bold" textAnchor="middle" style={getLineStyle(['gateway', 'nlu_intent'])}>Hợp lệ</text>
              </svg>
            </div>

            {/* Row 3: Block vs Intent */}
            <div className="flex justify-between w-full max-w-[520px] gap-4">
              {/* Left Column: Block */}
              <div 
                onClick={() => handleNodeClick('block_violation')}
                className={getNodeClass('block_violation', 'border-red-500 bg-red-950/20', 'red') + " w-40 text-center"}
                onMouseEnter={() => !isDebugMode && setActiveNode('block_violation')}
                onMouseLeave={() => !isDebugMode && setActiveNode(null)}
              >
                <div className="font-bold text-red-400 text-[13px] flex items-center justify-center gap-1.5">
                  <AlertTriangle size={14} />
                  <span>Chặn nội dung vi phạm</span>
                </div>
                <p className="text-[10px] text-red-400/50 mt-0.5">Dừng pipeline & cảnh báo</p>
              </div>

              {/* Right Column: Intent Classifier */}
              <div 
                onClick={() => handleNodeClick('nlu_intent')}
                className={getNodeClass('nlu_intent', 'border-indigo-500 bg-white/10', 'indigo') + " w-40 text-center"}
                onMouseEnter={() => !isDebugMode && setActiveNode('nlu_intent')}
                onMouseLeave={() => !isDebugMode && setActiveNode(null)}
              >
                <div className="font-bold text-indigo-400 text-[13px] flex items-center justify-center gap-1.5">
                  <Brain size={14} />
                  <span>Intent Classifier & Slots</span>
                </div>
                <p className="text-[10px] text-white/75 mt-0.5">Phân tích ý định & Thực thể</p>
              </div>
            </div>

            {/* Link 3 Right -> Split (Task Agent vs Query Expansion) */}
            <div className="w-full flex justify-between w-full max-w-[520px] gap-4 relative">
              {/* Left Column: Red flow line */}
              <div className="w-40 flex justify-center">
                <svg className="w-16 h-8" viewBox="0 0 64 100" preserveAspectRatio="none" style={getLineStyle(['block_violation'])}>
                  <line x1="32" y1="0" x2="32" y2="100" stroke="#ef4444" strokeWidth="2.5" strokeDasharray="4 4" className="flow-line" />
                </svg>
              </div>
              {/* Right Column: Split line */}
              <div className="w-[336px] flex justify-center relative">
                <svg className="w-[336px] h-8" viewBox="0 0 336 32" preserveAspectRatio="none">
                  {/* Down and left to Task Agent */}
                  <path 
                    d="M168 0 V12 H72 V32" 
                    stroke="#f59e0b" 
                    strokeWidth="2.5" 
                    className="flow-line" 
                    fill="none" 
                    style={getLineStyle(['nlu_intent', 'task_agent'])}
                  />
                  <path 
                    d="M68 26 L72 32 L76 26" 
                    stroke="#f59e0b" 
                    strokeWidth="2" 
                    fill="none" 
                    style={getLineStyle(['nlu_intent', 'task_agent'])}
                  />
                  
                  {/* Down and right to Query Expansion */}
                  <path 
                    d="M168 0 V12 H264 V32" 
                    stroke="#a855f7" 
                    strokeWidth="2.5" 
                    className="flow-line" 
                    fill="none" 
                    style={getLineStyle(['nlu_intent', 'query_expansion'])}
                  />
                  <path 
                    d="M260 26 L264 32 L268 26" 
                    stroke="#a855f7" 
                    strokeWidth="2" 
                    fill="none" 
                    style={getLineStyle(['nlu_intent', 'query_expansion'])}
                  />
                  
                  <text x="110" y="10" fill="#f59e0b" className="text-[7.5px] font-bold" textAnchor="middle" style={getLineStyle(['nlu_intent', 'task_agent'])}>Small-talk/Cước đơn</text>
                  <text x="226" y="10" fill="#a855f7" className="text-[7.5px] font-bold" textAnchor="middle" style={getLineStyle(['nlu_intent', 'query_expansion'])}>Hỏi đáp nghiệp vụ</text>
                </svg>
              </div>
            </div>

            {/* Row 4: Task Agent vs Query Expansion */}
            <div className="flex justify-between w-full max-w-[520px] gap-4">
              {/* Left Column: Red flow line */}
              <div className="w-40 flex justify-center items-center h-[60px]">
                <svg className="w-16 h-full" viewBox="0 0 64 100" preserveAspectRatio="none" style={getLineStyle(['block_violation'])}>
                  <line x1="32" y1="0" x2="32" y2="100" stroke="#ef4444" strokeWidth="2.5" strokeDasharray="4 4" className="flow-line" />
                </svg>
              </div>
              
              {/* Right Column: Task Agent & Query Expansion */}
              <div className="flex gap-4 w-[336px]">
                {/* Task Agent */}
                <div 
                  onClick={() => handleNodeClick('task_agent')}
                  className={getNodeClass('task_agent', 'border-amber-500 bg-white/10', 'amber') + " w-36 text-center"}
                  onMouseEnter={() => !isDebugMode && setActiveNode('task_agent')}
                  onMouseLeave={() => !isDebugMode && setActiveNode(null)}
                >
                  <div className="font-bold text-amber-400 text-[13px] flex items-center justify-center gap-1.5">
                    <Zap size={14} />
                    <span>Task Agent (Fast)</span>
                  </div>
                  <p className="text-[10px] text-white/75 mt-0.5">Trả lời nhanh cước/smalltalk</p>
                </div>

                {/* Query Expansion */}
                <div 
                  onClick={() => handleNodeClick('query_expansion')}
                  className={getNodeClass('query_expansion', 'border-purple-500 bg-white/10', 'purple') + " w-36 text-center"}
                  onMouseEnter={() => !isDebugMode && setActiveNode('query_expansion')}
                  onMouseLeave={() => !isDebugMode && setActiveNode(null)}
                >
                  <div className="font-bold text-purple-400 text-[13px] flex items-center justify-center gap-1.5">
                    <Cpu size={14} />
                    <span>Query Expand & Rewrite</span>
                  </div>
                  <p className="text-[10px] text-white/75 mt-0.5">Tối ưu hóa câu hỏi</p>
                </div>
              </div>
            </div>

            {/* RAG Main Stream starting from Query Expansion */}
            <div className="w-full flex justify-between w-full max-w-[520px] gap-4">
              {/* Left Column: Red flow line */}
              <div className="w-40 flex justify-center">
                <svg className="w-16 h-full min-h-[300px]" viewBox="0 0 64 100" preserveAspectRatio="none" style={getLineStyle(['block_violation'])}>
                  <line x1="32" y1="0" x2="32" y2="100" stroke="#ef4444" strokeWidth="2.5" strokeDasharray="4 4" className="flow-line" />
                </svg>
              </div>

              {/* Right Column: RAG Main Stream */}
              <div className="w-[336px] flex justify-between">
                {/* Yellow flow line under Task Agent */}
                <div className="w-36 flex justify-center">
                  <svg className="w-16 h-full min-h-[300px]" viewBox="0 0 64 100" preserveAspectRatio="none" style={getLineStyle(['task_agent'])}>
                    <line x1="32" y1="0" x2="32" y2="100" stroke="#f59e0b" strokeWidth="2.5" strokeDasharray="6 4" className="flow-line" />
                  </svg>
                </div>

                {/* RAG Main Stream */}
                <div className="w-36 flex flex-col items-center">
                  
                  {/* Link Query Expansion -> Hybrid Search */}
                  <svg className="w-16 h-8" viewBox="0 0 64 32" style={getLineStyle(['query_expansion', 'hybrid_search'])}>
                    <line x1="32" y1="0" x2="32" y2="32" stroke="#a855f7" strokeWidth="2.5" className="flow-line" />
                    <path d="M28 26 L32 32 L36 26" stroke="#a855f7" strokeWidth="2" fill="none" />
                  </svg>

                  {/* Node 5: Hybrid Search */}
                  <div 
                    onClick={() => handleNodeClick('hybrid_search')}
                    className={getNodeClass('hybrid_search', 'border-cyan-500 bg-white/10', 'cyan') + " w-36 text-center"}
                    onMouseEnter={() => !isDebugMode && setActiveNode('hybrid_search')}
                    onMouseLeave={() => !isDebugMode && setActiveNode(null)}
                  >
                    <div className="font-bold text-cyan-400 text-[13px] flex items-center justify-center gap-1.5">
                      <Search size={14} />
                      <span>Hybrid Search</span>
                    </div>
                    <p className="text-[10px] text-white/75 mt-0.5">Truy vấn vector & BM25</p>
                  </div>

                  {/* Link Hybrid Search -> Reranker */}
                  <svg className="w-16 h-8" viewBox="0 0 64 32" style={getLineStyle(['hybrid_search', 'reranker'])}>
                    <line x1="32" y1="0" x2="32" y2="32" stroke="#06b6d4" strokeWidth="2.5" className="flow-line" />
                    <path d="M28 26 L32 32 L36 26" stroke="#06b6d4" strokeWidth="2" fill="none" />
                  </svg>

                  {/* Node 6: Reranker */}
                  <div 
                    onClick={() => handleNodeClick('reranker')}
                    className={getNodeClass('reranker', 'border-pink-500 bg-white/10', 'pink') + " w-36 text-center"}
                    onMouseEnter={() => !isDebugMode && setActiveNode('reranker')}
                    onMouseLeave={() => !isDebugMode && setActiveNode(null)}
                  >
                    <div className="font-bold text-pink-400 text-[13px] flex items-center justify-center gap-1.5">
                      <Layers size={14} />
                      <span>Cohere Reranker</span>
                    </div>
                    <p className="text-[10px] text-white/75 mt-0.5">Sắp xếp liên quan</p>
                  </div>

                  {/* Link Reranker -> Parent-Child Expansion */}
                  <svg className="w-16 h-8" viewBox="0 0 64 32" style={getLineStyle(['reranker', 'context_expansion'])}>
                    <line x1="32" y1="0" x2="32" y2="32" stroke="#ec4799" strokeWidth="2.5" className="flow-line" />
                    <path d="M28 26 L32 32 L36 26" stroke="#ec4799" strokeWidth="2" fill="none" />
                  </svg>

                  {/* Node 7: Parent-Child Expansion */}
                  <div 
                    onClick={() => handleNodeClick('context_expansion')}
                    className={getNodeClass('context_expansion', 'border-teal-500 bg-white/10', 'teal') + " w-36 text-center"}
                    onMouseEnter={() => !isDebugMode && setActiveNode('context_expansion')}
                    onMouseLeave={() => !isDebugMode && setActiveNode(null)}
                  >
                    <div className="font-bold text-teal-400 text-[13px] flex items-center justify-center gap-1.5">
                      <Layers size={14} />
                      <span>Parent-Child</span>
                    </div>
                    <p className="text-[10px] text-white/75 mt-0.5">Mở rộng ngữ cảnh</p>
                  </div>

                  {/* Link Context Expansion -> LLM */}
                  <svg className="w-16 h-8" viewBox="0 0 64 32" style={getLineStyle(['context_expansion', 'llm_gen'])}>
                    <line x1="32" y1="0" x2="32" y2="32" stroke="#14b8a6" strokeWidth="2.5" className="flow-line" />
                    <path d="M28 26 L32 32 L36 26" stroke="#14b8a6" strokeWidth="2" fill="none" />
                  </svg>

                  {/* Node 8: LLM */}
                  <div 
                    onClick={() => handleNodeClick('llm_gen')}
                    className={getNodeClass('llm_gen', 'border-violet-500 bg-white/10', 'violet') + " w-36 text-center"}
                    onMouseEnter={() => !isDebugMode && setActiveNode('llm_gen')}
                    onMouseLeave={() => !isDebugMode && setActiveNode(null)}
                  >
                    <div className="font-bold text-violet-400 text-[13px] flex items-center justify-center gap-1.5">
                      <Sparkles size={14} />
                      <span>LLM (Gemini)</span>
                    </div>
                    <p className="text-[10px] text-white/75 mt-0.5">Sinh câu trả lời</p>
                  </div>

                </div>
              </div>
            </div>

            {/* Merge Links back to Output */}
            <div className="w-full flex justify-center h-12 relative max-w-[520px]">
              <svg className="w-[520px] h-12" viewBox="0 0 520 48" preserveAspectRatio="none">
                {/* Flow from Block Violation (red) */}
                <path 
                  d="M80 0 V16 H260 V48" 
                  stroke="#ef4444" 
                  strokeWidth="2" 
                  strokeDasharray="4 4" 
                  className="flow-line" 
                  fill="none" 
                  style={getLineStyle(['block_violation', 'output_guardrail'])}
                />
                <path d="M256 42 L260 48 L264 42" stroke="#ef4444" strokeWidth="2" fill="none" style={getLineStyle(['block_violation', 'output_guardrail'])} />

                {/* Flow from Task Agent (orange) */}
                <path 
                  d="M256 0 V16 H260 V48" 
                  stroke="#f59e0b" 
                  strokeWidth="2" 
                  className="flow-line" 
                  fill="none" 
                  style={getLineStyle(['task_agent', 'output_guardrail'])}
                />
                <path d="M256 42 L260 48 L264 42" stroke="#f59e0b" strokeWidth="2" fill="none" style={getLineStyle(['task_agent', 'output_guardrail'])} />

                {/* Flow from LLM (purple) */}
                <path 
                  d="M448 0 V16 H260 V48" 
                  stroke="#8b5cf6" 
                  strokeWidth="2" 
                  className="flow-line" 
                  fill="none" 
                  style={getLineStyle(['llm_gen', 'output_guardrail'])}
                />
                <path d="M256 42 L260 48 L264 42" stroke="#8b5cf6" strokeWidth="2" fill="none" style={getLineStyle(['llm_gen', 'output_guardrail'])} />
              </svg>
            </div>

            {/* Node 8.5: Output Guardrail */}
            <div 
              onClick={() => handleNodeClick('output_guardrail')}
              className={getNodeClass('output_guardrail', 'border-rose-500 bg-white/10', 'rose') + " w-48 text-center"}
              onMouseEnter={() => !isDebugMode && setActiveNode('output_guardrail')}
              onMouseLeave={() => !isDebugMode && setActiveNode(null)}
            >
              <div className="font-bold text-rose-400 text-[13px] flex items-center justify-center gap-1.5">
                <Shield size={14} />
                <span>Output Guardrails</span>
              </div>
              <p className="text-[10px] text-white/75 mt-0.5">Kiểm duyệt an toàn đầu ra</p>
            </div>

            {/* Link 8.5 -> 9 */}
            <svg className="w-16 h-6" viewBox="0 0 64 24" style={getLineStyle(['output_guardrail', 'output'])}>
              <line x1="32" y1="0" x2="32" y2="24" stroke="#00c897" strokeWidth="2.5" className="flow-line" />
              <path d="M28 18 L32 24 L36 18" stroke="#00c897" strokeWidth="2" fill="none" />
            </svg>

            {/* Node 9: Output */}
            <div 
              onClick={() => handleNodeClick('output')}
              className={getNodeClass('output', 'border-[#00c897] bg-white/10', 'green') + " w-48 text-center"}
              onMouseEnter={() => !isDebugMode && setActiveNode('output')}
              onMouseLeave={() => !isDebugMode && setActiveNode(null)}
            >
              <div className="font-bold text-[#00c897] text-[13px] flex items-center justify-center gap-1.5">
                <MessageSquare size={14} />
                <span>Output Response (SSE)</span>
              </div>
              <p className="text-[10px] text-white/75 mt-0.5">Truyên phát thời gian thực</p>
            </div>

          </div>
        </div>

        {/* Right Column: Bảng Chi Tiết Quy Trình (4 cols) */}
        <div className="xl:col-span-4 sticky top-6">
          <div className="rounded-3xl border border-outline-variant/20 dark:border-white/10 bg-[#0d1527] p-6 min-h-[500px] flex flex-col justify-between shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full blur-2xl pointer-events-none"></div>
            
            <div className="relative z-10">
              <div className="flex items-center gap-3 pb-4 border-b border-white/10 mb-6">
                <div className={`p-2 rounded-lg bg-white/5 ${activeInfo.color.split(' ')[1]}`}>
                  <ActiveIcon size={24} />
                </div>
                <div>
                  <span className="text-[10px] font-bold text-white/60 uppercase tracking-widest">Trạng thái: {activeInfo.status}</span>
                  <h3 className="font-bold text-white text-lg leading-tight mt-0.5">{activeInfo.title}</h3>
                </div>
              </div>
              
              <div className="space-y-5">
                <div>
                  <h4 className="text-xs font-bold text-[#00c897] uppercase tracking-widest mb-1.5">Mô tả công việc</h4>
                  <p className="text-sm text-white/80 leading-relaxed font-medium font-sans">{activeInfo.desc}</p>
                </div>

                <div>
                  <h4 className="text-xs font-bold text-secondary uppercase tracking-widest mb-1.5">Chi tiết triển khai</h4>
                  <p className="text-sm text-white/90 leading-relaxed font-normal bg-white/5 p-4 rounded-xl border border-white/5 font-sans">
                    {activeInfo.details}
                  </p>
                </div>

                {/* Direct Instruction for Debug details */}
                {isDebugMode && debugData && debugSteps.includes(effectiveActiveNode) && (
                  <div className="bg-[#00c897]/5 border border-[#00c897]/20 p-4 rounded-xl text-center">
                    <span className="text-xs font-bold text-[#00c897] block mb-1">CÓ DỮ LIỆU THỬ NGHIỆM</span>
                    <p className="text-[11px] text-white/90 mb-2">Nhấn trực tiếp vào hộp Node trên sơ đồ để mở Dialog xem chi tiết Input và Output.</p>
                    <button 
                      onClick={() => handleNodeClick(effectiveActiveNode)}
                      className="px-3 py-1.5 bg-[#00c897] text-[#090e17] rounded-lg text-xs font-bold hover:bg-[#00b084] transition-colors inline-flex items-center gap-1"
                    >
                      <Code size={12} />
                      <span>Xem dữ liệu Node</span>
                    </button>
                  </div>
                )}
              </div>
            </div>

            <div className="mt-8 pt-4 border-t border-white/10 flex items-center justify-between text-[10px] text-white/60 font-mono relative z-10">
              <span>Hệ thống NLU-Gateway v1.2</span>
              <span>Xanh SM AI Lab</span>
            </div>
          </div>
        </div>

      </div>

      {/* Dialog Modal containing details of clicked node during debugging */}
      {selectedModalNode && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-md p-4">
          <div className="bg-[#0d1527] border border-white/10 rounded-3xl max-w-4xl w-full max-h-[85vh] flex flex-col shadow-2xl relative overflow-hidden text-white animate-in fade-in zoom-in-95 duration-200">
            <div className="absolute top-0 right-0 w-80 h-80 bg-primary/5 rounded-full blur-3xl pointer-events-none"></div>
            
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-white/2 relative z-10">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg bg-white/5 ${NODES[selectedModalNode]?.color.split(' ')[1]}`}>
                  {(() => {
                    const Icon = NODES[selectedModalNode]?.icon || Brain;
                    return <Icon size={20} />;
                  })()}
                </div>
                <div>
                  <span className="text-[9px] font-bold text-white/60 uppercase tracking-widest font-mono">Dữ liệu phân tích Node</span>
                  <h3 className="font-bold text-white text-base leading-tight mt-0.5">{NODES[selectedModalNode]?.title}</h3>
                </div>
              </div>
              <button 
                onClick={() => setSelectedModalNode(null)}
                className="p-1.5 hover:bg-white/10 text-white/60 hover:text-white rounded-lg transition-colors"
              >
                <X size={18} />
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6 relative z-10">
              
              {/* If in debug mode and data is available, show runtime results */}
              {isDebugMode && debugData && debugSteps.includes(selectedModalNode) ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-xs font-bold text-[#00c897] bg-[#00c897]/5 border border-[#00c897]/20 px-3 py-2 rounded-xl">
                    <CheckCircle size={14} />
                    <span>DỮ LIỆU CHẠY THỰC TẾ (RUNTIME DATA)</span>
                  </div>
                  
                  {renderNodeRuntimeData(selectedModalNode)}
                </div>
              ) : (
                <div className="bg-white/5 border border-white/5 p-4 rounded-xl text-center text-sm text-white/75 font-sans">
                  {isDebugMode 
                    ? "Node này không nằm trong luồng thực thi của câu hỏi hiện tại." 
                    : "Chưa chạy thử nghiệm. Vui lòng nhập câu hỏi và click 'Chạy từng bước' để kiểm tra dữ liệu Runtime của Node này."
                  }
                </div>
              )}

              {/* Documentation/Architecture Section */}
              <div className="space-y-3 pt-4 border-t border-white/5 font-sans">
                <div className="flex items-center gap-2 text-xs font-bold text-[#00c897] uppercase tracking-wider">
                  <Info size={14} />
                  <span>MÔ TẢ KIẾN TRÚC (SPECIFICATIONS)</span>
                </div>
                <div className="bg-white/5 border border-white/5 rounded-2xl p-5 space-y-4">
                  <div>
                    <h4 className="text-xs font-bold text-white/60 uppercase tracking-widest mb-1">Nguyên lý hoạt động</h4>
                    <p className="text-sm text-white/80 leading-relaxed font-sans">{NODES[selectedModalNode]?.desc}</p>
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-white/60 uppercase tracking-widest mb-1">Chi tiết kỹ thuật</h4>
                    <p className="text-sm text-white/90 leading-relaxed font-sans">{NODES[selectedModalNode]?.details}</p>
                  </div>
                </div>
              </div>

            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 border-t border-white/10 bg-white/2 flex justify-between items-center text-[10px] text-white/60 font-mono relative z-10">
              <span>Xanh SM RAG System Debugger</span>
              <button 
                onClick={() => setSelectedModalNode(null)}
                className="px-4 py-2 bg-white/5 hover:bg-white/10 text-white rounded-lg text-xs font-bold transition-colors font-sans"
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
