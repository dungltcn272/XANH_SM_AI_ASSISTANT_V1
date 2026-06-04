import { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { api } from './api';
import ChatLayout from './components/ChatLayout';
import AdminLayout from './components/AdminLayout';
import CommandCenter from './pages/CommandCenter';
import AIEvalLab from './pages/AIEvalLab';
import PipelineManager from './pages/PipelineManager';
import RAGHistory from './pages/RAGHistory';
import IngestionManager from './pages/IngestionManager';
import DatabaseManager from './pages/DatabaseManager';
import AgentCrawler from './pages/AgentCrawler';
import { Moon, Sun, Monitor, Shield, MessageSquare, LogOut, History, Plus, User, HelpCircle, X } from 'lucide-react';
import { GoogleLogin } from '@react-oauth/google';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8 text-on-surface-variant animate-pulse font-semibold">Loading authorization state...</div>;
  if (!user || user.type === 'guest') return <Navigate to="/" replace />;
  return children;
}

function MainLayout({ children }) {
  const { user, logout, loginWithGoogle } = useAuth();
  const [theme, setTheme] = useState('light');
  const [conversations, setConversations] = useState([]);
  const [showTopicsDialog, setShowTopicsDialog] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const activeConversationId = searchParams.get('c');

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);
    document.documentElement.setAttribute('data-theme', savedTheme);
    if (savedTheme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, []);

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

  const isChat = location.pathname === '/';
  const isAdmin = location.pathname.startsWith('/admin');

  return (
    <div className="flex h-screen w-full bg-background font-sans text-on-surface">
      {/* Sidebar for Guest/User Chat */}
      {!isAdmin && (
        <div className="w-72 bg-surface-container-lowest/60 backdrop-blur-xl border-r border-outline-variant/30 flex flex-col p-6 z-10 shadow-lg shrink-0 hidden md:flex">
          <div 
            className="flex flex-col gap-1.5 mb-8 items-start cursor-pointer hover:opacity-85 transition-opacity" 
            onClick={() => {
              navigate('/');
              window.dispatchEvent(new Event('refresh-conversations'));
            }}
          >
            <img 
              src="/logo.svg" 
              alt="Xanh SM Logo" 
              className="h-8 w-auto object-contain"
            />
            <div className="text-xs font-semibold text-on-surface-variant uppercase tracking-widest mt-1">
              {user?.type === 'user' ? user.name : 'Guest Session'}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto pr-2 flex flex-col gap-2">

            {/* Chat History Section (Only for logged-in Users) */}
            {user?.type === 'user' && (
              <div className="mt-8">
                <div className="flex justify-between items-center mb-4">
                  <span className="text-xs font-bold tracking-wider text-on-surface-variant/70 uppercase">LỊCH SỬ CHAT</span>
                  <button 
                    onClick={() => {
                      navigate('/');
                      window.dispatchEvent(new Event('refresh-conversations'));
                    }} 
                    className="text-primary hover:bg-primary/10 p-1 rounded-full transition-colors"
                  >
                    <Plus size={16} />
                  </button>
                </div>
                <div className="flex flex-col gap-1">
                  {conversations.length === 0 && (
                    <div className="text-sm text-on-surface-variant/70 italic p-2">Chưa có cuộc trò chuyện nào.</div>
                  )}
                  {conversations.map(conv => (
                    <button 
                      key={conv.id} 
                      className={`flex items-center gap-3 p-3 rounded-xl w-full text-left transition-all text-sm ${activeConversationId === conv.id ? 'bg-primary/10 text-primary font-bold' : 'text-on-surface-variant hover:bg-surface-variant hover:text-primary'}`} 
                      onClick={() => navigate(`/?c=${conv.id}`)}
                    >
                      <History size={16} className="shrink-0" />
                      <span className="whitespace-nowrap overflow-hidden text-ellipsis">
                        {conv.title || 'New Conversation'}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Bottom Actions */}
          <div className="mt-auto pt-4 border-t border-outline-variant/30 flex flex-col gap-2">
            <button className="flex items-center gap-3 p-3 rounded-xl w-full text-left transition-all text-on-surface-variant hover:bg-surface-variant hover:text-primary font-medium" onClick={toggleTheme}>
              {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
              {theme === 'light' ? 'Dark Mode' : 'Light Mode'}
            </button>
            <button className="flex items-center gap-3 p-3 rounded-xl w-full text-left transition-all bg-error/10 text-error hover:bg-error hover:text-white font-medium shadow-sm" onClick={handleLogout}>
              <LogOut size={18} />
              Đăng xuất
            </button>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className={`flex-1 flex flex-col relative overflow-hidden ${isAdmin ? 'w-full' : ''}`}>
        {!isAdmin && (
          <header className="h-16 flex items-center justify-between px-8 bg-surface-container-lowest/40 backdrop-blur-md border-b border-outline-variant/20 z-20 shrink-0 shadow-sm">
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-lg text-primary md:block hidden">Trợ lý Ảo Xanh SM AI</h3>
              <h3 className="font-bold text-base text-primary md:hidden block">Xanh SM AI</h3>
              <button 
                onClick={() => setShowTopicsDialog(true)}
                className="p-1.5 rounded-full hover:bg-surface-variant text-on-surface-variant hover:text-primary transition-all ml-1 shadow-sm border border-outline-variant/20 flex items-center justify-center"
                title="Danh mục chủ đề hỗ trợ"
              >
                <HelpCircle size={18} />
              </button>
            </div>
            
            {/* Right side: Login/Logout button & Avatar */}
            <div className="flex items-center gap-4">
              {user?.type === 'user' ? (
                <div className="flex items-center gap-3">
                  <button 
                    onClick={handleLogout}
                    className="px-4 py-1.5 text-xs font-bold rounded-full bg-error text-white hover:bg-red-600 transition-all active:scale-95 shadow-md"
                  >
                    Đăng xuất
                  </button>
                  <div 
                    className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white text-xs font-bold shadow-md uppercase border border-primary/20"
                    title={user.email}
                  >
                    {user.name ? user.name[0] : <User size={14} />}
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-3">
                  <GoogleLogin
                    onSuccess={async (credentialResponse) => {
                      const success = await loginWithGoogle(credentialResponse.credential);
                      if (success) {
                        api.getConversations().then(setConversations).catch(console.error);
                      }
                    }}
                    onError={() => console.error('Đăng nhập Google thất bại')}
                    shape="pill"
                    theme="filled_blue"
                    size="large"
                    text="signin_with"
                  />
                  <div className="w-8 h-8 rounded-full bg-surface-variant flex items-center justify-center text-on-surface-variant text-xs font-bold shadow-sm border border-outline-variant/30">
                    <User size={14} />
                  </div>
                </div>
              )}
            </div>
          </header>
        )}
        
        {children}

        {/* Topics Dialog Modal */}
        {showTopicsDialog && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
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
      </div>
    </div>
  );
}

function App() {
  return (
    <Routes>
      {/* User Chat Route */}
      <Route path="/" element={
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
        <Route path="eval" element={<AIEvalLab />} />
        <Route path="pipeline" element={<PipelineManager />} />
        <Route path="agent-crawler" element={<AgentCrawler />} />
        <Route path="history" element={<RAGHistory />} />
        <Route path="ingest" element={<IngestionManager />} />
        <Route path="db" element={<DatabaseManager />} />
      </Route>
      
      {/* Redirect all other paths to home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
