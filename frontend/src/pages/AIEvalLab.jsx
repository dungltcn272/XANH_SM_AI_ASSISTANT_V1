import { useEffect, useMemo, useRef, useState } from 'react';
import {
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Database,
  Filter,
  Info,
  MoreVertical,
  Pause,
  PlayCircle,
  RefreshCw,
  Search,
  Terminal as TerminalIcon,
  X,
  XCircle
} from 'lucide-react';
import { api } from '../api';

const fallbackMetrics = {
  retrieval: { recall_5: 0, recall_10: 0, mrr: 0, ndcg_5: 0 },
  generation: { faithfulness: 0, correctness: 0, relevancy: 0 },
  system_latency: 0,
  total_cases: 0,
  golden_total_cases: 0,
  pending_cases: 0
};

const metricMeta = [
  { key: 'recall_5', label: 'Recall@5', group: 'retrieval', color: 'emerald', good: 'high', desc: 'Tỷ lệ tài liệu hoặc context đúng được tìm thấy trong top 5 kết quả truy xuất. Cao nghĩa là retriever bắt đúng nguồn sớm.' },
  { key: 'recall_10', label: 'Recall@10', group: 'retrieval', color: 'emerald', good: 'high', desc: 'Tỷ lệ tài liệu đúng xuất hiện trong top 10. Chỉ số này phản ánh độ phủ trước khi rerank/chọn context.' },
  { key: 'mrr', label: 'MRR', group: 'retrieval', color: 'emerald', good: 'high', desc: 'Mean Reciprocal Rank đo vị trí của kết quả đúng đầu tiên. Càng gần 1, tài liệu đúng càng nằm ở đầu danh sách.' },
  { key: 'ndcg_5', label: 'NDCG@5', group: 'retrieval', color: 'violet', good: 'high', desc: 'Đo chất lượng xếp hạng trong top 5, có tính đến vị trí và mức độ liên quan của từng tài liệu.' },
  { key: 'faithfulness', label: 'Faithfulness', group: 'generation', color: 'cyan', good: 'high', desc: 'Độ trung thực của câu trả lời so với context. Thấp nghĩa là câu trả lời có thể thêm thông tin không được tài liệu hỗ trợ.' },
  { key: 'correctness', label: 'Correctness', group: 'generation', color: 'cyan', good: 'high', desc: 'Mức độ đúng của câu trả lời so với expected answer/keywords trong golden set.' },
  { key: 'relevancy', label: 'Answer Relevancy', group: 'generation', color: 'cyan', good: 'high', desc: 'Mức độ trả lời trực tiếp vào câu hỏi, hạn chế lan man hoặc trả lời lệch ý.' },
  { key: 'system_latency', label: 'Latency (avg)', group: 'root', color: 'orange', good: 'low', suffix: 's', desc: 'Thời gian xử lý trung bình cho một case. Thấp hơn là tốt hơn; thường bị ảnh hưởng bởi NLU, retrieval, rerank và LLM synthesis.' }
];

const metricDescriptions = Object.fromEntries(metricMeta.map(item => [item.label, item.desc]));

const issueDescriptions = {
  'Latency': 'Case nổi bật vì thời gian xử lý cao hơn ngưỡng. Thường liên quan đến context dài, rerank chậm hoặc LLM synthesis lâu.',
  'NDCG@5': 'Case nổi bật vì chất lượng xếp hạng top 5 thấp. Retriever có thể tìm được tài liệu nhưng đặt tài liệu đúng chưa đủ cao.',
  'Faithfulness': 'Case nổi bật vì câu trả lời chưa bám sát context, có nguy cơ thêm thông tin ngoài tài liệu.',
  'Correctness': 'Case nổi bật vì nội dung trả lời chưa khớp expected keywords/answer trong golden set.',
  'Recall@5': 'Case nổi bật vì top 5 chưa chứa đủ tài liệu hoặc context mong đợi.'
};

const colorClass = {
  emerald: {
    text: 'text-emerald-300',
    value: 'text-emerald-50',
    line: 'stroke-emerald-400',
    bar: 'bg-emerald-400',
    bg: 'bg-emerald-500/15',
    border: 'border-emerald-400/25'
  },
  cyan: {
    text: 'text-cyan-300',
    value: 'text-cyan-50',
    line: 'stroke-cyan-400',
    bar: 'bg-cyan-400',
    bg: 'bg-cyan-500/15',
    border: 'border-cyan-400/25'
  },
  violet: {
    text: 'text-violet-300',
    value: 'text-violet-50',
    line: 'stroke-violet-400',
    bar: 'bg-violet-400',
    bg: 'bg-violet-500/15',
    border: 'border-violet-400/25'
  },
  orange: {
    text: 'text-orange-300',
    value: 'text-orange-300',
    line: 'stroke-orange-400',
    bar: 'bg-orange-400',
    bg: 'bg-orange-500/15',
    border: 'border-orange-400/25'
  }
};

function clampScore(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return 0;
  return Math.max(0, Math.min(1, n));
}

function formatScore(value, digits = 2) {
  const n = Number(value);
  return Number.isFinite(n) ? n.toFixed(digits) : '0.00';
}

function metricValue(metrics, meta) {
  if (meta.group === 'root') return Number(metrics[meta.key] || 0);
  return Number(metrics[meta.group]?.[meta.key] || 0);
}

function rowScore(row, key) {
  const direct = Number(row?.[key]);
  if (Number.isFinite(direct)) return direct;
  const retrieval = Number(row?.retrieval?.[key]);
  if (Number.isFinite(retrieval)) return retrieval;
  const generation = Number(row?.generation?.[key]);
  if (Number.isFinite(generation)) return generation;
  return 0;
}

function formatDelta(value, lowerIsBetter = false) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return 'n/a';
  const n = Number(value);
  const isGood = lowerIsBetter ? n < 0 : n > 0;
  const arrow = n === 0 ? '->' : isGood ? 'up' : 'down';
  return `${arrow} ${n > 0 ? '+' : ''}${n.toFixed(3)}`;
}

function shortTime(value) {
  if (!value) return 'n/a';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'n/a';
  return date.toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
}

function Sparkline({ values = [], color = 'emerald', latency = false }) {
  const safe = values.map(Number).filter(Number.isFinite);
  if (safe.length < 2) {
    return (
      <div className="flex h-9 w-full items-center justify-center rounded border border-dashed border-slate-700/70 bg-slate-950/30 text-[10px] text-slate-600">
        No history
      </div>
    );
  }
  const max = Math.max(...safe, latency ? 1 : 0.01);
  const min = Math.min(...safe, 0);
  const range = max - min || 1;
  const points = safe
    .map((v, i) => {
      const x = safe.length === 1 ? 96 : (i / (safe.length - 1)) * 96;
      const y = 30 - ((v - min) / range) * 24;
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <svg viewBox="0 0 96 34" className="h-9 w-full overflow-visible" aria-hidden="true">
      <polyline points={points} fill="none" strokeWidth="2.2" className={colorClass[color].line} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function MetricCard({ meta, value, delta, trend }) {
  const palette = colorClass[meta.color];
  const progress = meta.good === 'low' ? Math.max(0.08, Math.min(1, value / 15)) : clampScore(value);

  return (
    <div className="group relative rounded-lg border border-slate-700/70 bg-slate-950/60 p-3 shadow-[0_0_0_1px_rgba(15,23,42,0.35)]">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-medium text-slate-300">{meta.label}</span>
        <Info size={13} className="text-slate-500" />
      </div>
      <div className={`mt-3 text-2xl font-semibold tabular-nums ${palette.value}`}>
        {meta.suffix ? value.toFixed(2) + meta.suffix : formatScore(value)}
      </div>
      <div className={`mt-1 text-xs ${palette.text}`}>{formatDelta(delta, meta.good === 'low')}</div>
      <div className="mt-2">
        <Sparkline values={trend} color={meta.color} latency={meta.good === 'low'} />
      </div>
      <div className="mt-2 h-1.5 rounded-full bg-slate-800">
        <div className={`h-full rounded-full ${palette.bar}`} style={{ width: `${Math.max(8, progress * 100)}%` }} />
      </div>
      <Tooltip>{meta.desc}</Tooltip>
    </div>
  );
}

function StatusBadge({ status }) {
  const normalized = status || 'pending';
  const cls =
    normalized === 'completed'
      ? 'bg-emerald-500/15 text-emerald-300 border-emerald-400/20'
      : normalized === 'failed'
        ? 'bg-red-500/15 text-red-300 border-red-400/20'
        : 'bg-amber-500/15 text-amber-300 border-amber-400/20';
  return <span className={`inline-flex rounded px-2 py-1 text-[11px] font-medium capitalize border ${cls}`}>{normalized}</span>;
}

function LevelBadge({ level }) {
  const normalized = (level || 'unknown').toLowerCase();
  const cls =
    normalized === 'simple'
      ? 'bg-lime-500/15 text-lime-300 border-lime-400/20'
      : normalized === 'medium'
        ? 'bg-sky-500/15 text-sky-300 border-sky-400/20'
        : normalized === 'hard'
          ? 'bg-fuchsia-500/15 text-fuchsia-300 border-fuchsia-400/20'
          : 'bg-slate-700 text-slate-300 border-slate-600';
  return <span className={`inline-flex rounded px-2 py-1 text-[11px] font-semibold uppercase border ${cls}`}>{normalized}</span>;
}

function ScoreCell({ label, value }) {
  const score = clampScore(value);
  const color = score >= 0.75 ? 'bg-emerald-400' : score >= 0.55 ? 'bg-amber-400' : 'bg-red-400';
  return (
    <div className="group relative min-w-[48px]">
      <div className="text-xs text-slate-100 tabular-nums">{formatScore(value)}</div>
      <div className="mt-1 h-1 rounded-full bg-slate-800" title={label}>
        <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.max(4, score * 100)}%` }} />
      </div>
      <Tooltip>{metricDescriptions[label] || label}</Tooltip>
    </div>
  );
}

export default function AIEvalLab() {
  const [running, setRunning] = useState(false);
  const [runDescription, setRunDescription] = useState('');
  const [logs, setLogs] = useState([]);
  const [metrics, setMetrics] = useState(fallbackMetrics);
  const [dataset, setDataset] = useState([]);
  const [evalHistory, setEvalHistory] = useState({ runs: [], trend: [], delta: {} });
  const [filters, setFilters] = useState({ search: '', level: 'all', category: 'all', status: 'all' });
  const [page, setPage] = useState(1);
  const [dialog, setDialog] = useState(null);
  const terminalRef = useRef(null);

  useEffect(() => {
    loadEvalData().catch(console.error);
  }, []);

  useEffect(() => {
    if (terminalRef.current) terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
  }, [logs]);

  const loadEvalData = async () => {
    const [data, history] = await Promise.all([
      api.getEvalResults(),
      api.getEvalRuns(12).catch(() => ({ runs: [], trend: [], delta: {} }))
    ]);

    if (data?.metrics) {
      setMetrics({
        retrieval: data.metrics.retrieval || fallbackMetrics.retrieval,
        generation: data.metrics.generation || fallbackMetrics.generation,
        system_latency: Number(data.metrics.average_latency_sec || 0),
        total_cases: Number(data.metrics.total_cases || 0),
        golden_total_cases: Number(data.metrics.golden_total_cases || data.metrics.total_cases || 0),
        pending_cases: Number(data.metrics.pending_cases || 0)
      });
    }

    if (data?.details) setDataset(data.details);
    setEvalHistory(history || { runs: [], trend: [], delta: {} });
  };

  const runEvaluation = async () => {
    if (running) return;
    setRunning(true);
    setLogs([
      `[${new Date().toLocaleTimeString('vi-VN')}] INFO  Starting evaluation run`,
      `[${new Date().toLocaleTimeString('vi-VN')}] INFO  Dataset: golden_50`
    ]);

    try {
      const apiBase = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api';
      const response = await fetch(`${apiBase}/admin/evaluate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${api.getAuthToken() || ''}`
        },
        body: JSON.stringify({ description: runDescription })
      });

      if (!response.ok || !response.body) throw new Error(`HTTP ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const text = decoder.decode(value);
        const lines = text.split('\n');

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const data = line.slice(6);
          if (data.trim() === '[DONE]') {
            setLogs(prev => [...prev, `[${new Date().toLocaleTimeString('vi-VN')}] SUCCESS Evaluation completed`]);
            await loadEvalData();
            break;
          }
          try {
            const obj = JSON.parse(data);
            const level = obj.error ? 'ERROR' : obj.warning ? 'WARN' : 'INFO';
            setLogs(prev => [...prev, `[${new Date().toLocaleTimeString('vi-VN')}] ${level}  ${obj.step || obj.message || obj.error || JSON.stringify(obj)}`]);
          } catch {
            setLogs(prev => [...prev, `[${new Date().toLocaleTimeString('vi-VN')}] INFO  ${data}`]);
          }
        }
      }
    } catch (err) {
      setLogs(prev => [...prev, `[${new Date().toLocaleTimeString('vi-VN')}] ERROR ${err.message}`]);
    } finally {
      setRunning(false);
    }
  };

  const levelOptions = useMemo(() => [...new Set(dataset.map(row => row.level).filter(Boolean))].sort(), [dataset]);
  const categoryOptions = useMemo(() => [...new Set(dataset.map(row => row.category).filter(Boolean))].sort(), [dataset]);
  const statusOptions = useMemo(
    () => [...new Set(dataset.map(row => row.status || (row.answer ? 'completed' : 'pending')).filter(Boolean))].sort(),
    [dataset]
  );

  const filteredDataset = useMemo(() => {
    const needle = filters.search.trim().toLowerCase();
    return dataset.filter(row => {
      const rowStatus = row.status || (row.answer ? 'completed' : 'pending');
      const haystack = [
        row.id,
        row.query,
        row.answer,
        row.category,
        row.level,
        ...(row.expected_keywords || []),
        ...(row.expected_sources || [])
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();

      return (
        (!needle || haystack.includes(needle)) &&
        (filters.level === 'all' || row.level === filters.level) &&
        (filters.category === 'all' || row.category === filters.category) &&
        (filters.status === 'all' || rowStatus === filters.status)
      );
    });
  }, [dataset, filters]);

  useEffect(() => {
    setPage(1);
  }, [filters]);

  const trend = evalHistory.trend || [];
  const latestRuns = evalHistory.runs || [];
  const deltas = evalHistory.delta || {};
  const latestRun = latestRuns[0];

  const allProblematicCases = useMemo(() => {
    return [...dataset]
      .map(row => {
        const scores = [
          ['NDCG@5', rowScore(row, 'ndcg_5')],
          ['Faithfulness', rowScore(row, 'faithfulness')],
          ['Correctness', rowScore(row, 'correctness')],
          ['Recall@5', rowScore(row, 'recall_5')]
        ];
        const lowest = scores.sort((a, b) => Number(a[1] || 0) - Number(b[1] || 0))[0];
        const latency = Number(row.latency_seconds || 0);
        return { ...row, issueLabel: latency > 10 ? 'Latency' : lowest[0], issueValue: latency > 10 ? latency : Number(lowest[1] || 0) };
      })
      .filter(row => row.issueValue < 0.7 || row.issueLabel === 'Latency')
      .sort((a, b) => (a.issueLabel === 'Latency' ? -1 : a.issueValue) - (b.issueLabel === 'Latency' ? -1 : b.issueValue));
  }, [dataset]);
  const problematicCases = allProblematicCases.slice(0, 4);

  const progress = metrics.golden_total_cases ? (metrics.total_cases / metrics.golden_total_cases) * 100 : 0;
  const passRate = dataset.length
    ? Math.round((dataset.filter(row => (row.status || (row.answer ? 'completed' : 'pending')) === 'completed').length / dataset.length) * 100)
    : 0;
  const pageSize = 10;
  const totalPages = Math.max(1, Math.ceil(filteredDataset.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const pageRows = filteredDataset.slice((currentPage - 1) * pageSize, currentPage * pageSize);
  const pageNumbers = Array.from({ length: totalPages }, (_, idx) => idx + 1);
  const openCasesDialog = (title, rows) => setDialog({ type: 'cases', title, rows });
  const openRunsDialog = () => setDialog({ type: 'runs', title: 'Recent evaluation runs', rows: latestRuns });

  return (
    <div className="-m-6 min-h-screen bg-[#07111c] p-4 text-slate-100 md:p-6">
      <div className="mx-auto max-w-[1680px]">
        <header className="mb-5 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-white">RAG Evaluation Lab</h1>
            <p className="mt-1 text-sm text-slate-400">Evaluate RAG quality, latency and regression across golden cases.</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-2 rounded-md border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-200">
              <Database size={15} className="text-sky-300" /> GPT-4o-mini
            </span>
            <span className="rounded-md border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-200">Dataset: golden_50</span>
            <span className="rounded-md border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-200">{metrics.golden_total_cases || 50} cases</span>
            <span className="inline-flex items-center gap-2 rounded-md border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-300">
              <Clock3 size={15} /> Last run: {latestRun ? shortTime(latestRun.created_at) : 'n/a'}
            </span>
            <button onClick={loadEvalData} className="rounded-md border border-slate-700 bg-slate-950/70 p-2 text-slate-200 hover:border-sky-400 hover:text-sky-200">
              <RefreshCw size={18} />
            </button>
          </div>
        </header>

        <div className="space-y-4">
            <section className="rounded-lg border border-slate-700/70 bg-[#0b1622] p-4">
              <h2 className="mb-3 text-sm font-semibold text-white">Performance Overview</h2>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4 2xl:grid-cols-8">
                {metricMeta.map(meta => (
                  <MetricCard
                    key={meta.key}
                    meta={meta}
                    value={metricValue(metrics, meta)}
                    delta={meta.key === 'system_latency' ? (deltas.average_latency_sec ?? deltas.system_latency) : deltas[meta.key]}
                    trend={trend.map(row => (meta.key === 'system_latency' ? row.latency : row[meta.key])).filter(v => v !== undefined)}
                  />
                ))}
              </div>
            </section>

            <section className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,2fr)_minmax(360px,1fr)]">
              <div className="min-w-0 space-y-4">
                <div className="overflow-hidden rounded-lg border border-slate-700/70 bg-[#0b1622]">
                  <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
                    <div className="flex items-center gap-2">
                      <TerminalIcon size={17} className="text-slate-400" />
                      <h2 className="text-sm font-semibold text-white">Live Evaluation Terminal</h2>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={runEvaluation}
                        disabled={running}
                        className={`inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-xs font-medium ${
                          running ? 'bg-emerald-500/20 text-emerald-200' : 'bg-emerald-500/15 text-emerald-300 hover:bg-emerald-500/25'
                        }`}
                      >
                        <PlayCircle size={14} /> {running ? 'Streaming' : 'Run'}
                      </button>
                      <button className="inline-flex items-center gap-2 rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-300 hover:border-slate-500">
                        <Pause size={14} /> Pause
                      </button>
                      <button onClick={() => setLogs([])} className="rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-300 hover:border-slate-500">
                        Clear
                      </button>
                    </div>
                  </div>
                  <div className="border-b border-slate-800 bg-[#08121d] px-4 py-2 flex items-center gap-3">
                    <span className="text-xs text-slate-400 font-medium shrink-0">Ghi chú:</span>
                    <input
                      type="text"
                      value={runDescription}
                      onChange={e => setRunDescription(e.target.value)}
                      placeholder="Nhập mô tả cho lần chạy đánh giá này (ví dụ: đổi model NLU, tăng RERANK_TOP_N...)"
                      disabled={running}
                      className="flex-1 bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500 disabled:opacity-50"
                    />
                  </div>
                  <div ref={terminalRef} className="h-[190px] overflow-auto bg-[#06101a] px-5 py-4 font-mono text-xs leading-6 text-slate-300">
                    {(logs.length ? logs : [
                      '[09:12:03] INFO  Ready for evaluation run',
                      `[09:12:03] INFO  Dataset: golden_50 (${metrics.golden_total_cases || 50} cases)`,
                      '[09:12:04] INFO  Retriever: Hybrid BM25 + Vector | Reranker: Cohere',
                      '[09:12:04] INFO  Input Gateway safety enabled'
                    ]).map((line, idx) => {
                      const tone = line.includes('ERROR') ? 'text-red-300' : line.includes('WARN') ? 'text-amber-300' : line.includes('SUCCESS') ? 'text-emerald-300' : 'text-slate-300';
                      return <div key={`${line}-${idx}`} className={tone}>{line}</div>;
                    })}
                  </div>
                  <div className="grid grid-cols-2 gap-3 border-t border-slate-800 px-4 py-3 text-xs text-slate-400 md:grid-cols-6">
                    <span>Progress <b className="text-slate-100">{metrics.total_cases}/{metrics.golden_total_cases || 50}</b></span>
                    <span className="md:col-span-2">
                      <span className="inline-block h-1.5 w-full rounded-full bg-slate-800 align-middle">
                        <span className="block h-full rounded-full bg-sky-400" style={{ width: `${Math.min(100, progress)}%` }} />
                      </span>
                    </span>
                    <span>Pass <b className="text-emerald-300">{passRate}%</b></span>
                    <span>Pending <b className="text-amber-300">{metrics.pending_cases}</b></span>
                    <span>Latency <b className="text-orange-300">{metrics.system_latency.toFixed(2)}s</b></span>
                  </div>
                </div>

                <Panel title="Detailed Metric Trends" action={<span className="rounded border border-slate-700 px-2 py-1 text-xs text-slate-300">Historical performance (Last 12 runs)</span>}>
                  <div className="grid grid-cols-1 gap-x-8 gap-y-4 md:grid-cols-2">
                    {metricMeta.map(meta => {
                      const values = trend.map(row => row[meta.key === 'system_latency' ? 'latency' : meta.key]).filter(v => v !== undefined);
                      const latestValue = metricValue(metrics, meta);
                      const palette = colorClass[meta.color];
                      
                      return (
                        <div key={meta.key} className="group flex items-center gap-4 rounded-md border border-slate-800/40 bg-slate-900/20 p-2 transition-all hover:border-slate-700/60 hover:bg-slate-900/40">
                          <div className="w-24 shrink-0">
                            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{meta.label}</div>
                            <div className={`mt-0.5 text-base font-bold tabular-nums ${palette.value}`}>
                              {meta.suffix ? latestValue.toFixed(2) + meta.suffix : formatScore(latestValue)}
                            </div>
                          </div>
                          <div className="h-8 flex-1 min-w-0">
                            <Sparkline values={values} color={meta.color} latency={meta.good === 'low'} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </Panel>
              </div>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-1">
                <Panel title="Top Problematic Cases" action={<button onClick={() => openCasesDialog('All problematic cases', allProblematicCases)} className="text-xs text-sky-300 hover:text-sky-200">View all</button>}>
                  <p className="mb-3 text-xs leading-relaxed text-slate-400">Các case nổi bật theo latency cao hoặc metric thấp nhất dưới ngưỡng 0.70.</p>
                  <div className="space-y-3">
                    {(problematicCases.length ? problematicCases : dataset.slice(0, 4)).map((row, idx) => (
                      <div key={row.id || idx} className="grid grid-cols-[28px_minmax(0,1fr)] gap-2">
                        <span className={`flex h-5 w-5 items-center justify-center rounded text-xs font-semibold ${idx === 0 ? 'bg-red-500' : idx === 1 ? 'bg-orange-500' : 'bg-amber-500'}`}>{idx + 1}</span>
                        <div className="min-w-0">
                          <div className="flex items-center justify-between gap-2">
                            <p className="truncate text-sm font-medium text-slate-100">Case #{row.id || idx + 1}</p>
                            <span className="group relative rounded border border-orange-400/25 px-1.5 py-0.5 text-[10px] text-orange-300">
                              {row.issueLabel || 'Review'} {row.issueValue ? Number(row.issueValue).toFixed(row.issueLabel === 'Latency' ? 2 : 2) : ''}
                              <Tooltip>{issueDescriptions[row.issueLabel] || 'Case cần admin xem lại vì có dấu hiệu yếu hơn các case khác.'}</Tooltip>
                            </span>
                          </div>
                          <p className="mt-1 line-clamp-2 text-xs text-slate-400">{row.query}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </Panel>

                <Panel title="Recent Runs" action={<button onClick={openRunsDialog} className="text-xs text-sky-300 hover:text-sky-200">View all</button>}>
                  <div className="space-y-2">
                    {(latestRuns.length ? latestRuns.slice(0, 4) : []).map(run => (
                      <div key={run.id || run.run_name} className="flex flex-col gap-1 rounded-md py-1.5 text-sm border-b border-slate-800/40 last:border-0">
                        <div className="flex items-center justify-between gap-3">
                          <span className="min-w-0 flex items-center gap-2 text-slate-300 font-medium">
                            {run.status === 'failed' ? <XCircle size={13} className="text-red-400" /> : <CheckCircle2 size={13} className="text-lime-400" />}
                            <span className="truncate">{run.run_name}</span>
                          </span>
                          <span className="flex items-center gap-2 text-xs text-slate-500">
                            {shortTime(run.created_at)}
                            <StatusBadge status={run.status || 'completed'} />
                          </span>
                        </div>
                        {run.description && (
                          <div className="pl-5 text-xs text-slate-400 truncate" title={run.description}>
                            {run.description}
                          </div>
                        )}
                      </div>
                    ))}
                    {!latestRuns.length && <p className="text-sm text-slate-500">No eval runs recorded yet.</p>}
                  </div>
                </Panel>
              </div>
            </section>

            <section className="overflow-hidden rounded-lg border border-slate-700/70 bg-[#0b1622]">
              <div className="flex flex-col gap-3 border-b border-slate-800 px-4 py-3 xl:flex-row xl:items-center xl:justify-between">
                <div className="flex items-center gap-3">
                  <h2 className="text-sm font-semibold text-white">Golden Dataset & Results</h2>
                  <span className="rounded bg-slate-800 px-2 py-1 text-xs text-slate-300">{filteredDataset.length} cases</span>
                </div>
                <div className="flex flex-col gap-2 md:flex-row md:items-center">
                  <div className="relative">
                    <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                    <input
                      value={filters.search}
                      onChange={e => setFilters(prev => ({ ...prev, search: e.target.value }))}
                      placeholder="Search by query, case..."
                      className="h-9 w-full rounded-md border border-slate-700 bg-slate-950 pl-9 pr-3 text-xs text-slate-100 outline-none placeholder:text-slate-500 focus:border-sky-400 md:w-64"
                    />
                  </div>
                  <SelectFilter value={filters.level} onChange={level => setFilters(prev => ({ ...prev, level }))} options={levelOptions} allLabel="All levels" />
                  <SelectFilter value={filters.category} onChange={category => setFilters(prev => ({ ...prev, category }))} options={categoryOptions} allLabel="All categories" />
                  <SelectFilter value={filters.status} onChange={status => setFilters(prev => ({ ...prev, status }))} options={statusOptions} allLabel="All statuses" />
                  <button className="inline-flex h-9 items-center justify-center rounded-md border border-slate-700 px-3 text-slate-300 hover:border-slate-500">
                    <Filter size={16} />
                  </button>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[1180px] text-left text-xs">
                  <thead className="bg-slate-950/50 text-slate-400">
                    <tr>
                      <th className="px-4 py-3 font-medium">#</th>
                      <th className="px-4 py-3 font-medium">Query</th>
                      <th className="px-4 py-3 font-medium">Answer</th>
                      <th className="px-4 py-3 font-medium">Level</th>
                      <th className="px-4 py-3 font-medium">Category</th>
                      <th className="px-4 py-3 font-medium">Status</th>
                      <th className="px-4 py-3 font-medium">Metrics (R@5 / Faith / Corr / NDCG@5)</th>
                      <th className="px-4 py-3 font-medium">Latency</th>
                      <th className="px-4 py-3 font-medium">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {pageRows.map((row, idx) => {
                      const status = row.status || (row.answer ? 'completed' : 'pending');
                      const latency = Number(row.latency_seconds || 0);
                      const rowNumber = (currentPage - 1) * pageSize + idx + 1;
                      return (
                        <tr key={row.id || idx} className="hover:bg-slate-900/60">
                          <td className="px-4 py-3 text-slate-400">{rowNumber}</td>
                          <td className="max-w-[300px] px-4 py-3">
                            <div className="truncate text-slate-100">{row.query}</div>
                            <div className="mt-1 truncate text-[11px] text-slate-500">{row.id}</div>
                          </td>
                          <td className="max-w-[320px] px-4 py-3">
                            <button
                              onClick={() => setDialog({ type: 'case', title: `Case #${rowNumber}`, row })}
                              className="line-clamp-2 text-left text-slate-300 hover:text-sky-200"
                            >
                              {row.answer || 'Chưa có câu trả lời'}
                            </button>
                          </td>
                          <td className="px-4 py-3"><LevelBadge level={row.level} /></td>
                          <td className="px-4 py-3 text-slate-300">{row.category || 'unknown'}</td>
                          <td className="px-4 py-3"><StatusBadge status={status} /></td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-3">
                              <ScoreCell label="Recall@5" value={rowScore(row, 'recall_5')} />
                              <ScoreCell label="Faithfulness" value={rowScore(row, 'faithfulness')} />
                              <ScoreCell label="Correctness" value={rowScore(row, 'correctness')} />
                              <ScoreCell label="NDCG@5" value={rowScore(row, 'ndcg_5')} />
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <span className={`rounded border px-2 py-1 tabular-nums ${latency > 8 ? 'border-red-400/20 bg-red-500/10 text-red-300' : 'border-emerald-400/20 bg-emerald-500/10 text-emerald-300'}`}>
                              {latency ? `${latency.toFixed(2)}s` : 'n/a'}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-slate-400">
                            <button onClick={() => setDialog({ type: 'case', title: `Case #${rowNumber}`, row })} className="rounded p-1 hover:bg-slate-800 hover:text-sky-200">
                              <MoreVertical size={16} />
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <div className="flex flex-col gap-3 border-t border-slate-800 px-4 py-3 text-xs text-slate-400 md:flex-row md:items-center md:justify-between">
                <span>
                  Showing {filteredDataset.length ? (currentPage - 1) * pageSize + 1 : 0} to {Math.min(currentPage * pageSize, filteredDataset.length)} of {filteredDataset.length} results
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage(prev => Math.max(1, prev - 1))}
                    disabled={currentPage === 1}
                    className="rounded-md border border-slate-700 p-2 text-slate-300 disabled:cursor-not-allowed disabled:opacity-40 hover:border-slate-500"
                  >
                    <ChevronLeft size={14} />
                  </button>
                  {pageNumbers.map(num => (
                    <button
                      key={num}
                      onClick={() => setPage(num)}
                      className={`h-8 min-w-8 rounded-md border px-2 ${num === currentPage ? 'border-sky-400 bg-sky-500/15 text-sky-200' : 'border-slate-700 text-slate-300 hover:border-slate-500'}`}
                    >
                      {num}
                    </button>
                  ))}
                  <button
                    onClick={() => setPage(prev => Math.min(totalPages, prev + 1))}
                    disabled={currentPage === totalPages}
                    className="rounded-md border border-slate-700 p-2 text-slate-300 disabled:cursor-not-allowed disabled:opacity-40 hover:border-slate-500"
                  >
                    <ChevronRight size={14} />
                  </button>
                  <span className="rounded-md border border-slate-700 px-3 py-2">10 / page</span>
                </div>
              </div>
            </section>
        </div>
      </div>
      {dialog && <EvalDialog dialog={dialog} onClose={() => setDialog(null)} />}
    </div>
  );
}

function SelectFilter({ value, onChange, options, allLabel }) {
  return (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      className="h-9 rounded-md border border-slate-700 bg-slate-950 px-3 text-xs text-slate-100 outline-none focus:border-sky-400"
    >
      <option value="all">{allLabel}</option>
      {options.map(option => (
        <option key={option} value={option}>{option}</option>
      ))}
    </select>
  );
}

function Panel({ title, action, children }) {
  return (
    <section className="rounded-lg border border-slate-700/70 bg-[#0b1622] p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 className="text-sm font-semibold text-white">{title}</h2>
        {action}
      </div>
      {children}
    </section>
  );
}

function Tooltip({ children }) {
  return (
    <div className="pointer-events-none absolute left-1/2 top-full z-40 mt-2 w-64 -translate-x-1/2 rounded-lg border border-slate-700 bg-slate-950 p-3 text-xs leading-relaxed text-slate-200 opacity-0 shadow-2xl transition-opacity group-hover:opacity-100">
      {children}
    </div>
  );
}

function EvalDialog({ dialog, onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
      <div className="max-h-[88vh] w-full max-w-5xl overflow-hidden rounded-lg border border-slate-700 bg-[#0b1622] text-slate-100 shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-800 px-5 py-4">
          <h2 className="text-base font-semibold text-white">{dialog.title}</h2>
          <button onClick={onClose} className="rounded-md border border-slate-700 p-2 text-slate-300 hover:border-slate-500 hover:text-white">
            <X size={16} />
          </button>
        </div>
        <div className="max-h-[calc(88vh-65px)] overflow-auto p-5">
          {dialog.type === 'case' && <CaseDetail row={dialog.row} />}
          {dialog.type === 'cases' && <CaseList rows={dialog.rows || []} />}
          {dialog.type === 'runs' && <RunList rows={dialog.rows || []} />}
        </div>
      </div>
    </div>
  );
}

function CaseDetail({ row }) {
  if (!row) return null;
  return (
    <div className="space-y-5">
      <div>
        <p className="text-xs uppercase tracking-wide text-slate-500">Query</p>
        <p className="mt-1 text-sm leading-relaxed text-slate-100">{row.query}</p>
      </div>
      <div>
        <p className="text-xs uppercase tracking-wide text-slate-500">Answer</p>
        <pre className="mt-2 whitespace-pre-wrap rounded-lg border border-slate-800 bg-slate-950/70 p-4 text-sm leading-relaxed text-slate-200">{row.answer || 'Chưa có câu trả lời'}</pre>
      </div>
      <div className="grid gap-3 md:grid-cols-4">
        <ScoreBox label="Recall@5" value={rowScore(row, 'recall_5')} />
        <ScoreBox label="Faithfulness" value={rowScore(row, 'faithfulness')} />
        <ScoreBox label="Correctness" value={rowScore(row, 'correctness')} />
        <ScoreBox label="NDCG@5" value={rowScore(row, 'ndcg_5')} />
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <TextList title="Expected keywords" items={row.expected_keywords || []} />
        <TextList title="Expected sources" items={row.expected_sources || []} />
      </div>
    </div>
  );
}

function CaseList({ rows }) {
  if (!rows.length) return <p className="text-sm text-slate-400">Không có case nổi bật.</p>;
  return (
    <div className="space-y-3">
      {rows.map((row, idx) => (
        <div key={row.id || idx} className="rounded-lg border border-slate-800 bg-slate-950/50 p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-white">{row.id || `case_${idx + 1}`}</p>
              <p className="mt-1 line-clamp-2 text-sm text-slate-300">{row.query}</p>
            </div>
            <span className="group relative rounded border border-orange-400/25 px-2 py-1 text-xs text-orange-300">
              {row.issueLabel || 'Review'} {row.issueValue ? Number(row.issueValue).toFixed(row.issueLabel === 'Latency' ? 2 : 2) : ''}
              <Tooltip>{issueDescriptions[row.issueLabel] || 'Case cần admin xem lại.'}</Tooltip>
            </span>
          </div>
          <p className="mt-3 line-clamp-3 text-xs leading-relaxed text-slate-400">{row.answer || 'Chưa có câu trả lời'}</p>
        </div>
      ))}
    </div>
  );
}

function RunList({ rows }) {
  if (!rows.length) return <p className="text-sm text-slate-400">Chưa có lịch sử eval.</p>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[1200px] text-left text-xs">
        <thead className="text-slate-400">
          <tr>
            <th className="px-3 py-2">Run</th>
            <th className="px-3 py-2">Mô tả</th>
            <th className="px-3 py-2">Model</th>
            <th className="px-3 py-2">Dataset</th>
            <th className="px-3 py-2">Cases</th>
            <th className="px-3 py-2">Status</th>
            <th className="px-3 py-2">Recall@5</th>
            <th className="px-3 py-2">Recall@10</th>
            <th className="px-3 py-2">MRR</th>
            <th className="px-3 py-2">NDCG@5</th>
            <th className="px-3 py-2">Faithfulness</th>
            <th className="px-3 py-2">Correctness</th>
            <th className="px-3 py-2">Relevancy</th>
            <th className="px-3 py-2">Latency</th>
            <th className="px-3 py-2">Created</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {rows.map(run => (
            <tr key={run.id || run.run_name}>
              <td className="px-3 py-3 text-slate-100 font-medium">{run.run_name}</td>
              <td className="px-3 py-3 text-slate-300 max-w-[200px] truncate" title={run.description || ''}>
                {run.description || <span className="text-slate-600 italic">No description</span>}
              </td>
              <td className="px-3 py-3 text-slate-300 truncate" title={run.model_name || ''}>{run.model_name || 'gpt-4o-mini'}</td>
              <td className="px-3 py-3 text-slate-300">{run.dataset_name}</td>
              <td className="px-3 py-3 text-slate-300">{run.total_cases || 0}</td>
              <td className="px-3 py-3"><StatusBadge status={run.status || 'completed'} /></td>
              <td className="px-3 py-3 text-slate-300">{formatScore(run.retrieval?.recall_5)}</td>
              <td className="px-3 py-3 text-slate-300">{formatScore(run.retrieval?.recall_10)}</td>
              <td className="px-3 py-3 text-slate-300">{formatScore(run.retrieval?.mrr)}</td>
              <td className="px-3 py-3 text-slate-300">{formatScore(run.retrieval?.ndcg_5)}</td>
              <td className="px-3 py-3 text-slate-300">{formatScore(run.generation?.faithfulness)}</td>
              <td className="px-3 py-3 text-slate-300">{formatScore(run.generation?.correctness)}</td>
              <td className="px-3 py-3 text-slate-300">{formatScore(run.generation?.relevancy)}</td>
              <td className="px-3 py-3 text-orange-300 font-medium">{Number(run.average_latency_sec || 0).toFixed(2)}s</td>
              <td className="px-3 py-3 text-slate-400">{shortTime(run.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ScoreBox({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/50 p-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 text-xl font-semibold text-slate-100">{formatScore(value)}</p>
    </div>
  );
}

function TextList({ title, items }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/50 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">{title}</p>
      <div className="mt-2 flex flex-wrap gap-2">
        {items.length ? items.map(item => (
          <span key={item} className="rounded border border-slate-700 bg-slate-900 px-2 py-1 text-xs text-slate-300">{item}</span>
        )) : <span className="text-xs text-slate-500">Không có dữ liệu</span>}
      </div>
    </div>
  );
}
