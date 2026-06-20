import {
  ChevronRight,
  Clock3,
  DollarSign,
  Heart,
  Info,
  MapPin,
  Star,
  ThumbsDown,
  Utensils,
  X,
} from 'lucide-react';

const FoodMetric = ({ icon: Icon, label, value }) => (
  <div className="flex items-center gap-1.5 md:gap-2 min-w-0">
    <div className="w-7 h-7 md:w-8 md:h-8 rounded-full bg-surface-container-high/70 dark:bg-white/10 flex items-center justify-center text-on-surface shrink-0">
      <Icon size={14} className="md:w-4 md:h-4" />
    </div>
    <div className="min-w-0 leading-tight">
      <div className="text-[10px] md:text-[11px] text-on-surface-variant/80 truncate">{label}</div>
      <div className="text-xs md:text-sm font-black text-[#009e79] truncate">{value}</div>
    </div>
  </div>
);

export const FoodExplanationModal = ({ item, onClose }) => {
  if (!item) return null;

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-surface-container-lowest w-full max-w-lg rounded-3xl shadow-2xl border border-outline-variant/30 overflow-hidden text-on-surface">
        <div className="flex items-center justify-between p-5 border-b border-outline-variant/20 bg-surface-container-low">
          <h3 className="font-bold text-lg flex items-center gap-2">
            <Info size={20} className="text-primary" />
            Vì sao gợi ý "{item.name}"?
          </h3>
          <button onClick={onClose} className="p-1.5 rounded-full hover:bg-surface-variant text-on-surface-variant">
            <X size={18} />
          </button>
        </div>
        <div className="p-5 overflow-y-auto max-h-[60vh] space-y-4 text-sm">
          <div className="bg-primary/5 p-4 rounded-xl border border-primary/20">
            <div className="font-black text-3xl text-primary text-center">{((item.score || 0) * 100).toFixed(1)}%</div>
            <div className="text-center text-xs font-semibold text-on-surface-variant uppercase mt-1">Độ phù hợp tổng thể</div>
          </div>

          {item.reason && (
            <div className="bg-primary/5 p-3.5 rounded-xl border border-primary/10">
              <h4 className="font-bold text-xs text-primary uppercase tracking-wider mb-1">Lý do gợi ý</h4>
              <p className="text-on-surface-variant text-xs md:text-sm leading-relaxed">{item.reason}</p>
            </div>
          )}

          {item.advice && (
            <div className="bg-[#00c897]/5 p-3.5 rounded-xl border border-[#00c897]/20">
              <h4 className="font-bold text-xs text-[#008f6f] uppercase tracking-wider mb-1">Lời khuyên ăn uống</h4>
              <p className="text-on-surface-variant text-xs md:text-sm leading-relaxed">{item.advice}</p>
            </div>
          )}

          <div className="text-xs text-on-surface-variant/80 italic text-center mt-4 pt-4 border-t border-outline-variant/20">
            Kết quả được chấm điểm tự động dựa trên học máy và thuật toán nội bộ của Xanh SM AI.
          </div>
        </div>
      </div>
    </div>
  );
};

export const FoodRecommendationRow = ({ item, index, onOpenMenu, onLike, onDismiss, onDislike, onExplain }) => {
  const Wrapper = item.order_url ? 'a' : 'div';
  const wrapperProps = item.order_url ? {
    href: item.order_url,
    target: '_blank',
    rel: 'noopener noreferrer',
  } : {};
  const isBest = item.is_best || index === 0;

  return (
    <Wrapper
      {...wrapperProps}
      onClick={() => onOpenMenu?.(item, index)}
      className={`relative grid grid-cols-[72px_minmax(0,1fr)] sm:grid-cols-[96px_minmax(0,1fr)] md:grid-cols-[170px_1fr_auto] gap-2.5 md:gap-4 p-2.5 md:p-4 rounded-2xl border bg-white/75 dark:bg-white/[0.04] transition-all group overflow-hidden ${
        isBest
          ? 'border-[#00c897]/40 shadow-[0_8px_24px_rgba(0,200,151,0.10)]'
          : 'border-outline-variant/20 hover:border-[#00c897]/30'
      }`}
    >
      {isBest && (
        <div className="absolute left-2 top-2 md:left-3 md:top-3 z-10 rounded-full bg-[#00a884] px-2 md:px-2.5 py-0.5 md:py-1 text-[9px] md:text-[11px] font-black text-white shadow-sm max-w-[120px] md:max-w-none truncate">
          Gợi ý phù hợp nhất
        </div>
      )}

      <img
        src={item.image_url || '/Bot.png'}
        alt={item.name || 'Món ăn'}
        className="w-full h-[72px] sm:h-[92px] md:h-[122px] rounded-xl object-cover border border-outline-variant/10 bg-surface-container-high"
        loading="lazy"
      />

      <div className="min-w-0 flex flex-col justify-center gap-2 md:gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h4 className="text-sm sm:text-base md:text-lg font-black text-on-surface leading-snug line-clamp-1">
              {item.name}
            </h4>
            {item.rating && (
              <span className="inline-flex items-center gap-1 rounded-full bg-[#00c897]/10 px-1.5 md:px-2 py-0.5 text-xs md:text-sm font-black text-[#008f6f]">
                <Star size={12} className="md:w-3.5 md:h-3.5" fill="currentColor" />
                {item.rating}
              </span>
            )}
          </div>
          <p className="mt-1 text-xs md:text-sm text-on-surface-variant/85 leading-relaxed line-clamp-2">
            {item.reason || item.dish_name || item.address || 'Phù hợp với nhu cầu món ăn của bạn.'}
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-1.5 md:gap-3">
          <FoodMetric icon={Clock3} label="Giao khoảng" value={item.eta_text || 'Đang cập nhật'} />
          <FoodMetric icon={MapPin} label="Cách bạn" value={item.distance_text || 'Đang cập nhật'} />
          <FoodMetric icon={DollarSign} label="Phí giao từ" value={item.delivery_fee_text || 'Đang cập nhật'} />
        </div>
      </div>

      <div className="col-span-2 md:col-span-1 flex flex-col sm:flex-row md:flex-col items-stretch sm:items-center md:items-center justify-between md:justify-center gap-2 md:gap-3 min-w-0">
        <div className="flex items-center justify-center sm:justify-start md:justify-center gap-1 md:gap-1.5 min-w-0">
          {[
            { title: 'Lưu lựa chọn', icon: Heart, action: onLike },
            { title: 'Giải thích', icon: Info, action: onExplain },
            { title: 'Bỏ qua', icon: X, action: onDismiss },
            { title: 'Không phù hợp', icon: ThumbsDown, action: onDislike },
          ].map(({ title, icon: ActionIcon, action }) => (
            <button
              key={title}
              type="button"
              className={`w-8 h-8 md:w-9 md:h-9 rounded-full flex items-center justify-center transition-colors ${
                item.interaction === (title === 'Lưu lựa chọn' ? 'like' : title === 'Không phù hợp' ? 'dislike' : '')
                  ? 'bg-[#00c897] text-white'
                  : 'bg-surface-container-high/70 dark:bg-white/10 text-[#00a884] hover:bg-[#00c897] hover:text-white'
              }`}
              title={title}
              onClick={(event) => {
                event.preventDefault();
                event.stopPropagation();
                action?.(item, index);
              }}
            >
              <ActionIcon size={14} className="md:w-4 md:h-4" fill={item.interaction === (title === 'Lưu lựa chọn' ? 'like' : title === 'Không phù hợp' ? 'dislike' : '') ? 'currentColor' : 'none'} />
            </button>
          ))}
        </div>
        <span className="inline-flex w-full sm:w-auto items-center justify-center gap-1.5 md:gap-2 rounded-xl border border-[#00a884] px-3 md:px-4 py-2 text-xs md:text-sm font-black text-[#008f6f] group-hover:bg-[#00c897] group-hover:text-white transition-colors whitespace-nowrap min-w-0">
          Xem thực đơn
          <ChevronRight size={14} className="md:w-4 md:h-4" />
        </span>
      </div>
    </Wrapper>
  );
};

export const FoodCardShimmer = () => (
  <div className="my-2 grid grid-cols-[72px_minmax(0,1fr)] sm:grid-cols-[96px_minmax(0,1fr)] md:grid-cols-[170px_1fr_auto] gap-2.5 md:gap-4 p-2.5 md:p-4 rounded-2xl border border-[#00c897]/25 bg-white/70 dark:bg-white/[0.04] overflow-hidden animate-pulse">
    <div className="w-full h-[72px] sm:h-[92px] md:h-[122px] rounded-xl bg-[#00c897]/15" />
    <div className="min-w-0 flex flex-col justify-center gap-3">
      <div className="h-5 w-3/4 rounded-full bg-on-surface/10" />
      <div className="h-3 w-full rounded-full bg-on-surface/10" />
      <div className="h-3 w-2/3 rounded-full bg-on-surface/10" />
      <div className="grid grid-cols-3 gap-3 pt-2">
        <div className="h-8 rounded-full bg-[#00c897]/10" />
        <div className="h-8 rounded-full bg-[#00c897]/10" />
        <div className="h-8 rounded-full bg-[#00c897]/10" />
      </div>
    </div>
    <div className="hidden md:flex flex-col justify-center gap-3">
      <div className="h-9 w-28 rounded-xl bg-[#00c897]/10" />
      <div className="h-9 w-28 rounded-xl bg-on-surface/10" />
    </div>
  </div>
);

export const FoodRecommendationList = ({ data, onOpenMenu, onLike, onDismiss, onDislike, onExplain }) => {
  const items = data?.items || [];
  const moreItems = data?.more_items || [];
  if (!items.length) return null;

  return (
    <div className="w-full rounded-2xl md:rounded-3xl border border-white/50 dark:border-white/10 bg-white/72 dark:bg-white/[0.03] p-3 md:p-5 shadow-[0_12px_40px_rgba(0,0,0,0.05)]">
      <div className="flex items-start gap-2.5 md:gap-3 mb-3 md:mb-4">
        <div className="w-9 h-9 md:w-12 md:h-12 rounded-full bg-[#00c897]/12 text-[#009e79] flex items-center justify-center shrink-0">
          <Utensils size={18} className="md:w-[22px] md:h-[22px]" />
        </div>
        <div className="min-w-0">
          <h3 className="text-base md:text-2xl font-black text-on-surface leading-tight">
            {data.title || 'Một vài quán phù hợp gần bạn'}
          </h3>
          <p className="mt-1 text-xs md:text-base text-on-surface-variant/85 leading-relaxed">
            {data.subtitle || 'Đã sắp xếp theo khoảng cách, thời gian giao hàng và mức độ phù hợp với nhu cầu của bạn.'}
          </p>
        </div>
      </div>

      <div className="flex flex-col gap-3">
        {items.map((item, index) => (
          <FoodRecommendationRow
            key={item.item_id || index}
            item={item}
            index={index}
            onOpenMenu={onOpenMenu}
            onLike={onLike}
            onDismiss={onDismiss}
            onDislike={onDislike}
            onExplain={onExplain}
          />
        ))}
      </div>

      {moreItems.length > 0 && (
        <div className="mt-4 rounded-2xl border border-outline-variant/20 bg-white/50 dark:bg-white/[0.03] p-3">
          <div className="flex items-center justify-between gap-3 mb-3">
            <div className="text-sm font-black text-on-surface">Thêm lựa chọn gần bạn</div>
            <ChevronRight size={18} className="text-[#00a884]" />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
            {moreItems.map((item, index) => (
              <a
                key={item.item_id || index}
                href={item.order_url || '#'}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => onOpenMenu?.(item, index + items.length)}
                className="grid grid-cols-[64px_1fr] gap-3 rounded-xl border border-outline-variant/20 bg-white/70 dark:bg-white/[0.04] p-2 hover:border-[#00c897]/40 transition-colors"
              >
                <img src={item.image_url || '/Bot.png'} alt={item.name || 'Món ăn'} className="w-16 h-16 rounded-lg object-cover bg-surface-container-high" loading="lazy" />
                <div className="min-w-0 text-xs leading-snug">
                  <div className="font-black text-on-surface truncate">{item.name}</div>
                  <div className="mt-1 flex items-center gap-1 text-[#009e79] font-black">
                    <Star size={12} fill="currentColor" />
                    {item.rating || '4.5'}
                  </div>
                  <div className="mt-1 text-on-surface-variant/80 truncate">{item.distance_text} · {item.eta_text}</div>
                  <div className="text-on-surface-variant/80 truncate">Phí giao từ {item.delivery_fee_text}</div>
                </div>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
