import { useCallback, useEffect, useRef, useState } from 'react';
import {
  DatabaseZap,
  FileDown,
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
    await loadSources(filters);
  };

  return (
    <div className="flex flex-col h-full overflow-y-auto p-4 md:p-8 gap-6">
      <header>
        <h1 className="text-3xl font-black text-on-surface mb-1">Knowledge Builder</h1>
        <p className="text-sm text-on-surface-variant">
          Quản lý nguồn crawl, đồng bộ URL registry, sinh Markdown sạch và vận hành clear/ingest tri thức tách biệt.
        </p>
      </header>

      <section className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 glass-panel border border-outline-variant/30 rounded-2xl p-5">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
            <div>
              <h2 className="text-lg font-bold text-on-surface">URL Registry</h2>
              <p className="text-xs text-on-surface-variant">
                Tổng {registryStats.total || 0} URL · profile: main_site {registryStats.by_profile?.main_site || 0}, platform_crawler {registryStats.by_profile?.platform || 0}, pdf_parser {registryStats.by_profile?.platform_pdf || 0}
              </p>
              <p className="text-[11px] text-on-surface-variant">
                Nhóm dữ liệu: vehicle {registryStats.by_category?.vehicle || 0}, pdf {registryStats.by_category?.pdf || 0}, news {registryStats.by_category?.news || 0}, term-policies {registryStats.by_category?.['term-policies'] || 0} · đang hiển thị {sources.length} dòng
              </p>
            </div>
            <button onClick={syncUrlsJson} disabled={Boolean(busy)} className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-primary text-white text-sm font-bold disabled:opacity-50">
              {busy === 'sync' ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={16} />}
              Sync urls.json
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-2 mb-4">
            <div className="relative md:col-span-1">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant" />
              <input className="w-full pl-9 pr-3 py-2 rounded-xl bg-surface-container border border-outline-variant/30 text-sm" placeholder="Search URL/title" value={filters.keyword} onChange={(e) => setFilters({ ...filters, keyword: e.target.value })} />
            </div>
            <select className="px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/30 text-sm" value={filters.source_profile} onChange={(e) => setFilters({ ...filters, source_profile: e.target.value })}>
              <option value="">All profiles</option>
              {profiles.map((p) => <option key={p} value={p}>{profileLabels[p] || p}</option>)}
            </select>
            <select className="px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/30 text-sm" value={filters.category} onChange={(e) => setFilters({ ...filters, category: e.target.value })}>
              <option value="">All categories</option>
              {categories.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
            <button onClick={applyFilters} className="px-4 py-2 rounded-xl bg-surface-container-high text-on-surface text-sm font-bold border border-outline-variant/30">Apply</button>
          </div>

          <div className="overflow-auto border border-outline-variant/20 rounded-xl max-h-[420px]">
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-surface-container-high text-on-surface">
                <tr>
                  <th className="text-left p-3">On</th>
                  <th className="text-left p-3">Title / URL</th>
                  <th className="text-left p-3">Profile</th>
                  <th className="text-left p-3">Category</th>
                  <th className="text-left p-3">Type</th>
                  <th className="text-right p-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {sources.map((item) => (
                  <tr key={item.id} className="border-t border-outline-variant/15 hover:bg-surface-container/60">
                    <td className="p-3">
                      <button onClick={() => toggleSource(item)} className={`w-9 h-5 rounded-full p-0.5 flex ${item.enabled ? 'bg-primary justify-end' : 'bg-outline-variant justify-start'}`}>
                        <span className="w-4 h-4 rounded-full bg-white" />
                      </button>
                    </td>
                    <td className="p-3 min-w-[320px]">
                      <div className="font-bold text-on-surface">{item.title || '(no title)'}</div>
                      <div className="text-on-surface-variant break-all">{item.url}</div>
                    </td>
                    <td className="p-3">{item.source_profile}</td>
                    <td className="p-3">{item.category}</td>
                    <td className="p-3">{item.document_type}</td>
                    <td className="p-3">
                      <div className="flex justify-end gap-2">
                        <button onClick={() => editSource(item)} className="p-2 rounded-lg hover:bg-primary/10 text-primary" title="Edit"><Pencil size={15} /></button>
                        <button onClick={() => deleteSource(item)} className="p-2 rounded-lg hover:bg-error/10 text-error" title="Delete"><Trash2 size={15} /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="glass-panel border border-outline-variant/30 rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-on-surface">{editingId ? 'Edit URL' : 'Add URL'}</h2>
            {editingId && <button onClick={resetForm} className="p-2 rounded-lg hover:bg-surface-container"><X size={16} /></button>}
          </div>
          <div className="space-y-3">
            <input className="w-full px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/30 text-sm" placeholder="Title" value={form.title} onChange={(e) => updateForm('title', e.target.value)} />
            <textarea className="w-full px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/30 text-sm min-h-[76px]" placeholder="URL" value={form.url} onChange={(e) => updateForm('url', e.target.value)} />
            <div className="grid grid-cols-2 gap-2">
              <select className="px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/30 text-sm" value={form.source_profile} onChange={(e) => updateForm('source_profile', e.target.value)}>
                {profiles.map((p) => <option key={p} value={p}>{profileLabels[p] || p}</option>)}
              </select>
              <select className="px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/30 text-sm" value={form.source_type} onChange={(e) => updateForm('source_type', e.target.value)}>
                <option value="web">web</option>
                <option value="pdf">pdf</option>
              </select>
              <select className="px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/30 text-sm" value={form.category} onChange={(e) => updateForm('category', e.target.value)}>
                {categories.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
              <select className="px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/30 text-sm" value={form.document_type} onChange={(e) => updateForm('document_type', e.target.value)}>
                {documentTypes.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <input className="w-full px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/30 text-sm" placeholder="Output dir" value={form.output_dir} onChange={(e) => updateForm('output_dir', e.target.value)} />
            <textarea className="w-full px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/30 text-sm min-h-[64px]" placeholder="Notes" value={form.notes} onChange={(e) => updateForm('notes', e.target.value)} />
            <label className="flex items-center gap-2 text-sm text-on-surface-variant">
              <input type="checkbox" checked={form.enabled} onChange={(e) => updateForm('enabled', e.target.checked)} />
              Enabled for crawl
            </label>
            <button onClick={saveSource} disabled={Boolean(busy) || !form.url.trim()} className="w-full py-3 rounded-xl bg-gradient-to-r from-primary to-secondary text-white font-bold inline-flex justify-center items-center gap-2 disabled:opacity-50">
              {busy === 'save' ? <Loader2 size={18} className="animate-spin" /> : editingId ? <Save size={18} /> : <Plus size={18} />}
              {editingId ? 'Save URL' : 'Add URL'}
            </button>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="glass-panel border border-outline-variant/30 rounded-2xl p-5 space-y-4">
          <h2 className="text-lg font-bold text-on-surface">Crawl & Clean</h2>
          <p className="text-xs text-on-surface-variant">Crawler chỉ sinh Markdown/PDF Markdown trong data/. Không clear và không ingest.</p>
          <button onClick={() => runStreamAction('crawl-main', 'Crawl Main Site -> Markdown', api.runCrawler)} disabled={Boolean(busy)} className="w-full py-3 rounded-xl bg-blue-600 text-white font-bold inline-flex justify-center items-center gap-2 disabled:opacity-50">
            {busy === 'crawl-main' ? <Loader2 size={18} className="animate-spin" /> : <FileDown size={18} />}
            Crawl Main Site
          </button>
          <button onClick={() => runStreamAction('crawl-platform', 'Crawl Vehicle/PDF -> Markdown', api.runAgentCrawler)} disabled={Boolean(busy)} className="w-full py-3 rounded-xl bg-cyan-600 text-white font-bold inline-flex justify-center items-center gap-2 disabled:opacity-50">
            {busy === 'crawl-platform' ? <Loader2 size={18} className="animate-spin" /> : <FileDown size={18} />}
            Crawl Vehicle/PDF
          </button>
        </div>

        <div className="glass-panel border border-outline-variant/30 rounded-2xl p-5 space-y-4">
          <h2 className="text-lg font-bold text-on-surface">Knowledge Operations</h2>
          <p className="text-xs text-on-surface-variant">Clear và Ingest là hai thao tác độc lập. Ingest không clear ngầm.</p>
          <input className="w-full px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/30 text-sm" placeholder="Nhập CLEAR để xóa knowledge" value={confirmText} onChange={(e) => setConfirmText(e.target.value)} />
          <button onClick={() => runJsonAction('clear', 'Clear ALL Knowledge', api.clearAllKnowledge)} disabled={Boolean(busy) || confirmText !== 'CLEAR'} className="w-full py-3 rounded-xl bg-error text-white font-bold inline-flex justify-center items-center gap-2 disabled:opacity-50">
            {busy === 'clear' ? <Loader2 size={18} className="animate-spin" /> : <Trash2 size={18} />}
            Clear ALL Knowledge
          </button>
          <button onClick={() => runJsonAction('ingest-all', 'Ingest ALL From data/', api.ingestAllKnowledge)} disabled={Boolean(busy)} className="w-full py-3 rounded-xl bg-emerald-600 text-white font-bold inline-flex justify-center items-center gap-2 disabled:opacity-50">
            {busy === 'ingest-all' ? <Loader2 size={18} className="animate-spin" /> : <DatabaseZap size={18} />}
            Ingest ALL From data/
          </button>
        </div>

        <div className="bg-[#05090f] rounded-2xl border border-outline-variant/30 overflow-hidden min-h-[260px] flex flex-col">
          <div className="px-4 py-3 bg-white/5 border-b border-white/10 text-xs font-mono text-white/50">knowledge_builder.log</div>
          <div ref={terminalRef} className="p-4 overflow-y-auto font-mono text-xs flex-1 text-green-300">
            {logs.length === 0 ? <div className="text-white/25 italic">Logs sẽ hiện ở đây...</div> : logs.map((log, idx) => (
              <pre key={idx} className={`whitespace-pre-wrap mb-2 ${log.includes('[ERROR]') ? 'text-red-400' : log.includes('[SYSTEM]') ? 'text-blue-400' : 'text-green-300'}`}>{log}</pre>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}


