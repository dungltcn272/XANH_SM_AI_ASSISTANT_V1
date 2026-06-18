import { useState } from 'react';
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
  Zap,
} from 'lucide-react';

const t = {
  powered: 'AI-powered',
  titleA: 'Xanh SM',
  titleB: 'AI Assistant',
  hero: 'Tr\u1ee3 l\u00fd AI th\u00f4ng minh gi\u00fap b\u1ea1n t\u00ecm hi\u1ec3u m\u1ecdi th\u00f4ng tin v\u1ec1 d\u1ecbch v\u1ee5, xe \u0111i\u1ec7n, gi\u00e1 c\u01b0\u1edbc, \u01b0u \u0111\u00e3i v\u00e0 v\u1eadn h\u00e0nh c\u1ee7a Xanh SM.',
  smart: 'Th\u00f4ng minh',
  fast: 'Nhanh ch\u00f3ng',
  accurate: 'Ch\u00ednh x\u00e1c',
  secure: 'B\u1ea3o m\u1eadt',
  ask: 'H\u1ecfi t\u00f4i b\u1ea5t k\u1ef3 \u0111i\u1ec1u g\u00ec v\u1ec1 Xanh SM...',
  service: 'D\u1ecbch v\u1ee5',
  pricing: 'Gi\u00e1 c\u01b0\u1edbc',
  vehicle: 'Xe \u0111i\u1ec7n',
  news: 'Tin t\u1ee9c',
  promo: '\u01afu \u0111\u00e3i',
  food: 'Food AI',
  analytics: 'Analytics',
  discover: 'Kh\u00e1m ph\u00e1 kh\u1ea3 n\u0103ng c\u1ee7a AI Assistant',
  allFeatures: 'T\u1ea5t c\u1ea3 t\u00ednh n\u0103ng',
  mayCare: 'B\u1ea1n c\u00f3 th\u1ec3 quan t\u00e2m',
  recent: 'C\u00e2u h\u1ecfi g\u1ea7n \u0111\u00e2y',
  viewAll: 'Xem t\u1ea5t c\u1ea3',
  ctaTitle: 'Tr\u1ea3i nghi\u1ec7m d\u1ecbch v\u1ee5 xanh th\u00f4ng minh c\u00f9ng Xanh SM',
  ctaButton: 'T\u00ecm hi\u1ec3u ngay',
  securityTitle: 'B\u1ea3o m\u1eadt d\u1eef li\u1ec7u tuy\u1ec7t \u0111\u1ed1i',
  securitySub: 'D\u1eef li\u1ec7u c\u1ee7a b\u1ea1n \u0111\u01b0\u1ee3c m\u00e3 h\u00f3a v\u00e0 b\u1ea3o v\u1ec7 theo ti\u00eau chu\u1ea9n qu\u1ed1c t\u1ebf',
};

const orbitItems = [
  { label: t.pricing, icon: Tag, x: 24, y: -230, rotate: -8, color: 'text-amber-500' },
  { label: t.vehicle, icon: Car, x: 232, y: -124, rotate: 7, color: 'text-emerald-500' },
  { label: t.news, icon: Newspaper, x: 266, y: 34, rotate: -5, color: 'text-violet-500' },
  { label: t.analytics, icon: BarChart2, x: 160, y: 184, rotate: 9, color: 'text-blue-500' },
  { label: t.food, icon: Utensils, x: -42, y: 226, rotate: -7, color: 'text-orange-500' },
  { label: t.promo, icon: Gift, x: -230, y: 80, rotate: 6, color: 'text-red-500' },
  { label: t.service, icon: Car, x: -210, y: -104, rotate: -10, color: 'text-teal-500' },
];

const capabilityCards = [
  {
    title: 'Knowledge Search',
    desc: 'T\u00ecm ki\u1ebfm v\u00e0 tra c\u1ee9u trong to\u00e0n b\u1ed9 kho tri th\u1ee9c',
    image: '/knowledge_search.png',
  },
  {
    title: 'Deep Research',
    desc: 'Nghi\u00ean c\u1ee9u chuy\u00ean s\u00e2u v\u00e0 truy xu\u1ea5t \u0111a ngu\u1ed3n',
    image: '/deep_research.png',
  },
  {
    title: 'Vehicle Expert',
    desc: 'H\u1ecfi \u0111\u00e1p chi ti\u1ebft v\u1ec1 VF3, VF5, VF6, VF8...',
    image: '/vehicle_expert.png',
  },
  {
    title: 'Pricing Assistant',
    desc: 'T\u00ednh gi\u00e1 c\u01b0\u1edbc, xem ch\u00ednh s\u00e1ch v\u00e0 \u01b0u \u0111\u00e3i hi\u1ec7n h\u00e0nh',
    image: '/pricing_assistant.png',
  },
  {
    title: 'News Digest',
    desc: 'T\u1ed5ng h\u1ee3p tin t\u1ee9c m\u1edbi nh\u1ea5t v\u1ec1 Xanh SM v\u00e0 th\u1ecb tr\u01b0\u1eddng',
    image: '/news_digest.png',
  },
  {
    title: 'Food Recommendation',
    desc: 'G\u1ee3i \u00fd m\u00f3n ngon, \u0111\u1ecba \u0111i\u1ec3m \u0103n u\u1ed1ng ph\u00f9 h\u1ee3p v\u1edbi b\u1ea1n',
    image: '/food_recommendation.png',
  },
  {
    title: 'Policy & Support',
    desc: 'Ch\u00ednh s\u00e1ch, \u0111i\u1ec1u kho\u1ea3n v\u00e0 h\u1ed7 tr\u1ee3 kh\u00e1ch h\u00e0ng',
    image: '/policy_support.png',
  },
  {
    title: 'Data Analytics',
    desc: 'Th\u1ed1ng k\u00ea, b\u00e1o c\u00e1o v\u00e0 insight th\u00f4ng minh',
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
  [Car, 'Gi\u00e1 c\u01b0\u1edbc t\u1eeb s\u00e2n bay N\u1ed9i B\u00e0i \u0111\u1ebfn H\u00e0 N\u1ed9i?'],
  [Car, 'Xe VF6 c\u00f3 nh\u1eefng m\u00e0u n\u00e0o?'],
  [ShieldCheck, 'Ch\u00ednh s\u00e1ch b\u1ea3o h\u00e0nh pin xe VF5 nh\u01b0 th\u1ebf n\u00e0o?'],
  [Gift, '\u01afu \u0111\u00e3i hi\u1ec7n t\u1ea1i cho kh\u00e1ch h\u00e0ng m\u1edbi?'],
];

const recentQuestions = [
  ['Gi\u00e1 c\u01b0\u1edbc t\u1eeb s\u00e2n bay N\u1ed9i B\u00e0i \u0111\u1ebfn H\u00e0 N\u1ed9i?', '2 ph\u00fat tr\u01b0\u1edbc'],
  ['Ch\u00ednh s\u00e1ch b\u1ea3o h\u00e0nh pin xe VF5 nh\u01b0 th\u1ebf n\u00e0o?', '15 ph\u00fat tr\u01b0\u1edbc'],
  ['Tin t\u1ee9c m\u1edbi nh\u1ea5t v\u1ec1 Xanh SM?', '1 gi\u1edd tr\u01b0\u1edbc'],
  ['G\u1ee3i \u00fd qu\u00e1n \u0103n ngon g\u1ea7n \u0111\u00e2y?', '2 gi\u1edd tr\u01b0\u1edbc'],
  ['\u01afu \u0111\u00e3i hi\u1ec7n t\u1ea1i cho kh\u00e1ch h\u00e0ng m\u1edbi?', '3 gi\u1edd tr\u01b0\u1edbc'],
];

export default function LandingPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [isLeaving, setIsLeaving] = useState(false);
  const isAuthenticatedUser = user?.type === 'user';
  const displayName = isAuthenticatedUser ? (user.name || user.email || 'User') : 'Guest';
  const avatarUrl = isAuthenticatedUser ? user.avatar_url : null;
  const avatarInitial = (displayName || 'Guest').trim().charAt(0).toUpperCase() || 'G';

  const goToChat = () => {
    setIsLeaving(true);
    window.setTimeout(() => navigate('/chat'), 360);
  };

  return (
    <main className="min-h-screen overflow-x-hidden bg-[#effdfa] text-[#071638] [font-family:'Outfit','Inter',system-ui,sans-serif]">
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
          from { opacity: 0; transform: translateY(72px) scale(.975); }
          to { opacity: 1; transform: translateY(0) scale(1); }
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
        @supports not (animation-timeline: view()) {
          .hero-exit { animation: none; }
          .reveal-pro { animation-timeline: auto; animation-range: normal; }
        }
      `}</style>

      {isLeaving && (
        <div className="page-leave fixed inset-0 z-[999] bg-[#effdfa]/92 backdrop-blur-xl">
          <div className="absolute left-1/2 top-1/2 h-16 w-16 -translate-x-1/2 -translate-y-1/2 rounded-full border-4 border-[#00d4aa]/25 border-t-[#00a884]" />
        </div>
      )}

      <div className="fixed inset-0 z-0 bg-[url('/bg_landing.png')] bg-cover bg-center bg-no-repeat" />

      <section className="relative z-10 min-h-[940px] overflow-hidden">
        <div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(255,255,255,.56)_0%,rgba(255,255,255,.22)_45%,rgba(255,255,255,.05)_100%)]" />
        <span className="spark-dot absolute right-[13%] top-[12%] h-2 w-2 rounded-full bg-white shadow-[0_0_24px_8px_rgba(255,255,255,.9)]" />
        <span className="spark-dot absolute right-[35%] top-[23%] h-1.5 w-1.5 rounded-full bg-white shadow-[0_0_18px_7px_rgba(255,255,255,.85)]" style={{ animationDelay: '1.2s' }} />

        <header className="relative z-30 mx-auto flex h-[92px] max-w-[1460px] items-center justify-between px-4 md:px-5">
          <button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} className="flex items-center gap-3">
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

        <div className="relative z-20 mx-auto grid max-w-[1460px] grid-cols-1 items-start gap-2 px-4 pt-6 md:px-5 lg:grid-cols-[0.86fr_1.14fr]">
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
            <div className="orbit-pulse absolute left-[54%] top-[37%] h-[520px] w-[520px] rounded-full border border-white/60 bg-white/8 shadow-[inset_0_0_55px_rgba(255,255,255,.62)] backdrop-blur-[1px]" />
            <div className="orbit-pulse absolute left-[54%] top-[37%] h-[360px] w-[360px] rounded-full border-[18px] border-[#6cebd8]/42 bg-[#00d4aa]/12 shadow-[0_0_120px_rgba(0,212,170,.34)] backdrop-blur-[2px]" style={{ animationDelay: '.35s' }} />

            {orbitItems.map((item, index) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.label}
                  className="absolute left-[54%] top-[37%] z-20"
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

            <div className="absolute left-[54%] top-[37%] z-10 flex h-[365px] w-[365px] -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-white/10 backdrop-blur-[2px]">
              <img src="/Bot.png" alt="Xanh SM AI Assistant" className="float-soft h-full w-full object-contain drop-shadow-[0_36px_50px_rgba(0,89,105,.3)]" />
            </div>
          </div>
        </div>
      </section>

      <div className="relative z-30 -mt-[250px] space-y-5 px-4 pb-8 md:px-5">
        <section id="capabilities" className="reveal-pro mx-auto max-w-[1380px] rounded-[30px] border border-white/86 bg-white/88 p-6 shadow-[0_26px_84px_rgba(0,88,110,.12)] md:p-7">
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

        <section className="reveal-pro mx-auto max-w-[1380px] rounded-[34px] border border-white/90 bg-white/92 p-5 shadow-[0_24px_74px_rgba(0,88,110,.11)]">
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
                      {stat.up ? '\u2191' : '\u2193'} {stat.delta}
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

        <section className="reveal-pro mx-auto max-w-[1380px] rounded-[28px] border border-white/86 bg-white/88 p-5 shadow-[0_22px_70px_rgba(0,88,110,.1)] md:p-6">
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

        <section className="reveal-pro mx-auto grid max-w-[1380px] grid-cols-1 gap-5 lg:grid-cols-[1fr_1fr]">
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

        <section className="reveal-pro mx-auto grid max-w-[1380px] grid-cols-1 gap-4 rounded-[26px] border border-[#c8f6ec] bg-[#e9fffa] p-5 shadow-[0_20px_60px_rgba(0,88,110,.08)] md:grid-cols-4 md:items-center md:p-6">
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
