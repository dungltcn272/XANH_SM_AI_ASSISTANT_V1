import { useMemo, useState } from 'react';
import {
  AlertTriangle,
  ArrowRight,
  Brain,
  CheckCircle,
  ChevronRight,
  Code,
  Database,
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

const PIPELINE_NODES = [
  {
    id: 'user_input',
    title: 'User Input',
    subtitle: 'Nhận câu hỏi',
    icon: PlayCircle,
    tone: 'emerald',
    desc: 'Người dùng gửi câu hỏi thô qua API chat hoặc endpoint debug.',
    details: 'Pipeline bắt đầu từ query gốc, sau đó normalize nhẹ trước khi đi vào safety gateway.'
  },
  {
    id: 'gateway',
    title: 'Input Gateway Safety',
    subtitle: 'Chặn sớm rủi ro',
    icon: Shield,
    tone: 'rose',
    desc: 'Chặn prompt injection, yêu cầu lộ system prompt/API key/cấu hình nội bộ và yêu cầu bôi nhọ không căn cứ.',
    details: 'Safety chính nằm ở đầu vào. Answer path hiện không còn dùng Output Guardrail làm node chặn chính để tránh false-positive.'
  },
  {
    id: 'early_cache',
    title: 'Early Exact Cache',
    subtitle: 'Hit là trả ngay',
    icon: Database,
    tone: 'sky',
    desc: 'Tìm exact match trong SemanticCache bằng câu hỏi gốc đã normalize.',
    details: 'Nếu cache hit, hệ thống trả câu trả lời qua SSE và bỏ qua NLU, retrieval, rerank, generation.'
  },
  {
    id: 'unified_nlu',
    title: 'Unified NLU',
    subtitle: 'Intent + rewrite + expansion',
    icon: Brain,
    tone: 'indigo',
    desc: 'Một lần gọi LLM để phân loại intent, viết lại câu hỏi, sinh tối đa một expanded query và suggested answer.',
    details: 'NLU dùng gpt-4o-mini, temperature thấp, max_tokens hiện là 220 để giảm output budget và worst-case latency.'
  },
  {
    id: 'second_cache',
    title: 'Second Exact Cache',
    subtitle: 'Cache theo rewritten query',
    icon: Database,
    tone: 'blue',
    desc: 'Kiểm tra cache lần hai bằng câu hỏi đã rewrite.',
    details: 'Bắt được các câu hỏi diễn đạt khác nhau nhưng cùng ý nghĩa sau khi NLU chuẩn hóa.'
  },
  {
    id: 'hybrid_search',
    title: 'Hybrid Retrieval',
    subtitle: 'Dense + Sparse + SQL',
    icon: Search,
    tone: 'cyan',
    desc: 'Kết hợp dense vector, sparse/BM25 và SQL keyword fallback trên document_chunks.',
    details: 'SQL fallback giúp bắt literal quan trọng như mã xe, giá, số liệu, tên chính sách hoặc điều kiện trong PDF.'
  },
  {
    id: 'reranker',
    title: 'Cohere Reranker',
    subtitle: 'Sắp xếp lại context',
    icon: Layers,
    tone: 'pink',
    desc: 'Dùng Cohere rerank để đưa chunk liên quan nhất lên đầu trước khi mở rộng context.',
    details: 'Reranker là một nguồn latency đáng kể vì là API call riêng, nhưng giúp giảm nhiễu cho prompt.'
  },
  {
    id: 'context_expansion',
    title: 'Parent / Section Expansion',
    subtitle: 'Mở rộng bảng/điều khoản',
    icon: Layers,
    tone: 'teal',
    desc: 'Mở rộng theo parent_chunk_id hoặc section khi chunk đủ liên quan.',
    details: 'Giúp LLM đọc trọn bảng biểu, điều khoản PDF hoặc chính sách dài; đồng thời dedupe header/nội dung trùng.'
  },
  {
    id: 'llm_gen',
    title: 'LLM Synthesis',
    subtitle: 'Sinh câu trả lời',
    icon: Sparkles,
    tone: 'violet',
    desc: 'LLM tổng hợp câu trả lời dựa trên context đã rerank/mở rộng và query đã rewrite.',
    details: 'Câu trả lời được stream qua SSE kèm sources/citations. Độ dài context là một nguyên nhân lớn của latency.'
  },
  {
    id: 'semantic_cache',
    title: 'Save Semantic Cache',
    subtitle: 'Lưu câu gốc + rewrite',
    icon: Database,
    tone: 'amber',
    desc: 'Lưu câu trả lời hợp lệ vào SemanticCache cho cả query gốc và rewritten query.',
    details: 'Giúp các lượt hỏi sau hit cache ở Early Cache hoặc Second Cache.'
  },
  {
    id: 'output',
    title: 'SSE Output',
    subtitle: 'Trả answer + sources',
    icon: MessageSquare,
    tone: 'emerald',
    desc: 'Trả kết quả cuối cùng cho frontend bằng Server-Sent Events.',
    details: 'Telemetry ghi nhận latency, số chunk và thông tin debug phục vụ quan sát chất lượng.'
  }
];

const BRANCHES = [
  { from: 'gateway', to: 'block_violation', label: 'Unsafe', tone: 'rose' },
  { from: 'early_cache', to: 'output', label: 'Cache hit', tone: 'sky' },
  { from: 'unified_nlu', to: 'small_talk', label: 'small-talk', tone: 'amber' },
  { from: 'unified_nlu', to: 'block_violation', label: 'sensitive', tone: 'rose' },
  { from: 'second_cache', to: 'output', label: 'Cache hit', tone: 'blue' }
];

const SPECIAL_NODES = {
  block_violation: {
    title: 'Refusal Response',
    subtitle: 'Dừng pipeline',
    icon: AlertTriangle,
    tone: 'rose',
    desc: 'Trả thông báo từ chối khi gateway hoặc NLU xác định nội dung không an toàn.',
    details: 'Áp dụng cho prompt injection, secret leakage, malicious defamation hoặc sensitive intent.'
  },
  small_talk: {
    title: 'Fast Small-talk',
    subtitle: 'Trả nhanh',
    icon: Zap,
    tone: 'amber',
    desc: 'Trả suggested_answer từ NLU cho câu chào hỏi hoặc câu không cần RAG.',
    details: 'Không đi qua retriever/reranker/LLM synthesis đầy đủ.'
  },
  evaluation: {
    title: 'Evaluation History',
    subtitle: 'evaluation_runs',
    icon: CheckCircle,
    tone: 'lime',
    desc: 'Ragas eval ghi evaluation_report.json và snapshot vào bảng evaluation_runs.',
    details: 'Admin UI dùng lịch sử này để xem recent runs, trend và delta so với lần eval trước.'
  }
};

const toneClass = {
  emerald: 'border-emerald-400/40 text-emerald-300 bg-emerald-500/10',
  rose: 'border-rose-400/40 text-rose-300 bg-rose-500/10',
  sky: 'border-sky-400/40 text-sky-300 bg-sky-500/10',
  indigo: 'border-indigo-400/40 text-indigo-300 bg-indigo-500/10',
  blue: 'border-blue-400/40 text-blue-300 bg-blue-500/10',
  cyan: 'border-cyan-400/40 text-cyan-300 bg-cyan-500/10',
  pink: 'border-pink-400/40 text-pink-300 bg-pink-500/10',
  teal: 'border-teal-400/40 text-teal-300 bg-teal-500/10',
  violet: 'border-violet-400/40 text-violet-300 bg-violet-500/10',
  amber: 'border-amber-400/40 text-amber-300 bg-amber-500/10',
  lime: 'border-lime-400/40 text-lime-300 bg-lime-500/10'
};

export default function PipelineManager() {
  const [selectedNode, setSelectedNode] = useState(PIPELINE_NODES[0].id);
  const [testQuery, setTestQuery] = useState('');
  const [debugData, setDebugData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const allNodes = useMemo(() => {
    const map = Object.fromEntries(PIPELINE_NODES.map(node => [node.id, node]));
    return { ...map, ...SPECIAL_NODES };
  }, []);

  const selected = allNodes[selectedNode] || PIPELINE_NODES[0];
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
    <div className="max-w-[1600px] mx-auto w-full pb-16">
      <header className="mb-6">
        <h1 className="text-3xl font-bold text-on-surface">Pipeline Manager</h1>
        <p className="mt-2 text-on-surface-variant">
          Sơ đồ admin theo pipeline hiện tại: safety ở đầu vào, cache hai lớp, Unified NLU, Hybrid Retrieval, Cohere Rerank, Context Expansion, LLM Synthesis và Semantic Cache.
        </p>
      </header>

      <section className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_420px] gap-6">
        <div className="rounded-2xl border border-outline-variant/40 bg-[#0b121e] p-5 shadow-xl">
          <div className="flex flex-col gap-4">
            <div className="grid grid-cols-1 md:grid-cols-2 2xl:grid-cols-3 gap-3">
              {PIPELINE_NODES.map((node, index) => (
                <PipelineNode
                  key={node.id}
                  node={node}
                  index={index + 1}
                  active={selectedNode === node.id}
                  executed={executed.includes(node.id)}
                  onClick={() => setSelectedNode(node.id)}
                />
              ))}
            </div>

            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
              <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-white">
                <ArrowRight size={16} className="text-sky-300" />
                Nhánh rẽ quan trọng
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                {BRANCHES.map(branch => (
                  <button
                    key={`${branch.from}-${branch.to}`}
                    onClick={() => setSelectedNode(branch.to)}
                    className={`rounded-lg border p-3 text-left ${toneClass[branch.tone]} hover:bg-white/10 transition-colors`}
                  >
                    <div className="text-xs uppercase tracking-wide opacity-70">{branch.label}</div>
                    <div className="mt-1 flex items-center gap-2 text-sm font-semibold">
                      <span>{allNodes[branch.from]?.title}</span>
                      <ChevronRight size={14} />
                      <span>{allNodes[branch.to]?.title}</span>
                    </div>
                  </button>
                ))}
                <button
                  onClick={() => setSelectedNode('evaluation')}
                  className={`rounded-lg border p-3 text-left ${toneClass.lime} hover:bg-white/10 transition-colors`}
                >
                  <div className="text-xs uppercase tracking-wide opacity-70">Benchmark</div>
                  <div className="mt-1 text-sm font-semibold">evaluation_report.json + evaluation_runs</div>
                </button>
              </div>
            </div>
          </div>
        </div>

        <aside className="space-y-5">
          <div className="rounded-2xl border border-outline-variant/40 bg-[#0d1527] p-5 shadow-xl">
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

          <form onSubmit={runDebug} className="rounded-2xl border border-outline-variant/40 bg-[#0d1527] p-5 shadow-xl">
            <div className="flex items-center gap-2 text-sm font-semibold text-white">
              <Play size={16} className="text-emerald-300" />
              Chạy thử pipeline
            </div>
            <textarea
              value={testQuery}
              onChange={e => setTestQuery(e.target.value)}
              rows={4}
              placeholder="Nhập câu hỏi để debug pipeline..."
              className="mt-4 w-full rounded-xl border border-white/10 bg-black/30 p-3 text-sm text-white outline-none placeholder:text-white/35 focus:border-emerald-400"
            />
            <div className="mt-3 flex gap-2">
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
                  setSelectedNode('user_input');
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
            <div className="rounded-2xl border border-outline-variant/40 bg-[#0d1527] p-5 shadow-xl">
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

function PipelineNode({ node, index, active, executed, onClick }) {
  const Icon = node.icon;
  return (
    <button
      onClick={onClick}
      className={`group relative rounded-xl border p-4 text-left transition-all hover:-translate-y-0.5 ${
        active ? `${toneClass[node.tone]} shadow-lg` : 'border-white/10 bg-white/[0.04] text-white/80 hover:bg-white/[0.07]'
      } ${executed ? 'ring-1 ring-emerald-400/40' : ''}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-black/25 text-xs font-bold">{index}</span>
          <Icon size={18} />
        </div>
        {executed && <CheckCircle size={16} className="text-emerald-300" />}
      </div>
      <div className="mt-3 text-sm font-bold">{node.title}</div>
      <div className="mt-1 text-xs opacity-70">{node.subtitle}</div>
      {index < PIPELINE_NODES.length && (
        <ArrowRight size={16} className="absolute right-3 top-1/2 hidden translate-x-6 text-white/25 2xl:block" />
      )}
    </button>
  );
}

function RuntimeSummary({ data }) {
  const rows = [
    ['Intent', data.intent || 'n/a'],
    ['Gateway', data.safety_res?.safe === false ? 'blocked' : 'safe / n/a'],
    ['Rewritten query', data.rewritten_query || data.query || 'n/a'],
    ['Answer preview', data.answer ? `${String(data.answer).slice(0, 140)}...` : 'n/a'],
    ['Latency', data.latency_seconds ? `${data.latency_seconds}s` : data.total_latency_ms ? `${data.total_latency_ms}ms` : 'n/a']
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
  const blocked = data.safety_res?.safe === false || String(data.answer || '').toLowerCase().includes('vi phạm chính sách');
  if (blocked) return [...steps, 'block_violation', 'output'];

  if (data.cache_hit || data.cache_hit_stage === 'early') return [...steps, 'early_cache', 'output'];
  steps.push('early_cache', 'unified_nlu');

  if (data.intent === 'sensitive') return [...steps, 'block_violation', 'output'];
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
