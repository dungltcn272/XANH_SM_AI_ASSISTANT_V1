import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { LayoutDashboard, Beaker, Database, History, Hammer, MessageSquareHeart, Bot } from 'lucide-react';

export default function AdminLayout() {
  const navigate = useNavigate();
  const location = useLocation();

  const navSections = [
    {
      title: 'OVERVIEW',
      items: [
        { path: '/admin', label: 'Command Center', icon: <LayoutDashboard size={18} /> },
      ]
    },
    {
      title: 'KNOWLEDGE BASE',
      items: [
        { path: '/admin/knowledge-builder', label: 'Knowledge Hub', icon: <Database size={18} /> },
      ]
    },
    {
      title: 'SYSTEM LOGS',
      items: [
        { path: '/admin/history', label: 'History', icon: <History size={18} /> },
      ]
    },
    {
      title: 'ADVANCED',
      items: [
        { path: '/admin/db', label: 'Database Manager', icon: <Hammer size={18} /> },
        { path: '/admin/eval', label: 'AIEval Lab', icon: <Beaker size={18} /> },
        { path: '/admin/reviews', label: 'User Reviews', icon: <MessageSquareHeart size={18} /> },
        { path: '/admin/ml', label: 'AI Models (MLOps)', icon: <Bot size={18} /> },
      ]
    }
  ];

  return (
    <div className="dark w-full h-full">
      <div className="flex h-screen bg-background text-on-surface w-full overflow-hidden transition-colors duration-200">

      {/* SideNavBar */}
      <aside className="fixed left-0 top-0 h-screen w-64 bg-[#0b111a] border-r border-[#1e293b] hidden md:flex flex-col p-4 gap-y-4 z-40 overflow-y-auto no-scrollbar">
        <div className="flex flex-col gap-1 px-2 mt-2 mb-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-[#0f1520] border border-[#00c897]/30 flex items-center justify-center">
              <div className="w-4 h-4 bg-[#00c897] shadow-[0_0_10px_#00c897] opacity-80" style={{ clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)' }}></div>
            </div>
            <div>
              <h2 className="text-lg font-bold text-[#00c897] cursor-pointer" onClick={() => navigate('/')}>
                RAG_XANH_SM
              </h2>
              <p className="text-[10px] font-semibold text-[#94a3b8] tracking-widest">AI OPERATIONS</p>
            </div>
          </div>
        </div>
        
        <nav className="flex flex-col gap-6 flex-1 mt-2">
          {navSections.map((section, idx) => (
            <div key={idx} className="flex flex-col gap-2">
              <h3 className="text-[10px] font-bold text-[#475569] px-3 uppercase tracking-wider">{section.title}</h3>
              <div className="flex flex-col gap-1">
                {section.items.map(item => {
                  const isActive = location.pathname === item.path || (item.path !== '/admin' && location.pathname.startsWith(item.path));
                  return (
                    <button
                      key={item.path}
                      onClick={() => navigate(item.path)}
                      className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 text-sm font-medium ${
                        isActive 
                          ? 'bg-[#00c897]/10 text-[#00c897] border border-[#00c897]/20 shadow-[inset_0_0_12px_rgba(0,200,151,0.1)]' 
                          : 'text-[#94a3b8] hover:text-[#f8f9ff] hover:bg-[#1e293b]/50 border border-transparent'
                      }`}
                    >
                      <span className={`${isActive ? 'text-[#00c897]' : 'text-[#64748b]'}`}>{item.icon}</span>
                      <span>{item.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        <div className="mt-auto pt-6 border-t border-[#1e293b] flex items-center gap-3 px-2">
           <button className="w-full py-2.5 bg-[#1e293b]/50 text-[#94a3b8] hover:text-white rounded-lg border border-[#1e293b] font-medium transition-all text-sm flex items-center justify-center gap-2" onClick={() => navigate('/')}>
             <LayoutDashboard size={16} />
             Back to Chat
           </button>
        </div>
      </aside>

      {/* Main Content Area */}
      {/* Main Content Area */}
      <main className="flex-1 h-full pt-4 pb-12 px-4 md:pl-[280px] md:pr-8 overflow-y-auto bg-[#070b14] transition-colors duration-200">
        <Outlet />
      </main>

    </div>
    </div>
  );
}
