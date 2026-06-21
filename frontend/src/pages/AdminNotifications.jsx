import { useEffect, useMemo, useState } from 'react';
import { Archive, Bell, Edit3, Megaphone, Plus, RefreshCw, Save, Send } from 'lucide-react';
import { api } from '../api';

const EMPTY_FORM = {
  title: '',
  summary: '',
  body: '',
  notification_type: 'feature_update',
  audience: 'all_users',
  priority: 50,
  action_label: '',
  action_url: '/chat',
  published_at: '',
  expires_at: '',
};

const statusStyles = {
  draft: 'bg-slate-500/15 text-slate-300 border-slate-500/20',
  published: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/20',
  archived: 'bg-amber-500/15 text-amber-300 border-amber-500/20',
};

export default function AdminNotifications() {
  const [items, setItems] = useState([]);
  const [status, setStatus] = useState('all');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);

  const selected = useMemo(() => items.find(item => item.id === editing), [items, editing]);

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.getAdminNotifications(status);
      setItems(data);
    } catch (error) {
      console.error(error);
      alert('Không tải được danh sách thông báo');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [status]);

  const resetForm = () => {
    setEditing(null);
    setForm(EMPTY_FORM);
  };

  const editItem = (item) => {
    setEditing(item.id);
    setForm({
      title: item.title || '',
      summary: item.summary || '',
      body: item.body || '',
      notification_type: item.notification_type || 'announcement',
      audience: item.audience || 'all_users',
      priority: item.priority ?? 100,
      action_label: item.action_label || '',
      action_url: item.action_url || '',
      published_at: item.published_at ? item.published_at.slice(0, 16) : '',
      expires_at: item.expires_at ? item.expires_at.slice(0, 16) : '',
    });
  };

  const updateField = (field, value) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const payload = () => ({
    ...form,
    priority: Number(form.priority) || 100,
    published_at: form.published_at || null,
    expires_at: form.expires_at || null,
  });

  const save = async () => {
    if (!form.title.trim() || !form.body.trim()) {
      alert('Cần nhập tiêu đề và nội dung');
      return;
    }
    setSaving(true);
    try {
      if (editing) {
        await api.updateAdminNotification(editing, payload());
      } else {
        const created = await api.createAdminNotification(payload());
        setEditing(created.id);
      }
      await load();
    } catch (error) {
      console.error(error);
      alert('Lưu thông báo thất bại');
    } finally {
      setSaving(false);
    }
  };

  const setItemStatus = async (id, nextStatus) => {
    try {
      await api.updateAdminNotificationStatus(id, nextStatus);
      await load();
    } catch (error) {
      console.error(error);
      alert('Cập nhật trạng thái thất bại');
    }
  };

  const archive = async (id) => {
    try {
      await api.archiveAdminNotification(id);
      await load();
    } catch (error) {
      console.error(error);
      alert('Archive thất bại');
    }
  };

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-5 text-slate-100">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-2 text-[#00c897]">
            <Bell size={20} />
            <span className="text-xs font-black uppercase tracking-widest">Admin Broadcasts</span>
          </div>
          <h1 className="mt-2 text-2xl font-black">Notifications</h1>
          <p className="mt-1 text-sm font-medium text-slate-400">
            Tạo thông báo custom để gửi đến toàn bộ user.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={status}
            onChange={(event) => setStatus(event.target.value)}
            className="rounded-lg border border-slate-700 bg-[#0f172a] px-3 py-2 text-sm font-bold text-slate-200 outline-none focus:border-[#00c897]"
          >
            <option value="all">Tất cả</option>
            <option value="draft">Draft</option>
            <option value="published">Published</option>
            <option value="archived">Archived</option>
          </select>
          <button
            onClick={load}
            className="flex items-center gap-2 rounded-lg border border-slate-700 px-3 py-2 text-sm font-bold text-slate-300 transition hover:border-[#00c897]/60 hover:text-[#00c897]"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
          <button
            onClick={resetForm}
            className="flex items-center gap-2 rounded-lg bg-[#00c897] px-4 py-2 text-sm font-black text-white transition hover:bg-[#00b084]"
          >
            <Plus size={16} />
            New
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[minmax(0,1fr)_420px]">
        <div className="overflow-hidden rounded-xl border border-slate-800 bg-[#0b111a]">
          <div className="border-b border-slate-800 px-5 py-4 text-sm font-black uppercase tracking-wider text-slate-400">
            Danh sách thông báo
          </div>
          <div className="divide-y divide-slate-800">
            {items.length === 0 ? (
              <div className="p-8 text-center text-sm font-semibold text-slate-500">
                Chưa có thông báo nào.
              </div>
            ) : items.map((item) => (
              <article key={item.id} className="p-5 transition hover:bg-white/[0.02]">
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div className="min-w-0 flex-1">
                    <div className="mb-2 flex flex-wrap items-center gap-2">
                      <span className={`rounded-full border px-2.5 py-1 text-[11px] font-black uppercase ${statusStyles[item.status] || statusStyles.draft}`}>
                        {item.status}
                      </span>
                      <span className="rounded-full bg-[#00c897]/10 px-2.5 py-1 text-[11px] font-black uppercase text-[#00c897]">
                        {item.notification_type}
                      </span>
                      <span className="text-xs font-semibold text-slate-500">Priority {item.priority}</span>
                    </div>
                    <h2 className="truncate text-base font-black text-slate-100">{item.title}</h2>
                    {item.summary && <p className="mt-1 line-clamp-2 text-sm font-medium text-slate-400">{item.summary}</p>}
                    <p className="mt-2 line-clamp-2 text-sm text-slate-500">{item.body}</p>
                  </div>
                  <div className="flex shrink-0 flex-wrap gap-2">
                    <button
                      onClick={() => editItem(item)}
                      className="flex items-center gap-1.5 rounded-lg border border-slate-700 px-3 py-2 text-xs font-bold text-slate-300 transition hover:border-[#00c897]/60 hover:text-[#00c897]"
                    >
                      <Edit3 size={14} />
                      Edit
                    </button>
                    {item.status !== 'published' && (
                      <button
                        onClick={() => setItemStatus(item.id, 'published')}
                        className="flex items-center gap-1.5 rounded-lg bg-emerald-500/15 px-3 py-2 text-xs font-black text-emerald-300 transition hover:bg-emerald-500/25"
                      >
                        <Send size={14} />
                        Publish
                      </button>
                    )}
                    {item.status !== 'archived' && (
                      <button
                        onClick={() => archive(item.id)}
                        className="flex items-center gap-1.5 rounded-lg bg-amber-500/15 px-3 py-2 text-xs font-black text-amber-300 transition hover:bg-amber-500/25"
                      >
                        <Archive size={14} />
                        Archive
                      </button>
                    )}
                  </div>
                </div>
              </article>
            ))}
          </div>
        </div>

        <aside className="rounded-xl border border-slate-800 bg-[#0b111a] p-5">
          <div className="mb-4 flex items-center gap-2">
            <Megaphone size={18} className="text-[#00c897]" />
            <h2 className="text-base font-black">{selected ? 'Chỉnh sửa thông báo' : 'Tạo thông báo'}</h2>
          </div>
          <div className="space-y-4">
            <label className="block">
              <span className="mb-1 block text-xs font-black uppercase text-slate-500">Tiêu đề</span>
              <input
                value={form.title}
                onChange={(event) => updateField('title', event.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-[#070b14] px-3 py-2 text-sm font-semibold text-slate-100 outline-none focus:border-[#00c897]"
              />
            </label>
            <label className="block">
              <span className="mb-1 block text-xs font-black uppercase text-slate-500">Tóm tắt</span>
              <textarea
                value={form.summary}
                onChange={(event) => updateField('summary', event.target.value)}
                rows={2}
                className="w-full resize-none rounded-lg border border-slate-700 bg-[#070b14] px-3 py-2 text-sm font-semibold text-slate-100 outline-none focus:border-[#00c897]"
              />
            </label>
            <label className="block">
              <span className="mb-1 block text-xs font-black uppercase text-slate-500">Nội dung</span>
              <textarea
                value={form.body}
                onChange={(event) => updateField('body', event.target.value)}
                rows={6}
                className="w-full resize-none rounded-lg border border-slate-700 bg-[#070b14] px-3 py-2 text-sm font-semibold leading-relaxed text-slate-100 outline-none focus:border-[#00c897]"
              />
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label className="block">
                <span className="mb-1 block text-xs font-black uppercase text-slate-500">Loại</span>
                <select
                  value={form.notification_type}
                  onChange={(event) => updateField('notification_type', event.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-[#070b14] px-3 py-2 text-sm font-bold text-slate-100 outline-none focus:border-[#00c897]"
                >
                  <option value="feature_update">Feature update</option>
                  <option value="announcement">Announcement</option>
                  <option value="maintenance">Maintenance</option>
                  <option value="warning">Warning</option>
                </select>
              </label>
              <label className="block">
                <span className="mb-1 block text-xs font-black uppercase text-slate-500">Priority</span>
                <input
                  type="number"
                  value={form.priority}
                  onChange={(event) => updateField('priority', event.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-[#070b14] px-3 py-2 text-sm font-bold text-slate-100 outline-none focus:border-[#00c897]"
                />
              </label>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <label className="block">
                <span className="mb-1 block text-xs font-black uppercase text-slate-500">CTA label</span>
                <input
                  value={form.action_label}
                  onChange={(event) => updateField('action_label', event.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-[#070b14] px-3 py-2 text-sm font-semibold text-slate-100 outline-none focus:border-[#00c897]"
                />
              </label>
              <label className="block">
                <span className="mb-1 block text-xs font-black uppercase text-slate-500">CTA URL</span>
                <input
                  value={form.action_url}
                  onChange={(event) => updateField('action_url', event.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-[#070b14] px-3 py-2 text-sm font-semibold text-slate-100 outline-none focus:border-[#00c897]"
                />
              </label>
            </div>
            <button
              onClick={save}
              disabled={saving}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-[#00c897] px-4 py-3 text-sm font-black text-white transition hover:bg-[#00b084] disabled:opacity-50"
            >
              <Save size={16} />
              {saving ? 'Đang lưu...' : 'Lưu thông báo'}
            </button>
          </div>
        </aside>
      </div>
    </div>
  );
}
