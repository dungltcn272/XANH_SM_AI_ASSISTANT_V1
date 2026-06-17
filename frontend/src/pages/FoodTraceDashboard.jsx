import { useState, useEffect } from 'react';
import { Database, Search, Filter, Loader2, ChevronDown, ChevronRight, Activity, MapPin, Tag } from 'lucide-react';
import { api } from '../api';

export default function FoodTraceDashboard() {
  const [traces, setTraces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [expandedRow, setExpandedRow] = useState(null);

  useEffect(() => {
    fetchTraces();
  }, []);

  const fetchTraces = async () => {
    try {
      setLoading(true);
      const data = await api.getFoodTraces(0, 50);
      setTraces(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const toggleRow = (id) => {
    setExpandedRow(expandedRow === id ? null : id);
  };

  return (
    <div className="flex flex-col h-full space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-primary flex items-center gap-2">
            <Database size={28} />
            Food Recommendation Logs
          </h1>
          <p className="text-sm text-on-surface-variant mt-1">
            Theo dõi chi tiết các lượt gợi ý món ăn, điểm số recall và ranking
          </p>
        </div>
        <div className="bg-surface-container py-2 px-4 rounded-xl shadow-sm text-sm font-semibold border border-outline-variant/30 flex items-center gap-2">
          <span>Tổng số lượt gợi ý:</span>
          <span className="text-primary text-lg">{total}</span>
        </div>
      </div>

      <div className="glass-panel p-6 rounded-3xl flex-1 flex flex-col border border-outline-variant/30 overflow-hidden shadow-sm">
        <div className="flex items-center gap-4 mb-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant" size={18} />
            <input 
              type="text" 
              placeholder="Tìm kiếm theo truy vấn, intent..." 
              className="w-full bg-surface-container pl-10 pr-4 py-2.5 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 text-on-surface border border-outline-variant/20 transition-all shadow-inner"
            />
          </div>
          <button className="p-2.5 rounded-full bg-surface-container hover:bg-surface-variant text-on-surface-variant border border-outline-variant/20 transition-all flex items-center gap-2 shadow-sm text-sm font-semibold">
            <Filter size={18} />
            <span>Lọc nâng cao</span>
          </button>
        </div>

        <div className="flex-1 overflow-auto rounded-2xl border border-outline-variant/20">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-surface-variant/50 sticky top-0 z-10 text-xs uppercase tracking-wider font-semibold text-on-surface-variant">
              <tr>
                <th className="px-4 py-3"></th>
                <th className="px-4 py-3">Thời gian</th>
                <th className="px-4 py-3">Truy vấn (Original)</th>
                <th className="px-4 py-3">Intent</th>
                <th className="px-4 py-3">Lat/Lng</th>
                <th className="px-4 py-3">Ứng viên / Trả về</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/20 bg-surface">
              {loading ? (
                <tr>
                  <td colSpan="6" className="text-center py-12">
                    <Loader2 className="animate-spin mx-auto text-primary" size={24} />
                  </td>
                </tr>
              ) : traces.length === 0 ? (
                <tr>
                  <td colSpan="6" className="text-center py-12 text-on-surface-variant italic">
                    Chưa có lịch sử gợi ý món ăn.
                  </td>
                </tr>
              ) : (
                traces.map((t) => {
                  let loc = {};
                  try { loc = JSON.parse(t.location_json); } catch(e) {}
                  let stats = {};
                  try { stats = JSON.parse(t.candidate_stats_json); } catch(e) {}
                  
                  return (
                    <React.Fragment key={t.trace_id}>
                      <tr 
                        className={`hover:bg-surface-variant/30 cursor-pointer transition-colors ${expandedRow === t.trace_id ? 'bg-primary/5' : ''}`}
                        onClick={() => toggleRow(t.trace_id)}
                      >
                        <td className="px-4 py-3 text-on-surface-variant">
                          {expandedRow === t.trace_id ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                        </td>
                        <td className="px-4 py-3">
                          {new Date(t.created_at).toLocaleString('vi-VN')}
                        </td>
                        <td className="px-4 py-3 font-semibold text-primary truncate max-w-[200px]" title={t.original_query}>
                          {t.original_query}
                        </td>
                        <td className="px-4 py-3">
                          <span className="px-2 py-1 bg-secondary/10 text-secondary rounded-lg text-xs font-bold">
                            {t.intent}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-on-surface-variant text-xs">
                          {loc.lat && loc.lng ? `${loc.lat.toFixed(4)}, ${loc.lng.toFixed(4)}` : 'N/A'}
                        </td>
                        <td className="px-4 py-3 text-xs">
                          <span className="font-semibold">{stats.total_candidates || 0}</span> / {stats.returned_count || 0}
                        </td>
                      </tr>
                      
                      {expandedRow === t.trace_id && (
                        <tr className="bg-surface-variant/10">
                          <td colSpan="6" className="p-4 border-b border-outline-variant/30">
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                              <div className="bg-surface p-4 rounded-xl border border-outline-variant/20 shadow-sm">
                                <h4 className="font-bold mb-3 flex items-center gap-2 text-primary">
                                  <Activity size={16} /> Chi tiết Pipeline
                                </h4>
                                <div className="space-y-2 text-xs">
                                  <p><strong>Query Rewritten:</strong> {t.rewritten_query}</p>
                                  <p><strong>NLU:</strong> <pre className="bg-surface-container p-2 rounded mt-1 overflow-x-auto">{t.nlu_json}</pre></p>
                                  <p><strong>Context:</strong> <pre className="bg-surface-container p-2 rounded mt-1 overflow-x-auto">{t.user_context_json}</pre></p>
                                </div>
                              </div>
                              <div className="bg-surface p-4 rounded-xl border border-outline-variant/20 shadow-sm">
                                <h4 className="font-bold mb-3 flex items-center gap-2 text-secondary">
                                  <Tag size={16} /> Kết quả LLM
                                </h4>
                                <div className="space-y-2 text-xs h-full">
                                  <pre className="bg-surface-container p-2 rounded mt-1 overflow-x-auto h-full max-h-48 whitespace-pre-wrap">{t.answer_llm_json}</pre>
                                </div>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
