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

const FLOW_EDGES = [
  { from: 'user_input', to: 'gateway' },
  { from: 'gateway', to: 'refusal', label: 'unsafe', tone: 'rose' },
  { from: 'gateway', to: 'early_cache', label: 'safe' },
  { from: 'early_cache', to: 'output', label: 'cache hit', tone: 'sky', path: 'cache-output' },
  { from: 'early_cache', to: 'nlu_fast_gate', label: 'miss' },
  { from: 'nlu_fast_gate', to: 'domain_vocabulary', label: 'yes', tone: 'amber' },
  { from: 'nlu_fast_gate', to: 'llm_nlu', label: 'no', tone: 'violet' },
  { from: 'domain_vocabulary', to: 'intent' },
  { from: 'llm_nlu', to: 'intent' },
  { from: 'intent', to: 'small_talk', label: 'small-talk', tone: 'amber' },
  { from: 'intent', to: 'refusal', label: 'sensitive', tone: 'rose', path: 'intent-refusal' },
  { from: 'intent', to: 'second_cache', label: 'rag' },
  { from: 'second_cache', to: 'output', label: 'cache hit', tone: 'blue', path: 'second-output' },
  { from: 'second_cache', to: 'hybrid_search', label: 'miss' },
  { from: 'hybrid_search', to: 'reranker' },
  { from: 'reranker', to: 'context_expansion' },
  { from: 'context_expansion', to: 'llm_gen' },
  { from: 'llm_gen', to: 'semantic_cache' },
  { from: 'semantic_cache', to: 'output' },
  { from: 'hybrid_search', to: 'evaluation', label: 'eval suite', tone: 'lime', dashed: true, path: 'eval' }
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

const edgeColor = {
  rose: '#fb7185',
  sky: '#38bdf8',
  blue: '#60a5fa',
  amber: '#fbbf24',
  violet: '#a78bfa',
  lime: '#a3e635',
  default: '#475569'
};

const NODE_WIDTH = 200;
const NODE_HEIGHT = 76;

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
              <div className="text-xs text-white/45">Click vào node để xem ý nghĩa; chạy debug để highlight nhánh thực tế.</div>
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
  const mainPath = ['user_input', 'gateway', 'early_cache', 'nlu_fast_gate', 'intent', 'second_cache', 'hybrid_search', 'reranker', 'context_expansion', 'llm_gen', 'semantic_cache', 'output'];

  return (
    <div className="rounded-xl border border-white/10 bg-[#020817] p-4">
      <div className="mb-4 grid grid-cols-1 gap-3 lg:grid-cols-3">
        <FlowLegend tone="emerald" label="Executed" desc="Nhánh đã chạy trong lần debug gần nhất" />
        <FlowLegend tone="amber" label="Fast path" desc="NLU local + Domain Vocabulary, không gọi LLM NLU" />
        <FlowLegend tone="violet" label="LLM fallback" desc="Dùng NLU_MODEL khi cần rewrite/ngữ cảnh" />
      </div>

      <div className="overflow-x-auto">
        <div className="min-w-[1560px] space-y-6 pb-2">
          <FlowLane title="Happy Path" subtitle="Luồng chính khi câu hỏi an toàn, cache miss và cần RAG">
            {mainPath.map((id, index) => (
              <FlowStepGroup key={id}>
                <LaneNode
                  node={nodeMap[id]}
                  selected={selectedNode === id}
                  executed={executed.includes(id)}
                  onClick={() => onSelect(id)}
                />
                {index < mainPath.length - 1 && <LaneArrow active={isAdjacentExecuted(id, mainPath[index + 1], executed)} />}
              </FlowStepGroup>
            ))}
          </FlowLane>

          <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
            <FlowBranch
              title="Safety & Early Exit"
              desc="Các nhánh dừng sớm để tránh tốn token/latency."
              items={[
                ['gateway', 'unsafe', 'refusal'],
                ['intent', 'sensitive', 'refusal'],
                ['intent', 'small-talk', 'small_talk'],
                ['early_cache', 'cache hit', 'output'],
                ['second_cache', 'cache hit', 'output']
              ]}
              nodeMap={nodeMap}
              selectedNode={selectedNode}
              executed={executed}
              onSelect={onSelect}
            />

            <FlowBranch
              title="NLU Routing"
              desc="Fast-path xử lý câu rõ ràng; LLM NLU chỉ dùng khi cần hiểu ngữ cảnh."
              items={[
                ['nlu_fast_gate', 'yes', 'domain_vocabulary'],
                ['domain_vocabulary', 'enrich', 'intent'],
                ['nlu_fast_gate', 'no', 'llm_nlu'],
                ['llm_nlu', 'json', 'intent']
              ]}
              nodeMap={nodeMap}
              selectedNode={selectedNode}
              executed={executed}
              onSelect={onSelect}
            />

            <FlowBranch
              title="Evaluation Loop"
              desc="Benchmark và review thực tế dùng để phát hiện regression."
              items={[
                ['hybrid_search', 'eval cases', 'evaluation'],
                ['evaluation', 'report', 'output']
              ]}
              nodeMap={nodeMap}
              selectedNode={selectedNode}
              executed={executed}
              onSelect={onSelect}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function FlowLane({ title, subtitle, children }) {
  return (
    <div className="rounded-2xl border border-slate-700/70 bg-slate-950/70 p-4">
      <div className="mb-4 flex items-end justify-between gap-4">
        <div>
          <div className="text-sm font-bold text-white">{title}</div>
          <div className="text-xs text-white/45">{subtitle}</div>
        </div>
      </div>
      <div className="flex items-stretch gap-2">{children}</div>
    </div>
  );
}

function FlowStepGroup({ children }) {
  return <div className="flex shrink-0 items-center gap-2">{children}</div>;
}

function LaneNode({ node, selected, executed, compact = false, onClick }) {
  const Icon = node.icon;
  return (
    <button
      type="button"
      onClick={onClick}
      className={`min-h-[76px] ${compact ? 'w-[178px]' : 'w-[152px]'} rounded-xl border p-3 text-left transition hover:-translate-y-0.5 ${
        selected ? toneClass[node.tone] : 'border-slate-700 bg-slate-900/80 text-white/75 hover:bg-slate-800'
      } ${executed ? 'ring-2 ring-emerald-400/60' : ''}`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <Icon size={15} className="shrink-0" />
            <span className="truncate text-xs font-bold">{node.title}</span>
          </div>
          <div className="mt-1 truncate text-[11px] opacity-65">{node.subtitle}</div>
        </div>
        {executed && <CheckCircle size={14} className="shrink-0 text-emerald-300" />}
      </div>
    </button>
  );
}

function LaneArrow({ active }) {
  return (
    <div className={`flex w-8 shrink-0 items-center ${active ? 'text-emerald-300' : 'text-slate-600'}`}>
      <div className={`h-px flex-1 ${active ? 'bg-emerald-300' : 'bg-slate-700'}`} />
      <span className="-ml-0.5 text-lg leading-none">›</span>
    </div>
  );
}

function FlowBranch({ title, desc, items, nodeMap, selectedNode, executed, onSelect }) {
  return (
    <div className="rounded-2xl border border-slate-700/70 bg-slate-950/70 p-4">
      <div className="mb-4">
        <div className="text-sm font-bold text-white">{title}</div>
        <div className="text-xs text-white/45">{desc}</div>
      </div>
      <div className="space-y-3">
        {items.map(([from, label, to]) => (
          <div key={`${from}-${label}-${to}`} className="grid grid-cols-[minmax(0,1fr)_76px_minmax(0,1fr)] items-center gap-2">
            <LaneNode
              compact
              node={nodeMap[from]}
              selected={selectedNode === from}
              executed={executed.includes(from)}
              onClick={() => onSelect(from)}
            />
            <div className={`rounded-full border px-2 py-1 text-center text-[11px] font-bold ${
              isAdjacentExecuted(from, to, executed) ? 'border-emerald-400/50 bg-emerald-500/10 text-emerald-200' : 'border-slate-700 bg-slate-900 text-slate-400'
            }`}>
              {label}
            </div>
            <LaneNode
              compact
              node={nodeMap[to]}
              selected={selectedNode === to}
              executed={executed.includes(to)}
              onClick={() => onSelect(to)}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

function FlowLegend({ tone, label, desc }) {
  return (
    <div className={`rounded-xl border p-3 ${toneClass[tone]}`}>
      <div className="text-xs font-bold uppercase tracking-wide">{label}</div>
      <div className="mt-1 text-xs opacity-70">{desc}</div>
    </div>
  );
}

function FlowNode({ node, active, executed, onClick }) {
  const Icon = node.icon;
  const decision = node.kind === 'decision';
  const subgraph = node.kind === 'subgraph';

  return (
    <button
      onClick={onClick}
      style={{ left: node.x, top: node.y, width: NODE_WIDTH, minHeight: NODE_HEIGHT }}
      className={`absolute text-left transition-all hover:-translate-y-0.5 ${
        decision ? 'rounded-xl border-dashed' : subgraph ? 'rounded-2xl border-dashed' : 'rounded-xl'
      } border p-3 ${
        active ? `${toneClass[node.tone]} shadow-lg shadow-black/30` : 'border-slate-700 bg-slate-950 text-white/75 hover:bg-slate-900'
      } ${executed ? 'ring-2 ring-emerald-400/60' : ''}`}
    >
      <div>
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <Icon size={16} className="shrink-0" />
              <span className="truncate text-sm font-bold leading-tight">{node.title}</span>
            </div>
            <div className="mt-1 truncate text-xs opacity-65">{node.subtitle}</div>
          </div>
          <div className="flex shrink-0 items-center gap-1">
            {decision && <span className="rounded-md border border-current/25 px-1.5 py-0.5 text-[10px] font-bold uppercase opacity-75">if</span>}
            {executed && <CheckCircle size={15} className="text-emerald-300" />}
          </div>
        </div>
      </div>
    </button>
  );
}

function FlowEdge({ edge, from, to, active }) {
  const start = edgeStart(edge, from, to);
  const end = edgeEnd(edge, from, to);
  const color = active ? '#34d399' : edgeColor[edge.tone] || edgeColor.default;
  const strokeWidth = active ? 2.6 : 1.5;
  const dash = edge.dashed && !active ? '5 5' : undefined;
  const mid = { x: (start.x + end.x) / 2, y: (start.y + end.y) / 2 };

  const d = edgePath(edge, start, end);

  return (
    <g>
      <path
        d={d}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeDasharray={dash}
        markerEnd={active ? 'url(#arrow-active)' : 'url(#arrow)'}
        opacity={active ? 1 : 0.72}
      />
      {edge.label && (
        <g>
          <rect x={mid.x - 40} y={mid.y - 12} width="80" height="24" rx="7" fill="#020817" stroke={color} opacity="0.96" />
          <text x={mid.x} y={mid.y + 4} textAnchor="middle" fontSize="11" fill={color} fontWeight="700">
            {edge.label}
          </text>
        </g>
      )}
    </g>
  );
}

function edgeStart(edge, from, to) {
  if (edge.path === 'cache-output') return { x: from.x + NODE_WIDTH / 2, y: from.y + NODE_HEIGHT };
  if (edge.path === 'second-output') return { x: from.x + NODE_WIDTH / 2, y: from.y + NODE_HEIGHT };
  if (edge.path === 'intent-refusal') return { x: from.x + NODE_WIDTH / 2, y: from.y };
  if (edge.path === 'eval') return { x: from.x + NODE_WIDTH / 2, y: from.y + NODE_HEIGHT };
  if (Math.abs(to.x - from.x) < 24) return { x: from.x + NODE_WIDTH / 2, y: from.y + (to.y >= from.y ? NODE_HEIGHT : 0) };
  return {
    x: from.x + (to.x >= from.x ? NODE_WIDTH : 0),
    y: from.y + NODE_HEIGHT / 2
  };
}

function edgeEnd(edge, from, to) {
  if (edge.path === 'cache-output') return { x: to.x + NODE_WIDTH / 2, y: to.y };
  if (edge.path === 'second-output') return { x: to.x + NODE_WIDTH / 2, y: to.y };
  if (edge.path === 'intent-refusal') return { x: to.x + NODE_WIDTH / 2, y: to.y + NODE_HEIGHT };
  if (edge.path === 'eval') return { x: to.x + NODE_WIDTH / 2, y: to.y };
  if (Math.abs(to.x - from.x) < 24) return { x: to.x + NODE_WIDTH / 2, y: to.y + (to.y >= from.y ? 0 : NODE_HEIGHT) };
  return {
    x: to.x + (to.x >= from.x ? 0 : NODE_WIDTH),
    y: to.y + NODE_HEIGHT / 2
  };
}

function edgePath(edge, start, end) {
  if (edge.path === 'cache-output') {
    return `M ${start.x} ${start.y} V 806 H ${end.x} V ${end.y}`;
  }
  if (edge.path === 'second-output') {
    return `M ${start.x} ${start.y} V 806 H ${end.x} V ${end.y}`;
  }
  if (edge.path === 'intent-refusal') {
    return `M ${start.x} ${start.y} V 166 H ${end.x} V ${end.y}`;
  }
  if (edge.path === 'eval') {
    return `M ${start.x} ${start.y} V 824 H ${end.x} V ${end.y}`;
  }
  if (Math.abs(start.x - end.x) < 2 || Math.abs(start.y - end.y) < 2) {
    return `M ${start.x} ${start.y} L ${end.x} ${end.y}`;
  }
  const midX = (start.x + end.x) / 2;
  return `M ${start.x} ${start.y} H ${midX} V ${end.y} H ${end.x}`;
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

function isEdgeActive(edge, executed) {
  const fromIndex = executed.indexOf(edge.from);
  const toIndex = executed.indexOf(edge.to);
  return fromIndex >= 0 && toIndex === fromIndex + 1;
}

function isAdjacentExecuted(from, to, executed) {
  const fromIndex = executed.indexOf(from);
  const toIndex = executed.indexOf(to);
  return fromIndex >= 0 && toIndex === fromIndex + 1;
}
