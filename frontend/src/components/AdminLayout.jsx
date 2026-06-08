import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { LayoutDashboard, Beaker, Network, Database, History, User as UserIcon, Hammer } from 'lucide-react';

export default function AdminLayout() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { path: '/admin', label: 'Command Center', icon: <LayoutDashboard size={20} /> },
    { path: '/admin/eval', label: 'AI Evaluation Lab', icon: <Beaker size={20} /> },
    { path: '/admin/pipeline', label: 'Pipeline Manager', icon: <Network size={20} /> },
    { path: '/admin/knowledge-builder', label: 'Knowledge Builder', icon: <Hammer size={20} /> },
    { path: '/admin/history', label: 'RAG History', icon: <History size={20} /> },
    { path: '/admin/ingest', label: 'Crawl & Ingest', icon: <Database size={20} /> },
    { path: '/admin/db', label: 'Raw Database', icon: <Database size={20} /> }
  ];

  return (
    <div className="flex h-screen bg-background text-on-surface w-full overflow-hidden transition-colors duration-200">

      {/* SideNavBar */}
      <aside className="fixed left-4 top-4 h-[calc(100vh-32px)] w-64 rounded-2xl glass-panel shadow-lg hidden md:flex flex-col p-6 gap-y-6 z-40">
        <div className="flex flex-col gap-1">
          <h2 className="text-xl font-bold text-primary cursor-pointer hover:opacity-80 transition-opacity" onClick={() => navigate('/')}>
            Xanh SM AI
          </h2>
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
                    : 'text-on-surface-variant hover:text-primary hover:bg-surface-container/50'
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
      <main className="flex-1 h-full pt-8 pb-12 px-4 md:pl-[300px] md:pr-8 overflow-y-auto bg-background transition-colors duration-200">
        <Outlet />
      </main>

    </div>
  );
}
