import { createPortal } from 'react-dom';
import { Bell, Check, Megaphone, Sparkles, Wrench, AlertTriangle } from 'lucide-react';

const typeIcon = {
  feature_update: Sparkles,
  maintenance: Wrench,
  warning: AlertTriangle,
  announcement: Megaphone,
};

const typeLabel = {
  feature_update: 'Tính năng mới',
  maintenance: 'Bảo trì',
  warning: 'Lưu ý',
  announcement: 'Thông báo',
};

const formatDate = (value) => {
  if (!value) return '';
  try {
    return new Intl.DateTimeFormat('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(value));
  } catch {
    return '';
  }
};

const NotificationDropdown = ({
  isOpen,
  onClose,
  notifications = [],
  unreadCount = 0,
  loading = false,
  onMarkRead,
  onMarkAllRead,
}) => {
  if (!isOpen) return null;

  const content = (
    <div className="notification-portal-wrapper font-sans">
      <div
        className="fixed inset-0 z-[999998] bg-black/60 backdrop-blur-md"
        onClick={onClose}
      />

      <div
        className="fixed left-1/2 top-1/2 z-[999999] flex max-h-[85vh] w-[92%] max-w-[640px] -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden rounded-[28px] border border-black/10 bg-surface text-on-surface shadow-[0_25px_70px_rgba(0,0,0,0.45)] dark:border-white/10 dark:bg-[#0c1618]"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex shrink-0 items-center justify-between border-b border-outline/10 bg-surface-container-low px-6 py-5 dark:bg-white/5 md:px-8">
          <div className="flex items-center gap-3">
            <h3 className="m-0 flex items-center gap-2 text-lg font-black">
              Thông báo
              {unreadCount > 0 && (
                <span className="rounded-full bg-red-500 px-2 py-0.5 text-[11px] font-black text-white">
                  {unreadCount}
                </span>
              )}
            </h3>
          </div>
          <button
            type="button"
            onClick={onMarkAllRead}
            disabled={!unreadCount}
            className="text-xs font-bold text-primary transition hover:underline disabled:cursor-not-allowed disabled:opacity-40"
          >
            Đánh dấu đã đọc
          </button>
        </div>

        <div className="no-scrollbar flex-1 overflow-y-auto p-5 md:p-8">
          {loading ? (
            <div className="space-y-3">
              {[0, 1, 2].map((item) => (
                <div key={item} className="h-24 animate-pulse rounded-2xl bg-black/5 dark:bg-white/5" />
              ))}
            </div>
          ) : notifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-[#00c897]/10 text-[#00a884]">
                <Bell size={24} />
              </div>
              <h4 className="text-base font-black">Chưa có thông báo mới</h4>
              <p className="mt-2 max-w-sm text-sm font-medium leading-relaxed text-on-surface-variant/80">
                Các cập nhật tính năng và thông tin vận hành sẽ xuất hiện tại đây.
              </p>
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              {notifications.map((notification) => {
                const Icon = typeIcon[notification.type] || Megaphone;
                return (
                  <article
                    key={notification.id}
                    className={`rounded-2xl border p-4 transition ${
                      notification.is_read
                        ? 'border-outline-variant/20 bg-white/45 dark:bg-white/[0.03]'
                        : 'border-[#00c897]/30 bg-[#00c897]/10 dark:bg-[#00c897]/10'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[#00c897]/10 text-[#008f72] dark:text-[#00c897]">
                        <Icon size={18} />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="mb-1 flex flex-wrap items-center gap-2">
                          {!notification.is_read && (
                            <span className="rounded-md bg-blue-500/15 px-2 py-0.5 text-[10px] font-black uppercase text-blue-600 dark:text-blue-300">
                              Mới
                            </span>
                          )}
                          <span className="text-[10px] font-black uppercase tracking-wide text-[#008f72]">
                            {typeLabel[notification.type] || typeLabel.announcement}
                          </span>
                          <span className="text-[11px] font-semibold text-on-surface-variant/55">
                            {formatDate(notification.published_at || notification.created_at)}
                          </span>
                        </div>
                        <h4 className="text-base font-black leading-snug">{notification.title}</h4>
                        {notification.summary && (
                          <p className="mt-2 text-sm font-semibold leading-relaxed text-on-surface-variant/90">
                            {notification.summary}
                          </p>
                        )}
                        <p className="mt-3 whitespace-pre-line text-sm font-medium leading-relaxed text-on-surface-variant">
                          {notification.body}
                        </p>
                        <div className="mt-4 flex flex-wrap items-center gap-2">
                          {notification.action_url && (
                            <a
                              href={notification.action_url}
                              onClick={() => onMarkRead?.(notification.id)}
                              className="rounded-full bg-[#00c897] px-4 py-2 text-xs font-black text-white shadow-[0_8px_18px_rgba(0,200,151,0.25)] transition hover:bg-[#00b084]"
                            >
                              {notification.action_label || 'Mở'}
                            </a>
                          )}
                          {!notification.is_read && (
                            <button
                              type="button"
                              onClick={() => onMarkRead?.(notification.id)}
                              className="flex items-center gap-1.5 rounded-full border border-outline-variant/30 px-3 py-2 text-xs font-bold text-on-surface-variant transition hover:border-[#00c897]/40 hover:text-[#00a884]"
                            >
                              <Check size={14} />
                              Đã đọc
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </div>

        <div className="flex shrink-0 justify-center border-t border-outline/10 bg-surface-container-low px-6 py-4 dark:bg-white/5">
          <button
            type="button"
            onClick={onClose}
            className="flex w-full max-w-[220px] items-center justify-center gap-2 rounded-full bg-[#00c897] py-3 text-sm font-black text-white shadow-[0_8px_25px_rgba(0,200,151,0.35)] transition hover:bg-[#00b084]"
          >
            <Check size={18} />
            Đã hiểu
          </button>
        </div>
      </div>
    </div>
  );

  return createPortal(content, document.body);
};

export default NotificationDropdown;
