import { useMemo, useState } from 'react';
import {
  AlertTriangle,
  Brain,
  CheckCircle,
  Database,
  GitBranch,
  Layers,
  MessageSquare,
  Search,
  Shield,
  Sparkles
} from 'lucide-react';

const FLOW_NODES = [
  {
    id: 'gateway',
    title: 'Input Gateway Safety',
    subtitle: 'Safety đầu vào',
    icon: Shield,
    tone: 'rose',
    kind: 'decision',
    desc: 'Chặn prompt injection, yêu cầu lộ system prompt/API key/cấu hình nội bộ và yêu cầu bôi nhọ không căn cứ.',
    details: 'Safety chính nằm ở đầu vào để answer path không phải tự kiểm duyệt lại câu trả lời hợp lệ.'
  },
  {
    id: 'prompt_injection_warning',
    title: 'Prompt Injection / Defamation',
    subtitle: 'Mối đe dọa bảo mật',
    icon: AlertTriangle,
    tone: 'slate',
    kind: 'process',
    desc: 'Phát hiện các hành vi tấn công prompt injection, rò rỉ thông tin mật hoặc bôi nhọ ác ý.',
    details: 'Khi phát hiện nguy cơ, hệ thống chuyển hướng trực tiếp sang nhánh Từ chối để bảo vệ hệ thống.'
  },
  {
    id: 'early_cache',
    title: 'Early Exact Cache',
    subtitle: 'Cache câu gốc',
    icon: Database,
    tone: 'sky',
    kind: 'decision',
    desc: 'Tìm exact match trong SemanticCache bằng câu hỏi gốc đã normalize.',
    details: 'Nếu hit, hệ thống trả lời ngay qua SSE và bỏ qua NLU, retrieval, rerank, generation.'
  },
  {
    id: 'llm_nlu',
    title: 'Unified LLM NLU',
    subtitle: 'Intent + Rewrite + Answer',
    icon: Brain,
    tone: 'violet',
    kind: 'process',
    desc: 'Phân loại intent, rewrite query, và trực tiếp sinh câu trả lời nếu là small-talk/sensitive.',
    details: 'Model NLU xử lý luôn câu trả lời cho các intent không cần RAG để tiết kiệm latency.'
  },
  {
    id: 'intent',
    title: 'Intent',
    subtitle: 'rag / food / small-talk / sensitive',
    icon: GitBranch,
    tone: 'cyan',
    kind: 'decision',
    desc: 'Điều hướng theo intent sau LLM NLU.',
    details: 'Phân luồng tới rag_chain, food_chain, small_talk, hoặc refusal.'
  },
  {
    id: 'food_nlu',
    title: 'Entity Extraction',
    subtitle: 'Trích xuất món ăn, địa điểm',
    icon: Brain,
    tone: 'violet',
    kind: 'process',
    desc: 'Trích xuất thực thể đồ ăn, địa chỉ, khoảng cách từ câu người dùng.',
    details: 'Dùng riêng cho intent food_recommendation.'
  },
  {
    id: 'food_context',
    title: 'User Context',
    subtitle: 'Ngữ cảnh & Bộ lọc',
    icon: Layers,
    tone: 'sky',
    kind: 'process',
    desc: 'Áp dụng ngữ cảnh người dùng, vị trí hiện tại và các bộ lọc yêu cầu.',
    details: 'Kết hợp sở thích cá nhân.'
  },
  {
    id: 'food_retrieval',
    title: 'Candidate Retrieval',
    subtitle: 'Tìm quán ăn phù hợp',
    icon: Search,
    tone: 'teal',
    kind: 'process',
    desc: 'Truy xuất các món ăn/nhà hàng phù hợp với entities và context.',
    details: 'Lọc qua database vector hoặc catalog SQL.'
  },
  {
    id: 'food_llm',
    title: 'Food LLM Synthesis',
    subtitle: 'Đánh giá & Gợi ý',
    icon: Sparkles,
    tone: 'emerald',
    kind: 'process',
    desc: 'Tạo câu trả lời tự nhiên từ danh sách nhà hàng.',
    details: 'Gợi ý món ăn tối ưu nhất.'
  },
  {
    id: 'small_talk',
    title: 'NLU Fast Answer',
    subtitle: 'NLU trực tiếp trả lời',
    icon: MessageSquare,
    tone: 'amber',
    kind: 'terminal',
    desc: 'Trả kết quả từ NLU cho các câu giao tiếp cơ bản.',
    details: 'Không cần đi qua RAG Retriever hay mô hình LLM thứ hai.'
  },
  {
    id: 'second_cache',
    title: 'Second Exact Cache',
    subtitle: 'Cache query rewrite',
    icon: Database,
    tone: 'blue',
    kind: 'decision',
    desc: 'Kiểm tra cache lần hai bằng rewritten_query.',
    details: 'Bắt được các câu hỏi diễn đạt khác nhau nhưng cùng ý nghĩa sau khi NLU chuẩn hóa.'
  },
  {
    id: 'refusal',
    title: 'Refusal Response',
    subtitle: 'Dừng pipeline',
    icon: AlertTriangle,
    tone: 'rose',
    kind: 'terminal',
    desc: 'Trả câu từ chối trực tiếp từ NLU (sensitive) hoặc Input Gateway (unsafe).',
    details: 'Áp dụng cho prompt injection, secret leakage, malicious defamation hoặc yêu cầu vượt chính sách.'
  },
  {
    id: 'hybrid_search',
    title: 'Hybrid Retrieval',
    subtitle: 'Dense + Sparse',
    icon: Search,
    tone: 'cyan',
    kind: 'process',
    desc: 'Kết hợp dense vector, sparse/BM25 và SQL keyword fallback trên document_chunks.',
    details: 'SQL fallback giúp bắt literal quan trọng như mã xe, giá, số liệu, tên chính sách hoặc điều kiện trong PDF.'
  },
  {
    id: 'reranker',
    title: 'Cohere Reranker',
    subtitle: 'Xếp hạng context',
    icon: Layers,
    tone: 'pink',
    kind: 'process',
    desc: 'Dùng Cohere rerank để đưa chunk liên quan nhất lên đầu trước khi mở rộng context.',
    details: 'Đây là API call riêng nên có latency, nhưng giúp giảm nhiễu mạnh trước khi đưa context vào LLM.'
  },
  {
    id: 'context_expansion',
    title: 'Parent / Section Context',
    subtitle: 'Mở rộng context',
    icon: Layers,
    tone: 'teal',
    kind: 'process',
    desc: 'Mở rộng theo parent_chunk_id hoặc section khi chunk đủ liên quan.',
    details: 'Giúp LLM đọc trọn bảng biểu, điều khoản PDF hoặc chính sách dài; đồng thời dedupe header/nội dung trùng.'
  },
  {
    id: 'llm_gen',
    title: 'LLM Synthesis',
    subtitle: 'SSE Stream',
    icon: Sparkles,
    tone: 'violet',
    kind: 'process',
    desc: 'Tổng hợp câu trả lời dựa trên context đã rerank/mở rộng và query đã rewrite.',
    details: 'Câu trả lời được stream qua SSE kèm sources/citations. Độ dài context là một nguồn latency lớn.'
  },
  {
    id: 'semantic_cache',
    title: 'Save Semantic Cache',
    subtitle: 'Ghi cache kết quả',
    icon: Database,
    tone: 'lime',
    kind: 'process',
    desc: 'Lưu câu trả lời hợp lệ vào SemanticCache cho cả query gốc và rewritten query.',
    details: 'Giúp các lượt hỏi sau hit cache ở Early Cache hoặc Second Cache.'
  },
  {
    id: 'output',
    title: 'Stream Answer + Citations',
    subtitle: 'SSE Output Stream',
    icon: MessageSquare,
    tone: 'emerald',
    kind: 'terminal',
    desc: 'Trả kết quả cuối cùng cho frontend qua Server-Sent Events.',
    details: 'Telemetry ghi nhận latency, token, sources, nlu_fast_path và các thông tin debug phục vụ quan sát chất lượng.'
  }
];

export default function PipelineManager() {
  const [selectedNode, setSelectedNode] = useState('nlu_fast_gate');

  const nodeMap = useMemo(() => Object.fromEntries(FLOW_NODES.map(node => [node.id, node])), []);
  const executed = useMemo(() => [], []);

  return (
    <div className="mx-auto w-full max-w-[1760px] pb-16">
      <header className="mb-6 flex flex-col gap-2">
        <h1 className="text-3xl font-bold text-on-surface">Pipeline Manager</h1>
        <p className="max-w-5xl text-sm text-on-surface-variant">
          Sơ đồ quản lý luồng xử lý RAG: Input Gateway Safety, Cache hai lớp, NLU fast-path, LLM NLU fallback,
          Hybrid Retrieval, Cohere Rerank, Context Expansion, LLM Synthesis và Save Semantic Cache.
        </p>
      </header>

      <section className="flex flex-col xl:flex-row gap-6 h-[calc(100vh-140px)]">
        {/* Full Width Flowchart Workspace */}
        <div className="w-full rounded-2xl border border-[#1e293b]/60 bg-[#0b0f19] p-4 shadow-xl overflow-hidden flex flex-col relative glass-panel">
          <div className="mb-3 flex items-center justify-between gap-3 shrink-0 z-10">
            <div>
              <div className="text-sm font-semibold text-white">RAG Processing Pipeline Flowchart</div>
              <div className="text-xs text-[#94a3b8]">Flowchart Workspace</div>
            </div>
            <div className="flex gap-2">
              <div className="rounded-lg border border-[#00c897]/30 bg-[#00c897]/10 px-3 py-1.5 text-[11px] font-bold tracking-wider text-[#00c897]">
                NLU_MODEL: GPT-4O-MINI
              </div>
            </div>
          </div>

          <div className="flex-1 overflow-auto custom-scrollbar relative border border-[#1e293b]/30 rounded-xl bg-[#030914] background-grid">
            <ReadableFlow
              nodeMap={nodeMap}
              selectedNode={selectedNode}
              executed={executed}
              onSelect={setSelectedNode}
            />
          </div>
        </div>
      </section>
      
      {/* Background grid pattern for flowchart */}
      <style>{`
        .background-grid {
          background-image: 
            linear-gradient(to right, rgba(255,255,255,0.02) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255,255,255,0.02) 1px, transparent 1px);
          background-size: 20px 20px;
        }
      `}</style>
    </div>
  );
}

function ReadableFlow({ nodeMap, selectedNode, executed, onSelect }) {
  const nodes = {
    gateway: { x: 600, y: 80 },
    prompt_injection_warning: { x: 200, y: 200 },
    early_cache: { x: 600, y: 220 },
    llm_nlu: { x: 600, y: 360 },
    intent: { x: 600, y: 500 },
    refusal: { x: 200, y: 640 },
    small_talk: { x: 400, y: 640 },
    second_cache: { x: 600, y: 640 },
    food_nlu: { x: 850, y: 640 },
    food_context: { x: 850, y: 760 },
    food_retrieval: { x: 850, y: 860 },
    food_llm: { x: 850, y: 960 },
    hybrid_search: { x: 600, y: 760 },
    reranker: { x: 600, y: 860 },
    context_expansion: { x: 600, y: 960 },
    llm_gen: { x: 600, y: 1060 },
    semantic_cache: { x: 600, y: 1160 },
    output: { x: 600, y: 1300 }
  };

  const edges = [
    { from: 'gateway', to: 'early_cache', label: 'Safe', tone: 'sky', d: 'M 600 112 V 180', labelX: 600, labelY: 150 },
    { from: 'gateway', to: 'prompt_injection_warning', label: 'Unsafe', tone: 'rose', d: 'M 535 80 H 200 V 170', labelX: 360, labelY: 70 },
    { from: 'prompt_injection_warning', to: 'refusal', tone: 'rose', d: 'M 200 227 V 615' },
    { from: 'early_cache', to: 'output', label: 'Cache Hit (~5ms)', tone: 'sky', d: 'M 665 220 H 1100 V 1250 H 600 V 1273', labelX: 880, labelY: 210 },
    { from: 'early_cache', to: 'llm_nlu', label: 'Cache Miss', tone: 'slate', d: 'M 600 252 V 333', labelX: 600, labelY: 290 },
    { from: 'llm_nlu', to: 'intent', tone: 'violet', d: 'M 600 384 V 468' },
    
    { from: 'intent', to: 'refusal', label: 'sensitive', tone: 'rose', d: 'M 535 500 H 200 V 615', labelX: 280, labelY: 490 },
    { from: 'intent', to: 'small_talk', label: 'small-talk', tone: 'amber', d: 'M 535 500 H 400 V 615', labelX: 460, labelY: 490 },
    { from: 'intent', to: 'second_cache', label: 'rag', tone: 'cyan', d: 'M 600 532 V 608', labelX: 600, labelY: 570 },
    { from: 'intent', to: 'food_nlu', label: 'food', tone: 'teal', d: 'M 665 500 H 850 V 613', labelX: 750, labelY: 490 },
    
    { from: 'food_nlu', to: 'food_context', tone: 'teal', d: 'M 850 664 V 733' },
    { from: 'food_context', to: 'food_retrieval', tone: 'teal', d: 'M 850 784 V 833' },
    { from: 'food_retrieval', to: 'food_llm', tone: 'teal', d: 'M 850 884 V 933' },
    { from: 'food_llm', to: 'output', tone: 'emerald', d: 'M 850 984 V 1250 H 600 V 1273' },
    
    { from: 'small_talk', to: 'output', tone: 'amber', d: 'M 400 663 V 1250 H 600 V 1273' },
    { from: 'refusal', to: 'output', tone: 'rose', d: 'M 200 663 V 1250 H 600 V 1273' },
    
    { from: 'second_cache', to: 'output', label: 'Cache Hit', tone: 'blue', d: 'M 665 640 H 1000 V 1250 H 600 V 1273', labelX: 830, labelY: 630 },
    { from: 'second_cache', to: 'hybrid_search', label: 'Cache Miss', tone: 'cyan', d: 'M 600 672 V 730', labelX: 600, labelY: 700 },
    
    { from: 'hybrid_search', to: 'reranker', tone: 'cyan', d: 'M 600 787 V 833' },
    { from: 'reranker', to: 'context_expansion', tone: 'pink', d: 'M 600 884 V 933' },
    { from: 'context_expansion', to: 'llm_gen', tone: 'teal', d: 'M 600 984 V 1033' },
    { from: 'llm_gen', to: 'semantic_cache', tone: 'violet', d: 'M 600 1084 V 1133' },
    { from: 'semantic_cache', to: 'output', tone: 'emerald', d: 'M 600 1184 V 1273' }
  ];

  return (
    <div className="rounded-xl border border-white/10 bg-[#030914] p-3 shadow-inner">
      <style>
        {`
          @keyframes flowDash {
            to { stroke-dashoffset: -20; }
          }
          .animate-flow-dash {
            animation: flowDash 0.7s linear infinite;
          }
          @keyframes glowPulse {
            0%, 100% { filter: drop-shadow(0 0 2px currentColor); }
            50% { filter: drop-shadow(0 0 6px currentColor); }
          }
          .glow-active {
            animation: glowPulse 2s ease-in-out infinite;
          }
        `}
      </style>
      <div className="overflow-x-auto overflow-y-hidden custom-scrollbar">
        <div className="relative h-[1480px] min-w-[1000px] origin-top-left max-w-[1200px] mx-auto">
          <svg className="absolute inset-0 h-full w-full" viewBox="0 0 1000 1480" aria-hidden="true">
            <defs>
              <marker id="pipeline-arrow" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto" markerUnits="strokeWidth">
                <path d="M0,0 L0,6 L6,3 z" fill="currentColor" />
              </marker>
            </defs>
            {edges.map(edge => (
              <PipelineEdge
                key={`${edge.from}-${edge.to}-${edge.label || ''}`}
                edge={edge}
                active={executed.includes(edge.from) && executed.includes(edge.to)}
              />
            ))}
          </svg>

          {Object.entries(nodes).map(([id, pos]) => (
            <PipelineBox
              key={id}
              node={nodeMap[id]}
              x={pos.x}
              y={pos.y}
              selected={selectedNode === id}
              executed={executed.includes(id)}
              onClick={() => onSelect(id)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function PipelineBox({ node, x, y, selected, executed, onClick }) {
  if (!node) return null;
  const Icon = node.icon;
  const isSelected = selected;
  const isExecuted = executed;

  let width = 160;
  let height = 48;
  if (node.kind === 'decision') {
    width = 130;
    height = 64;
  } else if (node.kind === 'terminal') {
    width = 150;
    height = 46;
    if (node.id === 'output') {
      width = 200;
      height = 54;
    }
  } else if (node.id === 'hybrid_search') {
    width = 190;
    height = 54;
  } else if (node.id === 'prompt_injection_warning') {
    width = 160;
    height = 54;
  }

  const theme = {
    emerald: { border: 'text-emerald-400', bg: 'bg-emerald-500/10', text: 'text-emerald-300', glow: 'rgba(16,185,129,0.3)', fill: 'rgba(6, 78, 59, 0.4)' },
    rose: { border: 'text-rose-400', bg: 'bg-rose-500/10', text: 'text-rose-300', glow: 'rgba(244,63,94,0.3)', fill: 'rgba(159, 18, 57, 0.4)' },
    sky: { border: 'text-sky-400', bg: 'bg-sky-500/10', text: 'text-sky-300', glow: 'rgba(14,165,233,0.3)', fill: 'rgba(12, 74, 96, 0.4)' },
    indigo: { border: 'text-indigo-400', bg: 'bg-indigo-500/10', text: 'text-indigo-300', glow: 'rgba(99,102,241,0.3)', fill: 'rgba(49, 46, 129, 0.4)' },
    blue: { border: 'text-blue-400', bg: 'bg-blue-500/10', text: 'text-blue-300', glow: 'rgba(59,130,246,0.3)', fill: 'rgba(30, 58, 138, 0.4)' },
    cyan: { border: 'text-cyan-400', bg: 'bg-cyan-500/10', text: 'text-cyan-300', glow: 'rgba(6,182,212,0.3)', fill: 'rgba(21, 94, 117, 0.4)' },
    pink: { border: 'text-pink-400', bg: 'bg-pink-500/10', text: 'text-pink-300', glow: 'rgba(236,72,153,0.3)', fill: 'rgba(131, 24, 67, 0.4)' },
    teal: { border: 'text-teal-400', bg: 'bg-teal-500/10', text: 'text-teal-300', glow: 'rgba(20,184,166,0.3)', fill: 'rgba(17, 94, 89, 0.4)' },
    violet: { border: 'text-violet-400', bg: 'bg-violet-500/10', text: 'text-violet-300', glow: 'rgba(139,92,246,0.3)', fill: 'rgba(88, 28, 135, 0.4)' },
    amber: { border: 'text-amber-400', bg: 'bg-amber-500/10', text: 'text-amber-300', glow: 'rgba(245,158,11,0.3)', fill: 'rgba(120, 53, 4, 0.4)' },
    lime: { border: 'text-lime-400', bg: 'bg-lime-500/10', text: 'text-lime-300', glow: 'rgba(132,204,22,0.3)', fill: 'rgba(63, 98, 18, 0.4)' },
    slate: { border: 'text-slate-400', bg: 'bg-slate-500/10', text: 'text-slate-300', glow: 'rgba(100,116,139,0.2)', fill: 'rgba(30, 41, 59, 0.4)' }
  }[node.tone] || { border: 'text-slate-500', bg: 'bg-slate-800/10', text: 'text-slate-300', glow: 'rgba(100,116,139,0.1)', fill: 'rgba(30, 41, 59, 0.4)' };

  let overrideFill = null;
  let overrideStroke = null;
  let textClass = 'text-slate-200';
  let subtitleClass = 'text-slate-400';

  if (node.id === 'gateway') {
    overrideFill = 'url(#gateway-grad)';
    overrideStroke = '#ef4444';
    textClass = 'text-white font-extrabold';
    subtitleClass = 'text-red-100';
  } else if (node.id === 'small_talk') {
    overrideFill = 'url(#smalltalk-grad)';
    overrideStroke = '#f59e0b';
    textClass = 'text-slate-900 font-extrabold';
    subtitleClass = 'text-amber-950/80';
  } else if (node.id === 'refusal') {
    overrideFill = 'url(#refusal-grad)';
    overrideStroke = '#f43f5e';
    textClass = 'text-white font-extrabold';
    subtitleClass = 'text-rose-100';
  } else if (node.id === 'output') {
    overrideFill = 'url(#output-grad)';
    overrideStroke = '#10b981';
    textClass = 'text-white font-extrabold';
    subtitleClass = 'text-emerald-100';
  }

  const isHighlighted = isSelected || isExecuted;
  const strokeColor = overrideStroke || (isSelected ? '#34d399' : isExecuted ? '#10b981' : 'rgba(148, 163, 184, 0.4)');
  const fillColor = overrideFill || (isSelected ? 'rgba(30, 41, 59, 0.95)' : isExecuted ? theme.fill : 'rgba(15, 23, 42, 0.85)');
  const strokeWidth = isSelected ? 3 : isExecuted ? 2 : 1.5;

  return (
    <button
      type="button"
      onClick={onClick}
      style={{ left: x - width/2, top: y - height/2, width: `${width}px`, height: `${height}px` }}
      className={`absolute transition-all duration-300 hover:scale-[1.03] hover:shadow-2xl focus:outline-none group`}
    >
      <svg className="absolute inset-0 w-full h-full pointer-events-none overflow-visible">
        <defs>
          <filter id={`glow-${node.id}`} x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="5" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
          <linearGradient id="gateway-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#f87171" stopOpacity="0.95" />
            <stop offset="100%" stopColor="#be123c" stopOpacity="0.95" />
          </linearGradient>
          <linearGradient id="smalltalk-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#fbbf24" stopOpacity="0.95" />
            <stop offset="100%" stopColor="#d97706" stopOpacity="0.95" />
          </linearGradient>
          <linearGradient id="refusal-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#fb7185" stopOpacity="0.95" />
            <stop offset="100%" stopColor="#9f1239" stopOpacity="0.95" />
          </linearGradient>
          <linearGradient id="output-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#34d399" stopOpacity="0.95" />
            <stop offset="100%" stopColor="#047857" stopOpacity="0.95" />
          </linearGradient>
        </defs>

        {isHighlighted && (
          node.kind === 'decision' ? (
            <polygon
              points={`${width/2},2 2,${height/2} ${width/2},${height-2} ${width-2},${height/2}`}
              fill="none"
              stroke={isSelected ? '#34d399' : '#10b981'}
              strokeWidth={6}
              opacity={0.35}
              filter={`url(#glow-${node.id})`}
            />
          ) : node.kind === 'terminal' ? (
            <rect
              x="2" y="2" width={width-4} height={height-4} rx={height/2} ry={height/2}
              fill="none"
              stroke={isSelected ? '#34d399' : '#10b981'}
              strokeWidth={6}
              opacity={0.35}
              filter={`url(#glow-${node.id})`}
            />
          ) : (
            <rect
              x="2" y="2" width={width-4} height={height-4} rx={8} ry={8}
              fill="none"
              stroke={isSelected ? '#34d399' : '#10b981'}
              strokeWidth={6}
              opacity={0.35}
              filter={`url(#glow-${node.id})`}
            />
          )
        )}

        {node.kind === 'decision' ? (
          <polygon
            points={`${width/2},2 2,${height/2} ${width/2},${height-2} ${width-2},${height/2}`}
            fill={fillColor}
            stroke={strokeColor}
            strokeWidth={strokeWidth}
            className="transition-all duration-300"
          />
        ) : node.kind === 'terminal' ? (
          <g>
            <rect
              x="2" y="2" width={width-4} height={height-4} rx={height/2} ry={height/2}
              fill={fillColor}
              stroke={strokeColor}
              strokeWidth={strokeWidth}
              className="transition-all duration-300"
            />
            {node.id === 'output' && (
              <rect
                x="6" y="6" width={width-12} height={height-12} rx={(height-12)/2} ry={(height-12)/2}
                fill="none"
                stroke={strokeColor}
                strokeWidth={1}
                opacity={0.4}
              />
            )}
          </g>
        ) : (
          <rect
            x="2" y="2" width={width-4} height={height-4} rx={8} ry={8}
            fill={fillColor}
            stroke={strokeColor}
            strokeWidth={strokeWidth}
            className="transition-all duration-300"
          />
        )}
      </svg>

      <div className="relative z-10 flex flex-col items-center justify-center w-full h-full px-3 text-center select-none">
        <div className="flex items-center justify-center gap-1.5 w-full">
          {Icon && <Icon size={node.kind === 'decision' ? 10 : 12} className={`shrink-0 ${node.id === 'gateway' || node.id === 'refusal' || node.id === 'output' ? 'text-white' : node.id === 'small_talk' ? 'text-slate-900' : theme.text}`} />}
          <span className={`truncate text-[9.5px] font-bold tracking-wide uppercase ${node.id === 'gateway' || node.id === 'refusal' || node.id === 'output' ? 'text-white' : node.id === 'small_talk' ? 'text-slate-900' : textClass}`}>
            {node.title}
          </span>
          {isExecuted && <CheckCircle size={10} className={`shrink-0 ${node.id === 'gateway' || node.id === 'refusal' || node.id === 'output' ? 'text-emerald-200' : node.id === 'small_talk' ? 'text-emerald-900' : 'text-emerald-400'}`} />}
        </div>
        {node.subtitle && (
          <div className={`mt-0.5 truncate text-[7.5px] font-medium ${node.id === 'gateway' || node.id === 'refusal' || node.id === 'output' ? 'text-white/80' : node.id === 'small_talk' ? 'text-slate-900/80' : subtitleClass}`}>
            {node.subtitle}
          </div>
        )}
      </div>
    </button>
  );
}

function PipelineEdge({ edge, active }) {
  const color = active ? '#10b981' : edgeStroke(edge.tone);
  const labelPos = (edge.labelX && edge.labelY)
    ? { x: edge.labelX, y: edge.labelY }
    : labelPoint(edge.d);

  const labelWidth = edge.label ? Math.max(edge.label.length * 5.5 + 12, 45) : 0;

  return (
    <g style={{ color }} className={active ? 'glow-active' : ''}>
      <path
        d={edge.d}
        fill="none"
        stroke={active ? '#059669' : edgeStroke(edge.tone)}
        strokeWidth={active ? 3 : 1.5}
        opacity={active ? 0.35 : 0.15}
      />
      <path
        d={edge.d}
        fill="none"
        stroke="currentColor"
        strokeWidth={active ? 2.2 : 1.2}
        strokeDasharray={active ? '6 4' : '4 4'}
        className={active ? 'animate-flow-dash' : ''}
        markerEnd="url(#pipeline-arrow)"
        opacity={active ? 1 : 0.45}
      />
      {edge.label && (
        <g className="cursor-default">
          <rect
            x={labelPos.x - labelWidth / 2}
            y={labelPos.y - 9}
            width={labelWidth}
            height={18}
            rx="4"
            fill="#090d16"
            stroke={active ? '#10b981' : 'rgba(148, 163, 184, 0.3)'}
            strokeWidth="1"
          />
          <text
            x={labelPos.x}
            y={labelPos.y + 3.5}
            textAnchor="middle"
            fontSize="8"
            fill={active ? '#34d399' : '#94a3b8'}
            fontWeight="700"
            className="select-none font-sans tracking-wide"
          >
            {edge.label}
          </text>
        </g>
      )}
    </g>
  );
}

function edgeStroke(tone) {
  return {
    emerald: '#10b981',
    rose: '#f43f5e',
    sky: '#0ea5e9',
    blue: '#3b82f6',
    amber: '#f59e0b',
    violet: '#8b5cf6',
    cyan: '#06b6d4',
    pink: '#ec4899',
    teal: '#14b8a6',
    lime: '#84cc16',
    slate: '#475569'
  }[tone] || '#475569';
}

function labelPoint(path) {
  const nums = [...path.matchAll(/-?\d+/g)].map(match => Number(match[0]));
  if (nums.length < 4) return { x: 0, y: 0 };
  return {
    x: (nums[0] + nums[nums.length - 2]) / 2,
    y: (nums[1] + nums[nums.length - 1]) / 2
  };
}


