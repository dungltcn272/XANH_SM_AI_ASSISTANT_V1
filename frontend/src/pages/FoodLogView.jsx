import { useState, useEffect } from 'react';
import { Search, ShieldCheck, Copy, Download, Play, ChevronDown, ChevronRight, Check, X, Box, Target, Activity, MapPin, Tag } from 'lucide-react';
import { api } from '../api';

export default function FoodLogView() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLog, setSelectedLog] = useState(null);
  const [copiedId, setCopiedId] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 50;
  const [totalLogs, setTotalLogs] = useState(0);
  const [date, setDate] = useState('');
  const [pageInput, setPageInput] = useState('1');
  const [expandedSections, setExpandedSections] = useState({
    nlu: true,
    context: false,
    trace: false
  });

  const handlePageInputChange = (e) => {
    setPageInput(e.target.value);
  };

  const handlePageInputSubmit = () => {
    let targetPage = parseInt(pageInput, 10);
    const totalPages = Math.ceil(totalLogs / pageSize) || 1;
    if (isNaN(targetPage) || targetPage < 1) targetPage = 1;
    else if (targetPage > totalPages) targetPage = totalPages;
    setCurrentPage(targetPage);
    setPageInput(targetPage.toString());
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handlePageInputSubmit();
  };

  useEffect(() => {
    const fetchLogs = async () => {
      setLoading(true);
      try {
        const skip = (currentPage - 1) * pageSize;
        const data = await api.getFoodLogs(skip, pageSize, date);
        setLogs(data?.items || []);
        setTotalLogs(data?.total || 0);
        if (data?.items && data.items.length > 0) {
          setSelectedLog(prev => prev || data.items[0]);
        }
      } catch (err) {
        console.error(err);
      }
      setLoading(false);
    };
    fetchLogs();
  }, [currentPage, date]);

  const filteredLogs = logs.filter(log => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return true;
    return (
      (log.original_query || '').toLowerCase().includes(q)
    );
  });

  const handleCopyId = (id) => {
    navigator.clipboard.writeText(id);
    setCopiedId(true);
    setTimeout(() => setCopiedId(false), 2000);
  };

  const toggleSection = (section) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const parseJsonSafe = (str, fallback = {}) => {
    try {
      return JSON.parse(str);
    } catch {
      return fallback;
    }
  };

  return (
    <div className="flex h-full gap-4 overflow-hidden p-4 md:p-6 bg-[#070b14]">
      {/* Left Pane: Master List */}
      <div className="w-[380px] shrink-0 flex flex-col glass-panel rounded-2xl border border-[#1e293b]/60 overflow-hidden bg-[#0b0f19] shadow-xl">
        <div className="p-4 border-b border-[#1e293b]/60 shrink-0">
          <h2 className="text-lg font-bold text-white mb-4">Food Recommendation Logs</h2>
          
          <div className="relative mb-3">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[#64748b]" size={16} />
            <input 
              type="text" 
              placeholder="Search query..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[#0f1520] border border-[#1e293b] focus:border-[#f59e0b]/50 focus:ring-1 focus:ring-[#f59e0b]/50 outline-none pl-9 pr-4 py-2 rounded-lg text-sm text-white placeholder:text-[#64748b] transition-all"
            />
          </div>
        </div>

        <div className="px-4 py-2 bg-[#0f1520]/50 border-b border-[#1e293b]/60 text-xs text-[#94a3b8] flex justify-between items-center shrink-0">
          <span>Showing {filteredLogs.length} of {totalLogs} logs</span>
          <div className="flex items-center gap-2">
            <input type="date" value={date} onChange={e => {setDate(e.target.value); setCurrentPage(1); setPageInput('1');}} className="bg-[#0f1520] border border-[#1e293b] text-[#94a3b8] rounded px-1.5 py-0.5 outline-none" />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-2">
          {loading ? (
            <div className="text-center p-8 text-[#64748b] animate-pulse">Loading logs...</div>
          ) : filteredLogs.length === 0 ? (
            <div className="text-center p-8 text-[#64748b] italic">No logs found.</div>
          ) : (
            filteredLogs.map(log => {
              const isSelected = selectedLog?.trace_id === log.trace_id;
              const stats = parseJsonSafe(log.candidate_stats_json);
              const loc = parseJsonSafe(log.location_json);
              
              return (
                <div 
                  key={log.trace_id} 
                  onClick={() => setSelectedLog(log)}
                  className={`p-3 rounded-xl border cursor-pointer transition-all ${
                    isSelected 
                      ? 'bg-[#f59e0b]/10 border-[#f59e0b]/50 shadow-[0_0_15px_rgba(245,158,11,0.1)]' 
                      : 'bg-[#0f1520] border-[#1e293b] hover:border-[#334155] hover:bg-[#151b2b]'
                  }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-bold text-[#e2e8f0] text-sm line-clamp-1 flex-1 pr-2">{log.original_query || 'Unknown query'}</h4>
                    <span className="text-[10px] text-[#94a3b8] whitespace-nowrap">
                      {new Date(log.created_at).toLocaleTimeString('en-US', {hour12: false})}
                    </span>
                  </div>
                  <div className="flex justify-between items-end">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[#1e293b] text-[#f59e0b] uppercase tracking-wider border border-[#334155]">
                      LOG
                    </span>
                    <div className="flex flex-col items-end text-[10px] text-[#64748b]">
                      <span>{loc.lat && loc.lng ? `${loc.lat.toFixed(3)}, ${loc.lng.toFixed(3)}` : 'No Location'}</span>
                      <span className="font-mono mt-0.5">{stats.returned_count || 0} returned</span>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        <div className="p-4 border-t border-[#1e293b]/60 flex items-center justify-between text-xs shrink-0">
          <span className="text-[#64748b]">Total: {totalLogs}</span>
          <div className="flex items-center gap-2">
            <button
              disabled={currentPage === 1}
              onClick={() => { setCurrentPage(p => p - 1); setPageInput(String(currentPage - 1)); }}
              className="px-2 py-1 bg-[#1e293b] text-white rounded disabled:opacity-50"
            >
              Prev
            </button>
            <div className="flex items-center gap-1.5 text-xs text-[#94a3b8]">
              <span>Trang</span>
              <input
                type="number"
                value={pageInput}
                onChange={handlePageInputChange}
                onBlur={handlePageInputSubmit}
                onKeyDown={handleKeyDown}
                className="w-12 px-1 py-0.5 text-center bg-[#0f1520] border border-[#1e293b] rounded focus:outline-none focus:border-[#00c897] text-white"
              />
              <span>/ {Math.ceil(totalLogs / pageSize) || 1}</span>
            </div>
            <button
              disabled={currentPage >= Math.ceil(totalLogs / pageSize)}
              onClick={() => { setCurrentPage(p => p + 1); setPageInput(String(currentPage + 1)); }}
              className="px-2 py-1 bg-[#1e293b] text-white rounded disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Right Pane: Detail View */}
      {selectedLog ? (
        <div className="flex-1 flex flex-col glass-panel rounded-2xl border border-[#1e293b]/60 overflow-hidden bg-[#0b0f19] shadow-xl">
          {/* Detail Header */}
          <div className="px-6 py-4 border-b border-[#1e293b]/60 flex justify-between items-center shrink-0">
            <div className="flex items-center gap-3">
              <span className="text-sm font-semibold text-[#94a3b8]">Trace ID: <span className="font-mono text-[#cbd5e1]">{selectedLog.trace_id}</span></span>
              <button onClick={() => handleCopyId(selectedLog.trace_id)} className="text-[#64748b] hover:text-white transition-colors" title="Copy ID">
                {copiedId ? <Check size={14} className="text-[#00c897]" /> : <Copy size={14} />}
              </button>
            </div>
            <div className="flex items-center gap-2">
              <button className="px-3 py-1.5 rounded-lg bg-[#1e293b] hover:bg-[#334155] text-white text-xs font-semibold flex items-center gap-1.5 transition-colors">
                <Download size={14} /> Export JSON
              </button>
              <button className="p-1.5 rounded-lg hover:bg-[#ef4444]/20 text-[#64748b] hover:text-[#ef4444] transition-colors ml-2" onClick={() => setSelectedLog(null)}>
                <X size={18} />
              </button>
            </div>
          </div>

          {/* Detail Scrollable Content */}
          <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-6">
            
            {/* Top Cards: Question & Answer */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              {/* Question Card */}
              <div className="rounded-xl border border-[#00c897]/30 bg-[#00c897]/5 p-5 flex flex-col">
                <span className="text-[10px] font-bold text-[#00c897] uppercase tracking-wider mb-2">Question</span>
                <p className="text-lg font-bold text-white mb-4 flex-1">{selectedLog.original_query}</p>
                <div className="flex gap-6 text-xs text-[#94a3b8] mt-auto">
                  <span>Conversation ID: <span className="text-[#cbd5e1] font-mono">{selectedLog.conversation_id?.substring(0,8) || 'unknown'}</span></span>
                  <span>Generated at: <span className="text-[#cbd5e1]">{new Date(selectedLog.created_at).toLocaleTimeString()}</span></span>
                </div>
              </div>

              {/* Answer / Result Card */}
              <div className="rounded-xl border border-[#8b5cf6]/30 bg-[#8b5cf6]/5 p-5 flex flex-col">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-[10px] font-bold text-[#8b5cf6] uppercase tracking-wider">Recommendation Result</span>
                  <Activity size={14} className="text-[#8b5cf6]" />
                </div>
                <div className="text-sm text-[#e2e8f0] mb-4 flex-1 overflow-y-auto max-h-32 custom-scrollbar">
                  <pre className="text-xs font-mono whitespace-pre-wrap">{selectedLog.answer_llm_json || 'No LLM answer'}</pre>
                </div>
                <div className="flex gap-6 text-xs text-[#94a3b8] mt-auto border-t border-[#8b5cf6]/20 pt-2">
                  <span>Model: <span className="text-[#cbd5e1] font-mono">Llama-3</span></span>
                  <span>Candidates: <span className="text-[#cbd5e1]">{parseJsonSafe(selectedLog.candidate_stats_json).returned_count || 0}</span></span>
                </div>
              </div>
            </div>

            {/* Metrics Row */}
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-xl border border-[#1e293b] bg-[#0f1520] p-4 flex items-center gap-3">
                <div className="p-2 rounded-lg bg-[#3b82f6]/10 text-[#3b82f6]"><MapPin size={18} /></div>
                <div>
                  <div className="text-[10px] text-[#64748b] uppercase tracking-wider font-bold mb-0.5">Location</div>
                  <div className="text-sm font-bold text-white">
                    {parseJsonSafe(selectedLog.location_json).lat ? 'Detected' : 'None'}
                  </div>
                </div>
              </div>
              <div className="rounded-xl border border-[#1e293b] bg-[#0f1520] p-4 flex items-center gap-3">
                <div className="p-2 rounded-lg bg-[#8b5cf6]/10 text-[#8b5cf6]"><Tag size={18} /></div>
                <div>
                  <div className="text-[10px] text-[#64748b] uppercase tracking-wider font-bold mb-0.5">Total Candidates</div>
                  <div className="text-sm font-bold text-white">
                    {parseJsonSafe(selectedLog.candidate_stats_json).total_candidates || 0}
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom Grid: NLU, Latency Breakdown, Raw Trace */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              
              {/* Left Col: Accordions */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Box size={16} className="text-[#f59e0b]" /> Extraction & Context
                </h3>
                
                {/* NLU Result */}
                <div className="rounded-xl border border-[#1e293b] bg-[#0f1520] overflow-hidden">
                  <button 
                    onClick={() => toggleSection('nlu')}
                    className="w-full px-4 py-3 flex justify-between items-center hover:bg-[#1e293b]/50 transition-colors"
                  >
                    <span className="text-xs font-bold text-[#e2e8f0]">NLU Extraction JSON</span>
                    {expandedSections.nlu ? <ChevronDown size={14} className="text-[#64748b]"/> : <ChevronRight size={14} className="text-[#64748b]"/>}
                  </button>
                  {expandedSections.nlu && (
                    <div className="px-4 pb-4 border-t border-[#1e293b] pt-3">
                      <pre className="text-[11px] text-[#00c897] font-mono overflow-x-auto">
{JSON.stringify(parseJsonSafe(selectedLog.nlu_json), null, 2)}
                      </pre>
                    </div>
                  )}
                </div>

                {/* Context Expansion */}
                <div className="rounded-xl border border-[#1e293b] bg-[#0f1520] overflow-hidden">
                  <button 
                    onClick={() => toggleSection('context')}
                    className="w-full px-4 py-3 flex justify-between items-center hover:bg-[#1e293b]/50 transition-colors"
                  >
                    <span className="text-xs font-bold text-[#e2e8f0]">User Context (Filters)</span>
                    {expandedSections.context ? <ChevronDown size={14} className="text-[#64748b]"/> : <ChevronRight size={14} className="text-[#64748b]"/>}
                  </button>
                  {expandedSections.context && (
                    <div className="px-4 pb-4 border-t border-[#1e293b] pt-3">
                      <pre className="text-[11px] text-[#3b82f6] font-mono overflow-x-auto">
{JSON.stringify(parseJsonSafe(selectedLog.user_context_json), null, 2)}
                      </pre>
                    </div>
                  )}
                </div>

              </div>

              {/* Right Col: Latency & Raw Trace */}
              <div className="space-y-6">

                {/* Raw Trace */}
                <div>
                  <div className="rounded-xl border border-[#1e293b] bg-[#0f1520] overflow-hidden">
                    <button 
                      onClick={() => toggleSection('trace')}
                      className="w-full px-4 py-3 flex justify-between items-center hover:bg-[#1e293b]/50 transition-colors"
                    >
                      <span className="text-xs font-bold text-[#e2e8f0]">Raw Food Trace JSON</span>
                      {expandedSections.trace ? <ChevronDown size={14} className="text-[#64748b]"/> : <ChevronRight size={14} className="text-[#64748b]"/>}
                    </button>
                    {expandedSections.trace && (
                      <div className="px-4 pb-4 border-t border-[#1e293b] pt-3 relative">
                        <button className="absolute top-4 right-4 text-[#64748b] hover:text-white" onClick={() => {
                          navigator.clipboard.writeText(JSON.stringify(selectedLog, null, 2));
                        }}><Copy size={14}/></button>
                        <pre className="text-[10px] text-[#94a3b8] font-mono overflow-x-auto max-h-[400px] custom-scrollbar">
{JSON.stringify(selectedLog, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>

              </div>
            </div>

          </div>
        </div>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center glass-panel rounded-2xl border border-[#1e293b]/60 bg-[#0b0f19] shadow-xl">
          <Target size={48} className="text-[#1e293b] mb-4" />
          <h3 className="text-lg font-bold text-[#94a3b8]">Select a food trace to view details</h3>
          <p className="text-sm text-[#64748b] mt-2 max-w-sm text-center">Click on any log entry in the left panel to explore its full execution trace.</p>
        </div>
      )}
    </div>
  );
}
