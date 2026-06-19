import { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import 'regenerator-runtime/runtime';
import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useSearchParams } from 'react-router-dom';
import { MapContainer, Marker, TileLayer, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { User, Loader2, Link2, Plus, Mic, MicOff, Send, Car, Key, Tag, Newspaper, ShieldCheck, CheckCheck, Gift, Info, X, Sparkles, PencilLine, Image as ImageIcon, ThumbsUp, ThumbsDown, Search, MapPin, Clock3, Star, Utensils, Heart, DollarSign, ChevronLeft, ChevronRight, LocateFixed } from 'lucide-react';
import { api } from '../api';
import { useAuth } from '../AuthContext';

const stripNode = (props) => {
  const rest = { ...props };
  delete rest.node;
  return rest;
};

const MessageCard = ({ icon, title, desc, image, link, index }) => {
  const IconComponent = useMemo(() => {
    switch (icon) {
      case 'car': return Car;
      case 'bike': return Car; // Bike icon would be better if available
      case 'gift': return Gift;
      case 'news': return Newspaper;
      case 'info': return Info;
      default: return Info;
    }
  }, [icon]);

  const CardWrapper = link ? 'a' : 'div';
  const wrapperProps = link ? {
    href: link,
    target: "_blank",
    rel: "noopener noreferrer",
    className: "flex items-center gap-4 p-4 my-2 bg-white/50 dark:bg-white/5 border border-outline-variant/20 rounded-2xl hover:bg-[#00c897]/5 transition-all group cursor-pointer"
  } : {
    className: "flex items-center gap-4 p-4 my-2 bg-white/50 dark:bg-white/5 border border-outline-variant/20 rounded-2xl transition-all"
  };

  return (
    <CardWrapper {...wrapperProps}>
      {image ? (
        <img
          src={image}
          alt={title || "Hình ảnh Xanh SM"}
          className="w-16 h-16 rounded-xl object-cover border border-outline-variant/20 bg-surface-container-high shrink-0"
          loading="lazy"
        />
      ) : (
        <div className={`w-12 h-12 rounded-xl bg-[#00c897]/10 flex items-center justify-center text-[#00c897] shrink-0 ${link ? 'group-hover:bg-[#00c897] group-hover:text-white' : ''} transition-all`}>
          <IconComponent size={24} />
        </div>
      )}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="w-5 h-5 rounded-full bg-[#00c897] text-white text-[10px] font-bold flex items-center justify-center shrink-0">
            {index}
          </span>
          <h4 className="font-bold text-sm text-on-surface truncate">{title}</h4>
        </div>
        <p className="text-xs text-on-surface-variant/80 line-clamp-2 leading-relaxed">
          {desc}
        </p>
      </div>
      {link && (
        <div className="text-[#00c897] opacity-0 group-hover:opacity-100 transition-opacity">
          <Plus size={16} className="rotate-45" />
        </div>
      )}
    </CardWrapper>
  );
};

const RagMediaCard = ({ card }) => {
  const [activeImage, setActiveImage] = useState(0);
  const images = card.images?.length ? card.images : (card.image_url ? [card.image_url] : []);
  const imageLabels = card.metadata?.image_labels || [];
  const Icon = card.type === 'vehicle' ? Car : card.type === 'news' ? Newspaper : Info;
  const Wrapper = card.url ? 'a' : 'div';
  const wrapperProps = card.url ? { href: card.url, target: '_blank', rel: 'noopener noreferrer' } : {};
  const imageIndex = images.length ? Math.min(activeImage, images.length - 1) : 0;
  const goPrev = (event) => {
    event.preventDefault();
    event.stopPropagation();
    setActiveImage((value) => (value - 1 + images.length) % images.length);
  };
  const goNext = (event) => {
    event.preventDefault();
    event.stopPropagation();
    setActiveImage((value) => (value + 1) % images.length);
  };

  return (
    <Wrapper
      {...wrapperProps}
      className="block min-w-[280px] sm:min-w-0 rounded-3xl border border-outline-variant/20 bg-white/78 dark:bg-white/[0.04] overflow-hidden hover:border-[#00c897]/40 transition-colors shadow-[0_18px_50px_rgba(0,0,0,0.06)]"
    >
      {images.length > 0 ? (
        <div className="relative bg-gradient-to-br from-[#bff4ed] to-[#22bdb9]">
          <img
            src={images[imageIndex]}
            alt={card.title || 'Xanh SM'}
            className="w-full h-52 md:h-64 object-contain p-4"
            loading="lazy"
          />
          {images.length > 1 && (
            <>
              <button
                type="button"
                onClick={goPrev}
                className="absolute left-3 top-1/2 -translate-y-1/2 w-9 h-9 rounded-full bg-white/92 text-[#0b2a45] shadow-md flex items-center justify-center hover:bg-white"
                aria-label="Ảnh trước"
              >
                <ChevronLeft size={20} />
              </button>
              <button
                type="button"
                onClick={goNext}
                className="absolute right-3 top-1/2 -translate-y-1/2 w-9 h-9 rounded-full bg-white/92 text-[#0b2a45] shadow-md flex items-center justify-center hover:bg-white"
                aria-label="Ảnh sau"
              >
                <ChevronRight size={20} />
              </button>
              <div className="absolute left-1/2 -translate-x-1/2 bottom-3 flex items-center gap-1.5">
                {images.map((_, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={(event) => {
                      event.preventDefault();
                      event.stopPropagation();
                      setActiveImage(idx);
                    }}
                    className={`h-1.5 rounded-full transition-all ${idx === imageIndex ? 'w-8 bg-white' : 'w-2 bg-white/55'}`}
                    aria-label={`Xem ảnh ${idx + 1}`}
                  />
                ))}
              </div>
            </>
          )}
        </div>
      ) : (
        <div className="h-32 flex items-center justify-center bg-[#00c897]/10 text-[#00a884]">
          <Icon size={34} />
        </div>
      )}
      <div className="p-4">
        <div className="flex items-center gap-2 text-[11px] uppercase tracking-wide font-black text-[#00a884] mb-2">
          <Icon size={14} />
          {card.type === 'vehicle' ? 'Xe điện' : card.type === 'news' ? 'Tin tức' : 'Thông tin'}
          {images.length > 1 && <span className="normal-case tracking-normal text-on-surface-variant/60">{imageIndex + 1}/{images.length}</span>}
        </div>
        <h4 className="font-black text-on-surface leading-snug line-clamp-2">{card.title}</h4>
        {card.description && (
          <p className="mt-2 text-sm text-on-surface-variant/85 leading-relaxed line-clamp-3">{card.description}</p>
        )}
        {imageLabels[imageIndex] && (
          <div className="mt-3 text-sm font-black text-[#00a884]">{imageLabels[imageIndex]}</div>
        )}
        {card.metadata?.date && (
          <div className="mt-3 text-xs font-bold text-on-surface-variant/60">{card.metadata.date}</div>
        )}
      </div>
    </Wrapper>
  );
};

const RagCardList = ({ cards }) => {
  if (!cards?.length) return null;
  const gridClass = cards.length === 1
    ? 'grid grid-cols-1 gap-3'
    : cards.length === 2
      ? 'grid grid-cols-1 md:grid-cols-2 gap-3'
      : 'flex gap-3 overflow-x-auto snap-x snap-mandatory no-scrollbar pb-1';
  return (
    <div className={gridClass}>
      {cards.map((card, index) => (
        <div key={`${card.title}-${index}`} className={cards.length > 2 ? 'snap-start' : ''}>
          <RagMediaCard card={card} />
        </div>
      ))}
    </div>
  );
};

const extractMarkdownImageCards = (content) => {
  const imageRegex = /!\[([^\]]*)\]\((https?:\/\/[^)\s]+)\)/g;
  const images = [];
  let match;
  while ((match = imageRegex.exec(content)) !== null) {
    images.push({ alt: match[1]?.trim(), url: match[2]?.trim() });
  }
  if (images.length < 2) {
    return { cleanContent: content, cards: [] };
  }

  const lower = content.toLowerCase();
  const type = lower.includes('vf') || lower.includes('xe') || lower.includes('màu sắc') || lower.includes('mau sac')
    ? 'vehicle'
    : lower.includes('tin tức') || lower.includes('tin tuc')
      ? 'news'
      : 'info';
  const titleMatch = content.match(/#{2,4}\s*([^\n]+)|(?:Hình ảnh|Các màu sắc|Màu sắc)[^\n]*/i);
  const title = titleMatch?.[1]?.trim() || titleMatch?.[0]?.replace(/^#{2,4}\s*/, '').trim() || (type === 'vehicle' ? 'Hình ảnh xe' : 'Hình ảnh liên quan');

  const lines = content.split('\n');
  const cleanLines = [];
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    if (imageRegex.test(line)) {
      imageRegex.lastIndex = 0;
      if (cleanLines.length && /^\s*[-*]\s+\S/.test(cleanLines[cleanLines.length - 1])) {
        cleanLines.pop();
      }
      continue;
    }
    imageRegex.lastIndex = 0;
    cleanLines.push(line);
  }

  return {
    cleanContent: cleanLines.join('\n').replace(/\n{3,}/g, '\n\n').trim(),
    cards: [{
      type,
      title,
      description: type === 'vehicle'
        ? 'Anh/chị có thể dùng mũi tên để xem các hình ảnh/màu sắc khác nhau.'
        : 'Anh/chị có thể vuốt hoặc bấm mũi tên để xem các hình ảnh liên quan.',
      image_url: images[0]?.url,
      images: images.map((image) => image.url),
      metadata: {
        image_labels: images.map((image) => image.alt).filter(Boolean),
      },
    }],
  };
};

const foodPinIcon = L.divIcon({
  className: '',
  html: '<div style="width:28px;height:28px;border-radius:9999px;background:#00a884;border:3px solid white;box-shadow:0 8px 24px rgba(0,168,132,.35);"></div>',
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

const FoodMapClickHandler = ({ onPick }) => {
  useMapEvents({
    click(event) {
      onPick({ lat: event.latlng.lat, lng: event.latlng.lng, label: 'Vị trí đã chọn trên bản đồ' });
    },
  });
  return null;
};

const FoodMapRecenter = ({ center }) => {
  const map = useMap();
  const [lat, lng] = center;

  useEffect(() => {
    map.setView([lat, lng], map.getZoom(), { animate: true });
  }, [map, lat, lng]);

  return null;
};

const FoodMapPicker = ({ selectedPin, onPick, onConfirm, interactive = true, heightClass = 'h-56 md:h-64' }) => {
  const center = [
    Number(selectedPin?.lat) || 10.7769,
    Number(selectedPin?.lng) || 106.7009,
  ];

  return (
    <div className={`relative ${heightClass} overflow-hidden rounded-2xl border border-outline-variant/15 bg-surface-container-high`}>
      <MapContainer
        center={center}
        zoom={15}
        scrollWheelZoom={interactive}
        dragging={interactive}
        doubleClickZoom={interactive}
        className="h-full w-full z-0"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FoodMapRecenter center={center} />
        {interactive && <FoodMapClickHandler onPick={onPick} />}
        <Marker position={center} icon={foodPinIcon} />
      </MapContainer>
      {interactive && (
        <button
          type="button"
          onClick={() => onConfirm?.(selectedPin)}
          className="absolute bottom-3 left-3 right-3 z-[500] h-11 rounded-xl bg-[#00a884] text-sm font-black text-white shadow-lg hover:bg-[#008f73] transition-colors"
        >
          Xác nhận vị trí đã chọn
        </button>
      )}
    </div>
  );
};

const FoodMetric = ({ icon: Icon, label, value }) => (
  <div className="flex items-center gap-2 min-w-0">
    <div className="w-8 h-8 rounded-full bg-surface-container-high/70 dark:bg-white/10 flex items-center justify-center text-on-surface shrink-0">
      <Icon size={16} />
    </div>
    <div className="min-w-0 leading-tight">
      <div className="text-[11px] text-on-surface-variant/80 truncate">{label}</div>
      <div className="text-sm font-black text-[#009e79] truncate">{value}</div>
    </div>
  </div>
);

const FoodExplanationModal = ({ item, onClose }) => {
  if (!item) return null;
  const bd = item.score_breakdown || {};
  
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
            <div className="font-black text-3xl text-primary text-center">{(item.score * 100).toFixed(1)}%</div>
            <div className="text-center text-xs font-semibold text-on-surface-variant uppercase mt-1">Độ phù hợp tổng thể</div>
          </div>
          
          <div className="space-y-3">
            {[
              { label: 'Ngữ nghĩa (Vector Recall)', val: bd.recall_score },
              { label: 'Khoảng cách (Nearby)', val: bd.nearby_score },
              { label: 'Phí giao hàng', val: bd.delivery_fee_score },
              { label: 'Thời gian giao (ETA)', val: bd.eta_score },
              { label: 'Mức giá (Budget)', val: bd.budget_score },
              { label: 'Khuyến mãi (Discount)', val: bd.discount_score },
              { label: 'Khớp danh mục', val: bd.category_score },
              { label: 'Khớp khẩu vị', val: bd.taste_score },
              { label: 'Điểm đánh giá', val: bd.rating_score },
              { label: 'Độ phổ biến', val: bd.popularity_score }
            ].map(m => m.val !== undefined && (
              <div key={m.label} className="flex items-center justify-between">
                <span className="text-on-surface-variant font-medium">{m.label}</span>
                <div className="flex items-center gap-2">
                  <div className="w-24 h-2 bg-surface-variant rounded-full overflow-hidden">
                    <div className="h-full bg-primary rounded-full" style={{ width: `${(m.val || 0) * 100}%` }} />
                  </div>
                  <span className="text-xs font-bold w-8 text-right">{(m.val * 10).toFixed(1)}</span>
                </div>
              </div>
            ))}
          </div>
          
          <div className="text-xs text-on-surface-variant/80 italic text-center mt-4 pt-4 border-t border-outline-variant/20">
            Kết quả được chấm điểm tự động dựa trên học máy và thuật toán nội bộ của Xanh SM AI.
          </div>
        </div>
      </div>
    </div>
  );
};

const FoodRecommendationRow = ({ item, index, onOpenMenu, onLike, onDismiss, onDislike, onExplain }) => {
  const Wrapper = item.order_url ? 'a' : 'div';
  const wrapperProps = item.order_url ? {
    href: item.order_url,
    target: "_blank",
    rel: "noopener noreferrer"
  } : {};
  const isBest = item.is_best || index === 0;

  return (
    <Wrapper
      {...wrapperProps}
      onClick={() => onOpenMenu?.(item, index)}
      className={`relative grid grid-cols-[96px_1fr] md:grid-cols-[170px_1fr_auto] gap-4 p-3 md:p-4 rounded-2xl border bg-white/75 dark:bg-white/[0.04] transition-all group ${
        isBest
          ? 'border-[#00c897]/40 shadow-[0_8px_24px_rgba(0,200,151,0.10)]'
          : 'border-outline-variant/20 hover:border-[#00c897]/30'
      }`}
    >
      {isBest && (
        <div className="absolute left-3 top-3 z-10 rounded-full bg-[#00a884] px-2.5 py-1 text-[11px] font-black text-white shadow-sm">
          Gợi ý phù hợp nhất
        </div>
      )}

      <img
        src={item.image_url || '/Bot.png'}
        alt={item.name || 'Món ăn'}
        className="w-full h-[92px] md:h-[122px] rounded-xl object-cover border border-outline-variant/10 bg-surface-container-high"
        loading="lazy"
      />

      <div className="min-w-0 flex flex-col justify-center gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h4 className="text-base md:text-lg font-black text-on-surface leading-snug line-clamp-1">
              {item.name}
            </h4>
            {item.rating && (
              <span className="inline-flex items-center gap-1 rounded-full bg-[#00c897]/10 px-2 py-0.5 text-sm font-black text-[#008f6f]">
                <Star size={14} fill="currentColor" />
                {item.rating}
              </span>
            )}
          </div>
          <p className="mt-1 text-sm text-on-surface-variant/85 leading-relaxed line-clamp-2">
            {item.reason || item.dish_name || item.address || 'Phù hợp với nhu cầu món ăn của bạn.'}
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <FoodMetric icon={Clock3} label="Giao khoảng" value={item.eta_text || 'Đang cập nhật'} />
          <FoodMetric icon={MapPin} label="Cách bạn" value={item.distance_text || 'Đang cập nhật'} />
          <FoodMetric icon={DollarSign} label="Phí giao từ" value={item.delivery_fee_text || 'Đang cập nhật'} />
        </div>
      </div>

      <div className="col-span-2 md:col-span-1 flex md:flex-col items-center justify-between md:justify-center gap-3">
        <div className="flex items-center gap-1.5">
          {[
            { title: 'Lưu lựa chọn', icon: Heart, action: onLike },
            { title: 'Giải thích', icon: Info, action: onExplain },
            { title: 'Bỏ qua', icon: X, action: onDismiss },
            { title: 'Không phù hợp', icon: ThumbsDown, action: onDislike },
          ].map(({ title, icon: ActionIcon, action }) => (
            <button
              key={title}
              type="button"
              className={`w-9 h-9 rounded-full flex items-center justify-center transition-colors ${
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
              <ActionIcon size={16} fill={item.interaction === (title === 'Lưu lựa chọn' ? 'like' : title === 'Không phù hợp' ? 'dislike' : '') ? 'currentColor' : 'none'} />
            </button>
          ))}
        </div>
        <span className="inline-flex items-center justify-center gap-2 rounded-xl border border-[#00a884] px-4 py-2 text-sm font-black text-[#008f6f] group-hover:bg-[#00c897] group-hover:text-white transition-colors whitespace-nowrap">
          Xem thực đơn
          <ChevronRight size={16} />
        </span>
      </div>
    </Wrapper>
  );
};

const FoodRecommendationList = ({ data, onOpenMenu, onLike, onDismiss, onDislike, onExplain }) => {
  const items = data?.items || [];
  const moreItems = data?.more_items || [];
  if (!items.length) return null;

  return (
    <div className="w-full rounded-3xl border border-white/50 dark:border-white/10 bg-white/72 dark:bg-white/[0.03] p-4 md:p-5 shadow-[0_12px_40px_rgba(0,0,0,0.05)]">
      <div className="flex items-start gap-3 mb-4">
        <div className="w-12 h-12 rounded-full bg-[#00c897]/12 text-[#009e79] flex items-center justify-center shrink-0">
          <Utensils size={22} />
        </div>
        <div className="min-w-0">
          <h3 className="text-xl md:text-2xl font-black text-on-surface leading-tight">
            {data.title || 'Một vài quán phù hợp gần bạn'}
          </h3>
          <p className="mt-1 text-sm md:text-base text-on-surface-variant/85 leading-relaxed">
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

const FoodLocationRequestCard = ({ request, onUseCurrentLocation, onSubmitAddress, onSelectMapLocation, savedLocations = [] }) => {
  const [address, setAddress] = useState('');
  const [mapMode, setMapMode] = useState(false);
  const [selectedPin, setSelectedPin] = useState({ lat: 10.7769, lng: 106.7009, label: 'Vị trí đã chọn trên bản đồ' });

  const submitAddress = (event) => {
    event.preventDefault();
    const trimmed = address.trim();
    if (!trimmed) return;
    onSubmitAddress(trimmed);
  };


  return (
    <div className="w-full">
      <div className="overflow-hidden rounded-3xl border border-outline-variant/20 bg-white/82 dark:bg-white/[0.04] shadow-[0_12px_40px_rgba(0,0,0,0.05)]">
        <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,0.95fr)_minmax(260px,1fr)] gap-4 p-4 md:p-5">
          <div className="flex flex-col justify-between gap-4">
            <div>
              <h3 className="text-lg md:text-xl font-black text-on-surface leading-snug">
                Để gợi ý món ăn gần bạn chính xác hơn, em cần biết vị trí hiện tại của bạn nhé!
              </h3>
              <p className="mt-3 text-sm md:text-base text-on-surface-variant/85 leading-relaxed">
                Em sẽ giúp bạn tìm quán gần nhất, ước tính thời gian giao hàng và tính phí ship chính xác.
              </p>
            </div>

            <div className="flex flex-col gap-2">
              <button
                type="button"
                onClick={onUseCurrentLocation}
                className="h-12 rounded-xl bg-[#00a884] px-4 text-sm md:text-base font-black text-white hover:bg-[#008f73] transition-colors inline-flex items-center justify-center gap-2"
              >
                <LocateFixed size={18} />
                {request?.current_location_label || 'Chia sẻ vị trí hiện tại'}
              </button>
              <button
                type="button"
                onClick={() => setMapMode(prev => !prev)}
                className="h-12 rounded-xl border border-[#00a884] px-4 text-sm md:text-base font-black text-[#008f6f] hover:bg-[#00c897]/10 transition-colors inline-flex items-center justify-center gap-2"
              >
                <MapPin size={18} />
                Chọn trên bản đồ
              </button>
            </div>
          </div>

          <div>
            <FoodMapPicker
              selectedPin={selectedPin}
              onPick={setSelectedPin}
              onConfirm={onSelectMapLocation}
              interactive={mapMode}
            />
            <div className="mt-2 text-xs text-on-surface-variant/75">
              Bạn có thể chia sẻ vị trí hiện tại hoặc chọn pin trên bản đồ
            </div>
          </div>
        </div>

        <form onSubmit={submitAddress} className="border-t border-outline-variant/15 p-4 md:p-5">
          <div className="flex flex-col sm:flex-row gap-2">
            <label className="relative flex-1">
              <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant/50" />
              <input
                value={address}
                onChange={(event) => setAddress(event.target.value)}
                placeholder={request?.address_placeholder || 'Nhập địa chỉ giao hàng'}
                className="w-full h-12 rounded-xl border border-outline-variant/30 bg-white/85 dark:bg-white/5 pl-10 pr-3 text-sm font-semibold text-on-surface outline-none focus:border-[#00c897] focus:ring-2 focus:ring-[#00c897]/15 transition-all"
              />
            </label>
            <button
              type="submit"
              className="h-12 rounded-xl border border-[#00a884] px-4 text-sm font-black text-[#008f6f] hover:bg-[#00c897] hover:text-white transition-colors whitespace-nowrap"
            >
              {request?.submit_label || 'Tìm quán gần đây'}
            </button>
          </div>
          {savedLocations.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {savedLocations.slice(0, 3).map((place) => (
                <button
                  key={place.id}
                  type="button"
                  onClick={() => onSelectMapLocation(place)}
                  className="rounded-full border border-[#00a884]/30 bg-[#00c897]/8 px-3 py-1.5 text-xs font-bold text-[#008f6f] hover:bg-[#00c897]/15 transition-colors"
                >
                  {place.label}
                </button>
              ))}
            </div>
          )}
        </form>
      </div>
    </div>
  );
};

const FoodLocationConfirmedCard = ({ location, onSaveNamedLocation }) => {
  if (!location) return null;
  return (
    <div className="grid grid-cols-1 lg:grid-cols-[minmax(220px,0.8fr)_minmax(260px,1fr)] gap-4 rounded-3xl border border-[#00c897]/25 bg-white/82 dark:bg-white/[0.04] p-4 md:p-5 shadow-[0_12px_40px_rgba(0,0,0,0.05)]">
      <div className="flex flex-col justify-center gap-3">
        <div className="flex items-center gap-2 text-lg font-black text-on-surface">
          <span className="w-8 h-8 rounded-full bg-[#00a884] text-white flex items-center justify-center">
            <CheckCheck size={18} />
          </span>
          Vị trí hiện tại của bạn
        </div>
        <div className="text-sm leading-relaxed text-on-surface-variant/90">
          {location.label || location.address || 'Đã cập nhật vị trí giao hàng'}
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => onSaveNamedLocation?.('home', 'Nhà', location)}
            className="rounded-full border border-[#00a884]/30 px-3 py-1.5 text-xs font-black text-[#008f6f] hover:bg-[#00c897]/10 transition-colors"
          >
            Lưu là Nhà
          </button>
          <button
            type="button"
            onClick={() => onSaveNamedLocation?.('work', 'Công ty', location)}
            className="rounded-full border border-[#00a884]/30 px-3 py-1.5 text-xs font-black text-[#008f6f] hover:bg-[#00c897]/10 transition-colors"
          >
            Lưu là Công ty
          </button>
        </div>
      </div>
      <FoodMapPicker
        selectedPin={{ lat: location.lat, lng: location.lng }}
        interactive={false}
        heightClass="h-40"
      />
    </div>
  );
};

export default function ChatLayout() {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [imageBase64, setImageBase64] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const fileInputRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [pipelineStep, setPipelineStep] = useState(null);
  const [isDeepSearch, setIsDeepSearch] = useState(false);
  
  // Feedback States
  const [feedbackModalOpen, setFeedbackModalOpen] = useState(false);
  const [feedbackMessageId, setFeedbackMessageId] = useState(null);
  const [feedbackTags, setFeedbackTags] = useState([]);
  const [feedbackComment, setFeedbackComment] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);
  const [submittedReviews, setSubmittedReviews] = useState({});
  const [savedFoodLocations, setSavedFoodLocations] = useState(() => {
    try {
      const parsed = JSON.parse(localStorage.getItem('xanhsm_food_locations') || '[]');
      // Fix broken encodings from older versions
      let hasChanges = false;
      const cleaned = parsed.map(item => {
        if (item.label === 'Cng ty' || item.label === 'C\\u00f4ng ty') { item.label = 'Công ty'; hasChanges = true; }
        if (item.label === 'Nh' || item.label === 'Nh\\u00e0') { item.label = 'Nhà'; hasChanges = true; }
        return item;
      });
      if (hasChanges) localStorage.setItem('xanhsm_food_locations', JSON.stringify(cleaned));
      return cleaned;
    } catch {
      return [];
    }
  });
  const [explainingFood, setExplainingFood] = useState(null);

  const handleReviewClick = async (messageId, rating) => {
    if (!messageId) return;
    if (rating === 'up') {
      try {
        await api.submitReview({ message_id: messageId, rating: 'up' });
        setSubmittedReviews(prev => ({ ...prev, [messageId]: 'up' }));
      } catch(e) {
        console.error("Failed to submit review", e);
      }
    } else {
      setFeedbackMessageId(messageId);
      setFeedbackTags([]);
      setFeedbackComment('');
      setFeedbackModalOpen(true);
    }
  };

  const submitDownReview = async () => {
    if (!feedbackMessageId) return;
    try {
      setSubmittingReview(true);
      await api.submitReview({
        message_id: feedbackMessageId,
        rating: 'down',
        reason_tags: feedbackTags,
        comment: feedbackComment
      });
      setSubmittedReviews(prev => ({ ...prev, [feedbackMessageId]: 'down' }));
      setFeedbackModalOpen(false);
    } catch(e) {
      console.error(e);
      alert('Gửi đánh giá thất bại');
    } finally {
      setSubmittingReview(false);
    }
  };

  const [searchParams, setSearchParams] = useSearchParams();
  const activeConversationId = searchParams.get('c');
  const currentConvIdRef = useRef(activeConversationId);
  const lastProcessedActiveConvIdRef = useRef(undefined);
  const messagesEndRef = useRef(null);
  const foodImpressionLoggedRef = useRef(new Set());

  const {
    transcript,
    listening,
    resetTranscript,
    browserSupportsSpeechRecognition
  } = useSpeechRecognition();

  const [recordingTime, setRecordingTime] = useState(0);
  const timerRef = useRef(null);

  const [isEditingVoiceText, setIsEditingVoiceText] = useState(false);
  const [voiceLanguage] = useState('vi-VN');

  useEffect(() => {
    if (listening && !isEditingVoiceText) {
      setTimeout(() => setRecordingTime(0), 0);
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [listening, isEditingVoiceText]);

  const formatRecordingTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  useEffect(() => {
    if (transcript && !isEditingVoiceText) {
      setTimeout(() => setInput(transcript), 0);
    }
  }, [transcript, isEditingVoiceText]);

  const handleVoiceInput = () => {
    if (listening) {
      SpeechRecognition.stopListening();
    } else {
      resetTranscript();
      setIsEditingVoiceText(false);
      SpeechRecognition.startListening({ language: voiceLanguage, continuous: true });
    }
  };

  const toggleEditingVoiceText = () => {
    if (!isEditingVoiceText) {
      SpeechRecognition.stopListening();
      setIsEditingVoiceText(true);
    } else {
      setIsEditingVoiceText(false);
      SpeechRecognition.startListening({ language: voiceLanguage, continuous: true });
    }
  };

  const cancelVoiceInput = () => {
    SpeechRecognition.stopListening();
    setTimeout(() => {
      resetTranscript();
      setInput('');
    }, 100);
  };

  const stopAndSendVoice = () => {
    // Stop recording first
    SpeechRecognition.stopListening();
    
    // We use a slightly longer delay to ensure the final transcript is captured and synced to 'input' state
    setTimeout(() => {
      // Use the transcript directly from the hook to avoid any state delay issues
      const finalContent = transcript.trim();
      if (finalContent) {
        // Trigger handle submit with the voice content
        handleSubmit(null, finalContent);
      }
      resetTranscript();
    }, 300);
  };

  const scrollToBottom = useCallback(() => {
    if (messages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages.length]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    if (activeConversationId !== lastProcessedActiveConvIdRef.current) {
      lastProcessedActiveConvIdRef.current = activeConversationId;
      currentConvIdRef.current = activeConversationId;
      foodImpressionLoggedRef.current = new Set();
      if (activeConversationId) {
        // Load history
        api.getConversationMessages(activeConversationId).then(msgs => {
          const formatted = msgs.map(m => {
            let parsedTrace = null;
            if (m.pipeline_trace) {
              try {
                parsedTrace = JSON.parse(m.pipeline_trace);
              } catch {
                // Ignore JSON parse errors for legacy data
              }
            }
            return {
              role: m.role, 
              content: m.content,
              created_at: m.created_at,
              foodRecommendations: parsedTrace?.food_recommendations,
              ragCards: parsedTrace?.rag_cards
            };
          });
          setMessages(formatted);
        }).catch(console.error);
      } else {
        // New conversation
        setTimeout(() => {
          setMessages([]);
        }, 0);
      }
    }
  }, [activeConversationId]);

  const handleSubmit = async (e, directQuery = null, displayQuery = null) => {
    e?.preventDefault();
    const query = (typeof directQuery === 'string' ? directQuery : input).trim();
    if (!query || loading) return;

    const userQuery = query;
    const visibleUserQuery = (displayQuery || userQuery).trim();
    const currentImageBase64 = imageBase64;
    setInput('');
    setImageBase64(null);
    setImagePreview(null);
    const now = new Date().toISOString();
    setMessages(prev => [...prev, { role: 'user', content: visibleUserQuery, image: imagePreview, created_at: now }]);
    setLoading(true);

    try {
      const response = await api.chatStream(userQuery, currentConvIdRef.current, currentImageBase64, isDeepSearch, displayQuery !== userQuery ? displayQuery : null);
      if (!response.ok) throw new Error('API Error');
      
      setMessages(prev => [...prev, { role: 'assistant', content: '', latency_ms: null, metrics: null, created_at: new Date().toISOString() }]);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      /* eslint-disable react-hooks/immutability */
      let streamReply = '';
      let streamBuffer = '';
      let streamSources = null;
      let streamMetrics = null;
      let streamFoodRecommendations = null;
      let streamFoodLocationRequest = null;
      let streamRagCards = [];

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        streamBuffer += decoder.decode(value, { stream: true });
        
        // SSE messages are separated by double newlines
        let boundary = streamBuffer.indexOf('\n\n');
        while (boundary !== -1) {
          const chunk = streamBuffer.slice(0, boundary);
          streamBuffer = streamBuffer.slice(boundary + 2);
          
          const lines = chunk.split('\n');
          let textDataParts = [];
          let isStep = false;
          let isMetrics = false;

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6); // remove 'data: '
              if (data === '[DONE]') continue;
              
              if (data.trim().startsWith('{')) {
                try {
                  const parsed = JSON.parse(data);
                  
                  let handledAsMetadata = false;

                  if (parsed.error) {
                    textDataParts.push(parsed.error);
                    handledAsMetadata = true;
                  } 
                  if (parsed.conversation_id) {
                    currentConvIdRef.current = parsed.conversation_id;
                    lastProcessedActiveConvIdRef.current = parsed.conversation_id;
                    setSearchParams({ c: parsed.conversation_id }, { replace: true });
                    isStep = true; 
                    handledAsMetadata = true;
                  } 
                  if (parsed.step) {
                    setPipelineStep(parsed.message || parsed.step);
                    isStep = true;
                    handledAsMetadata = true;
                  } 
                  if (parsed.metrics) {
                    streamMetrics = parsed.metrics;
                    isMetrics = true;
                    handledAsMetadata = true;
                  } 
                  if (parsed.sources) {
                    streamSources = parsed.sources;
                    handledAsMetadata = true;
                  } 
                  if (parsed.rag_card) {
                    streamRagCards = [...streamRagCards, parsed.rag_card];
                    handledAsMetadata = true;
                  }
                  if (parsed.food_recommendations) {
                    const incomingItems = parsed.food_recommendations?.items || [];
                    const currentItems = streamFoodRecommendations?.items || [];
                    if (incomingItems.length || !currentItems.length) {
                      streamFoodRecommendations = parsed.food_recommendations;
                    } else {
                      streamFoodRecommendations = {
                        ...parsed.food_recommendations,
                        ...streamFoodRecommendations,
                        trace_id: parsed.food_recommendations.trace_id || streamFoodRecommendations.trace_id,
                        items: currentItems,
                        more_items: streamFoodRecommendations.more_items || parsed.food_recommendations.more_items || []
                      };
                    }
                    handledAsMetadata = true;
                  }
                  if (parsed.food_card) {
                    const currentItems = streamFoodRecommendations?.items || [];
                    streamFoodRecommendations = {
                      title: streamFoodRecommendations?.title || 'Một vài quán phù hợp gần anh/chị',
                      subtitle: streamFoodRecommendations?.subtitle || 'AI đang gợi ý từng lựa chọn phù hợp cho anh/chị.',
                      query: streamFoodRecommendations?.query || userQuery,
                      trace_id: streamFoodRecommendations?.trace_id,
                      items: [...currentItems, parsed.food_card],
                      more_items: streamFoodRecommendations?.more_items || []
                    };
                    handledAsMetadata = true;
                  }
                  if (parsed.food_location_request) {
                    streamFoodLocationRequest = parsed.food_location_request;
                    handledAsMetadata = true;
                  }
                  if (parsed.message_id) {
                    setMessages(prev => {
                      const newMsgs = [...prev];
                      newMsgs[newMsgs.length - 1].id = parsed.message_id;
                      return newMsgs;
                    });
                    handledAsMetadata = true;
                  }
                  if (!handledAsMetadata) {
                    textDataParts.push(data);
                  }
                } catch(e) {
                  console.error("JSON parse error:", e);
                  textDataParts.push(data);
                }
              } else {
                textDataParts.push(data);
              }
            }
          }
          
          const textData = textDataParts.join('\n');
          
          if (!isStep && !isMetrics && textData.length > 0) {
             streamReply += textData;
             setPipelineStep(null);
          }
          
          setMessages(prev => {
            const newMsgs = [...prev];
            newMsgs[newMsgs.length - 1].content = streamReply;
            if (streamSources) {
              newMsgs[newMsgs.length - 1].sources = streamSources;
            }
            if (streamRagCards.length) {
              newMsgs[newMsgs.length - 1].ragCards = streamRagCards;
            }
            // Store metrics if received
            if (streamMetrics) {
              newMsgs[newMsgs.length - 1].metrics = streamMetrics;
              newMsgs[newMsgs.length - 1].latency_ms = streamMetrics.total_latency_ms;
            }
            if (streamFoodRecommendations) {
              newMsgs[newMsgs.length - 1].foodRecommendations = streamFoodRecommendations;
            }
            if (streamFoodLocationRequest) {
              newMsgs[newMsgs.length - 1].foodLocationRequest = streamFoodLocationRequest;
            }
            return newMsgs;
          });

          
          boundary = streamBuffer.indexOf('\n\n');
        }
      }
      
      // Mark loading complete when stream finishes
      /* eslint-enable react-hooks/immutability */
      setLoading(false);
      setPipelineStep(null);
      window.dispatchEvent(new Event('refresh-conversations'));
    } catch (error) {
      console.error('Chat stream error:', error);
      setMessages(prev => {
        const newMsgs = [...prev];
        const lastMsg = newMsgs.length > 0 ? newMsgs[newMsgs.length - 1] : null;
        if (lastMsg && lastMsg.role === 'assistant' && lastMsg.content === '') {
          lastMsg.content = 'Xin lỗi, hệ thống AI đang bận hoặc mất kết nối tới cơ sở dữ liệu. Vui lòng thử lại sau ít phút.';
        } else if (!lastMsg || lastMsg.role === 'user') {
          newMsgs.push({ role: 'assistant', content: 'Xin lỗi, hệ thống AI đang bận hoặc mất kết nối tới cơ sở dữ liệu. Vui lòng thử lại sau ít phút.', latency_ms: null, created_at: new Date().toISOString() });
        }
        return newMsgs;
      });
      setLoading(false);
      setPipelineStep(null);
      window.dispatchEvent(new Event('refresh-conversations'));
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const formatTime = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        alert("Kích thước ảnh tối đa là 5MB.");
        return;
      }
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
        const base64String = reader.result.replace(/^data:image\/[a-z]+;base64,/, "");
        setImageBase64(base64String);
      };
      reader.readAsDataURL(file);
    }
  };

  const handlePaste = (e) => {
    if (e.clipboardData.files && e.clipboardData.files.length > 0) {
      const file = e.clipboardData.files[0];
      if (file.type.startsWith('image/')) {
        e.preventDefault();
        handleImageUpload({ target: { files: [file] } });
      }
    }
  };

  const clearImage = () => {
    setImageBase64(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const logFoodInteraction = useCallback(async (eventType, item, rankPosition, data, message) => {
    try {
      await api.logFoodInteraction({
        event_type: eventType,
        conversation_id: currentConvIdRef.current || null,
        message_id: message?.id || null,
        item_id: item?.item_id || null,
        merchant_id: item?.merchant_id || null,
        rank_position: typeof rankPosition === 'number' ? rankPosition + 1 : null,
        query: data?.query || null,
        request_context: {
          title: data?.title,
          item_name: item?.name,
          dish_name: item?.dish_name,
          order_url: item?.order_url,
          distance_text: item?.distance_text,
          eta_text: item?.eta_text,
          delivery_fee_text: item?.delivery_fee_text,
          breakdown: item?.score_breakdown,
        }
      });
    } catch (error) {
      console.warn('Failed to log food interaction', error);
    }
  }, []);

  useEffect(() => {
    messages.forEach((msg, index) => {
      if (msg.role !== 'assistant' || !msg.foodRecommendations) return;
      const key = `${currentConvIdRef.current || 'new'}:${index}`;
      if (foodImpressionLoggedRef.current.has(key)) return;
      foodImpressionLoggedRef.current.add(key);
      const firstItem = msg.foodRecommendations.items?.[0] || null;
      logFoodInteraction('impression', firstItem, 0, msg.foodRecommendations, msg);
    });
  }, [messages, logFoodInteraction]);

  const buildFoodLocationQuery = (request, locationText) => {
    const baseQuery = request?.query || 'Gợi ý món ăn gần tôi';
    return `${baseQuery} ở ${locationText}`;
  };

  const isVietnamCoordinate = (lat, lng) => {
    const latNum = Number(lat);
    const lngNum = Number(lng);
    return latNum >= 8 && latNum <= 24 && lngNum >= 102 && lngNum <= 110;
  };

  const saveFoodLocation = useCallback((location) => {
    const nextLocation = {
      id: location.id || `loc_${Date.now()}`,
      label: location.label || 'Vị trí hiện tại',
      address: location.address || location.label || 'Vị trí hiện tại',
      lat: Number(location.lat),
      lng: Number(location.lng),
      saved_at: new Date().toISOString(),
    };
    setSavedFoodLocations(prev => {
      const next = [nextLocation, ...prev.filter(item => item.id !== nextLocation.id && item.label !== nextLocation.label)].slice(0, 5);
      localStorage.setItem('xanhsm_food_locations', JSON.stringify(next));
      return next;
    });
    return nextLocation;
  }, []);

  const markFoodLocationConfirmed = useCallback((location) => {
    setMessages(prev => {
      const next = [...prev];
      for (let i = next.length - 1; i >= 0; i -= 1) {
        if (next[i].role === 'assistant' && next[i].foodLocationRequest) {
          next[i] = { ...next[i], foodLocationConfirmed: location };
          break;
        }
      }
      return next;
    });
  }, []);

  const handleUseCurrentFoodLocation = (request) => {
    if (!navigator.geolocation) {
      alert('Trình duyệt chưa hỗ trợ lấy vị trí hiện tại.');
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude.toFixed(6);
        const lng = position.coords.longitude.toFixed(6);
        if (!isVietnamCoordinate(lat, lng)) {
          alert('Vị trí hiện tại chưa nằm trong khu vực Việt Nam mà catalog món ăn đang hỗ trợ. Bạn thử nhập địa chỉ ở Việt Nam hoặc chọn pin trên bản đồ nhé.');
          return;
        }
        const location = saveFoodLocation({ id: 'current', label: 'Vị trí hiện tại', lat, lng });
        markFoodLocationConfirmed(location);
        handleSubmit(null, buildFoodLocationQuery(request, `${lat},${lng}`), 'Đã chia sẻ vị trí hiện tại');
      },
      () => {
        alert('Chưa lấy được vị trí hiện tại. Bạn có thể nhập địa chỉ giao hàng hoặc thử cấp quyền vị trí lại.');
      },
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 }
    );
  };

  const handleSubmitFoodAddress = async (request, address) => {
    try {
      const result = await api.geocodeFoodAddress(address);
      const lat = Number(result.lat).toFixed(6);
      const lng = Number(result.lng).toFixed(6);
      const label = address || result.display_name || 'Địa chỉ giao hàng';
      const location = saveFoodLocation({ label, address: result.display_name || address, lat, lng });
      markFoodLocationConfirmed(location);
      handleSubmit(null, buildFoodLocationQuery(request, `${lat},${lng}`), label);
    } catch (error) {
      console.warn('Geocode failed', error);
      alert('Em chưa tìm được tọa độ cho địa chỉ này. Bạn thử nhập rõ hơn hoặc dùng vị trí hiện tại nhé.');
    }
  };

  const handleSelectMapFoodLocation = (request, pin) => {
    const lat = Number(pin.lat).toFixed(6);
    const lng = Number(pin.lng).toFixed(6);
    if (!isVietnamCoordinate(lat, lng)) {
      alert('Vị trí đã chọn chưa nằm trong khu vực Việt Nam.');
      return;
    }
    const location = saveFoodLocation({ label: pin.label || 'Vị trí đã chọn trên bản đồ', lat, lng });
    markFoodLocationConfirmed(location);
    handleSubmit(null, buildFoodLocationQuery(request, `${lat},${lng}`), location.label);
  };

  const handleSaveNamedFoodLocation = (id, label, location) => {
    saveFoodLocation({
      ...location,
      id,
      label,
      address: location.address || location.label,
    });
  };

  const renderContent = (content) => {
    const extractedMedia = extractMarkdownImageCards(content);
    const contentForMarkdown = extractedMedia.cleanContent || content;
    // Robust regex to handle optional colons, variable whitespace, and optional link
    const cardRegex = /:::card\s+\[icon:?\s*(.*?)\]\s+\[title:?\s*(.*?)\]\s+\[desc:?\s*(.*?)\](?:\s+\[image:?\s*(.*?)\])?(?:\s+\[link:?\s*(.*?)\])?\s+:::/g;
    const parts = [];
    let lastIndex = 0;
    let match;
    let cardIndex = 1;

    while ((match = cardRegex.exec(contentForMarkdown)) !== null) {
      // Add text before card
      if (match.index > lastIndex) {
        parts.push(contentForMarkdown.substring(lastIndex, match.index));
      }
      // Add card component
      parts.push(
        <MessageCard 
          key={`card-${cardIndex}`}
          icon={match[1]?.trim()}
          title={match[2]?.trim()}
          desc={match[3]?.trim()}
          image={match[4]?.trim()}
          link={match[5]?.trim()}
          index={cardIndex++}
        />
      );
      lastIndex = cardRegex.lastIndex;
    }
    // Add remaining text
    if (lastIndex < contentForMarkdown.length) {
      parts.push(contentForMarkdown.substring(lastIndex));
    }

    if (parts.length === 0) return (
      <div className="flex flex-col gap-4">
        {contentForMarkdown && (
          <ReactMarkdown 
            remarkPlugins={[remarkGfm]}
            components={markdownComponents}
          >
            {contentForMarkdown}
          </ReactMarkdown>
        )}
        {extractedMedia.cards.length > 0 && <RagCardList cards={extractedMedia.cards} />}
      </div>
    );

    return (
      <div className="flex flex-col gap-4">
        {parts.map((part, i) => (
          typeof part === 'string' ? (
            <ReactMarkdown 
              key={i}
              remarkPlugins={[remarkGfm]}
              components={markdownComponents}
            >
              {part}
            </ReactMarkdown>
          ) : part
        ))}
        {extractedMedia.cards.length > 0 && <RagCardList cards={extractedMedia.cards} />}
      </div>
    );
  };

  const markdownComponents = {
    ol: (props) => <ol className="list-decimal pl-5 my-2 ml-4" {...stripNode(props)} />,
    ul: (props) => <ul className="list-disc pl-5 my-2 ml-4" {...stripNode(props)} />,
    li: (props) => <li className="my-1" {...stripNode(props)} />,
    table: (props) => (
      <div className="overflow-x-auto my-4 w-full border border-primary/20 rounded-xl shadow-sm">
        <table className="w-full text-sm text-left m-0" {...stripNode(props)} />
      </div>
    ),
    thead: (props) => <thead className="text-xs uppercase bg-primary/10 text-primary" {...stripNode(props)} />,
    th: (props) => <th className="px-6 py-4 font-bold border-b border-primary/10 m-0" {...stripNode(props)} />,
    td: (props) => <td className="px-6 py-4 border-b border-surface-variant/50 m-0" {...stripNode(props)} />,
    tr: (props) => <tr className="hover:bg-surface-container-high/30 transition-colors m-0" {...stripNode(props)} />,
    a: (props) => (
      <a 
        className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-semibold italic underline transition-all"
        target="_blank"
        rel="noopener noreferrer"
        {...stripNode(props)}
      />
    ),
    img: (props) => (
      <div className="my-3 flex flex-col items-center rounded-2xl border border-outline-variant/20 bg-white/70 dark:bg-white/[0.04] p-2">
        <img 
          className="max-h-64 w-full object-contain rounded-xl cursor-zoom-in bg-surface-container-high/50"
          alt={props.alt || "Hình ảnh từ Xanh SM"}
          onClick={() => window.open(props.src, '_blank')}
          {...stripNode(props)}
        />
        {props.alt && (
          <span className="text-xs text-on-surface-variant/60 italic mt-2 text-center">
            {props.alt}
          </span>
        )}
      </div>
    )
  };

  const lastMsg = messages[messages.length - 1];
  const showSpinner = loading && (!lastMsg || lastMsg.role !== 'assistant' || !lastMsg.content);

  return (
    <div className="relative flex-1 min-h-0 flex flex-col w-full bg-transparent overflow-hidden">
      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-8px); }
        }
        .animate-float {
          animation: float 4s ease-in-out infinite;
        }
        .no-scrollbar::-webkit-scrollbar {
          display: none;
        }
        .no-scrollbar {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}</style>
      
      {/* Scrollable content container */}
      <div className="flex-1 overflow-y-auto w-full px-4 md:px-8 pt-6 pb-44 md:pb-52 no-scrollbar flex flex-col items-center">
        
        {/* Empty State Hero */}
        {messages.length === 0 && (
          <div className="w-full max-w-5xl flex flex-col items-center relative mt-2 mb-0 select-none">
            
            {/* Welcome Intro Section */}
            <div className="w-full flex flex-row items-center justify-between gap-4 sm:gap-6 md:gap-12 text-left">
              <div className="flex-1">
                <div className="flex items-center gap-1.5 text-xs text-primary dark:text-[#00c897] font-bold tracking-wider uppercase mb-2">
                  <span className="w-2 h-2 rounded-full bg-primary dark:bg-[#00c897] animate-pulse" />
                  Xanh SM AI Assistant
                </div>
                <h1 className="text-2xl md:text-4xl font-extrabold text-on-surface leading-tight">
                  Xin chào {user?.name ? (user.name.includes(' - ') ? user.name.split(' - ')[0].split(' ').pop() : user.name.split(' ').pop()) : 'bạn'} 👋 <br />
                  <span className="text-[#00c897]">Tôi có thể giúp gì cho bạn?</span>
                </h1>
                <p className="text-xs md:text-sm text-on-surface-variant/80 mt-2 max-w-lg leading-relaxed font-medium">
                  Tôi có thể giúp bạn tìm hiểu dịch vụ, giá cước, xe điện, ưu đãi và chính sách của Xanh SM.
                </p>
              </div>
              
              {/* Robot 3D Mascot Image */}
              <div className="w-28 h-28 sm:w-36 sm:h-36 md:w-[200px] md:h-[200px] lg:w-[220px] lg:h-[220px] xl:w-[240px] xl:h-[240px] flex items-center justify-center shrink-0 animate-float select-none">
                <img 
                  src="/Bot.png" 
                  alt="Xanh SM AI Mascot" 
                  className="w-full h-full object-contain filter drop-shadow-xl hover:scale-105 transition-transform duration-300 pointer-events-none"
                />
              </div>
            </div>
          </div>
        )}

        {/* Messages List */}
        {messages.length > 0 && (
          <div className="w-full max-w-5xl flex flex-col gap-8">
            {messages.map((msg, idx) => {
              const hasAssistantPayload = Boolean(
                msg.content ||
                msg.foodLocationRequest ||
                msg.foodLocationConfirmed ||
                msg.foodRecommendations ||
                msg.ragCards ||
                (msg.sources && msg.sources.length > 0)
              );
              if (msg.role === 'assistant' && (!hasAssistantPayload || (!msg.content && loading))) return null;
              return (
                <div key={idx} className={`flex flex-col w-full ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  {/* Header info */}
                  <div className={`flex items-center gap-2 mb-2 px-1 text-[11px] font-bold text-on-surface-variant/50 select-none ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                    {msg.role === 'user' ? (
                      <>
                        <span>Bạn</span>
                        <span>⬢</span>
                        <span>{formatTime(msg.created_at)}</span>
                      </>
                    ) : (
                      <>
                        <span className="text-[#00c897]">Xanh SM</span>
                        <div className="px-1.5 py-0.5 rounded-md border border-[#00c897]/30 text-[#00c897] scale-75 origin-left flex items-center justify-center font-black">AI</div>
                        <span>⬢</span>
                        <span>{formatTime(msg.created_at)}</span>
                      </>
                    )}
                  </div>

                  <div className={`flex gap-3 w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'} items-start`}>
                    {msg.role !== 'user' && (
                      <div className="w-10 h-10 rounded-full bg-white dark:bg-white/10 flex items-center justify-center text-white shrink-0 shadow-md border border-[#00c897]/20 relative overflow-hidden group">
                        <img src="/Bot.png" alt="Xanh SM AI" className="w-7 h-7 object-contain group-hover:scale-110 transition-transform" />
                      </div>
                    )}
                    
                    <div className={`max-w-[85%] ${msg.role === 'user' ? 'order-1' : 'order-2'}`}>
                      <div className={`p-4 md:p-5 rounded-3xl text-sm md:text-base leading-relaxed transition-all duration-300 flex flex-col gap-4 ${
                        msg.role === 'user' 
                          ? 'bg-gradient-to-br from-[#00c897] to-[#009e79] text-white rounded-tr-none shadow-[0_4px_16px_rgba(0,200,151,0.15)] dark:shadow-[0_4px_16px_rgba(0,200,151,0.05)] border border-[#00c897]/20' 
                          : 'bg-white/88 dark:bg-white/5 backdrop-blur-md border border-white/40 dark:border-white/10 text-on-surface rounded-tl-none shadow-[0_8px_30px_rgba(0,0,0,0.04)] dark:shadow-[0_8px_30px_rgba(0,0,0,0.2)]'
                      }`}>
                        {msg.role === 'user' ? (
                          <div className="flex flex-col gap-2">
                            {msg.image && (
                              <img src={msg.image} alt="User upload" className="max-w-[200px] max-h-[200px] rounded-xl object-contain bg-black/20" />
                            )}
                            <p className="whitespace-pre-wrap font-medium">{msg.content}</p>
                          </div>
                        ) : (
                          <div className="flex flex-col gap-4">
                            {msg.content && (
                              <div className="prose prose-sm md:prose-base dark:prose-invert max-w-none">
                                {renderContent(msg.content)}
                              </div>
                            )}
                            {msg.foodLocationRequest && (
                              <FoodLocationRequestCard
                                request={msg.foodLocationRequest}
                                onUseCurrentLocation={() => handleUseCurrentFoodLocation(msg.foodLocationRequest)}
                                onSubmitAddress={(address) => handleSubmitFoodAddress(msg.foodLocationRequest, address)}
                                onSelectMapLocation={(pin) => handleSelectMapFoodLocation(msg.foodLocationRequest, pin)}
                                savedLocations={savedFoodLocations}
                              />
                            )}
                            {msg.foodLocationConfirmed && (
                              <FoodLocationConfirmedCard
                                location={msg.foodLocationConfirmed}
                                onSaveNamedLocation={handleSaveNamedFoodLocation}
                              />
                            )}
                            {msg.foodRecommendations && (
                                <FoodRecommendationList
                                  data={msg.foodRecommendations}
                                  onOpenMenu={(item, rankPosition) => {
                                    logFoodInteraction('click_item', item, rankPosition, msg.foodRecommendations, msg);
                                    logFoodInteraction('click_out', item, rankPosition, msg.foodRecommendations, msg);
                                  }}
                                  onLike={(item, rankPosition) => {
                                    setMessages(prev => prev.map(m => m.id === msg.id ? {
                                      ...m,
                                      foodRecommendations: {
                                        ...m.foodRecommendations,
                                        items: m.foodRecommendations.items.map(i => i.item_id === item.item_id ? { ...i, interaction: i.interaction === 'like' ? null : 'like' } : i)
                                      }
                                    } : m));
                                    logFoodInteraction('like', item, rankPosition, msg.foodRecommendations, msg);
                                  }}
                                  onDismiss={(item, rankPosition) => {
                                    setMessages(prev => prev.map(m => m.id === msg.id ? {
                                      ...m,
                                      foodRecommendations: {
                                        ...m.foodRecommendations,
                                        items: m.foodRecommendations.items.filter(i => i.item_id !== item.item_id)
                                      }
                                    } : m));
                                    logFoodInteraction('dismiss', item, rankPosition, msg.foodRecommendations, msg);
                                  }}
                                  onDislike={(item, rankPosition) => {
                                    setMessages(prev => prev.map(m => m.id === msg.id ? {
                                      ...m,
                                      foodRecommendations: {
                                        ...m.foodRecommendations,
                                        items: m.foodRecommendations.items.map(i => i.item_id === item.item_id ? { ...i, interaction: i.interaction === 'dislike' ? null : 'dislike' } : i)
                                      }
                                    } : m));
                                    logFoodInteraction('dislike', item, rankPosition, msg.foodRecommendations, msg);
                                  }}
                                  onExplain={(item) => setExplainingFood(item)}
                                />
                            )}
                            {msg.ragCards && (
                              <RagCardList cards={msg.ragCards} />
                            )}
                          </div>
                        )}
                        {/* Citations / Sources */}
                        {msg.sources && msg.sources.length > 0 && (() => {
                          const uniqueSources = [];
                          const seenSources = new Set();
                          for (const src of msg.sources) {
                            const normalizedSource = (src.source || '').toLowerCase().trim();
                            if (normalizedSource && !seenSources.has(normalizedSource)) {
                              seenSources.add(normalizedSource);
                              uniqueSources.push(src);
                            }
                          }
                          return (
                            <div className="flex gap-2 flex-wrap mt-1">
                              {uniqueSources.slice(0, 3).map((src, i) => (
                                <a key={i} href={src.url || '#'} target="_blank" rel="noopener noreferrer" 
                                   className="flex items-center gap-1 text-[10px] font-bold bg-surface-container-high/50 text-primary px-3 py-1.5 rounded-full border border-primary/20 hover:bg-primary hover:text-white transition-all max-w-[240px]">
                                  <Link2 size={10} className="shrink-0" />
                                  <span className="truncate">
                                    {src.source ? src.source.replace(/\.(md|html|txt)$/i, '').replace(/[-_]/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Tài li!u Xanh SM'}
                                  </span>
                                </a>
                              ))}
                            </div>
                          );
                        })()}

                        {/* Assistant Footer */}
                        {msg.role === 'assistant' && (
                          <div className="mt-2 pt-3 border-t border-outline-variant/10 flex items-center justify-between text-[10px] font-bold text-on-surface-variant/40">
                            <div className="flex items-center gap-1.5">
                              <span className="scale-110">⏱️</span>
                              <span>Tổng thời gian: {msg.latency_ms ? `${Math.round(msg.latency_ms)}ms` : 'N/A'}</span>
                            </div>
                            <div className="flex items-center gap-3">
                              {msg.id && (
                                <div className="flex items-center gap-2">
                                  <button 
                                    onClick={() => handleReviewClick(msg.id, 'up')}
                                    className={`hover:text-[#00c897] transition-colors p-1 rounded-md ${submittedReviews[msg.id] === 'up' ? 'text-[#00c897] bg-[#00c897]/10' : ''}`}
                                    title="Hữu ích"
                                    disabled={!!submittedReviews[msg.id]}
                                  >
                                    <ThumbsUp size={14} />
                                  </button>
                                  <button 
                                    onClick={() => handleReviewClick(msg.id, 'down')}
                                    className={`hover:text-red-500 transition-colors p-1 rounded-md ${submittedReviews[msg.id] === 'down' ? 'text-red-500 bg-red-50' : ''}`}
                                    title="Không hữu ích"
                                    disabled={!!submittedReviews[msg.id]}
                                  >
                                    <ThumbsDown size={14} />
                                  </button>
                                </div>
                              )}
                              <div className="flex items-center gap-1.5">
                                <span>Nguồn: Xanh SM Official</span>
                                <ShieldCheck size={12} className="text-[#00c897]" />
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                      
                      {msg.role === 'user' && (
                        <div className="flex justify-end mt-1.5 px-1">
                          <CheckCheck size={14} className="text-[#00c897]" />
                        </div>
                      )}
                    </div>

                    {msg.role === 'user' && (
                      user?.type === 'user' ? (
                        <div 
                          className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white text-sm font-black shadow-md uppercase border border-primary/20 shrink-0 order-2 overflow-hidden"
                          title={user.email}
                        >
                          {user.name ? user.name[0] : <User size={18} />}
                        </div>
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-surface-container-high flex items-center justify-center text-primary shrink-0 shadow-sm order-2 border border-primary/10">
                          <User size={20} />
                        </div>
                      )
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {showSpinner && (
          <div className="w-full max-w-5xl flex gap-3 mt-2 justify-start">
            <div className="w-10 h-10 rounded-full bg-white dark:bg-white/10 flex items-center justify-center text-white shrink-0 shadow-md border border-[#00c897]/20 relative overflow-hidden">
               <img src="/Bot.png" alt="Xanh SM AI" className="w-7 h-7 object-contain animate-bounce" />
            </div>
            <div className="p-4 rounded-3xl bg-white/88 dark:bg-white/5 backdrop-blur-md border border-white/40 dark:border-white/10 text-on-surface rounded-tl-none shadow-sm flex items-center gap-3 max-w-[85%]">
              <Loader2 className="animate-spin text-[#00c897]" size={20} />
              <div className="flex flex-col gap-2">
                <span className="text-on-surface-variant/60 italic text-sm font-medium">
                  {pipelineStep ? pipelineStep : 'Đang phân tích dữ liệu...'}
                </span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Floating Chat Input centered responsively using absolute */}
      <div className="absolute bottom-6 left-0 right-0 px-4 md:px-8 flex flex-col items-center gap-4 z-40 pointer-events-none">
        
        {/* Suggestion Cards Grid (displayed only on empty state, right above input box) */}
        {messages.length === 0 && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 w-full max-w-5xl relative z-10 pointer-events-auto mb-1">
            {/* Card 1 */}
            <button
              onClick={(e) => handleSubmit(e, "Giá cước Xanh Car và Xanh Bike ở các khu vực")}
              className="glass-panel p-3 rounded-2xl text-left border border-white/10 dark:border-white/5 hover:border-[#00c897]/40 dark:hover:border-[#00c897]/40 hover:bg-[#00c897]/5 dark:hover:bg-[#00c897]/5 transition-all hover:-translate-y-0.5 group flex flex-col justify-between min-h-[100px] md:min-h-[120px] h-full shadow-sm"
            >
              <div className="w-8 h-8 rounded-lg bg-[#00c897]/10 flex items-center justify-center text-[#00c897] group-hover:bg-[#00c897] group-hover:text-white transition-colors shrink-0">
                <Car size={16} />
              </div>
              <div className="mt-1.5 md:mt-2 flex-grow">
                <h3 className="text-xs md:text-sm font-extrabold text-on-surface mb-0.5 truncate">Giá cước dịch vụ</h3>
                <p className="text-[10px] md:text-xs text-on-surface-variant/80 line-clamp-2 leading-relaxed font-medium">Xem bảng giá chi tiết cho từng loại dịch vụ</p>
              </div>
              <span className="text-[10px] md:text-xs font-extrabold text-[#00c897] mt-0.5 block select-none">Khám phá &rarr;</span>
            </button>

            {/* Card 2 */}
            <button
              onClick={(e) => handleSubmit(e, "Chính sách thuê xe VinFast chạy dịch vụ trên Green SM Platform")}
              className="glass-panel p-3 rounded-2xl text-left border border-white/10 dark:border-white/5 hover:border-blue-500/40 dark:hover:border-blue-500/40 hover:bg-blue-500/5 dark:hover:bg-blue-500/5 transition-all hover:-translate-y-0.5 group flex flex-col justify-between min-h-[100px] md:min-h-[120px] h-full shadow-sm"
            >
              <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-500 group-hover:bg-blue-500 group-hover:text-white transition-colors shrink-0">
                <Key size={16} />
              </div>
              <div className="mt-1.5 md:mt-2 flex-grow">
                <h3 className="text-xs md:text-sm font-extrabold text-on-surface mb-0.5 truncate">Thuê xe chạy dịch vụ</h3>
                <p className="text-[10px] md:text-xs text-on-surface-variant/80 line-clamp-2 leading-relaxed font-medium">Thông tin chi tiết về chính sách thuê xe điện VinFast</p>
              </div>
              <span className="text-[10px] md:text-xs font-extrabold text-blue-500 mt-0.5 block select-none">Tìm hiểu &rarr;</span>
            </button>

            {/* Card 3 */}
            <button
              onClick={(e) => handleSubmit(e, "Chính sách ưu đãi và khuyến mãi sạc pin trạm V-GREEN")}
              className="glass-panel p-3 rounded-2xl text-left border border-white/10 dark:border-white/5 hover:border-amber-500/40 dark:hover:border-amber-500/40 hover:bg-amber-500/5 dark:hover:bg-amber-500/5 transition-all hover:-translate-y-0.5 group flex flex-col justify-between min-h-[100px] md:min-h-[120px] h-full shadow-sm"
            >
              <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-500 group-hover:bg-amber-500 group-hover:text-white transition-colors shrink-0">
                <Tag size={16} />
              </div>
              <div className="mt-1.5 md:mt-2 flex-grow">
                <h3 className="text-xs md:text-sm font-extrabold text-on-surface mb-0.5 truncate">Ưu đãi & khuyến mãi</h3>
                <p className="text-[10px] md:text-xs text-on-surface-variant/80 line-clamp-2 leading-relaxed font-medium">Các chương trình ưu đãi mới nhất hiện nay</p>
              </div>
              <span className="text-[10px] md:text-xs font-extrabold text-amber-500 mt-0.5 block select-none">Xem ngay &rarr;</span>
            </button>

            {/* Card 4 */}
            <button
              onClick={(e) => handleSubmit(e, "Cập nhật các tin tức và sự ki!n m:i nhất từ Xanh SM")}
              className="glass-panel p-3 rounded-2xl text-left border border-white/10 dark:border-white/5 hover:border-purple-500/40 dark:hover:border-purple-500/40 hover:bg-purple-500/5 dark:hover:bg-purple-500/5 transition-all hover:-translate-y-0.5 group flex flex-col justify-between min-h-[100px] md:min-h-[120px] h-full shadow-sm"
            >
              <div className="w-8 h-8 rounded-lg bg-purple-500/10 flex items-center justify-center text-purple-500 group-hover:bg-purple-500 group-hover:text-white transition-colors shrink-0">
                <Newspaper size={16} />
              </div>
              <div className="mt-1.5 md:mt-2 flex-grow">
                <h3 className="text-xs md:text-sm font-extrabold text-on-surface mb-0.5 truncate">Tin tức Xanh SM</h3>
                <p className="text-[10px] md:text-xs text-on-surface-variant/80 line-clamp-2 leading-relaxed font-medium">Cập nhật tin tức, sự ki!n và thông báo m:i nhất</p>
              </div>
              <span className="text-[10px] md:text-xs font-extrabold text-purple-500 mt-0.5 block select-none">Đọc ngay &rarr;</span>
            </button>
          </div>
        )}

        {(listening || isEditingVoiceText) ? (
          /* Advanced Voice UI Overlay - Compact & Elegant */
          <div className="w-full max-w-4xl mx-auto glass-panel p-4 md:p-6 rounded-[28px] md:rounded-[32px] shadow-[0_20px_60px_rgba(0,0,0,0.06)] flex flex-col gap-3 md:gap-4 border-white/60 bg-white/95 dark:bg-[#0c1618]/95 backdrop-blur-3xl animate-in fade-in slide-in-from-bottom-4 duration-500 pointer-events-auto">
            
            <div className="flex flex-col md:flex-row items-center md:items-start gap-3 md:gap-6 text-center md:text-left">
              {/* Status & Timer Section - More Compact */}
              <div className="flex flex-row md:flex-col items-center gap-3 md:gap-2 shrink-0">
                <div className="w-12 h-12 md:w-16 md:h-16 rounded-full bg-[#00c897]/5 flex items-center justify-center text-[#00c897] relative border border-[#00c897]/10">
                  {listening && !isEditingVoiceText && (
                    <div className="absolute inset-0 rounded-full bg-[#00c897]/10 animate-ping"></div>
                  )}
                  <Mic className="w-6 h-6 md:w-8 md:h-8" strokeWidth={2.5} />
                </div>
                <div className="flex flex-col items-start md:items-center">
                  <span className="text-[9px] md:text-xs font-bold text-on-surface-variant/60 uppercase tracking-widest">Đang nghe...</span>
                  <span className="text-base md:text-lg font-black text-on-surface font-mono">{formatRecordingTime(recordingTime)}</span>
                </div>
              </div>

              {/* Transcription Display Section */}
              <div className="flex-1 flex flex-col gap-2 md:gap-3 w-full">
                <div className="flex items-center justify-center md:justify-start gap-2 text-[#00c897] text-[10px] md:text-xs font-bold">
                  <Sparkles size={14} fill="currentColor" className="animate-pulse" />
                  <span>Đang chuyỒn giọng nói thành vĒn bản...</span>
                </div>
                
                <div className="min-h-[50px] md:min-h-[60px] w-full">
                  {isEditingVoiceText ? (
                    <textarea
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      className="w-full bg-transparent border-none focus:ring-0 text-lg md:text-2xl font-bold text-on-surface p-0 resize-none outline-none placeholder:opacity-20 text-center md:text-left"
                      autoFocus
                      rows={2}
                    />
                  ) : (
                    <p className="text-lg md:text-2xl font-bold text-on-surface leading-snug break-words text-center md:text-left">
                      {input || <span className="opacity-20 italic font-medium text-lg">Hãy nói điều gì đó...</span>}
                      {listening && <span className="inline-block w-0.5 h-5 md:w-0.5 md:h-6 bg-[#00c897] ml-1 animate-pulse align-middle"></span>}
                    </p>
                  )}
                </div>

                {/* Animated Waveform - Lower height, more bars */}
                <div className="flex items-center gap-0.5 h-5 md:h-7 overflow-hidden w-full opacity-40">
                  {[...Array(window.innerWidth < 768 ? 40 : 80)].map((_, i) => (
                    <div 
                      key={i} 
                      className="w-[3px] bg-[#00c897] rounded-full transition-all duration-150"
                      style={{ 
                        height: listening ? `${20 + (i % 10) * 8}%` : '3px',
                        animation: listening ? `waveform 0.5s ease-in-out infinite alternate ${i * 0.008}s` : 'none'
                      }}
                    ></div>
                  ))}
                  <style dangerouslySetInnerHTML={{ __html: `
                    @keyframes waveform {
                      from { height: 20%; }
                      to { height: 100%; }
                    }
                  `}} />
                </div>
              </div>
            </div>

            {/* Actions Footer - More Compact */}
            <div className="flex items-center justify-center md:justify-end pt-3 md:pt-4 border-t border-on-surface/5">
              <div className="flex items-center gap-2 md:gap-3 w-full md:w-auto">
                <button 
                  onClick={toggleEditingVoiceText}
                  className={`flex-1 md:flex-none flex items-center justify-center gap-1.5 px-3 md:px-4 py-2 rounded-xl font-bold text-[11px] md:text-xs transition-all active:scale-95 ${
                    isEditingVoiceText 
                      ? 'bg-[#00c897]/10 text-[#00c897] border border-[#00c897]/20' 
                      : 'text-on-surface-variant hover:bg-surface-variant/50 border border-transparent'
                  }`}
                >
                  <PencilLine size={14} /> {isEditingVoiceText ? "Xong" : "Ch0nh sửa"}
                </button>
                <button 
                  onClick={cancelVoiceInput}
                  className="flex-1 md:flex-none flex items-center justify-center gap-1.5 px-3 md:px-5 py-2 rounded-xl border border-red-500/10 text-red-500 font-bold text-[11px] md:text-xs hover:bg-red-500/5 transition-all active:scale-95"
                >
                  <X size={14} strokeWidth={3} /> Hủy
                </button>
                <button 
                  onClick={stopAndSendVoice}
                  className="flex-1 md:flex-none flex items-center justify-center gap-2 px-5 md:px-7 py-2 rounded-xl bg-[#00c897] text-white font-black text-[11px] md:text-xs hover:brightness-105 shadow-lg shadow-[#00c897]/10 transition-all active:scale-95"
                >
                  <Send size={14} fill="white" /> Gửi
                </button>
              </div>
            </div>
          </div>
        ) : (
          /* Standard Input Box */
          <div className="w-full max-w-5xl glass-panel p-3 rounded-3xl shadow-[0_20px_50px_rgba(0,108,80,0.15)] flex flex-col gap-2 group border-white/20 dark:border-white/10 focus-within:border-[#00c897]/50 focus-within:ring-2 focus-within:ring-[#00c897]/10 transition-all bg-white/80 dark:bg-[#0c1618]/80 backdrop-blur-xl pointer-events-auto">
            {imagePreview && (
              <div className="relative w-20 h-20 mb-2 ml-2">
                <img src={imagePreview} alt="Preview" className="w-full h-full object-cover rounded-xl border border-[#00c897]/30 shadow-sm" />
                <button 
                  onClick={clearImage}
                  className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 shadow-md"
                >
                  <X size={12} />
                </button>
              </div>
            )}
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              onPaste={handlePaste}
              className="w-full bg-transparent border-none focus:ring-0 text-on-surface placeholder:text-on-surface-variant/60 font-bold px-2 py-1 resize-none max-h-32 min-h-[48px] outline-none text-sm"
              placeholder="Hỏi Xanh SM bất cứ điều gì..."
              rows={1}
            />
            
            <div className="flex items-center justify-between border-t border-outline-variant/10 pt-2 shrink-0">
              <div className="flex items-center gap-2 min-w-0 flex-1 mr-2">
                <input 
                  type="file" 
                  accept="image/*" 
                  ref={fileInputRef} 
                  onChange={handleImageUpload} 
                  className="hidden" 
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="w-8 h-8 rounded-full flex items-center justify-center text-on-surface-variant dark:text-white/60 hover:text-[#00c897] hover:bg-surface-variant/50 dark:hover:bg-white/10 transition-all active:scale-95 shrink-0"
                  title="Tải ảnh lên"
                >
                  <ImageIcon size={16} />
                </button>
                
                {/* Deep Search Toggle */}
                <button
                  onClick={() => {
                    if (user?.type === 'guest') {
                      alert("Vui lòng đăng nhập để sử dụng tính năng Tìm kiếm chuyên sâu (Deep Search).");
                      return;
                    }
                    setIsDeepSearch(!isDeepSearch);
                  }}
                  className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold transition-all border shrink-0 active:scale-95 ${
                    isDeepSearch
                      ? 'bg-gradient-to-r from-indigo-500/10 to-purple-500/10 text-indigo-600 dark:text-indigo-400 border-indigo-500/30 shadow-[0_0_10px_rgba(99,102,241,0.2)]'
                      : 'bg-transparent text-on-surface-variant/60 dark:text-white/40 border-transparent hover:bg-surface-variant/30 hover:text-on-surface-variant'
                  }`}
                  title={isDeepSearch ? "Tt Deep Search" : "Bt Deep Search (Tm kim chuyn su)"}
                >
                  <Search size={12} className={isDeepSearch ? "text-indigo-500" : ""} />
                  {isDeepSearch ? "Deep Search: Bật" : "Deep Search"}
                </button>

                {/* Horizontally scrollable suggestion pills */}

                <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-0.5 min-w-0 select-none">
                  <button 
                    onClick={(e) => handleSubmit(e, "Giá cước Xanh Car và Xanh Bike ở các khu vực")}
                    className="px-2.5 py-1 rounded-full bg-[#00c897]/10 hover:bg-[#00c897]/20 text-on-surface-variant dark:text-white/80 hover:text-[#00c897] text-[10px] font-bold transition-all border border-[#00c897]/20 whitespace-nowrap shrink-0 flex items-center gap-1 active:scale-95"
                  >
                    <span>🚗</span> Giá cước
                  </button>
                  <button 
                    onClick={(e) => handleSubmit(e, "Chính sách ưu đãi và khuyến mãi sạc pin trạm V-GREEN")}
                    className="px-2.5 py-1 rounded-full bg-[#00c897]/10 hover:bg-[#00c897]/20 text-on-surface-variant dark:text-white/80 hover:text-[#00c897] text-[10px] font-bold transition-all border border-[#00c897]/20 whitespace-nowrap shrink-0 flex items-center gap-1 active:scale-95"
                  >
                    <span>🎁</span> Ưu đãi
                  </button>
                  <button 
                    onClick={(e) => handleSubmit(e, "Chính sách thuê xe VinFast chạy dịch vụ trên Green SM Platform")}
                    className="px-2.5 py-1 rounded-full bg-[#00c897]/10 hover:bg-[#00c897]/20 text-on-surface-variant dark:text-white/80 hover:text-[#00c897] text-[10px] font-bold transition-all border border-[#00c897]/20 whitespace-nowrap shrink-0 flex items-center gap-1 active:scale-95"
                  >
                    <span>🔑</span> Thuê xe
                  </button>
                  <button 
                    onClick={(e) => handleSubmit(e, "Chính sách mua xe 0 đồng, thuê xe tự lái và ưu đãi sạc pin trạm V-GREEN cho xe VF 5, VF 6")}
                    className="px-2.5 py-1 rounded-full bg-[#00c897]/10 hover:bg-[#00c897]/20 text-on-surface-variant dark:text-white/80 hover:text-[#00c897] text-[10px] font-bold transition-all border border-[#00c897]/20 whitespace-nowrap shrink-0 flex items-center gap-1 active:scale-95"
                  >
                    <span>⚡</span> Xe điện
                  </button>
                </div>
              </div>
              
              <div className="flex items-center gap-1.5 shrink-0">
                {browserSupportsSpeechRecognition && (
                  <button
                    onClick={handleVoiceInput}
                    className={`w-8 h-8 rounded-full flex items-center justify-center transition-all active:scale-95 ${
                      listening 
                        ? 'bg-red-500 text-white shadow-lg animate-pulse' 
                        : 'text-on-surface-variant dark:text-white/60 hover:text-[#00c897] hover:bg-surface-variant/50 dark:hover:bg-white/10'
                    }`}
                    title={listening ? "Dừng ghi âm" : "Nhập li!u bằng giọng nói"}
                  >
                    {listening ? <MicOff size={16} /> : <Mic size={16} />}
                  </button>
                )}
                <button 
                  onClick={handleSubmit}
                  disabled={!input.trim() || loading}
                  className={`w-8 h-8 rounded-full flex items-center justify-center shadow-md transition-all ${
                    input.trim() && !loading 
                      ? 'bg-[#00c897] text-white hover:brightness-110 active:scale-95' 
                      : 'bg-surface-variant dark:bg-white/10 text-on-surface-variant/40 dark:text-white/30 cursor-not-allowed'
                  }`}
                >
                  <Send size={16} />
                </button>
              </div>
            </div>
          </div>
        )}
        
        <span className="text-[10px] text-on-surface-variant/60 flex items-center gap-1 select-none font-bold">
          <ShieldCheck size={12} /> Thông tin của bạn được bảo mật và chỉ sử dụng để hỗ trợ.
        </span>
      </div>

      {/* Food Explanation Modal */}
      {explainingFood && (
        <FoodExplanationModal item={explainingFood} onClose={() => setExplainingFood(null)} />
      )}

      {/* Feedback Modal */}
      {feedbackModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="bg-white dark:bg-surface-container-high rounded-2xl w-full max-w-md overflow-hidden shadow-2xl border border-outline-variant/20 flex flex-col scale-in-95 duration-200">
            <div className="p-5 border-b border-outline-variant/20 flex items-center justify-between bg-surface-container/30">
              <h3 className="font-bold text-lg text-on-surface">Đóng góp ý kiến</h3>
              <button 
                onClick={() => setFeedbackModalOpen(false)}
                className="p-2 text-on-surface-variant hover:bg-surface-variant rounded-full transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            
            <div className="p-5 space-y-5">
              <p className="text-sm text-on-surface-variant">Xin lỗi vì câu trả lời chưa đáp ứng mong đợi của bạn. Hãy cho chúng tôi biết lý do (chọn nhiều):</p>
              
              <div className="flex flex-wrap gap-2">
                {['Không đúng thực tế', 'Thiếu thông tin', 'Sai ngữ cảnh', 'Lỗi hiển thị', 'Lạc đề', 'Lý do khác'].map(tag => (
                  <button
                    key={tag}
                    onClick={() => {
                      if (feedbackTags.includes(tag)) setFeedbackTags(feedbackTags.filter(t => t !== tag));
                      else setFeedbackTags([...feedbackTags, tag]);
                    }}
                    className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all border ${
                      feedbackTags.includes(tag) 
                        ? 'bg-primary text-white border-primary shadow-md' 
                        : 'bg-transparent text-on-surface-variant border-outline-variant/40 hover:border-primary/50'
                    }`}
                  >
                    {tag}
                  </button>
                ))}
              </div>
              
              <div className="space-y-2">
                <label className="text-xs font-bold text-on-surface-variant uppercase tracking-wider">Bình luận thêm (không bắt bu"c)</label>
                <textarea
                  value={feedbackComment}
                  onChange={e => setFeedbackComment(e.target.value)}
                  placeholder="Góp ý của bạn sẽ giúp Xanh SM AI thông minh hơn..."
                  className="w-full bg-surface-container/50 border border-outline-variant/30 rounded-xl p-3 text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none h-24"
                ></textarea>
              </div>
            </div>
            
            <div className="p-5 border-t border-outline-variant/20 bg-surface-container/30 flex justify-end gap-3">
              <button 
                onClick={() => setFeedbackModalOpen(false)}
                className="px-4 py-2 font-semibold text-sm text-on-surface-variant hover:bg-surface-variant rounded-xl transition-colors"
              >
                Hủy
              </button>
              <button 
                onClick={submitDownReview}
                disabled={submittingReview || (feedbackTags.length === 0 && !feedbackComment.trim())}
                className="px-6 py-2 font-bold text-sm bg-primary text-white rounded-xl shadow-md hover:shadow-lg hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
              >
                {submittingReview && <Loader2 size={16} className="animate-spin" />}
                Gửi Đánh Giá
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
