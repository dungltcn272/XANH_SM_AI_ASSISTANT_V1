import { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { api } from './api';
import ChatLayout from './components/ChatLayout';
import AdminLayout from './components/AdminLayout';
import Login from './pages/Login';
import CommandCenter from './pages/CommandCenter';
import AIEvalLab from './pages/AIEvalLab';
import PipelineManager from './pages/PipelineManager';
import RAGHistory from './pages/RAGHistory';
import IngestionManager from './pages/IngestionManager';
import DatabaseManager from './pages/DatabaseManager';
import { Moon, Sun, Monitor, Shield, MessageSquare, LogOut, History, Plus } from 'lucide-react';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div>Loading...</div>;
  if (!user) return <Navigate to="/login" />;
  return children;
}

function MainLayout({ children }) {
  const { user, logout } = useAuth();
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
  }, []);

  useEffect(() => {
    if (user?.type === 'user') {
      api.getConversations().then(setConversations).catch(console.error);
    }
  }, [user]);

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isChat = location.pathname === '/';
  const isAdmin = location.pathname.startsWith('/admin');

  return (
    <div className="flex h-screen w-full bg-background font-sans text-on-surface">
      {/* Sidebar for Guest/User Chat */}
      {!isAdmin && (
        <div className="w-72 bg-surface-container-lowest/60 backdrop-blur-xl border-r border-outline-variant/30 flex flex-col p-6 z-10 shadow-lg shrink-0 hidden md:flex">
          <div className="flex items-center gap-4 mb-8">
            <div className="w-12 h-12 bg-gradient-to-br from-primary to-secondary rounded-2xl flex items-center justify-center text-white shadow-md">
              <MessageSquare size={24} />
            </div>
            <div>
              <h2 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-secondary">Xanh SM</h2>
              <div className="text-sm font-medium text-on-surface-variant">
                {user?.type === 'user' ? user.name : 'Guest Session'}
              </div>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto pr-2 flex flex-col gap-2">
            <div className="text-xs font-bold tracking-wider text-on-surface-variant/70 mb-2 mt-4 uppercase">MENU</div>
            <button 
              className={`flex items-center gap-3 p-3 rounded-xl w-full text-left transition-all ${isChat && !activeConversationId ? 'bg-primary/10 text-primary font-bold' : 'text-on-surface-variant hover:bg-surface-variant hover:text-primary font-medium'}`}
              onClick={() => navigate('/')}
            >
              <Monitor size={18} />
              User Chatbot
            </button>
            <button 
              className={`flex items-center gap-3 p-3 rounded-xl w-full text-left transition-all ${isAdmin ? 'bg-primary/10 text-primary font-bold' : 'text-on-surface-variant hover:bg-surface-variant hover:text-primary font-medium'}`}
              onClick={() => navigate('/admin')}
            >
              <Shield size={18} />
              Admin Dashboard
            </button>

            {/* Chat History Section (Only for logged-in Users) */}
            {user?.type === 'user' && (
              <div className="mt-8">
                <div className="flex justify-between items-center mb-4">
                  <span className="text-xs font-bold tracking-wider text-on-surface-variant/70 uppercase">LỊCH SỬ CHAT</span>
                  <button onClick={() => navigate('/')} className="text-primary hover:bg-primary/10 p-1 rounded-full transition-colors">
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
            <button className="flex items-center gap-3 p-3 rounded-xl w-full text-left transition-all text-error hover:bg-error-container hover:text-error font-medium" onClick={handleLogout}>
              <LogOut size={18} />
              Đăng xuất
            </button>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className={`flex-1 flex flex-col relative overflow-hidden ${isAdmin ? 'w-full' : ''}`}>
        {!isAdmin && (
          <div className="h-16 flex items-center justify-between px-8 bg-surface-container-lowest/60 backdrop-blur-xl border-b border-outline-variant/30 z-10 shrink-0 shadow-sm md:hidden">
            <h3 className="font-bold text-lg text-primary">Trợ lý Ảo Xanh SM</h3>
          </div>
        )}
        
        {children}
      </div>
    </div>
  );
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      
      {/* User Chat Route */}
      <Route path="/" element={
        <ProtectedRoute>
          <MainLayout>
            <ChatLayout />
          </MainLayout>
        </ProtectedRoute>
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
    </Routes>
  );
}

export default App;
