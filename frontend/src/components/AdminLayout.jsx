
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { LayoutDashboard, Beaker, Network, Database, History, Search, Bell, User as UserIcon } from 'lucide-react';

export default function AdminLayout() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { path: '/admin', label: 'Command Center', icon: <LayoutDashboard size={20} /> },
    { path: '/admin/eval', label: 'AI Evaluation Lab', icon: <Beaker size={20} /> },
    { path: '/admin/pipeline', label: 'Pipeline Manager', icon: <Network size={20} /> },
    { path: '/admin/history', label: 'RAG History', icon: <History size={20} /> },
    { path: '/admin/ingest', label: 'Crawl & Ingest', icon: <Database size={20} /> },
    { path: '/admin/db', label: 'Raw Database', icon: <Database size={20} /> }
  ];

  return (
    <div className="flex h-screen bg-surface-lowest text-on-surface w-full overflow-hidden">
      
      {/* Top Navbar */}
      <header className="fixed top-0 z-50 w-full backdrop-blur-md bg-white/60 border-b border-outline-variant/30 flex justify-between items-center px-4 md:px-8 py-4 shadow-sm">
        <div className="flex items-center gap-2" onClick={() => navigate('/')} style={{cursor: 'pointer'}}>
          <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-secondary">
            Xanh SM RAG
          </span>
        </div>
        
        <div className="hidden md:flex gap-8 items-center">
          <div className="flex items-center gap-4">
            <div className="bg-surface-container/40 border border-outline-variant/30 rounded-full px-4 py-2 flex items-center gap-2 text-on-surface-variant w-64">
              <Search size={18} />
              <input type="text" placeholder="Search evaluations..." className="bg-transparent border-none outline-none text-sm w-full" />
            </div>
            
            <div className="flex gap-2">
              <button className="w-10 h-10 rounded-full flex items-center justify-center hover:bg-surface-container/50 transition-all text-primary">
                <Bell size={20} />
              </button>
              <button className="w-10 h-10 rounded-full flex items-center justify-center hover:bg-surface-container/50 transition-all text-primary">
                <UserIcon size={20} />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* SideNavBar */}
      <aside className="fixed left-4 top-24 h-[calc(100vh-110px)] w-64 rounded-2xl bg-white/40 backdrop-blur-xl shadow-lg hidden md:flex flex-col p-6 gap-y-6 z-40 border border-white/60">
        <div className="flex flex-col gap-1">
          <h2 className="text-xl font-bold text-primary">Xanh SM AI</h2>
          <p className="text-xs font-semibold text-on-surface-variant uppercase tracking-widest">Precision Intelligence</p>
        </div>
        
        <button className="w-full py-3 bg-gradient-to-br from-primary to-secondary text-white rounded-full shadow-md font-semibold hover:shadow-lg transition-all" onClick={() => navigate('/')}>
           Về màn hình Chat
        </button>

        <nav className="flex flex-col gap-2 mt-4 flex-1">
          {navItems.map(item => {
            const isActive = location.pathname === item.path;
            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`flex items-center gap-3 px-4 py-3 rounded-full transition-all duration-300 font-medium text-sm ${
                  isActive 
                    ? 'bg-gradient-to-br from-primary to-secondary text-white shadow-md' 
                    : 'text-on-surface-variant hover:text-primary hover:bg-white/60'
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="mt-auto pt-6 border-t border-outline-variant/30 flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary">
            <UserIcon size={20} />
          </div>
          <div>
            <p className="text-sm font-semibold text-on-surface">{user?.name || 'Admin'}</p>
            <p className="text-[10px] text-on-surface-variant uppercase font-bold">{user?.role || 'System Admin'}</p>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 h-full pt-24 pb-12 px-4 md:pl-[300px] md:pr-8 overflow-y-auto bg-surface-lowest">
        <Outlet />
      </main>

    </div>
  );
}
