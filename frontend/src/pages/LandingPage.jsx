import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import {
  BarChart2,
  Bell,
  Car,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Database,
  Gift,
  Image as ImageIcon,
  Layers3,
  LockKeyhole,
  MessageSquare,
  Mic,
  Newspaper,
  Paperclip,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  Tag,
  Utensils,
  Map,
  MapPin,
  Zap,
} from 'lucide-react';

const t = {
  powered: 'AI-powered',
  titleA: 'Xanh SM',
  titleB: 'AI Assistant',
  hero: 'Trợ lý AI thông minh giúp bạn tìm hiểu mọi thông tin về dịch vụ, xe điện, giá cước, ưu đãi và vận hành của Xanh SM.',
  smart: 'Thông minh',
  fast: 'Nhanh chóng',
  accurate: 'Chính xác',
  secure: 'Bảo mật',
  ask: 'Hỏi tôi bất kỳ điều gì về Xanh SM...',
  service: 'Dịch vụ',
  pricing: 'Giá cước',
  vehicle: 'Xe điện',
  news: 'Tin tức',
  promo: 'Ưu đãi',
  food: 'Food AI',
  map: 'Map AI',
  analytics: 'Analytics',
  discover: 'Khám phá khả năng của AI Assistant',
  allFeatures: 'Tất cả tính năng',
  mayCare: 'Bạn có thể quan tâm',
  recent: 'Câu hỏi gần đây',
  viewAll: 'Xem tất cả',
  ctaTitle: 'Trải nghiệm dịch vụ xanh thông minh cùng Xanh SM',
  ctaButton: 'Tìm hiểu ngay',
  securityTitle: 'Bảo mật dữ liệu tuyệt đối',
  securitySub: 'Dữ liệu của bạn được mã hóa và bảo vệ theo tiêu chuẩn quốc tế',
};

const sceneTitles = ['Tổng quan', 'Khám phá', 'Hiệu năng', 'Hoạt động'];

const orbitItems = [
  { label: t.pricing, icon: Tag, x: 24, y: -230, rotate: -8, color: 'text-amber-500' },
  { label: t.vehicle, icon: Car, x: 232, y: -124, rotate: 7, color: 'text-emerald-500' },
  { label: t.news, icon: Newspaper, x: 266, y: 34, rotate: -5, color: 'text-violet-500' },
  { label: t.analytics, icon: BarChart2, x: 160, y: 184, rotate: 9, color: 'text-blue-500' },
  { label: t.map, icon: Map, x: -42, y: 226, rotate: -7, color: 'text-cyan-500' },
  { label: t.food, icon: Utensils, x: -230, y: 80, rotate: 6, color: 'text-orange-500' },
  { label: t.promo, icon: Gift, x: -230, y: 80, rotate: 6, color: 'text-red-500' },
  { label: t.service, icon: Car, x: -210, y: -104, rotate: -10, color: 'text-teal-500' },
];

const capabilityCards = [
  {
    title: 'Knowledge Search',
    desc: 'Tìm kiếm và tra cứu trong toàn bộ kho tri thức',
    image: '/knowledge_search.png',
  },
  {
    title: 'Deep Research',
    desc: 'Nghiên cứu chuyên sâu và truy xuất đa nguồn',
    image: '/deep_research.png',
  },
  {
    title: 'Vehicle Expert',
    desc: 'Hỏi đáp chi tiết về VF3, VF5, VF6, VF8...',
    image: '/vehicle_expert.png',
  },
  {
    title: 'Pricing Assistant',
    desc: 'Tính giá cước, xem chính sách và ưu đãi hiện hành',
    image: '/pricing_assistant.png',
  },
  {
    title: 'News Digest',
    desc: 'Tổng hợp tin tức mới nhất về Xanh SM và thị trường',
    image: '/news_digest.png',
  },
  {
    title: 'Food Recommendation',
    desc: 'Gợi ý món ngon, địa điểm ăn uống phù hợp với bạn',
    image: '/food_recommendation.png',
  },
  {
    title: 'Map Intelligence',
    desc: 'Tìm đường, đo khoảng cách và tránh điểm kẹt xe',
    image: '/map_intelligence.png',
  },
  {
    title: 'Policy & Support',
    desc: 'Chính sách, điều khoản và hỗ trợ khách hàng',
    image: '/policy_support.png',
  },
  {
    title: 'Data Analytics',
    desc: 'Thống kê, báo cáo và insight thông minh',
    image: '/data_analytics.png',
  },
];

const stats = [
  { value: '2.3M+', label: 'Documents Indexed', delta: '+12.5%', icon: Layers3, color: 'text-[#00a884]', up: true },
  { value: '99%', label: 'Faithfulness', delta: '+2.1%', icon: ShieldCheck, color: 'text-emerald-500', up: true },
  { value: '90%', label: 'Correctness', delta: '+3.7%', icon: TargetIcon, color: 'text-blue-500', up: true },
  { value: '120ms', label: 'Avg. Retrieval', delta: '-8.3%', icon: Zap, color: 'text-amber-500', up: false },
  { value: '95%', label: 'Cache Hit Rate', delta: '+5.6%', icon: Database, color: 'text-violet-500', up: true },
];

function TargetIcon(props) {
  return <CheckCircle2 {...props} />;
}

const interests = [
  [MapPin, 'Đường từ Hồ Gươm đến sân bay Nội Bài đi thế nào?'],
  [Car, 'Xe VF6 có những màu nào?'],
  [ShieldCheck, 'Chính sách bảo hành pin xe VF5 như thế nào?'],
  [Utensils, 'Gợi ý món ăn ngon gần đây?'],
];

const recentQuestions = [
  ['Từ đây đến Lăng Bác đi đường nào?', 'Vừa xong'],
  ['Giá cước từ sân bay Nội Bài đến Hà Nội?', '2 phút trước'],
  ['Khu vực Ngã Tư Sở có kẹt xe không?', '10 phút trước'],
  ['Chính sách bảo hành pin xe VF5 như thế nào?', '15 phút trước'],
  ['Tin tức mới nhất về Xanh SM?', '1 giờ trước'],
];

export default function LandingPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [isLeaving, setIsLeaving] = useState(false);
  const [activeScene, setActiveScene] = useState(0);
  const sceneLockRef = useRef(false);
  const touchStartRef = useRef(null);
  const isAuthenticatedUser = user?.type === 'user';
  const displayName = isAuthenticatedUser ? (user.name || user.email || 'User') : 'Guest';
  const avatarUrl = isAuthenticatedUser ? user.avatar_url : null;
  const avatarInitial = (displayName || 'Guest').trim().charAt(0).toUpperCase() || 'G';
  const sceneCount = 4;

  useEffect(() => {
    document.documentElement.classList.add('landing-scroll-hidden');
    document.body.classList.add('landing-scroll-hidden');

    return () => {
      document.documentElement.classList.remove('landing-scroll-hidden');
      document.body.classList.remove('landing-scroll-hidden');
    };
  }, []);

  const goToChat = () => {
    setIsLeaving(true);
    window.setTimeout(() => navigate('/chat'), 360);
  };

  const moveScene = (direction) => {
    if (sceneLockRef.current) return;

    setActiveScene((current) => {
      const next = Math.min(sceneCount - 1, Math.max(0, current + direction));
      if (next === current) return current;

      sceneLockRef.current = true;
      window.setTimeout(() => {
        sceneLockRef.current = false;
      }, 820);
      return next;
    });
  };

  const handleWheel = (event) => {
    event.preventDefault();
    if (Math.abs(event.deltaY) < 18) return;
    moveScene(event.deltaY > 0 ? 1 : -1);
  };

  const handleTouchStart = (event) => {
    touchStartRef.current = event.touches[0]?.clientY ?? null;
  };

  const handleTouchEnd = (event) => {
    if (touchStartRef.current === null) return;
    const endY = event.changedTouches[0]?.clientY ?? touchStartRef.current;
    const delta = touchStartRef.current - endY;
    touchStartRef.current = null;
    if (Math.abs(delta) < 42) return;
    moveScene(delta > 0 ? 1 : -1);
  };

  const handleKeyDown = (event) => {
    if (['ArrowDown', 'PageDown', ' '].includes(event.key)) {
      event.preventDefault();
      moveScene(1);
    }
    if (['ArrowUp', 'PageUp'].includes(event.key)) {
      event.preventDefault();
      moveScene(-1);
    }
  };

  const sceneStyle = (index) => {
    const delta = index - activeScene;
    return {
      opacity: delta === 0 ? 1 : 0,
      transform: delta === 0
        ? 'translate3d(0, 0, 0) scale(1)'
        : delta < 0
          ? 'translate3d(0, -13vh, 0) scale(.955)'
          : 'translate3d(0, 13vh, 0) scale(.955)',
      filter: delta === 0 ? 'blur(0)' : 'blur(14px)',
      pointerEvents: delta === 0 ? 'auto' : 'none',
      zIndex: delta === 0 ? 20 : 10 - Math.abs(delta),
    };
  };

  const sceneClass = 'scrolly-scene absolute inset-0 flex items-center overflow-hidden px-3 pb-4 pt-[88px] md:px-5 lg:pt-[132px]';

  return (
    <main
      className="h-screen overflow-hidden bg-[#effdfa] text-[#071638] outline-none [font-family:'Outfit','Inter',system-ui,sans-serif]"
      tabIndex={0}
      onWheel={handleWheel}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      onKeyDown={handleKeyDown}
    >
      <style>{`
        @keyframes floatSoft {
          0%, 100% { transform: translateY(0) rotate(var(--spin, 0deg)); }
          50% { transform: translateY(-13px) rotate(calc(var(--spin, 0deg) + 2deg)); }
        }
        @keyframes orbitPulse {
          0%, 100% { opacity: .55; transform: translate(-50%, -50%) scale(1); }
          50% { opacity: .95; transform: translate(-50%, -50%) scale(1.055); }
        }
        @keyframes risePro {
          from { opacity: 0; transform: translateY(110px) scale(.955); filter: blur(14px); }
          to { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
        }
        @keyframes panelLift {
          0% { opacity: 0; transform: translateY(150px) scale(.94) rotateX(8deg); filter: blur(18px); }
          45% { opacity: 1; transform: translateY(0) scale(1) rotateX(0); filter: blur(0); }
          100% { opacity: 1; transform: translateY(-18px) scale(.988) rotateX(0); filter: blur(0); }
        }
        @keyframes heroExit {
          from { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
          to { opacity: 0; transform: translateY(-132px) scale(.94); filter: blur(7px); }
        }
        @keyframes tinySpark {
          0%, 100% { opacity: .2; transform: translateY(0); }
          50% { opacity: .9; transform: translateY(-8px); }
        }
        @keyframes pageLeave {
          from { opacity: 0; transform: scale(1.04); }
          to { opacity: 1; transform: scale(1); }
        }
        .float-soft { animation: floatSoft 5.8s ease-in-out infinite; }
        .orbit-pulse { animation: orbitPulse 5s ease-in-out infinite; }
        .hero-exit {
          animation: heroExit linear both;
          animation-timeline: scroll(root);
          animation-range: 40px 600px;
        }
        .reveal-pro {
          animation: risePro .9s cubic-bezier(.16, 1, .3, 1) both;
          animation-timeline: view();
          animation-range: entry 0% cover 32%;
        }
        .spark-dot { animation: tinySpark 3.2s ease-in-out infinite; }
        .page-leave { animation: pageLeave .36s cubic-bezier(.16, 1, .3, 1) both; }
        .landing-scroll-hidden {
          height: 100%;
          overflow: hidden;
          scrollbar-width: none;
          -ms-overflow-style: none;
          scroll-behavior: smooth;
        }
        .landing-scroll-hidden::-webkit-scrollbar {
          width: 0;
          height: 0;
          display: none;
        }
        .landing-stage {
          perspective: 1200px;
          transform-style: preserve-3d;
        }
        .scrolly-scene {
          transition:
            opacity .72s cubic-bezier(.16, 1, .3, 1),
            transform .82s cubic-bezier(.16, 1, .3, 1),
            filter .72s cubic-bezier(.16, 1, .3, 1);
          will-change: opacity, transform, filter;
        }
        .scene-card {
          background: rgba(255, 255, 255, .86);
          border: 1px solid rgba(255, 255, 255, .78);
          box-shadow: 0 30px 90px rgba(0, 88, 110, .14);
          backdrop-filter: blur(24px);
        }
        .scene-tabs button {
          transition: transform .25s ease, background .25s ease, color .25s ease, opacity .25s ease;
        }
        .landing-panel {
          transform-origin: 50% 100%;
          will-change: transform, opacity, filter;
          animation: panelLift both cubic-bezier(.16, 1, .3, 1);
          animation-timeline: view();
          animation-range: entry -8% cover 58%;
        }
        @supports not (animation-timeline: view()) {
          .hero-exit { animation: none; }
          .reveal-pro { animation-timeline: auto; animation-range: normal; }
          .landing-panel { animation: risePro .85s cubic-bezier(.16, 1, .3, 1) both; }
        }
      `}</style>

      {isLeaving && (
        <div className="page-leave fixed inset-0 z-[999] bg-[#effdfa]/92 backdrop-blur-xl">
          <div className="absolute left-1/2 top-1/2 h-16 w-16 -translate-x-1/2 -translate-y-1/2 rounded-full border-4 border-[#00d4aa]/25 border-t-[#00a884]" />
        </div>
      )}

      <div className="fixed inset-0 z-0 bg-[url('/bg_landing.png')] bg-cover bg-center bg-no-repeat" />

      <header className="fixed left-0 right-0 top-0 z-40 mx-auto flex h-[92px] max-w-[1460px] items-center justify-between px-4 md:px-5">
        <button onClick={() => setActiveScene(0)} className="flex items-center gap-3">
          <img src="/logo.svg" alt="Xanh SM" className="h-12 w-auto" />
          <span className="hidden text-xs font-black uppercase tracking-[0.18em] text-[#0b1d43] md:block">AI Assistant</span>
        </button>

        <div className="flex items-center gap-3">
          <button onClick={goToChat} className="relative flex h-11 w-11 items-center justify-center rounded-full border border-white/80 bg-white/82 text-[#0b1d43] shadow-[0_14px_34px_rgba(40,91,118,.13)] backdrop-blur-xl">
            <Bell size={19} />
            <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-[10px] font-black text-white">2</span>
          </button>
          <button onClick={goToChat} className="flex h-11 items-center gap-2 rounded-full border border-white/80 bg-white/84 p-1.5 pr-4 shadow-[0_14px_34px_rgba(40,91,118,.13)] backdrop-blur-xl">
            <span className="flex h-8 w-8 items-center justify-center overflow-hidden rounded-full bg-[#00a884] text-sm font-black uppercase text-white">
              {avatarUrl ? <img src={avatarUrl} alt={displayName} className="h-full w-full object-cover" /> : avatarInitial}
            </span>
            <span className="hidden max-w-[180px] truncate text-sm font-black text-[#0b1d43] sm:inline">{displayName}</span>
            <ChevronDown size={16} className="text-[#71809b]" />
          </button>
        </div>
      </header>

      <div className="scene-tabs fixed left-1/2 top-[18px] z-50 flex max-w-[calc(100vw-220px)] -translate-x-1/2 items-center gap-2 overflow-x-auto rounded-full border border-white/70 bg-white/52 p-1.5 shadow-[0_14px_36px_rgba(40,91,118,.12)] backdrop-blur-2xl max-lg:hidden">
        {sceneTitles.map((title, index) => (
          <button
            key={title}
            onClick={() => setActiveScene(index)}
            className={`h-10 shrink-0 rounded-full px-4 text-sm font-black ${
              activeScene === index
                ? 'bg-[#00a884] text-white shadow-[0_12px_28px_rgba(0,168,132,.26)]'
                : 'text-[#0b1d43] opacity-75 hover:bg-white/72 hover:opacity-100'
            }`}
          >
            {title}
          </button>
        ))}
      </div>

      <section className={sceneClass} style={sceneStyle(0)}>
        <span className="spark-dot absolute right-[13%] top-[12%] h-2 w-2 rounded-full bg-white shadow-[0_0_24px_8px_rgba(255,255,255,.9)]" />
        <span className="spark-dot absolute right-[35%] top-[23%] h-1.5 w-1.5 rounded-full bg-white shadow-[0_0_18px_7px_rgba(255,255,255,.85)]" style={{ animationDelay: '1.2s' }} />

        <div className="relative z-20 mx-auto grid w-full max-w-[1460px] grid-cols-1 items-center gap-2 lg:grid-cols-[0.86fr_1.14fr]">
          <div className="hero-exit ml-0 max-w-[650px] lg:ml-9">
            <div className="inline-flex items-center gap-2 rounded-full bg-[#e0fbf5] px-5 py-3 text-sm font-black uppercase text-[#00a884] shadow-[0_14px_30px_rgba(0,168,132,.13)]">
              <Sparkles size={18} />
              {t.powered}
            </div>

            <h1 className="mt-5 text-[46px] font-black leading-[.94] tracking-[-0.055em] text-[#071638] md:text-[68px]">
              {t.titleA}
              <span className="block bg-gradient-to-r from-[#00a884] via-[#00cfaa] to-[#00b896] bg-clip-text text-transparent">{t.titleB}</span>
            </h1>

            <p className="mt-5 max-w-[520px] text-lg font-semibold leading-8 text-[#344667]">{t.hero}</p>

            <div className="mt-7 flex flex-wrap gap-3">
              {[
                [t.smart, CheckCircle2],
                [t.fast, Zap],
                [t.accurate, ShieldCheck],
                [t.secure, LockKeyhole],
              ].map(([label, Icon]) => (
                <span key={label} className="flex items-center gap-2 rounded-full border border-white/80 bg-white/76 px-4 py-2 text-sm font-black text-[#0b1d43] shadow-[0_10px_24px_rgba(40,91,118,.08)] backdrop-blur-xl">
                  <Icon size={16} className="text-[#00a884]" />
                  {label}
                </span>
              ))}
            </div>

            <div className="mt-7 max-w-[720px] rounded-[26px] border border-white/80 bg-white/90 p-4 shadow-[0_32px_90px_rgba(0,103,124,.18)] backdrop-blur-2xl">
              <button onClick={goToChat} className="flex min-h-[54px] w-full items-center justify-between rounded-2xl text-left">
                <span className="px-1 text-base font-semibold text-[#70809c]">{t.ask}</span>
                <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[#0be5c2] to-[#00a884] p-3 text-white shadow-[0_18px_42px_rgba(0,168,132,.34)]">
                  <Send size={21} />
                </span>
              </button>
              <div className="mt-3 flex flex-wrap gap-3">
                {[
                  ['Deep Search', Search],
                  ['Upload', Paperclip],
                  ['Voice', Mic],
                  ['Image', ImageIcon],
                ].map(([label, Icon]) => (
                  <button key={label} onClick={goToChat} className="flex h-10 items-center gap-2 rounded-2xl border border-[#dfe8f2] bg-white px-4 text-xs font-black text-[#0b1d43] shadow-sm transition-all hover:-translate-y-0.5 hover:border-[#00d4aa] hover:text-[#00a884]">
                    <Icon size={15} className="text-[#00a884]" />
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="hero-exit relative mx-auto hidden h-[640px] w-full max-w-[760px] translate-x-8 lg:block">
            <div className="orbit-pulse absolute left-[54%] top-[43%] h-[520px] w-[520px] rounded-full border border-white/60 bg-white/8 shadow-[inset_0_0_55px_rgba(255,255,255,.62)] backdrop-blur-[1px]" />
            <div className="orbit-pulse absolute left-[54%] top-[43%] h-[360px] w-[360px] rounded-full border-[18px] border-[#6cebd8]/42 bg-[#00d4aa]/12 shadow-[0_0_120px_rgba(0,212,170,.34)] backdrop-blur-[2px]" style={{ animationDelay: '.35s' }} />

            {orbitItems.map((item, index) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.label}
                  className="absolute left-[54%] top-[43%] z-20"
                  style={{ transform: `translate(calc(-50% + ${item.x}px), calc(-50% + ${item.y}px))` }}
                >
                  <button onClick={goToChat} className="float-soft w-[112px] rounded-[26px] border border-white/65 bg-white/40 p-3 text-center shadow-[0_22px_54px_rgba(31,83,105,.16)] backdrop-blur-md transition-all hover:-translate-y-1" style={{ '--spin': `${item.rotate}deg`, animationDelay: `${index * 0.2}s` }}>
                    <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-white/58 shadow-sm backdrop-blur-md">
                      <Icon size={25} className={item.color} />
                    </span>
                    <span className="mt-2 block text-xs font-black text-[#0b1d43]">{item.label}</span>
                  </button>
                </div>
              );
            })}

            <div className="absolute left-[54%] top-[43%] z-10 flex h-[365px] w-[365px] -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-white/10 backdrop-blur-[2px]">
              <img src="/Bot.png" alt="Xanh SM AI Assistant" className="float-soft h-full w-full object-contain drop-shadow-[0_36px_50px_rgba(0,89,105,.3)]" />
            </div>
          </div>
        </div>
      </section>

      <section className={sceneClass} style={sceneStyle(1)}>
        <div className="scene-card mx-auto flex max-h-[calc(100vh-106px)] w-full max-w-[1180px] flex-col justify-center rounded-[24px] p-3 md:max-h-[calc(100vh-158px)] md:rounded-[28px] md:p-5 xl:max-w-[1240px]">
          <div className="mb-3 flex items-center justify-between gap-4 md:mb-4">
            <h2 className="flex items-center gap-2 text-lg font-black leading-tight tracking-[-0.025em] text-[#071638] md:text-2xl xl:text-3xl">
              <Sparkles size={22} className="text-[#00a884] md:h-[26px] md:w-[26px]" />
              {t.discover}
            </h2>
            <button onClick={goToChat} className="hidden items-center gap-2 text-sm font-black text-[#00a884] md:flex">
              {t.allFeatures}
              <ChevronRight size={16} />
            </button>
          </div>

          <div className="mx-auto grid w-full max-w-[1120px] grid-cols-2 gap-2 overflow-hidden md:gap-3 xl:grid-cols-4">
            {capabilityCards.slice(0, 8).map((card, index) => (
              <button
                key={card.title}
                onClick={goToChat}
                className="group h-[126px] overflow-hidden rounded-[14px] border border-[#dbe7f2] bg-white text-left shadow-[0_10px_24px_rgba(16,52,79,.07)] transition-all duration-300 hover:-translate-y-2 hover:shadow-[0_24px_48px_rgba(0,116,140,.14)] md:h-[178px] md:rounded-[18px] xl:h-[188px]"
                style={{
                  transform: activeScene === 1 ? 'translateY(0)' : 'translateY(26px)',
                  transitionDelay: activeScene === 1 ? `${index * 55}ms` : '0ms',
                  opacity: activeScene === 1 ? 1 : 0,
                }}
              >
                <div className="h-[54px] overflow-hidden bg-[#f5fffc] md:h-[86px] xl:h-[92px]">
                  <img src={card.image} alt={card.title} className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105" />
                </div>
                <div className="p-2.5 md:p-3">
                  <h3 className="text-[11px] font-black tracking-[-0.02em] text-[#071638] md:text-base">{card.title}</h3>
                  <p className="mt-1.5 line-clamp-2 text-[10px] font-bold leading-4 text-[#304366] md:text-xs md:leading-5">{card.desc}</p>
                </div>
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className={sceneClass} style={sceneStyle(2)}>
        <div className="mx-auto grid w-full max-w-[1380px] grid-cols-1 gap-5 lg:grid-cols-[1.05fr_.95fr]">
          <div className="scene-card rounded-[30px] p-5 md:p-7">
            <h2 className="mb-5 flex items-center gap-3 text-2xl font-black tracking-[-0.025em] text-[#071638] md:text-3xl">
              <Layers3 size={27} className="text-[#00a884]" />
              Real-time intelligence
            </h2>
            <div className="grid grid-cols-2 gap-3 md:gap-4">
              {stats.slice(0, 4).map((stat, index) => {
                const Icon = stat.icon;
                return (
                  <div
                    key={stat.label}
                    className="relative min-h-[118px] overflow-hidden rounded-2xl border border-[#dcecf1] bg-white/88 p-4 shadow-sm md:min-h-[132px] md:p-5"
                    style={{
                      transform: activeScene === 2 ? 'translateY(0)' : 'translateY(30px)',
                      transition: 'opacity .5s ease, transform .55s cubic-bezier(.16, 1, .3, 1)',
                      transitionDelay: activeScene === 2 ? `${index * 70}ms` : '0ms',
                      opacity: activeScene === 2 ? 1 : 0,
                    }}
                  >
                    <div className="absolute bottom-3 left-4 right-4 h-9 opacity-40">
                      <svg viewBox="0 0 170 38" className="h-full w-full">
                        <path d="M0 25 C 28 9, 50 33, 78 18 S 132 13, 170 22" fill="none" stroke="currentColor" strokeWidth="2" className={stat.color} />
                      </svg>
                    </div>
                    <span className={`relative flex h-12 w-12 items-center justify-center rounded-2xl bg-white shadow-[0_10px_24px_rgba(29,65,87,.08)] ${stat.color}`}>
                      <Icon size={28} />
                    </span>
                    <div className="relative mt-4">
                      <div className="text-3xl font-black tracking-[-0.04em] text-[#071638] md:text-4xl">{stat.value}</div>
                      <div className="text-sm font-bold text-[#304366]">{stat.label}</div>
                      <div className={`mt-2 text-sm font-black ${stat.up ? 'text-[#00a884]' : 'text-orange-500'}`}>
                        {stat.up ? '↑' : '↓'} {stat.delta}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="scene-card hidden rounded-[30px] p-5 md:p-7 lg:block">
            <h2 className="mb-5 text-2xl font-black tracking-[-0.025em] text-[#071638] md:text-3xl">{t.mayCare}</h2>
            <div className="space-y-4">
              {interests.map(([Icon, question], index) => (
                <button
                  key={question}
                  onClick={goToChat}
                  className="flex min-h-[78px] w-full items-center gap-4 rounded-2xl border border-[#dfe8f2] bg-white/92 px-4 py-3 text-left shadow-sm transition-all hover:-translate-y-1 hover:border-[#00d4aa] hover:shadow-lg"
                  style={{
                    transform: activeScene === 2 ? 'translateX(0)' : 'translateX(36px)',
                    transitionDelay: activeScene === 2 ? `${index * 80 + 130}ms` : '0ms',
                    opacity: activeScene === 2 ? 1 : 0,
                  }}
                >
                  <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[#e0fbf5] text-[#00a884]">
                    <Icon size={23} />
                  </span>
                  <span className="text-sm font-black leading-5 text-[#0b1d43]">{question}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className={sceneClass} style={sceneStyle(3)}>
        <div className="mx-auto grid w-full max-w-[1380px] grid-cols-1 gap-5 lg:grid-cols-[1fr_1fr]">
          <div className="scene-card rounded-[30px] p-5 md:p-7">
            <div className="mb-5 flex items-center justify-between">
              <h2 className="text-2xl font-black tracking-[-0.025em] text-[#071638] md:text-3xl">{t.recent}</h2>
              <button onClick={goToChat} className="flex items-center gap-2 text-sm font-black text-[#00a884]">
                {t.viewAll}
                <ChevronRight size={16} />
              </button>
            </div>
            <div className="space-y-3">
              {recentQuestions.map(([question, time], index) => (
                <button
                  key={question}
                  onClick={goToChat}
                  className="flex w-full items-center justify-between gap-3 rounded-xl border border-[#dfe8f2] bg-white/92 px-4 py-3 text-left transition-all hover:border-[#00d4aa]"
                  style={{
                    transform: activeScene === 3 ? 'translateY(0)' : 'translateY(28px)',
                    transitionDelay: activeScene === 3 ? `${index * 70}ms` : '0ms',
                    opacity: activeScene === 3 ? 1 : 0,
                  }}
                >
                  <span className="flex min-w-0 items-center gap-3">
                    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#e0fbf5] text-[#00a884]">
                      <MessageSquare size={16} />
                    </span>
                    <span className="truncate text-sm font-bold text-[#0b1d43]">{question}</span>
                  </span>
                  <span className="shrink-0 text-xs font-bold text-[#70809c]">{time}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="hidden gap-5 lg:grid">
            <button onClick={goToChat} className="relative min-h-[286px] overflow-hidden rounded-[30px] border border-white/86 bg-white p-7 text-left shadow-[0_22px_70px_rgba(0,88,110,.1)] transition-all hover:-translate-y-1 hover:shadow-[0_30px_84px_rgba(0,168,132,.16)]">
              <img src="/cta_service.png" alt="" className="absolute inset-0 h-full w-full object-cover" />
              <div className="absolute inset-0 bg-gradient-to-r from-white via-white/86 to-white/8" />
              <div className="relative max-w-[330px]">
                <h2 className="text-3xl font-black leading-tight tracking-[-0.045em] text-[#071638]">{t.ctaTitle}</h2>
                <span className="mt-6 inline-flex items-center gap-2 rounded-full bg-[#00a884] px-5 py-3 text-sm font-black text-white shadow-[0_16px_34px_rgba(0,168,132,.3)]">
                  {t.ctaButton}
                  <ChevronRight size={17} />
                </span>
              </div>
            </button>

            <div className="scene-card grid grid-cols-1 gap-4 rounded-[26px] p-5 md:grid-cols-2">
              {[
                [LockKeyhole, t.securityTitle, t.securitySub],
                [ShieldCheck, 'ISO 27001', 'Certified'],
                [ShieldCheck, 'GDPR', 'Compliant'],
                [ShieldCheck, 'SOC 2', 'Type II'],
              ].map(([Icon, title, desc]) => (
                <div key={title} className="flex items-center gap-4">
                  <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-white text-[#00a884] shadow-sm">
                    <Icon size={24} />
                  </span>
                  <div>
                    <div className="text-base font-black text-[#071638]">{title}</div>
                    <div className="text-sm font-semibold text-[#52617b]">{desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <div className="hidden">
        <section id="capabilities" className="landing-panel mx-auto max-w-[1380px] rounded-[30px] border border-white/86 bg-white/88 p-6 shadow-[0_26px_84px_rgba(0,88,110,.12)] md:p-7">
          <div className="mb-6 flex items-center justify-between gap-4">
            <h2 className="flex items-center gap-3 text-2xl font-black tracking-[-0.025em] text-[#071638]">
              <Sparkles size={24} className="text-[#00a884]" />
              {t.discover}
            </h2>
            <button onClick={goToChat} className="hidden items-center gap-2 text-sm font-black text-[#00a884] md:flex">
              {t.allFeatures}
              <ChevronRight size={16} />
            </button>
          </div>

          <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-4">
            {capabilityCards.map((card, index) => (
              <button
                key={card.title}
                onClick={goToChat}
                className="reveal-pro group min-h-[250px] overflow-hidden rounded-[20px] border border-[#dbe7f2] bg-white text-left shadow-[0_14px_34px_rgba(16,52,79,.08)] transition-all hover:-translate-y-2 hover:shadow-[0_28px_58px_rgba(0,116,140,.16)]"
                style={{ animationDelay: `${index * 0.04}s` }}
              >
                <div className="h-[150px] overflow-hidden bg-[#f5fffc]">
                  <img src={card.image} alt={card.title} className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105" />
                </div>
                <div className="p-5">
                  <h3 className="text-lg font-black tracking-[-0.02em] text-[#071638]">{card.title}</h3>
                  <p className="mt-2 min-h-[44px] text-sm font-bold leading-6 text-[#304366]">{card.desc}</p>
                  <ChevronRight size={18} className="ml-auto mt-2 text-[#0b1d43] transition-transform group-hover:translate-x-1" />
                </div>
              </button>
            ))}
          </div>
        </section>

        <section className="landing-panel mx-auto max-w-[1380px] rounded-[34px] border border-white/90 bg-white/92 p-5 shadow-[0_24px_74px_rgba(0,88,110,.11)]">
          <div className="grid grid-cols-1 overflow-hidden rounded-[26px] bg-[#f7fffd] md:grid-cols-7">
            <div className="relative hidden min-h-[128px] items-center justify-center overflow-hidden md:flex">
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_42%_48%,rgba(0,212,170,.24),transparent_48%)]" />
              <Layers3 size={66} className="relative text-[#00a884] drop-shadow-[0_18px_24px_rgba(0,168,132,.22)]" />
            </div>
            {stats.map((stat) => {
              const Icon = stat.icon;
              return (
                <div key={stat.label} className="relative flex min-h-[128px] items-center gap-4 border-t border-[#dcecf1] p-5 md:border-l md:border-t-0">
                  <div className="absolute bottom-3 left-3 right-3 h-8 opacity-45">
                    <svg viewBox="0 0 170 38" className="h-full w-full">
                      <path d="M0 25 C 28 9, 50 33, 78 18 S 132 13, 170 22" fill="none" stroke="currentColor" strokeWidth="2" className={stat.color} />
                    </svg>
                  </div>
                  <span className={`relative flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-white shadow-[0_10px_24px_rgba(29,65,87,.08)] ${stat.color}`}>
                    <Icon size={28} />
                  </span>
                  <div className="relative">
                    <div className="text-3xl font-black tracking-[-0.04em] text-[#071638]">{stat.value}</div>
                    <div className="text-xs font-bold text-[#304366]">{stat.label}</div>
                    <div className={`mt-2 text-sm font-black ${stat.up ? 'text-[#00a884]' : 'text-orange-500'}`}>
                      {stat.up ? '↑' : '↓'} {stat.delta}
                    </div>
                  </div>
                </div>
              );
            })}
            <div className="relative hidden min-h-[128px] items-center justify-center overflow-hidden border-l border-[#dcecf1] md:flex">
              <div className="absolute h-28 w-28 rounded-full bg-[#0be5c2]/25 blur-xl" />
              <Database size={66} className="relative text-[#0bcfb0] drop-shadow-[0_18px_24px_rgba(0,168,132,.22)]" />
            </div>
          </div>
        </section>

        <section className="landing-panel mx-auto max-w-[1380px] rounded-[28px] border border-white/86 bg-white/88 p-5 shadow-[0_22px_70px_rgba(0,88,110,.1)] md:p-6">
          <h2 className="mb-5 text-2xl font-black tracking-[-0.025em] text-[#071638]">{t.mayCare}</h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-[1fr_1fr_1.12fr_1fr_auto]">
            {interests.map(([Icon, question]) => (
              <button key={question} onClick={goToChat} className="flex min-h-[74px] items-center gap-4 rounded-2xl border border-[#dfe8f2] bg-white px-4 py-3 text-left shadow-sm transition-all hover:-translate-y-1 hover:border-[#00d4aa] hover:shadow-lg">
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[#e0fbf5] text-[#00a884]">
                  <Icon size={23} />
                </span>
                <span className="text-sm font-black leading-5 text-[#0b1d43]">{question}</span>
              </button>
            ))}
            <button onClick={goToChat} className="hidden h-[74px] w-[54px] items-center justify-center rounded-2xl border border-[#dfe8f2] bg-white text-[#0b1d43] shadow-sm md:flex">
              <ChevronRight size={22} />
            </button>
          </div>
        </section>

        <section className="landing-panel mx-auto grid max-w-[1380px] grid-cols-1 gap-5 lg:grid-cols-[1fr_1fr]">
          <div className="rounded-[28px] border border-white/86 bg-white/90 p-6 shadow-[0_22px_70px_rgba(0,88,110,.1)]">
            <div className="mb-5 flex items-center justify-between">
              <h2 className="text-2xl font-black tracking-[-0.025em] text-[#071638]">{t.recent}</h2>
              <button onClick={goToChat} className="flex items-center gap-2 text-sm font-black text-[#00a884]">
                {t.viewAll}
                <ChevronRight size={16} />
              </button>
            </div>
            <div className="space-y-2">
              {recentQuestions.map(([question, time]) => (
                <button key={question} onClick={goToChat} className="flex w-full items-center justify-between gap-3 rounded-xl border border-[#dfe8f2] bg-white px-4 py-2.5 text-left transition-all hover:border-[#00d4aa]">
                  <span className="flex min-w-0 items-center gap-3">
                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-[#e0fbf5] text-[#00a884]">
                      <MessageSquare size={15} />
                    </span>
                    <span className="truncate text-sm font-bold text-[#0b1d43]">{question}</span>
                  </span>
                  <span className="shrink-0 text-xs font-bold text-[#70809c]">{time}</span>
                </button>
              ))}
            </div>
          </div>

          <button onClick={goToChat} className="relative min-h-[240px] overflow-hidden rounded-[28px] border border-white/86 bg-white p-7 text-left shadow-[0_22px_70px_rgba(0,88,110,.1)] transition-all hover:-translate-y-1 hover:shadow-[0_30px_84px_rgba(0,168,132,.16)]">
            <img src="/cta_service.png" alt="" className="absolute inset-0 h-full w-full object-cover" />
            <div className="absolute inset-0 bg-gradient-to-r from-white via-white/86 to-white/8" />
            <div className="relative max-w-[310px]">
              <h2 className="text-3xl font-black leading-tight tracking-[-0.045em] text-[#071638]">{t.ctaTitle}</h2>
              <span className="mt-6 inline-flex items-center gap-2 rounded-full bg-[#00a884] px-5 py-3 text-sm font-black text-white shadow-[0_16px_34px_rgba(0,168,132,.3)]">
                {t.ctaButton}
                <ChevronRight size={17} />
              </span>
            </div>
          </button>
        </section>

        <section className="landing-panel mx-auto grid max-w-[1380px] grid-cols-1 gap-4 rounded-[26px] border border-[#c8f6ec] bg-[#e9fffa] p-5 shadow-[0_20px_60px_rgba(0,88,110,.08)] md:grid-cols-4 md:items-center md:p-6">
          {[
            [LockKeyhole, t.securityTitle, t.securitySub],
            [ShieldCheck, 'ISO 27001', 'Certified'],
            [ShieldCheck, 'GDPR', 'Compliant'],
            [ShieldCheck, 'SOC 2', 'Type II'],
          ].map(([Icon, title, desc]) => (
            <div key={title} className="flex items-center gap-4">
              <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-white text-[#00a884] shadow-sm">
                <Icon size={24} />
              </span>
              <div>
                <div className="text-base font-black text-[#071638]">{title}</div>
                <div className="text-sm font-semibold text-[#52617b]">{desc}</div>
              </div>
            </div>
          ))}
        </section>
      </div>
    </main>
  );
}
