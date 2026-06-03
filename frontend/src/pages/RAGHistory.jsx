import { useState, useEffect } from 'react';
import { History, Search, ShieldAlert, ShieldCheck, PlayCircle } from 'lucide-react';
import { api } from '../api';

export default function RAGHistory() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const data = await api.getAdminLogs();
        setLogs(data || []);
      } catch (err) {
        console.error(err);
      }
      setLoading(false);
    };
    fetchLogs();
  }, []);

  const handleManualEval = (logId) => {
    // In a real app, we would call an API to evaluate this specific request
    // api.evaluateRequest(logId)
    alert(`Triggered manual evaluation for log ${logId}`);
  };

  if (loading) return <div className="p-8 text-on-surface-variant animate-pulse">Loading RAG history...</div>;

  return (
    <div className="max-w-[1600px] mx-auto w-full">
      {/* Header */}
      <div className="mb-10 flex justify-between items-end">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="inline-block w-3 h-3 rounded-full bg-primary animate-pulse shadow-[0_0_10px_#00c897]"></span>
            <span className="text-primary text-xs font-bold tracking-widest uppercase">System Logs</span>
          </div>
          <h2 className="text-3xl md:text-4xl font-bold text-on-surface">Lịch Sử RAG & Đánh Giá</h2>
          <p className="text-lg text-on-surface-variant mt-2 max-w-2xl">
            Giám sát toàn bộ lịch sử truy vấn của người dùng. Đánh giá chất lượng câu trả lời bằng hệ thống RAGAS.
          </p>
        </div>
        <div className="relative w-64 hidden md:block">
          <input 
            type="text" 
            placeholder="Tìm kiếm truy vấn..." 
            className="w-full bg-white/60 border border-outline-variant/50 focus:ring-2 focus:ring-primary/40 focus:border-primary outline-none pl-10 pr-4 py-2.5 rounded-full transition-all text-on-surface font-medium shadow-sm"
          />
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant/50" size={18} />
        </div>
      </div>

      {/* Grid List */}
      <div className="flex flex-col gap-4">
        {logs.map((log) => (
          <div key={log.id} className="glass-panel p-6 rounded-2xl flex flex-col gap-4 border border-outline-variant/30 hover:border-primary/30 transition-all group">
            
            <div className="flex justify-between items-start">
              <div className="flex gap-3 items-start flex-1">
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary shrink-0">
                  <History size={20} />
                </div>
                <div className="flex-1">
                  <h4 className="font-bold text-on-surface text-lg">{log.original_query || 'Unknown'}</h4>
                  {log.rewritten_query && log.rewritten_query !== log.original_query && (
                    <p className="text-xs text-on-surface-variant/80 italic mt-1 bg-on-surface-variant/5 px-2 py-1 rounded">
                      📝 Viết lại: {log.rewritten_query}
                    </p>
                  )}
                  <div className="text-xs text-on-surface-variant flex gap-4 mt-2 font-medium flex-wrap">
                    <span>🕐 {new Date(log.created_at + 'Z').toLocaleString('vi-VN')}</span>
                    <span>ID: <span className="font-mono">{log.conversation_id?.substring(0, 8) || 'N/A'}...</span></span>
                  </div>
                </div>
              </div>
              
              <div className="flex flex-col items-end gap-2">
                {log.blocked_by_guardrail ? (
                  <span className="flex items-center gap-1 text-xs font-bold bg-error/10 text-error px-3 py-1.5 rounded-full border border-error/20">
                    <ShieldAlert size={14} /> Bị chặn
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-xs font-bold bg-primary/10 text-primary px-3 py-1.5 rounded-full border border-primary/20">
                    <ShieldCheck size={14} /> An toàn
                  </span>
                )}
              </div>
            </div>

            {/* Detailed Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3 pb-3 border-b border-outline-variant/20">
              <div className="bg-surface-container-low p-3 rounded-lg">
                <p className="text-xs text-on-surface-variant/70 font-semibold">⏱️ Tổng thời gian</p>
                <p className="text-sm font-bold text-primary">{(log.total_latency_ms || 0).toFixed(0)}ms</p>
              </div>
              <div className="bg-surface-container-low p-3 rounded-lg">
                <p className="text-xs text-on-surface-variant/70 font-semibold">🔍 Search</p>
                <p className="text-sm font-bold text-secondary">{(log.search_latency_ms || 0).toFixed(0)}ms</p>
              </div>
              <div className="bg-surface-container-low p-3 rounded-lg">
                <p className="text-xs text-on-surface-variant/70 font-semibold">🤖 Generation</p>
                <p className="text-sm font-bold text-blue-500">{(log.generation_latency_ms || 0).toFixed(0)}ms</p>
              </div>
              <div className="bg-surface-container-low p-3 rounded-lg">
                <p className="text-xs text-on-surface-variant/70 font-semibold">💰 Cost</p>
                <p className="text-sm font-bold text-on-surface">${(log.cost_usd || 0).toFixed(6)}</p>
              </div>
            </div>

            {/* Token Count */}
            <div className="flex gap-3 items-center">
              <span className="text-xs font-mono bg-surface-container-high px-3 py-1 rounded text-on-surface-variant font-bold border border-outline-variant/30">
                📊 {log.total_tokens || 0} tokens
              </span>
              <span className="text-xs font-semibold text-on-surface-variant">
                (Input tokens + Output tokens)
              </span>
            </div>

            <div className="bg-surface-lowest p-4 rounded-xl text-sm text-on-surface border border-outline-variant/20 mt-2 line-clamp-3">
              <span className="font-bold text-primary mr-2">AI Trả lời:</span>
              {log.final_answer || <span className="italic text-on-surface-variant/50">Không có câu trả lời (bị chặn hoặc lỗi)</span>}
            </div>

            <div className="flex justify-between items-center mt-2 pt-4 border-t border-outline-variant/20">
              <div className="flex gap-2">
                {log.ragas_faithfulness && (
                  <span className="text-xs font-bold bg-secondary/10 text-secondary px-2 py-1 rounded border border-secondary/20">
                    Faithfulness: {log.ragas_faithfulness.toFixed(2)}
                  </span>
                )}
                {log.ragas_relevancy && (
                  <span className="text-xs font-bold bg-blue-500/10 text-blue-500 px-2 py-1 rounded border border-blue-500/20">
                    Relevancy: {log.ragas_relevancy.toFixed(2)}
                  </span>
                )}
              </div>
              
              <button 
                onClick={() => handleManualEval(log.id)}
                className="text-sm font-bold text-primary flex items-center gap-2 hover:bg-primary/10 px-4 py-2 rounded-full transition-colors"
              >
                <PlayCircle size={18} /> Chấm Điểm Request Này
              </button>
            </div>

          </div>
        ))}

        {logs.length === 0 && (
          <div className="text-center p-12 glass-panel rounded-2xl border border-outline-variant/30">
            <History size={48} className="mx-auto text-on-surface-variant/30 mb-4" />
            <h3 className="text-xl font-bold text-on-surface-variant">Chưa có dữ liệu lịch sử</h3>
            <p className="text-on-surface-variant/70 mt-2">Hệ thống chưa ghi nhận truy vấn nào.</p>
          </div>
        )}
      </div>
    </div>
  );
}
