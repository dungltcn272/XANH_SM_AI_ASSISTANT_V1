import { useCallback, useEffect, useRef, useState } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  DatabaseZap,
  FileDown,
  Image as ImageIcon,
  Loader2,
  Pencil,
  Plus,
  RefreshCw,
  Save,
  Search,
  Trash2,
  X,
} from 'lucide-react';
import { api } from '../api';

const emptyForm = {
  url: '',
  title: '',
  source_profile: 'main_site',
  source_type: 'web',
  category: 'user',
  document_type: 'service',
  output_dir: 'data/user',
  crawl_strategy: 'default',
  enabled: true,
  priority: 100,
  notes: '',
};

const categories = ['user', 'merchant', 'driver', 'green-care', 'helps', 'term-policies', 'vehicle', 'pdf', 'overview'];
const profiles = ['main_site', 'platform', 'platform_pdf'];
const documentTypes = ['service', 'pricing', 'policy', 'faq', 'news', 'news_list', 'vehicle', 'platform_overview', 'policy_page', 'policy_pdf', 'overview', 'driver', 'merchant'];

const profileLabels = {
  main_site: 'main_site',
  platform: 'platform_crawler',
  platform_pdf: 'pdf_parser',
};

async function readSse(response, onLine) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n\n');
    for (let i = 0; i < lines.length - 1; i += 1) {
      const line = lines[i];
      if (!line.startsWith('data: ')) continue;
      const dataStr = line.substring(6);
      if (dataStr === '[DONE]') continue;
      try {
        const data = JSON.parse(dataStr);
        if (data.step) onLine(data.step);
        if (data.error) onLine(`[ERROR] ${data.error}`);
      } catch {
        onLine(dataStr);
      }
    }
    buffer = lines[lines.length - 1];
  }
}

export default function KnowledgeBuilder() {
  const [sources, setSources] = useState([]);
  const [registryStats, setRegistryStats] = useState({ total: 0, by_profile: {}, by_category: {}, by_type: {} });
  const [filters, setFilters] = useState({ keyword: '', source_profile: '', category: '', enabled: '' });
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);
  const [logs, setLogs] = useState([]);
  const [busy, setBusy] = useState('');
  const [confirmText, setConfirmText] = useState('');
  const [crawlLimit, setCrawlLimit] = useState(2);
  const [crawlUnlimited, setCrawlUnlimited] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;
  const terminalRef = useRef(null);

  const loadSources = useCallback(async (nextFilters = {}) => {
    const [data, stats] = await Promise.all([
      api.getCrawlSources(nextFilters),
      api.getCrawlSourceStats(nextFilters),
    ]);
    setSources(data);
    setRegistryStats(stats);
  }, []);

  useEffect(() => {
    let isActive = true;
    Promise.all([
      api.getCrawlSources({}),
      api.getCrawlSourceStats({}),
    ]).then(([data, stats]) => {
      if (!isActive) return;
      setSources(data);
      setRegistryStats(stats);
    }).catch((err) => {
      if (isActive) setLogs((prev) => [...prev, `[ERROR] ${err.message}`]);
    });
    return () => {
      isActive = false;
    };
  }, []);

  useEffect(() => {
    if (terminalRef.current) terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
  }, [logs]);

  const appendLog = (line) => setLogs((prev) => [...prev, line]);

  const updateForm = (field, value) => {
    const next = { ...form, [field]: value };
    if (field === 'category') next.output_dir = `data/${value}`;
    if (field === 'source_profile' && value === 'platform_pdf') {
      next.source_type = 'pdf';
      next.category = 'vehicle';
      next.output_dir = 'data/vehicle';
      next.document_type = 'policy_pdf';
      next.crawl_strategy = 'pdf_extract';
    }
    if (field === 'source_profile' && value === 'platform') {
      next.category = 'vehicle';
      next.output_dir = 'data/vehicle';
    }
    setForm(next);
  };

  const resetForm = () => {
    setForm(emptyForm);
    setEditingId(null);
  };

  const saveSource = async () => {
    if (!form.url.trim()) return;
    setBusy('save');
    try {
      if (editingId) {
        await api.updateCrawlSource(editingId, form);
        appendLog(`[SYSTEM] Đã cập nhật URL: ${form.url}`);
      } else {
        await api.createCrawlSource(form);
        appendLog(`[SYSTEM] Đã thêm URL: ${form.url}`);
      }
      resetForm();
      await loadSources(filters);
    } catch (err) {
      appendLog(`[ERROR] ${err.message}`);
    } finally {
      setBusy('');
    }
  };

  const editSource = (item) => {
    setEditingId(item.id);
    setForm({
      url: item.url || '',
      title: item.title || '',
      source_profile: item.source_profile || 'main_site',
      source_type: item.source_type || 'web',
      category: item.category || 'user',
      document_type: item.document_type || 'service',
      output_dir: item.output_dir || `data/${item.category || 'user'}`,
      crawl_strategy: item.crawl_strategy || 'default',
      enabled: Boolean(item.enabled),
      priority: item.priority ?? 100,
      notes: item.notes || '',
    });
  };

  const deleteSource = async (item) => {
    if (!window.confirm(`Xóa URL này khỏi registry?\n${item.url}`)) return;
    setBusy(`delete-${item.id}`);
    try {
      await api.deleteCrawlSource(item.id);
      appendLog(`[SYSTEM] Đã xóa URL: ${item.url}`);
      await loadSources(filters);
    } catch (err) {
      appendLog(`[ERROR] ${err.message}`);
    } finally {
      setBusy('');
    }
  };

  const toggleSource = async (item) => {
    setBusy(`toggle-${item.id}`);
    try {
      await api.updateCrawlSource(item.id, { ...item, enabled: !item.enabled });
      await loadSources(filters);
    } catch (err) {
      appendLog(`[ERROR] ${err.message}`);
    } finally {
      setBusy('');
    }
  };

  const syncUrlsJson = async () => {
    setBusy('sync');
    try {
      const res = await api.syncCrawlSources();
      appendLog(
        `[SYSTEM] Sync urls.json: inserted=${res.inserted || 0}, updated=${res.updated || 0}, stale=${res.stale_not_in_urls_json || 0}`
      );
      await loadSources(filters);
    } catch (err) {
      appendLog(`[ERROR] ${err.message}`);
    } finally {
      setBusy('');
    }
  };

  const runStreamAction = async (key, label, fn) => {
    if (busy) return;
    setBusy(key);
    appendLog(`[SYSTEM] ${label}`);
    try {
      const response = await fn();
      await readSse(response, appendLog);
      appendLog(`[SYSTEM] Hoàn tất: ${label}`);
    } catch (err) {
      appendLog(`[ERROR] ${err.message}`);
    } finally {
      setBusy('');
    }
  };

  const runJsonAction = async (key, label, fn) => {
    if (busy) return;
    setBusy(key);
    appendLog(`[SYSTEM] ${label}`);
    try {
      const res = await fn();
      appendLog(JSON.stringify(res, null, 2));
    } catch (err) {
      appendLog(`[ERROR] ${err.message}`);
    } finally {
      setBusy('');
    }
  };

  const applyFilters = async () => {
    setCurrentPage(1);
    await loadSources(filters);
  };

  const totalPages = Math.max(1, Math.ceil(sources.length / itemsPerPage));
  const currentSources = sources.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  const selectedCrawlLimit = crawlUnlimited ? 0 : Math.max(1, Number(crawlLimit) || 1);

  return (
    <div className="flex flex-col h-full overflow-y-auto p-4 md:p-8 gap-6 bg-[#070b14]">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Knowledge Hub</h1>
          <p className="text-sm text-[#94a3b8]">
            Quản lý nguồn crawl, đồng bộ URL registry, sinh Markdown sạch và vận hành clear/ingest tri thức tách biệt.
          </p>
        </div>
      </header>

      <section className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Left Column: URL Registry */}
        <div className="xl:col-span-2 rounded-2xl border border-[#1e293b]/60 bg-[#0b0f19] p-5 shadow-xl glass-panel flex flex-col min-h-[500px]">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-5">
            <div>
              <h2 className="text-lg font-bold text-[#00c897] flex items-center gap-2">
                <DatabaseZap size={18} />
                URL Registry
              </h2>
              <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs font-medium text-[#94a3b8]">
                <span>Tổng: <b className="text-white">{registryStats.total || 0}</b></span>
                <span className="text-[#1e293b]">|</span>
                <span>main_site: <b className="text-white">{registryStats.by_profile?.main_site || 0}</b></span>
                <span>platform_crawler: <b className="text-white">{registryStats.by_profile?.platform || 0}</b></span>
                <span>pdf_parser: <b className="text-white">{registryStats.by_profile?.platform_pdf || 0}</b></span>
              </div>
            </div>
            <button onClick={syncUrlsJson} disabled={Boolean(busy)} className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-[#00c897]/10 text-[#00c897] hover:bg-[#00c897]/20 border border-[#00c897]/20 text-sm font-bold transition-all disabled:opacity-50">
              {busy === 'sync' ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={16} />}
              Sync urls.json
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-5">
            <div className="relative md:col-span-1">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#64748b]" />
              <input className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-[#0f1520] border border-[#1e293b] text-sm text-[#f8f9ff] focus:border-[#00c897]/50 focus:ring-1 focus:ring-[#00c897]/50 transition-all outline-none placeholder:text-[#64748b]" placeholder="Search URL/title..." value={filters.keyword} onChange={(e) => setFilters({ ...filters, keyword: e.target.value })} />
            </div>
            <select className="px-3 py-2.5 rounded-xl bg-[#0f1520] border border-[#1e293b] text-sm text-[#f8f9ff] focus:border-[#00c897]/50 outline-none" value={filters.source_profile} onChange={(e) => setFilters({ ...filters, source_profile: e.target.value })}>
              <option value="">All profiles</option>
              {profiles.map((p) => <option key={p} value={p}>{profileLabels[p] || p}</option>)}
            </select>
            <select className="px-3 py-2.5 rounded-xl bg-[#0f1520] border border-[#1e293b] text-sm text-[#f8f9ff] focus:border-[#00c897]/50 outline-none" value={filters.category} onChange={(e) => setFilters({ ...filters, category: e.target.value })}>
              <option value="">All categories</option>
              {categories.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
            <button onClick={applyFilters} className="px-4 py-2.5 rounded-xl bg-[#1e293b] hover:bg-[#334155] text-white text-sm font-bold transition-all">Apply Filters</button>
          </div>

          <div className="flex-1 overflow-auto border border-[#1e293b] rounded-xl bg-[#030914] custom-scrollbar">
            <table className="w-full text-xs text-left border-collapse">
              <thead className="sticky top-0 bg-[#0b0f19] text-[#64748b] shadow-[0_1px_0_0_#1e293b]">
                <tr>
                  <th className="p-3 font-semibold w-16">Status</th>
                  <th className="p-3 font-semibold">Title / URL</th>
                  <th className="p-3 font-semibold">Profile</th>
                  <th className="p-3 font-semibold">Category</th>
                  <th className="p-3 font-semibold">Type</th>
                  <th className="p-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {currentSources.map((item) => (
                  <tr key={item.id} className="border-b border-[#1e293b]/50 hover:bg-[#0f1520] transition-colors group">
                    <td className="p-3">
                      <button onClick={() => toggleSource(item)} className={`w-9 h-5 rounded-full p-0.5 flex transition-colors ${item.enabled ? 'bg-[#00c897] justify-end' : 'bg-[#334155] justify-start'}`}>
                        <span className="w-4 h-4 rounded-full bg-white shadow-sm" />
                      </button>
                    </td>
                    <td className="p-3 max-w-[320px]">
                      {item.title ? <div className="font-bold text-[#e2e8f0] truncate">{item.title}</div> : null}
                      <div className="text-[#64748b] truncate text-[11px] group-hover:text-[#94a3b8] transition-colors">{item.url}</div>
                    </td>
                    <td className="p-3">
                      <span className="inline-block px-2 py-1 rounded bg-[#1e293b]/50 text-[#94a3b8] text-[10px] uppercase font-bold">{item.source_profile}</span>
                    </td>
                    <td className="p-3 text-[#cbd5e1]">{item.category}</td>
                    <td className="p-3 text-[#cbd5e1]">{item.document_type}</td>
                    <td className="p-3">
                      <div className="flex justify-end gap-1 opacity-50 group-hover:opacity-100 transition-opacity">
                        <button onClick={() => editSource(item)} className="p-1.5 rounded hover:bg-[#3b82f6]/20 text-[#3b82f6] transition-colors" title="Edit"><Pencil size={14} /></button>
                        <button onClick={() => deleteSource(item)} className="p-1.5 rounded hover:bg-[#ef4444]/20 text-[#ef4444] transition-colors" title="Delete"><Trash2 size={14} /></button>
                      </div>
                    </td>
                  </tr>
                ))}
                {currentSources.length === 0 && (
                  <tr>
                    <td colSpan="6" className="p-8 text-center text-[#64748b] italic">Không tìm thấy dữ liệu.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          
          {/* Pagination Controls */}
          {sources.length > 0 && (
            <div className="flex items-center justify-between mt-5 text-xs">
              <span className="text-[#64748b]">
                Hiển thị <b className="text-white">{(currentPage - 1) * itemsPerPage + 1}-{Math.min(currentPage * itemsPerPage, sources.length)}</b> trong <b className="text-white">{sources.length}</b>
              </span>
              <div className="flex items-center gap-1">
                <button 
                  disabled={currentPage === 1}
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  className="p-1.5 rounded hover:bg-[#1e293b] text-[#94a3b8] disabled:opacity-30 transition-colors"
                >
                  <ChevronLeft size={16} />
                </button>
                {Array.from({ length: totalPages }).map((_, i) => {
                  const page = i + 1;
                  if (page === 1 || page === totalPages || (page >= currentPage - 1 && page <= currentPage + 1)) {
                    return (
                      <button 
                        key={page}
                        onClick={() => setCurrentPage(page)}
                        className={`w-7 h-7 rounded flex items-center justify-center text-[11px] transition-colors ${page === currentPage ? 'bg-[#00c897] text-white font-bold' : 'hover:bg-[#1e293b] text-[#94a3b8]'}`}
                      >
                        {page}
                      </button>
                    );
                  } else if (page === currentPage - 2 || page === currentPage + 2) {
                    return <span key={page} className="px-1 text-[#475569]">...</span>;
                  }
                  return null;
                })}
                <button 
                  disabled={currentPage === totalPages}
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  className="p-1.5 rounded hover:bg-[#1e293b] text-[#94a3b8] disabled:opacity-30 transition-colors"
                >
                  <ChevronRight size={16} />
                </button>
              </div>
              <div className="flex items-center gap-2">
                <select className="px-2 py-1.5 rounded bg-[#0f1520] border border-[#1e293b] text-[#94a3b8] text-xs outline-none">
                  <option>10 / trang</option>
                </select>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Add URL Form */}
        <div className="rounded-2xl border border-[#1e293b]/60 bg-[#0b0f19] p-5 shadow-xl glass-panel h-fit">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Plus size={18} className="text-[#00c897]" />
              {editingId ? 'Edit URL' : 'Add New URL'}
            </h2>
            {editingId && <button onClick={resetForm} className="p-1.5 rounded-lg hover:bg-[#1e293b] text-[#94a3b8] transition-colors"><X size={16} /></button>}
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-[10px] font-bold text-[#64748b] uppercase tracking-wider mb-1.5">Title</label>
              <input className="w-full px-3 py-2.5 rounded-lg bg-[#0f1520] border border-[#1e293b] text-sm text-[#f8f9ff] focus:border-[#00c897]/50 focus:ring-1 focus:ring-[#00c897]/50 outline-none" placeholder="Page title" value={form.title} onChange={(e) => updateForm('title', e.target.value)} />
            </div>
            <div>
              <label className="block text-[10px] font-bold text-[#64748b] uppercase tracking-wider mb-1.5">URL <span className="text-[#ef4444]">*</span></label>
              <textarea className="w-full px-3 py-2.5 rounded-lg bg-[#0f1520] border border-[#1e293b] text-sm text-[#f8f9ff] focus:border-[#00c897]/50 focus:ring-1 focus:ring-[#00c897]/50 outline-none min-h-[64px] resize-none" placeholder="https://..." value={form.url} onChange={(e) => updateForm('url', e.target.value)} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[10px] font-bold text-[#64748b] uppercase tracking-wider mb-1.5">Profile</label>
                <select className="w-full px-3 py-2.5 rounded-lg bg-[#0f1520] border border-[#1e293b] text-sm text-[#f8f9ff] outline-none" value={form.source_profile} onChange={(e) => updateForm('source_profile', e.target.value)}>
                  {profiles.map((p) => <option key={p} value={p}>{profileLabels[p] || p}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-[10px] font-bold text-[#64748b] uppercase tracking-wider mb-1.5">Type</label>
                <select className="w-full px-3 py-2.5 rounded-lg bg-[#0f1520] border border-[#1e293b] text-sm text-[#f8f9ff] outline-none" value={form.source_type} onChange={(e) => updateForm('source_type', e.target.value)}>
                  <option value="web">web</option>
                  <option value="pdf">pdf</option>
                </select>
              </div>
              <div>
                <label className="block text-[10px] font-bold text-[#64748b] uppercase tracking-wider mb-1.5">Category</label>
                <select className="w-full px-3 py-2.5 rounded-lg bg-[#0f1520] border border-[#1e293b] text-sm text-[#f8f9ff] outline-none" value={form.category} onChange={(e) => updateForm('category', e.target.value)}>
                  {categories.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-[10px] font-bold text-[#64748b] uppercase tracking-wider mb-1.5">Doc Type</label>
                <select className="w-full px-3 py-2.5 rounded-lg bg-[#0f1520] border border-[#1e293b] text-sm text-[#f8f9ff] outline-none" value={form.document_type} onChange={(e) => updateForm('document_type', e.target.value)}>
                  {documentTypes.map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-[10px] font-bold text-[#64748b] uppercase tracking-wider mb-1.5">Output Dir</label>
              <input className="w-full px-3 py-2.5 rounded-lg bg-[#0f1520] border border-[#1e293b] text-sm text-[#f8f9ff] outline-none" value={form.output_dir} onChange={(e) => updateForm('output_dir', e.target.value)} />
            </div>
            <label className="flex items-center gap-2 text-sm font-semibold text-[#e2e8f0] cursor-pointer mt-2">
              <input type="checkbox" checked={form.enabled} onChange={(e) => updateForm('enabled', e.target.checked)} className="w-4 h-4 rounded accent-[#00c897]" />
              Enabled for crawling
            </label>
            <button onClick={saveSource} disabled={Boolean(busy) || !form.url.trim()} className="w-full mt-2 py-3 rounded-lg bg-gradient-to-r from-[#00c897] to-[#00a67d] hover:from-[#00b084] hover:to-[#009570] shadow-[0_4px_15px_rgba(0,200,151,0.2)] text-white font-bold flex justify-center items-center gap-2 disabled:opacity-50 transition-all">
              {busy === 'save' ? <Loader2 size={16} className="animate-spin" /> : editingId ? <Save size={16} /> : <Plus size={16} />}
              {editingId ? 'Save Changes' : 'Add to Registry'}
            </button>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Crawl & Clean Card */}
        <div className="rounded-2xl border border-[#1e293b]/60 bg-[#0b0f19] p-5 shadow-xl glass-panel flex flex-col justify-between">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-2">
              <FileDown size={18} className="text-[#3b82f6]" />
              Data Pipeline Actions
            </h2>
            <p className="text-[11px] text-[#94a3b8] mb-4">Crawler sinh Markdown/PDF Markdown trong thư mục data/. Không clear và không ingest tự động.</p>
            <div className="grid grid-cols-[1fr_auto] gap-3 items-end mb-5">
              <div>
                <label className="block text-[10px] font-bold text-[#64748b] uppercase tracking-wider mb-1.5">Max URLs to Crawl</label>
                <input
                  type="number"
                  min="1"
                  value={crawlLimit}
                  disabled={crawlUnlimited}
                  onChange={(e) => setCrawlLimit(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-[#0f1520] border border-[#1e293b] text-sm text-white disabled:opacity-40 outline-none focus:border-[#3b82f6]/50"
                />
              </div>
              <label className="flex items-center gap-2 text-xs font-bold text-[#94a3b8] mb-2.5 cursor-pointer">
                <input type="checkbox" checked={crawlUnlimited} onChange={(e) => setCrawlUnlimited(e.target.checked)} className="accent-[#3b82f6]" />
                UNLIMITED
              </label>
            </div>
          </div>
          <div className="space-y-3">
            <button onClick={() => runStreamAction('crawl-all', `Crawl Data (${crawlUnlimited ? 'UNLIMITED' : `${selectedCrawlLimit} URLs`})`, () => api.runCrawler(selectedCrawlLimit))} disabled={Boolean(busy)} className="w-full py-2.5 rounded-lg bg-[#3b82f6]/10 text-[#3b82f6] border border-[#3b82f6]/30 hover:bg-[#3b82f6]/20 font-bold flex justify-center items-center gap-2 disabled:opacity-50 transition-all text-sm">
              {busy === 'crawl-all' ? <Loader2 size={16} className="animate-spin" /> : <FileDown size={16} />}
              Run Crawl Pipeline
            </button>
            <button onClick={() => runStreamAction('vlm-process', 'VLM Image Processing', api.runVLMProcessor)} disabled={Boolean(busy)} className="w-full py-2.5 rounded-lg bg-[#8b5cf6]/10 text-[#8b5cf6] border border-[#8b5cf6]/30 hover:bg-[#8b5cf6]/20 font-bold flex justify-center items-center gap-2 disabled:opacity-50 transition-all text-sm">
              {busy === 'vlm-process' ? <Loader2 size={16} className="animate-spin" /> : <ImageIcon size={16} />}
              Run VLM Processor
            </button>
          </div>
        </div>

        {/* Knowledge Operations Card */}
        <div className="rounded-2xl border border-[#1e293b]/60 bg-[#0b0f19] p-5 shadow-xl glass-panel flex flex-col justify-between">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-2">
              <DatabaseZap size={18} className="text-[#f59e0b]" />
              Database Operations
            </h2>
            <p className="text-[11px] text-[#94a3b8] mb-4">Quản lý Ingest dữ liệu vào Vector DB. Dữ liệu cũ cần phải Clear thủ công.</p>
            <div className="mb-5">
              <label className="block text-[10px] font-bold text-[#64748b] uppercase tracking-wider mb-1.5">Confirmation string</label>
              <input className="w-full px-3 py-2 rounded-lg bg-[#0f1520] border border-[#1e293b] text-sm text-white placeholder:text-[#64748b] outline-none focus:border-[#ef4444]/50" placeholder="Type CLEAR to unlock deletion" value={confirmText} onChange={(e) => setConfirmText(e.target.value)} />
            </div>
          </div>
          <div className="space-y-3">
            <button onClick={() => runJsonAction('clear', 'Clear ALL Knowledge', api.clearAllKnowledge)} disabled={Boolean(busy) || confirmText !== 'CLEAR'} className="w-full py-2.5 rounded-lg bg-[#ef4444]/10 text-[#ef4444] border border-[#ef4444]/30 hover:bg-[#ef4444]/20 font-bold flex justify-center items-center gap-2 disabled:opacity-50 transition-all text-sm">
              {busy === 'clear' ? <Loader2 size={16} className="animate-spin" /> : <Trash2 size={16} />}
              Clear ALL Knowledge DB
            </button>
            <div className="grid grid-cols-2 gap-3">
              <button onClick={() => runJsonAction('food-import', 'Import Food Catalog', () => api.importFoodCatalog({ path: 'data/food_catalog/shopeefood_catalog.jsonl' }))} disabled={Boolean(busy)} className="w-full py-2.5 rounded-lg bg-[#f59e0b]/10 text-[#f59e0b] border border-[#f59e0b]/30 hover:bg-[#f59e0b]/20 font-bold flex justify-center items-center gap-2 disabled:opacity-50 transition-all text-sm">
                {busy === 'food-import' ? <Loader2 size={16} className="animate-spin" /> : <DatabaseZap size={16} />}
                Ingest Food
              </button>
              <button onClick={() => runStreamAction('ingest-all', 'Ingest ALL From data/', api.runIngestion)} disabled={Boolean(busy)} className="w-full py-2.5 rounded-lg bg-[#00c897]/10 text-[#00c897] border border-[#00c897]/30 hover:bg-[#00c897]/20 font-bold flex justify-center items-center gap-2 disabled:opacity-50 transition-all text-sm">
                {busy === 'ingest-all' ? <Loader2 size={16} className="animate-spin" /> : <DatabaseZap size={16} />}
                Ingest Main
              </button>
            </div>
          </div>
        </div>

        {/* Terminal Log */}
        <div className="rounded-2xl border border-[#1e293b]/60 bg-black shadow-xl overflow-hidden flex flex-col h-[320px] lg:h-auto">
          <div className="px-4 py-2.5 bg-[#111] border-b border-[#333] flex items-center gap-2 shrink-0">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500"></span>
            <span className="w-2.5 h-2.5 rounded-full bg-yellow-500"></span>
            <span className="w-2.5 h-2.5 rounded-full bg-green-500"></span>
            <span className="ml-2 text-xs font-bold text-[#64748b] font-mono">knowledge_builder.log</span>
          </div>
          <div ref={terminalRef} className="flex-1 p-4 overflow-y-auto custom-scrollbar font-mono text-[11px] leading-relaxed bg-black text-[#00c897]">
            {logs.length === 0 ? (
              <div className="text-[#64748b] italic">Waiting for operations...</div>
            ) : (
              logs.map((log, idx) => (
                <div key={idx} className={`mb-1 ${log.includes('[ERROR]') ? 'text-red-400' : log.includes('[SYSTEM]') ? 'text-blue-400' : 'text-[#00c897]'}`}>
                  <span className="opacity-50 mr-2">{new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
                  {log}
                </div>
              ))
            )}
          </div>
        </div>
      </section>
    </div>
  );
}


