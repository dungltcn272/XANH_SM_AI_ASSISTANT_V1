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
import { Moon, Sun, Monitor, Shield, MessageSquare, LogOut, History, Plus, User } from 'lucide-react';
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
            <h3 className="font-bold text-lg text-primary md:block hidden">Trợ lý Ảo Xanh SM AI</h3>
            <h3 className="font-bold text-base text-primary md:hidden block">Xanh SM AI</h3>
            
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
