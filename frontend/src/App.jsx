import { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { api } from './api';
import ChatLayout from './components/ChatLayout';
import AdminLayout from './components/AdminLayout';
import NotificationDropdown from './components/NotificationDropdown';
import CommandCenter from './pages/CommandCenter';
import AIEvalLab from './pages/AIEvalLab';
import HistoryDashboard from './pages/HistoryDashboard';
import DatabaseManager from './pages/DatabaseManager';
import KnowledgeBuilder from './pages/KnowledgeBuilder';
import UserReviews from './pages/UserReviews';
import AdminNotifications from './pages/AdminNotifications';
import MLControlCenter from './pages/MLControlCenter';
import AdminLogin from './pages/AdminLogin';
import LandingPage from './pages/LandingPage';
import { Moon, Sun, LogOut, Plus, User, HelpCircle, X, Menu, ChevronLeft, ChevronRight, MoreHorizontal, Bell, ChevronDown, MessageSquare, Search } from 'lucide-react';
import { GoogleLogin } from '@react-oauth/google';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8 text-on-surface-variant animate-pulse font-semibold">Loading authorization state...</div>;
  if (!user || user.type === 'guest') return <Navigate to="/" replace />;
  return children;
}

const getGroupedConversations = (conversations) => {
  const groups = {
    today: [],
    yesterday: [],
    thisWeek: [],
    thisMonth: [],
    older: []
  };

  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  
  const startOfYesterday = new Date(startOfToday);
  startOfYesterday.setDate(startOfYesterday.getDate() - 1);
  
  const startOfThisWeek = new Date(startOfToday);
  startOfThisWeek.setDate(startOfThisWeek.getDate() - startOfToday.getDay());
  
  const startOfThisMonth = new Date(now.getFullYear(), now.getMonth(), 1);

  conversations.forEach(conv => {
    if (!conv.created_at) return;
    const date = new Date(conv.created_at);
    if (date >= startOfToday) {
      groups.today.push(conv);
    } else if (date >= startOfYesterday) {
      groups.yesterday.push(conv);
    } else if (date >= startOfThisWeek) {
      groups.thisWeek.push(conv);
    } else if (date >= startOfThisMonth) {
      groups.thisMonth.push(conv);
    } else {
      groups.older.push(conv);
    }
  });

  return [
    { label: 'Hôm nay', data: groups.today },
    { label: 'Hôm qua', data: groups.yesterday },
    { label: 'Tuần này', data: groups.thisWeek },
    { label: 'Tháng này', data: groups.thisMonth },
    { label: 'Trước đó', data: groups.older }
  ].filter(g => g.data.length > 0);
};

function SidebarContent({ user, conversations, activeConversationId, theme, toggleTheme, handleLogout, navigate, onClose, onCollapseToggle }) {
  const grouped = getGroupedConversations(conversations);

  return (
    <>
      <div className="flex items-center justify-between mb-6 shrink-0">
        <div 
          className="flex flex-col gap-1 items-start cursor-pointer hover:opacity-85 transition-opacity" 
          onClick={() => {
            navigate('/');
            onClose?.();
          }}
        >
          <img 
            src="/logo.svg" 
            alt="Xanh SM Logo" 
            className="h-8 w-auto object-contain dark:brightness-110"
          />
          <div className="text-[10px] font-bold text-on-surface-variant/50 uppercase tracking-widest mt-1">
            {user?.type === 'user' ? user.name : 'Guest Session'}
          </div>
        </div>
        
        {onCollapseToggle && (
          <button 
            onClick={onCollapseToggle}
            className="p-1.5 rounded-full hover:bg-surface-variant text-on-surface-variant shadow-xs border border-outline-variant/20 hidden md:flex items-center justify-center bg-white/40 dark:bg-transparent transition-all active:scale-95"
            title="Thu gọn thanh bên"
          >
            <ChevronLeft size={16} />
          </button>
        )}
      </div>

      <button 
        onClick={() => {
          navigate('/chat');
          window.dispatchEvent(new Event('refresh-conversations'));
          onClose?.();
        }} 
        className="flex items-center justify-center gap-2 py-3 px-4 rounded-full bg-gradient-to-r from-[#00c897] to-[#00a67d] hover:from-[#00b084] hover:to-[#009570] text-white font-bold shadow-[0_4px_15px_rgba(0,200,151,0.3)] hover:shadow-[0_6px_20px_rgba(0,200,151,0.45)] transition-all active:scale-95 text-xs w-full mb-6 shrink-0"
      >
        <Plus size={16} />
        Đoạn chat mới
      </button>

      {/* Chat History Header */}
      {user?.type === 'user' && conversations.length > 0 && (
        <div className="flex items-center justify-between mb-4 px-2.5 shrink-0">
          <span className="text-sm font-bold text-on-surface-variant/80">Lịch sử trò chuyện</span>
          <button className="p-1 rounded-full hover:bg-surface-variant text-on-surface-variant/60 hover:text-[#00c897] transition-all">
            <Search size={15} />
          </button>
        </div>
      )}

      <div className="flex-grow overflow-y-auto no-scrollbar">
        {user?.type === 'user' && (
          <div className="mt-1">
            {grouped.length === 0 && (
              <div className="text-xs text-on-surface-variant/50 italic p-2.5">Lịch sử trò chuyện trống</div>
            )}
            
            {grouped.map(group => (
              <div key={group.label} className="mb-4">
                <span className="text-[11px] font-bold text-on-surface-variant/50 block mb-1.5 px-2.5">
                  {group.label}
                </span>
                <div className="flex flex-col gap-1">
                  {group.data.map(conv => (
                    <div 
                      key={conv.id}
                      className="relative group/item"
                    >
                      <button 
                        className={`flex items-center gap-2.5 py-2 px-2.5 rounded-xl w-full text-left transition-all text-xs pr-8 ${activeConversationId === conv.id ? 'bg-[#00c897]/8 text-[#00c897] font-semibold border-l-2 border-[#00c897] rounded-l-none' : 'text-on-surface-variant/85 hover:bg-surface-variant/50 hover:text-[#00c897]'}`} 
                        onClick={() => {
                          navigate(`/chat?c=${conv.id}`);
                          onClose?.();
                        }}
                      >
                        <MessageSquare size={14} className={`shrink-0 transition-opacity ${activeConversationId === conv.id ? 'opacity-100 text-[#00c897]' : 'opacity-50 group-hover/item:opacity-90'}`} />
                        <span className="whitespace-nowrap overflow-hidden text-ellipsis">
                          {conv.title || 'New Conversation'}
                        </span>
                      </button>
                      
                      <button 
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-surface-variant text-on-surface-variant/65 opacity-0 group-hover/item:opacity-100 transition-opacity flex items-center justify-center"
                        onClick={(e) => {
                          e.stopPropagation();
                          // Show menu placeholder (no-op or simple delete later)
                        }}
                      >
                        <MoreHorizontal size={14} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="mt-auto pt-4 border-t border-outline-variant/30 flex flex-col gap-2 shrink-0">
        <div className="flex items-center justify-between p-2.5 rounded-xl hover:bg-surface-variant/40 transition-all">
          <div className="flex items-center gap-3 text-on-surface-variant font-medium text-xs">
            {theme === 'light' ? <Moon size={16} /> : <Sun size={16} />}
            <span>Dark mode</span>
          </div>
          <button 
            onClick={toggleTheme}
            className={`w-9 h-5 rounded-full p-0.5 transition-colors duration-200 focus:outline-none flex items-center ${theme === 'dark' ? 'bg-[#00c897]' : 'bg-slate-300 dark:bg-outline-variant/60'}`}
          >
            <div className={`w-4 h-4 rounded-full bg-white shadow-sm transition-transform duration-200 transform ${theme === 'dark' ? 'translate-x-4' : 'translate-x-0'}`} />
          </button>
        </div>

        <button 
          className="flex items-center gap-3 p-2.5 rounded-xl w-full text-left transition-all bg-error/10 text-error hover:bg-error hover:text-white font-medium shadow-xs text-xs" 
          onClick={() => {
            handleLogout();
            onClose?.();
          }}
        >
          <LogOut size={16} />
          Đăng xuất
        </button>
      </div>
    </>
  );
}

function MainLayout({ children }) {
  const { user, logout, loginWithGoogle } = useAuth();
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light');
  const [conversations, setConversations] = useState([]);
  const [showTopicsDialog, setShowTopicsDialog] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const activeConversationId = searchParams.get('c');
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [notificationUnreadCount, setNotificationUnreadCount] = useState(0);
  const [notificationsLoading, setNotificationsLoading] = useState(false);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  useEffect(() => {
    const fetchConvs = () => {
      if (user?.type === 'user') {
        api.getConversations().then(setConversations).catch(console.error);
      } else {
        setConversations([]);
      }
    };
    
    fetchConvs();
    
    window.addEventListener('refresh-conversations', fetchConvs);
    return () => {
      window.removeEventListener('refresh-conversations', fetchConvs);
    };
  }, [user]);

  const refreshNotifications = () => {
    if (user?.type !== 'user') {
      setNotifications([]);
      setNotificationUnreadCount(0);
      return;
    }
    setNotificationsLoading(true);
    api.getNotifications()
      .then((data) => {
        setNotifications(data.items || []);
        setNotificationUnreadCount(data.unread_count || 0);
      })
      .catch(console.error)
      .finally(() => setNotificationsLoading(false));
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refreshNotifications();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const handleMarkNotificationRead = async (id) => {
    setNotifications(prev => prev.map(item => item.id === id ? { ...item, is_read: true } : item));
    setNotificationUnreadCount(prev => Math.max(0, prev - 1));
    try {
      await api.markNotificationRead(id);
      refreshNotifications();
    } catch (error) {
      console.error(error);
      refreshNotifications();
    }
  };

  const handleMarkAllNotificationsRead = async () => {
    if (!notificationUnreadCount) return;
    setNotifications(prev => prev.map(item => ({ ...item, is_read: true })));
    setNotificationUnreadCount(0);
    try {
      await api.markAllNotificationsRead();
      refreshNotifications();
    } catch (error) {
      console.error(error);
      refreshNotifications();
    }
  };

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
    if (newTheme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const isAdmin = location.pathname.startsWith('/admin');

  return (
    <div className="flex h-screen w-full bg-[#f2f7f8] dark:bg-[#091118] text-on-surface relative overflow-hidden transition-colors duration-200">
      {/* Background Image decoration based on theme */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none z-0 select-none">
        <img 
          src={theme === 'light' ? '/bg_light.jpeg' : '/bg_dark.jpeg'} 
          alt="background" 
          className="w-full h-full object-cover opacity-100 transition-all duration-300"
        />
      </div>
      {/* Sidebar for Guest/User Chat */}
      {!isAdmin && (
        <>
          {/* Desktop Sidebar */}
          <div className={`bg-surface-container-lowest/60 backdrop-blur-xl border-r border-outline-variant/30 flex flex-col p-6 z-10 shadow-lg shrink-0 hidden md:flex transition-all duration-300 ${isSidebarCollapsed ? 'w-0 min-w-0 overflow-hidden p-0 border-r-0 opacity-0' : 'w-72'}`}>
            <SidebarContent 
              user={user}
              conversations={conversations}
              activeConversationId={activeConversationId}
              theme={theme}
              toggleTheme={toggleTheme}
              handleLogout={handleLogout}
              navigate={navigate}
              onCollapseToggle={() => setIsSidebarCollapsed(true)}
            />
          </div>

          {/* Mobile Sidebar (Drawer) */}
          <div className={`fixed inset-0 z-[100] md:hidden transition-all duration-300 ${isMobileSidebarOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}>
            {/* Backdrop */}
            <div className="absolute inset-0 bg-black/50 backdrop-blur-xs" onClick={() => setIsMobileSidebarOpen(false)} />
            
            {/* Drawer Content */}
            <div className={`absolute top-0 bottom-0 left-0 w-72 bg-surface flex flex-col p-6 z-[101] shadow-2xl transition-transform duration-300 transform ${isMobileSidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
              <SidebarContent 
                user={user}
                conversations={conversations}
                activeConversationId={activeConversationId}
                theme={theme}
                toggleTheme={toggleTheme}
                handleLogout={handleLogout}
                navigate={navigate}
                onClose={() => setIsMobileSidebarOpen(false)}
                onCollapseToggle={null}
              />
            </div>
          </div>
        </>
      )}

      {/* Main Content */}
      <div className={`flex-1 flex flex-col relative overflow-hidden ${isAdmin ? 'w-full' : ''}`}>
        {!isAdmin && (
          <header className="mx-4 md:mx-8 mt-4 mb-2 py-2.5 px-4 md:px-6 flex items-center justify-between bg-white/88 dark:bg-[#081217]/88 backdrop-blur-xl rounded-3xl border border-white/30 dark:border-cyan-500/10 z-20 shrink-0 shadow-[0_8px_30px_rgba(0,0,0,0.04)] dark:shadow-[0_8px_30px_rgba(0,0,0,0.25)] transition-all duration-200">
            <div className="flex items-center gap-3">
              {/* Hamburger Menu on Mobile */}
              <button 
                onClick={() => setIsMobileSidebarOpen(true)}
                className="p-1.5 rounded-full hover:bg-surface-variant text-on-surface-variant md:hidden flex items-center justify-center mr-1 border border-white/20 dark:border-white/10 shadow-sm bg-white/50 dark:bg-white/10 backdrop-blur-md transition-all"
                title="Mở lịch sử chat"
              >
                <Menu size={18} />
              </button>
              
              {/* Expand Sidebar Button on Desktop */}
              {isSidebarCollapsed && (
                <button 
                  onClick={() => setIsSidebarCollapsed(false)}
                  className="p-1.5 rounded-full hover:bg-surface-variant text-on-surface-variant shadow-xs border border-white/20 dark:border-white/10 hidden md:flex items-center justify-center mr-2 bg-white/50 dark:bg-white/10 backdrop-blur-md transition-all active:scale-95"
                  title="Mở rộng thanh bên"
                >
                  <ChevronRight size={18} />
                </button>
              )}

              {/* Status Badge - Floating & Stacked Layout */}
              <div className="flex items-center gap-3 select-none ml-2">
                {/* Green Dot Indicator */}
                <div className="w-2.5 h-2.5 rounded-full bg-[#00c897] shadow-[0_0_8px_#00c897] animate-pulse shrink-0" />
                
                <div className="flex flex-col text-left">
                  <div className="flex items-center gap-1">
                    <span className="font-extrabold text-sm text-on-surface tracking-wide leading-none">AI Online</span>
                    {/* Tiny Check Shield Icon */}
                    <svg className="w-3.5 h-3.5 text-[#00c897] shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                      <path d="m9 11 2 2 4-4"/>
                    </svg>
                  </div>
                  <span className="text-[10px] text-on-surface-variant/30 font-medium mt-0.5 italic">Dữ liệu cập nhật 20/06/2026</span>
                </div>
              </div>
            </div>
            
            {/* Right side: Login/Logout button & Avatar & Bell */}
            <div className="flex items-center gap-3">
              {/* Notification Bell */}
              {user?.type === 'user' && (
                <div className="">
                  <button 
                    id="notification-bell-button"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      setShowNotifications(prev => !prev);
                    }}
                    className={`p-2 rounded-full hover:bg-surface-variant text-on-surface-variant relative flex items-center justify-center border border-white/20 dark:border-white/10 shadow-xs bg-white/40 dark:bg-white/10 backdrop-blur-md transition-all ${showNotifications ? 'bg-surface-variant text-[#00c897]' : ''}`}
                  >
                    <Bell size={16} />
                    {notificationUnreadCount > 0 && (
                      <span className="absolute top-0.5 right-0.5 min-w-3.5 h-3.5 px-1 bg-red-500 rounded-full text-[8px] font-extrabold text-white flex items-center justify-center border border-surface scale-90">
                        {notificationUnreadCount > 9 ? '9+' : notificationUnreadCount}
                      </span>
                    )}
                  </button>
                </div>
              )}

              {user?.type === 'user' ? (
                <div className="relative">
                  <button 
                    onClick={() => setShowUserMenu(!showUserMenu)}
                    className="flex items-center gap-2 p-1.5 pr-3 rounded-full hover:bg-surface-variant/50 border border-white/20 dark:border-white/10 shadow-sm transition-all bg-white/40 dark:bg-white/10 backdrop-blur-md"
                  >
                    <div className="w-8 h-8 rounded-full bg-[#00c897] flex items-center justify-center text-white text-xs font-extrabold shadow-md uppercase border border-primary/10">
                      {user.name ? user.name[0] : <User size={14} />}
                    </div>
                    <span className="text-xs font-bold text-on-surface md:block hidden select-none">{user.name || 'Lương Tiến Dũng'}</span>
                    <ChevronDown size={14} className="text-on-surface-variant" />
                  </button>
                  
                  {showUserMenu && (
                    <>
                      <div className="fixed inset-0 z-[105]" onClick={() => setShowUserMenu(false)} />
                      <div className="absolute right-0 mt-2 w-48 bg-surface-container-lowest border border-outline-variant/30 rounded-2xl shadow-xl py-1 z-[110] animate-in fade-in slide-in-from-top-1 duration-150 text-on-surface">
                        <div className="px-4 py-2.5 border-b border-outline-variant/20">
                          <p className="text-[10px] font-semibold text-on-surface-variant uppercase tracking-wider">Tài khoản</p>
                          <p className="text-xs font-bold truncate mt-0.5">{user.email}</p>
                        </div>
                        <button 
                          onClick={() => {
                            setShowTopicsDialog(true);
                            setShowUserMenu(false);
                          }}
                          className="w-full text-left px-4 py-2 text-xs font-semibold hover:bg-surface-variant flex items-center gap-2 transition-colors"
                        >
                          <HelpCircle size={14} /> Danh mục hỗ trợ
                        </button>
                        <button 
                          onClick={() => {
                            handleLogout();
                            setShowUserMenu(false);
                          }}
                          className="w-full text-left px-4 py-2.5 text-xs font-bold text-error hover:bg-error/10 flex items-center gap-2 transition-colors border-t border-outline-variant/10"
                        >
                          <LogOut size={14} /> Đăng xuất
                        </button>
                      </div>
                    </>
                  )}
                </div>
              ) : (
                <div className="flex items-center gap-3">
                  {GOOGLE_CLIENT_ID ? (
                    <GoogleLogin
                      onSuccess={async (credentialResponse) => {
                        const success = await loginWithGoogle(credentialResponse.credential);
                        if (success) {
                          api.getConversations().then(setConversations).catch(console.error);
                        }
                      }}
                      onError={() => console.error('Đăng nhập Google thất bại')}
                      shape="pill"
                      theme={theme === 'dark' ? 'filled_blue' : 'outline'}
                      size="medium"
                      text="signin_with"
                    />
                  ) : null}
                </div>
              )}
            </div>
          </header>
        )}
        
        {children}

        {/* Topics Dialog Modal */}
        {showTopicsDialog && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[150] p-4">
            <div className="bg-surface-container-lowest border border-outline-variant/30 rounded-3xl w-full max-w-4xl shadow-2xl overflow-hidden max-h-[85vh] flex flex-col text-on-surface transition-all duration-200">
              {/* Header */}
              <div className="p-6 border-b border-outline-variant/20 flex items-center justify-between bg-surface-container-low shrink-0">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
                    <HelpCircle size={24} />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-on-surface">Danh mục Chủ đề Hỗ trợ</h2>
                    <p className="text-xs text-on-surface-variant mt-0.5">Tìm hiểu các chủ đề kiến thức Xanh SM AI có thể giải đáp</p>
                  </div>
                </div>
                <button 
                  onClick={() => setShowTopicsDialog(false)}
                  className="p-2 rounded-full hover:bg-surface-variant text-on-surface-variant hover:text-on-surface transition-all"
                >
                  <X size={20} />
                </button>
              </div>

              {/* Body */}
              <div className="p-6 overflow-y-auto max-h-[60vh] custom-scrollbar space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  
                  {/* Car/Bike Column */}
                  <div className="glass-panel p-5 rounded-2xl border border-outline-variant/20 space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">🚗</span>
                      <h3 className="font-bold text-primary text-base">Dịch vụ Di chuyển</h3>
                    </div>
                    <ul className="text-sm space-y-2 text-on-surface-variant list-disc pl-4">
                      <li><strong>Xanh SM Taxi:</strong> Giá cước xe điện (Green SM Car) theo từng tỉnh/thành phố.</li>
                      <li><strong>Xanh SM Luxury (Premium):</strong> Dịch vụ taxi tiện nghi vượt trội (Green SM Premium).</li>
                      <li><strong>Xanh SM Limo:</strong> Dịch vụ xe đẳng cấp cao cấp (Green SM Limo).</li>
                      <li><strong>Xanh SM Bike:</strong> Cước phí xe máy điện (Green SM Bike) khởi hành và tiếp theo.</li>
                      <li><strong>Xanh SM Mini:</strong> Dịch vụ xe điện cỡ nhỏ (Green SM Mini) nội đô.</li>
                      <li><strong>Xanh Sân Bay / Liên tỉnh:</strong> Di chuyển ngoại tỉnh và trọn gói sân bay.</li>
                      <li><strong>Green Tour:</strong> Thuê xe điện tự lái hoặc kèm tài xế theo gói.</li>
                    </ul>
                  </div>

                  {/* Express/Food Column */}
                  <div className="glass-panel p-5 rounded-2xl border border-outline-variant/20 space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">📦</span>
                      <h3 className="font-bold text-primary text-base">Giao hàng & Đồ ăn</h3>
                    </div>
                    <ul className="text-sm space-y-2 text-on-surface-variant list-disc pl-4">
                      <li><strong>Xanh Express:</strong> Giao hàng siêu tốc bằng xe máy điện.</li>
                      <li><strong>Xanh SM Van:</strong> Vận chuyển hàng cồng kềnh, dễ vỡ bằng xe Van điện (tải trọng tới 580kg).</li>
                      <li><strong>Xanh Food (GreenSM Ngon):</strong> Đặt món, thời gian giao hàng và các nhà hàng đối tác.</li>
                      <li><strong>Phụ phí & Quy định:</strong> Phụ phí ban đêm, thời tiết cực đoan, ngày lễ tết, phí nền tảng.</li>
                    </ul>
                  </div>

                  {/* Gift Card/Sub Column */}
                  <div className="glass-panel p-5 rounded-2xl border border-outline-variant/20 space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">💳</span>
                      <h3 className="font-bold text-primary text-base">Thẻ Quà tặng & Hội viên</h3>
                    </div>
                    <ul className="text-sm space-y-2 text-on-surface-variant list-disc pl-4">
                      <li><strong>Green Gift Card:</strong> Thẻ quà tặng dạng vật lý (thẻ cứng) và e-card.</li>
                      <li><strong>Kích hoạt & Sử dụng:</strong> Cách nạp mã giftcard, nạp tiền vào thẻ Xanh điện tử.</li>
                      <li><strong>Xanh Hội Viên (Green Subscription):</strong> Đăng ký gói ưu đãi giảm giá theo tuần/tháng.</li>
                    </ul>
                  </div>

                  {/* Green Care Column */}
                  <div className="glass-panel p-5 rounded-2xl border border-outline-variant/20 space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">🛡️</span>
                      <h3 className="font-bold text-primary text-base">Bảo hiểm chuyến đi (Green Care)</h3>
                    </div>
                    <ul className="text-sm space-y-2 text-on-surface-variant list-disc pl-4">
                      <li><strong>Bảo hiểm Hành khách:</strong> Quyền lợi bảo hiểm tai nạn cá nhân tới 500 triệu đồng.</li>
                      <li><strong>Bảo hiểm Giao hàng:</strong> Hạn mức bồi thường mất mát, hư hỏng hàng hóa 100%.</li>
                      <li><strong>Bảo hiểm Đồ ăn:</strong> Chính sách bồi hoàn khi đồ ăn bị đổ vỡ, giao sai đơn.</li>
                    </ul>
                  </div>

                  {/* Driver Policy Column */}
                  <div className="glass-panel p-5 rounded-2xl border border-outline-variant/20 space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">👤</span>
                      <h3 className="font-bold text-primary text-base">Đối tác Tài xế</h3>
                    </div>
                    <ul className="text-sm space-y-2 text-on-surface-variant list-disc pl-4">
                      <li><strong>Đăng ký đối tác:</strong> Quy trình tuyển dụng tài xế Bike, Car và Platform.</li>
                      <li><strong>Chiết khấu doanh thu:</strong> Tỷ lệ ăn chia doanh số và mức thưởng chuyến.</li>
                      <li><strong>Quy chế & Chế tài:</strong> Quy định trang phục, tác phong phục vụ chuẩn 5 sao và xử phạt.</li>
                    </ul>
                  </div>

                  {/* Merchant Column */}
                  <div className="glass-panel p-5 rounded-2xl border border-outline-variant/20 space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">🏪</span>
                      <h3 className="font-bold text-primary text-base">Đối tác Cửa hàng (Merchant)</h3>
                    </div>
                    <ul className="text-sm space-y-2 text-on-surface-variant list-disc pl-4">
                      <li><strong>Đăng ký gian hàng:</strong> Thủ tục đối với cá nhân, hộ kinh doanh và công ty.</li>
                      <li><strong>Phí chiết khấu:</strong> Tỷ lệ phí dịch vụ linh hoạt cho đối tác nhà hàng.</li>
                      <li><strong>Chu kỳ đối soát:</strong> Quy trình thanh toán tiền hàng và báo cáo doanh thu.</li>
                    </ul>
                  </div>

                  {/* Green SM Platform Column */}
                  <div className="glass-panel p-5 rounded-2xl border border-outline-variant/20 space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">🌐</span>
                      <h3 className="font-bold text-primary text-base">Green SM Platform</h3>
                    </div>
                    <ul className="text-sm space-y-2 text-on-surface-variant list-disc pl-4">
                      <li><strong>Mua & Thuê xe điện:</strong> Chính sách mua xe VinFast trực tiếp qua Green SM và thuê vận hành các dòng xe Minio Green, VF 5 Plus, Herio Green, Limo Green.</li>
                      <li><strong>Chương trình ưu đãi sạc pin:</strong> Quyền lợi miễn phí/ưu đãi sạc pin tại trạm sạc V-GREEN cho xe vận doanh.</li>
                      <li><strong>Hỗ trợ tài chính:</strong> Chương trình "Mua xe 0 đồng" vay tới 100%, hỗ trợ lãi suất cố định 7%/năm, và ưu đãi thành viên VinClub.</li>
                      <li><strong>Chuyển đổi xe xăng sang xe điện:</strong> Hỗ trợ giảm thêm 3% MSRP khi chuyển đổi từ xe xăng sang xe điện chạy dịch vụ.</li>
                      <li><strong>Chính sách & Pháp lý:</strong> Điều khoản sử dụng chung, chính sách bảo mật dữ liệu và hợp đồng dịch vụ.</li>
                    </ul>
                  </div>

                </div>
                
                {/* Policies & Help Section */}
                <div className="glass-panel p-5 rounded-2xl border border-outline-variant/20 space-y-3">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">📑</span>
                    <h3 className="font-bold text-primary text-base">Quy trình Hướng dẫn & Hỗ trợ chung</h3>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-on-surface-variant">
                    <ul className="space-y-2 list-disc pl-4">
                      <li><strong>Cách đặt đơn:</strong> Hướng dẫn đặt chuyến xe di chuyển và giao nhận hàng trên App.</li>
                      <li><strong>Tính năng GreenNow:</strong> Kết nối trực tiếp với tài xế tại chỗ nhanh chóng.</li>
                      <li><strong>Báo cáo sự cố:</strong> Xử lý khi thông tin xe không khớp, lái xe ẩu hoặc thái độ khiếm nhã.</li>
                    </ul>
                    <ul className="space-y-2 list-disc pl-4">
                      <li><strong>Phí hủy chuyến:</strong> Quy định áp dụng khi khách hàng hoặc tài xế hủy chuyến.</li>
                      <li><strong>Chính sách hoàn tiền:</strong> Điều khoản bồi hoàn và thời gian hoàn tiền vào ví.</li>
                      <li><strong>Bảo mật thông tin:</strong> Quyền riêng tư đối với dữ liệu của khách hàng và đối tác.</li>
                    </ul>
                  </div>
                </div>

              </div>

              {/* Footer */}
              <div className="p-4 border-t border-outline-variant/20 bg-surface-container-low text-center text-xs text-on-surface-variant shrink-0">
                Hệ thống RAG thông minh tự động hỗ trợ giải đáp 24/7 kiến thức dịch vụ Xanh SM.
              </div>
            </div>
          </div>
        )}

        {/* Notification Dropdown moved to app root level for z-index safety */}
        <NotificationDropdown 
          isOpen={showNotifications} 
          onClose={() => setShowNotifications(false)} 
          notifications={notifications}
          unreadCount={notificationUnreadCount}
          loading={notificationsLoading}
          onMarkRead={handleMarkNotificationRead}
          onMarkAllRead={handleMarkAllNotificationsRead}
        />
      </div>
    </div>
  );
}
import PresentationFlow from './pages/PresentationFlow';
import SlideShow from './pages/SlideShow';
import TechPresentation from './pages/TechPresentation';

function App() {
  return (
    <Routes>
      {/* Login Route */}
      <Route path="/admin-login" element={<AdminLogin />} />

      {/* Presentation Routes */}
      <Route path="/presentation" element={<PresentationFlow />} />
      <Route path="/slide" element={<SlideShow />} />
      <Route path="/tech" element={<TechPresentation />} />

      {/* Landing Route */}
      <Route path="/" element={<LandingPage />} />

      {/* User Chat Route */}
      <Route path="/chat" element={
        <MainLayout>
          <ChatLayout />
        </MainLayout>
      } />
      
      {/* Admin Routes */}
      <Route path="/admin" element={
        <ProtectedRoute>
          <AdminLayout />
        </ProtectedRoute>
      }>
        <Route index element={<CommandCenter />} />
        <Route path="reviews" element={<UserReviews />} />
        <Route path="notifications" element={<AdminNotifications />} />
        <Route path="eval" element={<AIEvalLab />} />
        <Route path="ml" element={<MLControlCenter />} />
        <Route path="knowledge-builder" element={<KnowledgeBuilder />} />
        <Route path="history" element={<HistoryDashboard />} />
        <Route path="db" element={<DatabaseManager />} />
      </Route>
      
      {/* Redirect all other paths to home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
