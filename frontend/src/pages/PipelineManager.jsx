import { useMemo, useState } from 'react';
import {
  AlertTriangle,
  Brain,
  CheckCircle,
  Code,
  Database,
  FileCheck,
  GitBranch,
  Layers,
  MessageSquare,
  Play,
  PlayCircle,
  RefreshCw,
  Search,
  Shield,
  Sparkles,
  X,
  Zap
} from 'lucide-react';
import { api } from '../api';

const FLOW_NODES = [
  {
    id: 'user_input',
    title: 'User Input',
    subtitle: 'Câu hỏi thô',
    icon: PlayCircle,
    tone: 'emerald',
    kind: 'terminal',
    x: 48,
    y: 72,
    desc: 'Người dùng gửi câu hỏi qua chat hoặc endpoint debug.',
    details: 'Pipeline bắt đầu từ query gốc, sau đó normalize nhẹ trước khi đi vào safety gateway.'
  },
  {
    id: 'gateway',
    title: 'Input Gateway Safety',
    subtitle: 'Safety đầu vào',
    icon: Shield,
    tone: 'rose',
    kind: 'decision',
    x: 308,
    y: 72,
    desc: 'Chặn prompt injection, yêu cầu lộ system prompt/API key/cấu hình nội bộ và yêu cầu bôi nhọ không căn cứ.',
    details: 'Safety chính nằm ở đầu vào để answer path không phải tự kiểm duyệt lại câu trả lời hợp lệ.'
  },
  {
    id: 'refusal',
    title: 'Refusal Response',
    subtitle: 'Dừng pipeline',
    icon: AlertTriangle,
    tone: 'rose',
    kind: 'terminal',
    x: 600,
    y: 34,
    desc: 'Trả thông báo từ chối khi câu hỏi không an toàn hoặc intent là sensitive.',
    details: 'Áp dụng cho prompt injection, secret leakage, malicious defamation hoặc yêu cầu vượt chính sách.'
  },
  {
    id: 'early_cache',
    title: 'Early Exact Cache',
    subtitle: 'Cache câu gốc',
    icon: Database,
    tone: 'sky',
    kind: 'decision',
    x: 308,
    y: 200,
    desc: 'Tìm exact match trong SemanticCache bằng câu hỏi gốc đã normalize.',
    details: 'Nếu hit, hệ thống trả lời ngay qua SSE và bỏ qua NLU, retrieval, rerank, generation.'
  },
  {
    id: 'nlu_fast_gate',
    title: 'NLU Fast-path?',
    subtitle: 'RAG rõ ràng?',
    icon: GitBranch,
    tone: 'indigo',
    kind: 'decision',
    x: 308,
    y: 328,
    desc: 'Quyết định câu hỏi có đủ tín hiệu domain để bỏ qua LLM NLU hay không.',
    details: 'Fast-path chạy khi câu hỏi có keyword/domain rõ và không cần rewrite theo lịch sử hội thoại.'
  },
  {
    id: 'domain_vocabulary',
    title: 'Domain Vocabulary',
    subtitle: 'Regex alias local',
    icon: Zap,
    tone: 'amber',
    kind: 'process',
    x: 48,
    y: 468,
    desc: 'Làm giàu query bằng từ điển miền tốc độ cao.',
    details: 'Map các câu viết tắt/sai chính tả như xsm, gsm, vgreen, dk, platfom, tx, bn, sạc free, ăn chia, đền hàng sang thuật ngữ tài liệu.'
  },
  {
    id: 'llm_nlu',
    title: 'LLM Unified NLU',
    subtitle: 'NLU_MODEL',
    icon: Brain,
    tone: 'violet',
    kind: 'process',
    x: 600,
    y: 468,
    desc: 'Dùng model NLU để phân loại intent, rewrite và mở rộng query khi fast-path không đủ chắc.',
    details: 'Model được cấu hình bằng NLU_MODEL, mặc định hiện là gpt-4o-mini. Nhánh này dành cho câu mơ hồ, cần lịch sử hội thoại hoặc cần rewrite.'
  },
  {
    id: 'intent',
    title: 'Intent',
    subtitle: 'rag / small-talk / sensitive',
    icon: GitBranch,
    tone: 'cyan',
    kind: 'decision',
    x: 308,
    y: 596,
    desc: 'Điều hướng theo intent sau fast-path hoặc LLM NLU.',
    details: 'rag đi tiếp retrieval; small-talk trả nhanh; sensitive đi refusal.'
  },
  {
    id: 'small_talk',
    title: 'Fast Small-talk',
    subtitle: 'Trả nhanh',
    icon: MessageSquare,
    tone: 'amber',
    kind: 'terminal',
    x: 48,
    y: 724,
    desc: 'Trả lời nhanh cho chào hỏi hoặc câu không cần RAG.',
    details: 'Không đi qua retriever/reranker/LLM synthesis đầy đủ.'
  },
  {
    id: 'second_cache',
    title: 'Second Exact Cache',
    subtitle: 'Cache query rewrite',
    icon: Database,
    tone: 'blue',
    kind: 'decision',
    x: 600,
    y: 596,
    desc: 'Kiểm tra cache lần hai bằng rewritten_query.',
    details: 'Bắt được các câu hỏi diễn đạt khác nhau nhưng cùng ý nghĩa sau khi NLU chuẩn hóa.'
  },
  {
    id: 'hybrid_search',
    title: 'Hybrid Retrieval',
    subtitle: 'Dense + Sparse + SQL',
    icon: Search,
    tone: 'cyan',
    kind: 'process',
    x: 852,
    y: 596,
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
    x: 1104,
    y: 596,
    desc: 'Dùng Cohere rerank để đưa chunk liên quan nhất lên đầu trước khi mở rộng context.',
    details: 'Đây là API call riêng nên có latency, nhưng giúp giảm nhiễu mạnh trước khi đưa context vào LLM.'
  },
  {
    id: 'context_expansion',
    title: 'Context Expansion',
    subtitle: 'Parent / Section',
    icon: Layers,
    tone: 'teal',
    kind: 'process',
    x: 1104,
    y: 724,
    desc: 'Mở rộng theo parent_chunk_id hoặc section khi chunk đủ liên quan.',
    details: 'Giúp LLM đọc trọn bảng biểu, điều khoản PDF hoặc chính sách dài; đồng thời dedupe header/nội dung trùng.'
  },
  {
    id: 'llm_gen',
    title: 'LLM Synthesis',
    subtitle: 'LLM_MODEL',
    icon: Sparkles,
    tone: 'violet',
    kind: 'process',
    x: 852,
    y: 724,
    desc: 'Tổng hợp câu trả lời dựa trên context đã rerank/mở rộng và query đã rewrite.',
    details: 'Câu trả lời được stream qua SSE kèm sources/citations. Độ dài context là một nguồn latency lớn.'
  },
  {
    id: 'semantic_cache',
    title: 'Save Semantic Cache',
    subtitle: 'Ghi cache',
    icon: Database,
    tone: 'lime',
    kind: 'process',
    x: 600,
    y: 724,
    desc: 'Lưu câu trả lời hợp lệ vào SemanticCache cho cả query gốc và rewritten query.',
    details: 'Giúp các lượt hỏi sau hit cache ở Early Cache hoặc Second Cache.'
  },
  {
    id: 'output',
    title: 'SSE Output',
    subtitle: 'Answer + sources',
    icon: MessageSquare,
    tone: 'emerald',
    kind: 'terminal',
    x: 308,
    y: 840,
    desc: 'Trả kết quả cuối cùng cho frontend qua Server-Sent Events.',
    details: 'Telemetry ghi nhận latency, token, sources, nlu_fast_path và các thông tin debug phục vụ quan sát chất lượng.'
  },
  {
    id: 'evaluation',
    title: 'Evaluation History',
    subtitle: 'evaluation_runs',
    icon: FileCheck,
    tone: 'lime',
    kind: 'subgraph',
    x: 852,
    y: 852,
    desc: 'Benchmark ghi evaluation_report.json và snapshot vào bảng evaluation_runs.',
    details: 'Admin UI dùng lịch sử này để xem recent runs, trend và delta so với lần eval trước.'
  }
];

const toneClass = {
  emerald: 'border-emerald-400/50 text-emerald-200 bg-emerald-500/10',
  rose: 'border-rose-400/50 text-rose-200 bg-rose-500/10',
  sky: 'border-sky-400/50 text-sky-200 bg-sky-500/10',
  indigo: 'border-indigo-400/50 text-indigo-200 bg-indigo-500/10',
  blue: 'border-blue-400/50 text-blue-200 bg-blue-500/10',
  cyan: 'border-cyan-400/50 text-cyan-200 bg-cyan-500/10',
  pink: 'border-pink-400/50 text-pink-200 bg-pink-500/10',
  teal: 'border-teal-400/50 text-teal-200 bg-teal-500/10',
  violet: 'border-violet-400/50 text-violet-200 bg-violet-500/10',
  amber: 'border-amber-400/50 text-amber-200 bg-amber-500/10',
  lime: 'border-lime-400/50 text-lime-200 bg-lime-500/10'
};

export default function PipelineManager() {
  const [selectedNode, setSelectedNode] = useState('nlu_fast_gate');
  const [testQuery, setTestQuery] = useState('');
  const [debugData, setDebugData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const nodeMap = useMemo(() => Object.fromEntries(FLOW_NODES.map(node => [node.id, node])), []);
  const selected = nodeMap[selectedNode] || nodeMap.nlu_fast_gate;
  const executed = useMemo(() => inferExecutedNodes(debugData), [debugData]);

  const runDebug = async e => {
    e.preventDefault();
    if (!testQuery.trim() || loading) return;
    setLoading(true);
    setError('');
    try {
      const data = await api.testPipeline(testQuery.trim());
      setDebugData(data);
      const steps = inferExecutedNodes(data);
      setSelectedNode(steps[steps.length - 1] || 'user_input');
    } catch (err) {
      setError(err.message || 'Không thể chạy debug pipeline.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto w-full max-w-[1760px] pb-16">
      <header className="mb-6 flex flex-col gap-2">
        <h1 className="text-3xl font-bold text-on-surface">Pipeline Manager</h1>
        <p className="max-w-5xl text-sm text-on-surface-variant">
          Sơ đồ admin theo pipeline hiện tại: Input Gateway, cache hai lớp, NLU fast-path với Domain Vocabulary, LLM NLU fallback,
          Hybrid Retrieval, Cohere Rerank, Context Expansion, LLM Synthesis và Semantic Cache.
        </p>
      </header>

      <section className="grid grid-cols-1 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)] gap-6">
        <div className="order-3 rounded-2xl border border-outline-variant/40 bg-[#07111f] p-4 shadow-xl xl:col-span-2">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div>
              <div className="text-sm font-semibold text-white">Mermaid-like Flow</div>
              <div className="text-xs text-white/45">Click vào node để xem ý nghĩa; chạy debug để highlight nhanh thực tế.</div>
            </div>
            <div className="rounded-lg border border-cyan-400/25 bg-cyan-500/10 px-3 py-2 text-xs font-semibold text-cyan-200">
              NLU_MODEL: gpt-4o-mini
            </div>
          </div>

          <ReadableFlow
            nodeMap={nodeMap}
            selectedNode={selectedNode}
            executed={executed}
            onSelect={setSelectedNode}
          />
        </div>

        <aside className="contents">
          <div className="order-2 rounded-2xl border border-outline-variant/40 bg-[#0d1527] p-5 shadow-xl">
            <div className="flex items-start gap-3">
              <div className={`rounded-xl border p-3 ${toneClass[selected.tone]}`}>
                <selected.icon size={22} />
              </div>
              <div>
                <div className="text-xs font-semibold uppercase tracking-wider text-white/50">Node detail</div>
                <h2 className="mt-1 text-xl font-bold text-white">{selected.title}</h2>
                <p className="mt-1 text-sm text-white/50">{selected.subtitle}</p>
              </div>
            </div>
            <div className="mt-5 space-y-4 text-sm leading-relaxed">
              <p className="text-white/80">{selected.desc}</p>
              <div className="rounded-xl border border-white/10 bg-black/20 p-4 text-white/75">{selected.details}</div>
            </div>
          </div>

          <form onSubmit={runDebug} className="order-1 rounded-2xl border border-outline-variant/40 bg-[#0d1527] p-5 shadow-xl">
            <div className="flex items-center gap-2 text-sm font-semibold text-white">
              <Play size={16} className="text-emerald-300" />
              Chạy thử pipeline
            </div>
            <textarea
              value={testQuery}
              onChange={e => setTestQuery(e.target.value)}
              rows={5}
              placeholder="Nhập câu hỏi để debug pipeline..."
              className="mt-4 w-full rounded-xl border border-white/10 bg-black/30 p-3 text-sm text-white outline-none placeholder:text-white/35 focus:border-emerald-400"
            />
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                type="submit"
                disabled={loading || !testQuery.trim()}
                className="inline-flex items-center gap-2 rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
              >
                {loading ? <RefreshCw size={15} className="animate-spin" /> : <PlayCircle size={15} />}
                Chạy debug
              </button>
              <button
                type="button"
                onClick={() => {
                  setDebugData(null);
                  setError('');
                  setTestQuery('');
                  setSelectedNode('nlu_fast_gate');
                }}
                className="inline-flex items-center gap-2 rounded-lg border border-white/10 px-4 py-2 text-sm font-semibold text-white/70 hover:text-white"
              >
                <X size={15} />
                Xóa
              </button>
            </div>
            {error && <p className="mt-3 text-sm text-rose-300">{error}</p>}
          </form>

          {debugData && (
            <div className="order-4 rounded-2xl border border-outline-variant/40 bg-[#0d1527] p-5 shadow-xl xl:col-span-2">
              <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-white">
                <Code size={16} className="text-sky-300" />
                Runtime debug
              </div>
              <RuntimeSummary data={debugData} />
              <pre className="mt-4 max-h-80 overflow-auto rounded-xl border border-white/10 bg-black/30 p-3 text-xs leading-relaxed text-white/80">
                {JSON.stringify(debugData, null, 2)}
              </pre>
            </div>
          )}
        </aside>
      </section>
    </div>
  );
}

function ReadableFlow({ nodeMap, selectedNode, executed, onSelect }) {
  const nodes = {
    user_input: { x: 425, y: 15 },
    gateway: { x: 425, y: 85 },
    refusal: { x: 150, y: 85 },
    early_cache: { x: 425, y: 155 },
    nlu_fast_gate: { x: 425, y: 225 },
    domain_vocabulary: { x: 280, y: 305 },
    llm_nlu: { x: 570, y: 305 },
    intent: { x: 425, y: 395 },
    small_talk: { x: 150, y: 395 },
    second_cache: { x: 700, y: 395 },
    hybrid_search: { x: 700, y: 475 },
    reranker: { x: 700, y: 555 },
    context_expansion: { x: 700, y: 635 },
    llm_gen: { x: 700, y: 715 },
    semantic_cache: { x: 425, y: 715 },
    output: { x: 425, y: 805 },
    evaluation: { x: 880, y: 475 }
  };

  const edges = [
    { from: 'user_input', to: 'gateway', tone: 'emerald', d: 'M 500 65 V 85' },
    { from: 'gateway', to: 'early_cache', label: 'safe', tone: 'sky', d: 'M 500 135 V 155' },
    { from: 'gateway', to: 'refusal', label: 'unsafe', tone: 'rose', d: 'M 425 110 H 300' },
    { from: 'early_cache', to: 'output', label: 'cache hit', tone: 'sky', d: 'M 425 180 H 70 V 830 H 425' },
    { from: 'early_cache', to: 'nlu_fast_gate', label: 'miss', tone: 'slate', d: 'M 500 205 V 225' },
    { from: 'nlu_fast_gate', to: 'domain_vocabulary', label: 'fast', tone: 'amber', d: 'M 425 250 H 355 V 305' },
    { from: 'domain_vocabulary', to: 'intent', label: 'enrich', tone: 'amber', d: 'M 355 355 V 395 H 425' },
    { from: 'nlu_fast_gate', to: 'llm_nlu', label: 'rewrite', tone: 'violet', d: 'M 575 250 H 645 V 305' },
    { from: 'llm_nlu', to: 'intent', label: 'json', tone: 'violet', d: 'M 645 355 V 395 H 575' },
    { from: 'intent', to: 'small_talk', label: 'small-talk', tone: 'amber', d: 'M 425 420 H 300' },
    { from: 'intent', to: 'refusal', label: 'sensitive', tone: 'rose', d: 'M 425 420 H 70 V 110 H 150' },
    { from: 'intent', to: 'second_cache', label: 'rag', tone: 'cyan', d: 'M 575 420 H 700' },
    { from: 'second_cache', to: 'output', label: 'cache hit', tone: 'blue', d: 'M 850 420 H 920 V 830 H 575' },
    { from: 'second_cache', to: 'hybrid_search', label: 'miss', tone: 'cyan', d: 'M 775 445 V 475' },
    { from: 'hybrid_search', to: 'reranker', tone: 'cyan', d: 'M 775 525 V 555' },
    { from: 'reranker', to: 'context_expansion', tone: 'pink', d: 'M 775 605 V 635' },
    { from: 'context_expansion', to: 'llm_gen', tone: 'teal', d: 'M 775 685 V 715' },
    { from: 'llm_gen', to: 'semantic_cache', tone: 'violet', d: 'M 700 740 H 575' },
    { from: 'semantic_cache', to: 'output', tone: 'emerald', d: 'M 500 765 V 805' },
    { from: 'small_talk', to: 'output', tone: 'amber', d: 'M 150 420 H 70 V 830 H 425' },
    { from: 'refusal', to: 'output', tone: 'rose', d: 'M 150 110 H 70 V 830 H 425' },
    { from: 'hybrid_search', to: 'evaluation', label: 'eval', tone: 'lime', d: 'M 850 500 H 880' }
  ];

  return (
    <div className="rounded-xl border border-white/10 bg-[#020817] p-3">
      <div className="overflow-x-auto overflow-y-hidden">
        <div className="relative h-[880px] min-w-[1000px] origin-top-left">
          <svg className="absolute inset-0 h-full w-full" viewBox="0 0 1000 880" aria-hidden="true">
            <defs>
              <marker id="pipeline-arrow" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto" markerUnits="strokeWidth">
                <path d="M0,0 L0,6 L6,3 z" fill="currentColor" />
              </marker>
            </defs>
            {edges.map(edge => (
              <PipelineEdge key={`${edge.from}-${edge.to}-${edge.label || ''}`} edge={edge} active={executed.includes(edge.from) && executed.includes(edge.to)} />
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
  const Icon = node.icon;
  return (
    <button
      type="button"
      onClick={onClick}
      style={{ left: x, top: y }}
      className={`absolute min-h-[50px] w-[150px] rounded-md border p-1.5 text-left transition-all hover:scale-[1.02] ${
        selected ? toneClass[node.tone] : 'border-slate-700 bg-slate-900/90 text-white/70 hover:bg-slate-800'
      } ${executed ? 'ring-1.5 ring-emerald-400/60' : ''}`}
    >
      <div className="flex items-start justify-between gap-1.5">
        <div className="min-w-0">
          <div className="flex items-center gap-1">
            <Icon size={12} className="shrink-0" />
            <span className="truncate text-[10px] font-bold leading-tight">{node.title}</span>
          </div>
          <div className="mt-0.5 truncate text-[9px] font-medium opacity-60">{node.subtitle}</div>
        </div>
        {executed && <CheckCircle size={10} className="mt-0.5 shrink-0 text-emerald-400" />}
      </div>
    </button>
  );
}

function PipelineEdge({ edge, active }) {
  const color = active ? '#34d399' : edgeStroke(edge.tone);
  const labelPos = labelPoint(edge.d);
  return (
    <g style={{ color }}>
      <path
        d={edge.d}
        fill="none"
        stroke="currentColor"
        strokeWidth={active ? 1.8 : 1.2}
        strokeDasharray="4 4"
        markerEnd="url(#pipeline-arrow)"
        opacity={active ? 1 : 0.5}
      />
      {edge.label && (
        <g>
          <rect x={labelPos.x - 25} y={labelPos.y - 9} width="50" height="18" rx="4" fill="#020817" stroke="currentColor" opacity="0.9" />
          <text x={labelPos.x} y={labelPos.y + 4} textAnchor="middle" fontSize="8" fill="currentColor" fontWeight="700">
            {edge.label}
          </text>
        </g>
      )}
    </g>
  );
}

function edgeStroke(tone) {
  return {
    emerald: '#34d399',
    rose: '#fb7185',
    sky: '#38bdf8',
    blue: '#60a5fa',
    amber: '#fbbf24',
    violet: '#a78bfa',
    cyan: '#22d3ee',
    pink: '#f472b6',
    teal: '#2dd4bf',
    lime: '#a3e635',
    slate: '#64748b'
  }[tone] || '#64748b';
}

function labelPoint(path) {
  const nums = [...path.matchAll(/-?\d+/g)].map(match => Number(match[0]));
  if (nums.length < 4) return { x: 0, y: 0 };
  return {
    x: (nums[0] + nums[nums.length - 2]) / 2,
    y: (nums[1] + nums[nums.length - 1]) / 2
  };
}
function RuntimeSummary({ data }) {
  const rows = [
    ['Intent', data.intent || 'n/a'],
    ['NLU fast-path', data.nlu_fast_path ? `${data.nlu_fast_path_reason || 'yes'}` : 'no / n/a'],
    ['NLU latency', data.nlu_latency_ms != null ? `${data.nlu_latency_ms}ms` : 'n/a'],
    ['Gateway', data.safety_res?.safe === false ? 'blocked' : 'safe / n/a'],
    ['Rewritten query', data.rewritten_query || data.query || 'n/a'],
    ['Answer preview', data.answer ? `${String(data.answer).slice(0, 140)}...` : 'n/a']
  ];

  return (
    <div className="space-y-2">
      {rows.map(([label, value]) => (
        <div key={label} className="grid grid-cols-[110px_minmax(0,1fr)] gap-3 text-xs">
          <span className="text-white/45">{label}</span>
          <span className="truncate text-white/85">{value}</span>
        </div>
      ))}
    </div>
  );
}

function inferExecutedNodes(data) {
  if (!data) return [];
  const steps = ['user_input', 'gateway'];
  const answer = String(data.answer || '').toLowerCase();
  const blocked = data.safety_res?.safe === false || answer.includes('vi phạm chính sách') || data.intent === 'sensitive';
  if (blocked) return [...steps, 'refusal', 'output'];

  if (data.cache_hit || data.cache_hit_stage === 'early') return [...steps, 'early_cache', 'output'];
  steps.push('early_cache', 'nlu_fast_gate');

  if (data.nlu_fast_path) steps.push('domain_vocabulary');
  else steps.push('llm_nlu');

  steps.push('intent');
  if (data.intent === 'small-talk') return [...steps, 'small_talk', 'output'];
  if (data.cache_hit_stage === 'second') return [...steps, 'second_cache', 'output'];

  return [
    ...steps,
    'second_cache',
    'hybrid_search',
    'reranker',
    'context_expansion',
    'llm_gen',
    'semantic_cache',
    'output'
  ];
}
