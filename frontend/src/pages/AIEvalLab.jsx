import { useState, useRef, useEffect, useMemo } from 'react';
import { PlayCircle, Terminal as TerminalIcon, Info, Search, X } from 'lucide-react';
import { api } from '../api';

export default function AIEvalLab() {
  const [running, setRunning] = useState(false);
  const [logs, setLogs] = useState([]);
  const [metrics, setMetrics] = useState({
    retrieval: { recall_5: 0, recall_10: 0, mrr: 0, ndcg_5: 0 },
    generation: { faithfulness: 0, correctness: 0, relevancy: 0 },
    system_latency: 0,
    total_cases: 0,
    golden_total_cases: 0,
    pending_cases: 0
  });
  const [dataset, setDataset] = useState([]);
  const [evalHistory, setEvalHistory] = useState({ runs: [], trend: [], delta: {} });
  const [filters, setFilters] = useState({
    search: '',
    level: 'all',
    category: 'all',
    status: 'all'
  });
  const terminalRef = useRef(null);

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs]);

  const loadEvalData = async () => {
    const [data, history] = await Promise.all([
      api.getEvalResults(),
      api.getEvalRuns(12).catch(() => ({ runs: [], trend: [], delta: {} }))
    ]);
       if (data && data.metrics) {
         setMetrics({
           retrieval: data.metrics.retrieval || { recall_5: 0, recall_10: 0, mrr: 0, ndcg_5: 0 },
           generation: data.metrics.generation || { faithfulness: 0, correctness: 0, relevancy: 0 },
           system_latency: data.metrics.average_latency_sec || 0,
           total_cases: data.metrics.total_cases || 0,
           golden_total_cases: data.metrics.golden_total_cases || data.metrics.total_cases || 0,
           pending_cases: data.metrics.pending_cases || 0
         });
       }
       if (data && data.details) {
         setDataset(data.details);
       }
       setEvalHistory(history || { runs: [], trend: [], delta: {} });
  };

  useEffect(() => {
    loadEvalData().catch(console.error);
  }, []);

  const runEvaluation = async () => {
    if (running) return;
    setRunning(true);
    setLogs(["[SYSTEM] Khởi động quá trình đánh giá toàn diện RAGAS Benchmark..."]);
    
    try {
      const apiBase = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api';
      const response = await fetch(`${apiBase}/admin/evaluate`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const text = decoder.decode(value);
        const lines = text.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data.trim() === '[DONE]') {
               setLogs(prev => [...prev, "[SYSTEM] Quá trình đánh giá hoàn tất."]);
               loadEvalData().catch(console.error);
               break;
            }
            try {
              const obj = JSON.parse(data);
              setLogs(prev => [...prev, `[INFO] ${obj.step || obj.message || obj.error || JSON.stringify(obj)}`]);
            } catch {
              setLogs(prev => [...prev, `> ${data}`]);
            }
          }
        }
      }
    } catch (err) {
      setLogs(prev => [...prev, "[ERROR] Lỗi khi chạy đánh giá: " + err.message]);
    }
    setRunning(false);
  };

  const METRIC_DESCS = {
    "Recall@5": "Tỉ lệ tài liệu thực sự liên quan được tìm thấy trong Top 5 kết quả tìm kiếm. Thể hiện chất lượng tìm kiếm dữ liệu.",
    "Recall@10": "Tỉ lệ tài liệu thực sự liên quan được tìm thấy trong Top 10 kết quả tìm kiếm. Đo lường độ phủ thông tin tối đa.",
    "Mean Reciprocal Rank": "Đánh giá chất lượng xếp hạng của tài liệu đúng đầu tiên. Càng gần 1.0 nghĩa là tài liệu chính xác nhất ở vị trí đầu.",
    "NDCG@5": "Normalized Discounted Cumulative Gain tại Top 5. Đo lường chất lượng xếp hạng dựa trên vị trí và độ liên quan của tài liệu.",
    "Faithfulness": "Độ trung thực: Thể hiện câu trả lời của AI có hoàn toàn dựa vào ngữ cảnh được truy vấn hay không, nhằm loại bỏ ảo giác.",
    "Answer Correctness": "Độ chính xác: So sánh sự tương đồng về nghĩa và thông tin giữa câu trả lời sinh ra so với đáp án chuẩn.",
    "Answer Relevancy": "Độ phù hợp: Đo lường mức độ tập trung trực diện của câu trả lời đối với câu hỏi gốc, tránh trả lời lan man.",
    "System Latency": "Độ trễ hệ thống: Thời gian xử lý trung bình cho mỗi truy vấn từ lúc nhận câu hỏi đến khi hoàn tất câu trả lời."
  };

  const hardCases = dataset.filter(row => row.level === 'hard').length;
  const pdfCases = dataset.filter(row => (row.expected_sources || []).some(source => source.startsWith('Chinh_sach') || source.startsWith('Chuong_trinh'))).length;
  const levelOptions = useMemo(() => [...new Set(dataset.map(row => row.level).filter(Boolean))].sort(), [dataset]);
  const categoryOptions = useMemo(() => [...new Set(dataset.map(row => row.category).filter(Boolean))].sort(), [dataset]);
  const statusOptions = useMemo(() => [...new Set(dataset.map(row => row.status || (row.answer ? 'completed' : 'pending')).filter(Boolean))].sort(), [dataset]);
  const filteredDataset = useMemo(() => {
    const needle = filters.search.trim().toLowerCase();
    return dataset.filter(row => {
      const rowStatus = row.status || (row.answer ? 'completed' : 'pending');
      const matchesSearch = !needle || [
        row.id,
        row.query,
        row.answer,
        row.category,
        row.level,
        ...(row.expected_keywords || []),
        ...(row.expected_sources || [])
      ].filter(Boolean).join(' ').toLowerCase().includes(needle);
      return (
        matchesSearch &&
        (filters.level === 'all' || row.level === filters.level) &&
        (filters.category === 'all' || row.category === filters.category) &&
        (filters.status === 'all' || rowStatus === filters.status)
      );
    });
  }, [dataset, filters]);
  const slowCases = dataset
    .filter(row => row.latency_seconds)
    .sort((a, b) => (b.latency_seconds || 0) - (a.latency_seconds || 0))
    .slice(0, 3);
  const latestRuns = evalHistory.runs || [];
  const historyDelta = evalHistory.delta || {};

  const formatDelta = (value, lowerIsBetter = false) => {
    if (value === null || value === undefined) return 'n/a';
    const isGood = lowerIsBetter ? value < 0 : value > 0;
    const sign = value > 0 ? '+' : '';
    return `${isGood ? '↑' : value === 0 ? '→' : '↓'} ${sign}${value.toFixed(3)}`;
  };

  const CircularProgress = ({ value, label, colorClass }) => {
    const dashArray = 364.4;
    const dashOffset = dashArray - (dashArray * value);
    
    return (
      <div className="glass-panel p-6 rounded-2xl flex flex-col items-center relative group/tooltip">
        <div className="flex items-center gap-1.5 mb-4 h-8 justify-center w-full">
          <p className="text-xs font-bold text-on-surface-variant uppercase tracking-widest text-center">{label}</p>
          <div className="relative text-on-surface-variant/40 hover:text-primary transition-colors cursor-help">
            <Info size={13} />
            <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-3.5 w-64 p-3.5 backdrop-blur-md border border-white/10 text-white text-xs rounded-xl shadow-2xl opacity-0 scale-95 pointer-events-none group-hover/tooltip:opacity-100 group-hover/tooltip:scale-100 transition-all duration-200 ease-out normal-case tracking-normal" style={{ backgroundColor: '#0b121e' }}>
              <p className="font-bold text-primary mb-1 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span>
                {label}
              </p>
              <p className="text-white/80 leading-relaxed font-medium">{METRIC_DESCS[label] || ""}</p>
              <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent" style={{ borderTopColor: '#0b121e' }}></div>
            </div>
          </div>
        </div>
        <div className="relative w-28 h-28 flex items-center justify-center">
          <svg className="w-full h-full -rotate-90">
            <circle className="text-surface-container-high" cx="56" cy="56" fill="transparent" r="50" stroke="currentColor" strokeWidth="6"></circle>
            <circle className={`${colorClass} transition-all duration-1000`} cx="56" cy="56" fill="transparent" r="50" stroke="currentColor" strokeDasharray={dashArray} strokeDashoffset={dashOffset} strokeWidth="6"></circle>
          </svg>
          <span className={`absolute text-2xl font-bold ${colorClass}`}>{value.toFixed(2)}</span>
        </div>
      </div>
    );
  };

  return (
    <div className="max-w-[1600px] mx-auto w-full pb-20">
      {/* Hero Section */}
      <section className="mb-12 relative w-full">
        <div className="glass-panel p-12 rounded-3xl flex flex-col items-center justify-center text-center relative overflow-hidden bg-white/60">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-primary to-transparent animate-pulse"></div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4 text-on-surface">Phòng Thử Nghiệm Đánh Giá RAG</h1>
          <p className="text-lg text-on-surface-variant max-w-2xl mb-8">
             Thực thi đánh giá RAGAS độ chính xác cao trên toàn bộ pipeline AI. Đo lường chuyên sâu Retrieval Metrics (Recall, MRR, NDCG) & Generation Metrics (Faithfulness, Correctness, Relevancy).
          </p>
          <button 
            onClick={runEvaluation} 
            disabled={running}
            className={`group relative px-10 py-5 rounded-full font-bold shadow-lg transition-all flex items-center gap-4 ${
              running 
                ? 'bg-surface-variant text-on-surface-variant cursor-not-allowed' 
                : 'bg-gradient-to-r from-primary to-secondary text-white hover:scale-105 active:scale-95 hover:shadow-[0_20px_50px_rgba(0,200,151,0.3)]'
            }`}
          >
            <PlayCircle size={32} />
            {running ? 'Đang chạy đánh giá...' : 'Run Full System Evaluation'}
            {!running && <div className="absolute inset-0 rounded-full border-2 border-white/30 animate-pulse"></div>}
          </button>
        </div>
      </section>

      {/* Metrics Grid */}
      <div className="mb-12">
          <h2 className="text-2xl font-bold mb-6 text-on-surface flex items-center gap-2">
            <span className="w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center text-sm">1</span>
            Retrieval Metrics
          </h2>
          <section className="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <CircularProgress value={metrics.retrieval.recall_5 || 0} label="Recall@5" colorClass="text-blue-500" />
            <CircularProgress value={metrics.retrieval.recall_10 || 0} label="Recall@10" colorClass="text-indigo-500" />
            <CircularProgress value={metrics.retrieval.mrr || 0} label="Mean Reciprocal Rank" colorClass="text-violet-500" />
            <CircularProgress value={metrics.retrieval.ndcg_5 || 0} label="NDCG@5" colorClass="text-fuchsia-500" />
          </section>

          <h2 className="text-2xl font-bold mb-6 text-on-surface flex items-center gap-2">
            <span className="w-8 h-8 rounded-full bg-secondary/20 text-secondary flex items-center justify-center text-sm">2</span>
            Generation Metrics & Latency
          </h2>
          <section className="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
            <CircularProgress value={metrics.generation.faithfulness || 0} label="Faithfulness" colorClass="text-emerald-500" />
            <CircularProgress value={metrics.generation.correctness || 0} label="Answer Correctness" colorClass="text-teal-500" />
            <CircularProgress value={metrics.generation.relevancy || 0} label="Answer Relevancy" colorClass="text-cyan-500" />
            
            <div className="glass-panel p-6 rounded-2xl flex flex-col items-center justify-center bg-orange-500/10 border border-orange-500/20 relative group/tooltip">
              <div className="flex items-center gap-1.5 mb-4 justify-center w-full">
                <p className="text-xs font-bold text-orange-600 uppercase tracking-widest">System Latency</p>
                <div className="relative text-orange-600/55 hover:text-orange-500 transition-colors cursor-help">
                  <Info size={13} />
                  <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-3.5 w-64 p-3.5 backdrop-blur-md border border-white/10 text-white text-xs rounded-xl shadow-2xl opacity-0 scale-95 pointer-events-none group-hover/tooltip:opacity-100 group-hover/tooltip:scale-100 transition-all duration-200 ease-out normal-case tracking-normal" style={{ backgroundColor: '#0b121e' }}>
                    <p className="font-bold text-orange-400 mb-1 flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse"></span>
                      System Latency
                    </p>
                    <p className="text-white/80 leading-relaxed font-medium">{METRIC_DESCS["System Latency"]}</p>
                    <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent" style={{ borderTopColor: '#0b121e' }}></div>
                  </div>
                </div>
              </div>
              <span className="text-4xl font-black text-orange-500 mb-2">{metrics.system_latency.toFixed(2)}s</span>
              <p className="text-sm font-medium text-orange-600/70">Avg per query</p>
              <p className="text-xs text-orange-600/50 mt-2">Total cases: {metrics.total_cases}</p>
            </div>
          </section>
      </div>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-12">
        <div className="glass-panel p-6 rounded-2xl border border-outline-variant/40">
          <p className="text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-2">Scoring Mode</p>
          <h3 className="text-xl font-bold text-on-surface mb-3">LLM-as-Judge + heuristic</h3>
          <p className="text-sm leading-relaxed text-on-surface-variant">
            Generation metrics được chấm bởi OpenAI gpt-4o-mini khi có API key. Retrieval metrics dùng keyword/source heuristic, riêng Recall@5 có thể được judge ghi đè bằng context_recall.
          </p>
        </div>
        <div className="glass-panel p-6 rounded-2xl border border-outline-variant/40">
          <p className="text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-2">Dataset Stress</p>
          <h3 className="text-xl font-bold text-on-surface mb-3">{metrics.golden_total_cases || metrics.total_cases || dataset.length || 0} cases</h3>
          <p className="text-sm leading-relaxed text-on-surface-variant">
            Report hiện có {hardCases} case khó và {pdfCases} case yêu cầu đọc tài liệu PDF/chính sách. {metrics.pending_cases > 0 ? `${metrics.pending_cases} case mới sẽ có kết quả sau lần chạy benchmark tiếp theo.` : 'Report hiện đã khớp số case golden.'}
          </p>
        </div>
        <div className="glass-panel p-6 rounded-2xl border border-orange-500/20 bg-orange-500/5">
          <p className="text-xs font-bold text-orange-600 uppercase tracking-widest mb-2">Latency Notes</p>
          <h3 className="text-xl font-bold text-orange-500 mb-3">{metrics.system_latency.toFixed(2)}s avg</h3>
          <p className="text-sm leading-relaxed text-orange-700/80">
            Benchmark latency gồm pipeline trả lời và một lượt LLM judge sau đó. Các case chậm thường do NLU LLM, rerank, context dài và generation dài.
          </p>
        </div>
      </section>

      <section className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-12">
        <div className="glass-panel p-6 rounded-2xl border border-outline-variant/40">
          <div className="flex items-center justify-between gap-4 mb-5">
            <div>
              <h2 className="text-2xl font-bold text-on-surface">Metric Trends</h2>
              <p className="text-xs text-on-surface-variant mt-1">Latest run compared with the previous saved run</p>
            </div>
            <span className="text-xs font-bold text-primary uppercase tracking-widest">{latestRuns.length} saved runs</span>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
            {[
              ['Recall@5', historyDelta.recall_5, false],
              ['Faith', historyDelta.faithfulness, false],
              ['Correct', historyDelta.correctness, false],
              ['NDCG@5', historyDelta.ndcg_5, false],
              ['Latency', historyDelta.latency, true],
            ].map(([label, value, lowerIsBetter]) => (
              <div key={label} className="rounded-xl border border-outline-variant/40 p-4 bg-surface-container/40">
                <p className="text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-2">{label}</p>
                <p className={`text-lg font-black ${value === null || value === undefined ? 'text-on-surface-variant' : (lowerIsBetter ? value < 0 : value > 0) ? 'text-emerald-500' : value === 0 ? 'text-on-surface-variant' : 'text-orange-500'}`}>
                  {formatDelta(value, lowerIsBetter)}
                </p>
              </div>
            ))}
          </div>
          {latestRuns.length === 0 && (
            <p className="text-sm text-on-surface-variant mt-4">No saved evaluation runs yet. Run a benchmark to start tracking improvement.</p>
          )}
        </div>

        <div className="glass-panel p-6 rounded-2xl border border-outline-variant/40">
          <div className="flex items-center justify-between gap-4 mb-5">
            <div>
              <h2 className="text-2xl font-bold text-on-surface">Recent Runs</h2>
              <p className="text-xs text-on-surface-variant mt-1">Saved in the evaluation_runs table</p>
            </div>
            <span className="text-xs font-bold text-secondary uppercase tracking-widest">History</span>
          </div>
          <div className="space-y-3 max-h-64 overflow-y-auto pr-1">
            {latestRuns.slice(0, 6).map(run => (
              <div key={run.id} className="flex items-center justify-between gap-4 rounded-xl border border-outline-variant/40 p-4 bg-surface-container/40">
                <div className="min-w-0">
                  <p className="font-mono text-xs font-bold text-on-surface truncate">{run.run_name}</p>
                  <p className="text-xs text-on-surface-variant mt-1">{run.dataset_name} · {run.model_name || 'model n/a'} · {run.total_cases} cases</p>
                </div>
                <div className="text-right shrink-0">
                  <span className={`px-2 py-1 rounded-md text-[11px] font-bold ${run.status === 'completed' ? 'bg-emerald-500/10 text-emerald-600' : 'bg-red-500/10 text-red-500'}`}>
                    {run.status}
                  </span>
                  <p className="font-mono text-xs text-orange-500 mt-2">{(run.average_latency_sec || 0).toFixed(2)}s</p>
                </div>
              </div>
            ))}
            {latestRuns.length === 0 && (
              <p className="text-sm text-on-surface-variant">No evaluation history found.</p>
            )}
          </div>
        </div>
      </section>

      {slowCases.length > 0 && (
        <section className="glass-panel p-6 rounded-2xl mb-12 border border-outline-variant/40">
          <div className="flex items-center justify-between gap-4 mb-4">
            <h2 className="text-2xl font-bold text-on-surface">Slowest Cases</h2>
            <span className="text-xs font-bold text-orange-500 uppercase tracking-widest">Latency audit</span>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {slowCases.map(row => (
              <div key={row.id || row.query} className="rounded-xl border border-outline-variant/40 p-4 bg-surface-container/40">
                <div className="flex items-center justify-between gap-3 mb-3">
                  <span className="text-xs font-bold text-primary uppercase">{row.level || 'case'}</span>
                  <span className="font-mono text-sm font-bold text-orange-500">{row.latency_seconds}s</span>
                </div>
                <p className="text-sm font-semibold text-on-surface line-clamp-2 mb-2">{row.query}</p>
                <p className="text-xs text-on-surface-variant">
                  Chunks: {row.num_chunks_before_expansion || 0} · Context: {row.compressed_context_len || 0} chars
                </p>
              </div>
            ))}
          </div>
        </section>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        {/* Terminal View */}
        <section className="w-full">
          <h2 className="text-2xl font-bold mb-6 text-on-surface">Evaluation Logs</h2>
          <div className="bg-[#0b121e] rounded-2xl overflow-hidden border border-outline-variant/30 shadow-2xl">
            <div className="flex items-center px-4 py-3 bg-white/5 border-b border-white/10">
              <div className="flex gap-2 mr-4">
                <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
                <div className="w-3 h-3 rounded-full bg-yellow-500/80"></div>
                <div className="w-3 h-3 rounded-full bg-green-500/80"></div>
              </div>
              <div className="flex items-center gap-2 text-white/50 text-xs font-mono">
                <TerminalIcon size={14} />
                <span>ragas_evaluation_pipeline.sh</span>
              </div>
            </div>
            <div 
              ref={terminalRef}
              className="p-6 h-[600px] overflow-y-auto font-mono text-sm"
              style={{ scrollBehavior: 'smooth' }}
            >
              {logs.length === 0 ? (
                 <div className="text-white/30 italic">Nhấn nút Run phía trên để bắt đầu đánh giá hệ thống...</div>
              ) : (
                logs.map((log, i) => (
                  <div key={i} className={`mb-2 ${log.includes('[ERROR]') ? 'text-red-400' : log.includes('[SYSTEM]') ? 'text-blue-400' : 'text-green-400'}`}>
                    {log}
                  </div>
                ))
              )}
              {running && (
                <div className="flex items-center gap-2 mt-4 text-white/50">
                  <span className="animate-pulse">_</span>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Dataset View */}
        <section className="w-full">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-6">
            <div>
              <h2 className="text-2xl font-bold text-on-surface">Golden Dataset & Results</h2>
              <p className="text-xs text-on-surface-variant mt-1">
                Showing {filteredDataset.length}/{dataset.length} cases
              </p>
            </div>
            <button
              onClick={() => setFilters({ search: '', level: 'all', category: 'all', status: 'all' })}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-outline-variant text-sm font-semibold text-on-surface-variant hover:text-primary hover:border-primary/40 transition-colors"
            >
              <X size={16} />
              Clear filters
            </button>
          </div>

          <div className="glass-panel rounded-2xl border border-outline-variant p-4 mb-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
              <label className="relative md:col-span-1">
                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant/60" />
                <input
                  value={filters.search}
                  onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                  placeholder="Search ID, query, answer..."
                  className="w-full h-11 pl-10 pr-3 rounded-xl bg-surface-container border border-outline-variant text-sm outline-none focus:border-primary"
                />
              </label>
              <select
                value={filters.level}
                onChange={(e) => setFilters(prev => ({ ...prev, level: e.target.value }))}
                className="h-11 rounded-xl bg-surface-container border border-outline-variant px-3 text-sm font-semibold outline-none focus:border-primary"
              >
                <option value="all">All levels</option>
                {levelOptions.map(level => <option key={level} value={level}>{level}</option>)}
              </select>
              <select
                value={filters.category}
                onChange={(e) => setFilters(prev => ({ ...prev, category: e.target.value }))}
                className="h-11 rounded-xl bg-surface-container border border-outline-variant px-3 text-sm font-semibold outline-none focus:border-primary"
              >
                <option value="all">All categories</option>
                {categoryOptions.map(category => <option key={category} value={category}>{category}</option>)}
              </select>
              <select
                value={filters.status}
                onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
                className="h-11 rounded-xl bg-surface-container border border-outline-variant px-3 text-sm font-semibold outline-none focus:border-primary"
              >
                <option value="all">All statuses</option>
                {statusOptions.map(status => <option key={status} value={status}>{status}</option>)}
              </select>
            </div>
          </div>
          <div className="glass-panel rounded-2xl overflow-hidden border border-outline-variant h-[650px] flex flex-col">
            <div className="overflow-y-auto flex-1 p-0">
              <table className="w-full text-left text-sm">
                <thead className="bg-surface-variant text-on-surface-variant sticky top-0 backdrop-blur-md bg-opacity-90">
                  <tr>
                    <th className="px-6 py-4 font-bold">Case</th>
                    <th className="px-6 py-4 font-bold">Query</th>
                    <th className="px-6 py-4 font-bold">Expected Keywords</th>
                    <th className="px-6 py-4 font-bold">AI Answer</th>
                    <th className="px-6 py-4 font-bold">Scores</th>
                    <th className="px-6 py-4 font-bold">Latency</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-outline-variant/30">
                  {filteredDataset.map((row, idx) => {
                    const rowStatus = row.status || (row.answer ? 'completed' : 'pending');
                    return (
                    <tr key={row.id || idx} className="hover:bg-surface-variant/20 transition-colors">
                      <td className="px-6 py-4 align-top min-w-[190px]">
                        <p className="font-mono text-xs font-bold text-on-surface">{row.id || '-'}</p>
                        <div className="flex flex-wrap gap-1 mt-2">
                          <span className="px-2 py-1 rounded-md bg-secondary/10 text-secondary text-[11px] font-bold uppercase">{row.level || 'n/a'}</span>
                          <span className="px-2 py-1 rounded-md bg-primary/10 text-primary text-[11px] font-bold">{row.category || 'general'}</span>
                          <span className={`px-2 py-1 rounded-md text-[11px] font-bold ${rowStatus === 'completed' ? 'bg-emerald-500/10 text-emerald-600' : 'bg-orange-500/10 text-orange-600'}`}>{rowStatus}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 align-top font-medium min-w-[260px]">{row.query}</td>
                      <td className="px-6 py-4 align-top min-w-[220px]">
                        <div className="flex flex-wrap gap-1">
                          {(row.expected_keywords || []).map((kw, i) => (
                            <span key={i} className="px-2 py-1 bg-primary/10 text-primary rounded-md text-xs font-semibold whitespace-nowrap">
                              {kw}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-6 py-4 align-top w-2/4">
                        <p className="line-clamp-3 text-on-surface-variant" title={row.answer}>
                          {row.answer || "N/A"}
                        </p>
                      </td>
                      <td className="px-6 py-4 align-top font-mono text-xs min-w-[140px]">
                        <div className="space-y-1 text-on-surface-variant">
                          <p>Faith: {(row.generation?.faithfulness ?? 0).toFixed(2)}</p>
                          <p>Correct: {(row.generation?.correctness ?? 0).toFixed(2)}</p>
                          <p>R@5: {(row.retrieval?.recall_5 ?? 0).toFixed(2)}</p>
                        </div>
                      </td>
                      <td className="px-6 py-4 align-top font-mono text-xs text-orange-500 whitespace-nowrap">
                        {row.latency_seconds ? `${row.latency_seconds}s` : '-'}
                      </td>
                    </tr>
                  )})}
                  {filteredDataset.length === 0 && (
                    <tr>
                      <td colSpan="6" className="px-6 py-12 text-center text-on-surface-variant italic">
                        No cases match the current filters.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
