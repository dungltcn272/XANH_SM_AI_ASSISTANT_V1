import { useState, useEffect } from 'react';
import { Users, Zap, ShieldAlert, Timer, ChevronRight } from 'lucide-react';
import { api } from '../api';

export default function CommandCenter() {
  const [stats, setStats] = useState({
    total_users: 0,
    total_requests: 0,
    total_blocked: 0,
    avg_latency: 0
  });
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [s, l] = await Promise.all([
          api.getDbStats().catch(() => null),
          api.getAdminLogs().catch(() => [])
        ]);
        if (s) {
          setStats({
            total_users: s.total_users || 0,
            total_requests: s.total_requests || 0,
            total_blocked: s.total_blocked || 0,
            avg_latency: s.avg_latency || 0.8
          });
        }
        if (l) setLogs(l.slice(0, 5)); // Just recent 5
      } catch (err) {
        console.error(err);
      }
      setLoading(false);
    };
    fetchData();
  }, []);

  if (loading) {
    return <div className="p-8 text-on-surface-variant animate-pulse">Loading command center...</div>;
  }

  return (
    <div className="max-w-[1600px] mx-auto w-full">
      {/* Welcome Header */}
      <div className="mb-10">
        <h2 className="text-3xl md:text-4xl font-bold text-on-surface flex items-center">
          AI Command Center
          <span className="text-primary bg-primary/10 px-3 py-1 rounded-full text-xs align-middle ml-4 font-bold border border-primary/20 shadow-sm">
            ECO MODE ACTIVE
          </span>
        </h2>
        <p className="text-lg text-on-surface-variant mt-2 max-w-2xl">
          Sustainable intelligence overview. Real-time monitoring of RAG performance and guardrail safety across global nodes.
        </p>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
        
        {/* Total Users */}
        <div className="glass-panel p-6 rounded-2xl relative overflow-hidden group hover:-translate-y-1 transition-transform">
          <div className="flex justify-between items-start mb-4">
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary mb-4 shadow-inner">
              <Users size={20} />
            </div>
          </div>
          <p className="text-on-surface-variant text-xs font-bold uppercase tracking-wider mb-1">Total Users</p>
          <h3 className="text-4xl font-bold text-primary drop-shadow-sm">{stats.total_users.toLocaleString()}</h3>
        </div>

        {/* Requests */}
        <div className="glass-panel p-6 rounded-2xl relative overflow-hidden group hover:-translate-y-1 transition-transform">
          <div className="flex justify-between items-start mb-4">
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-500 mb-4 shadow-inner">
              <Zap size={20} />
            </div>
          </div>
          <p className="text-on-surface-variant text-xs font-bold uppercase tracking-wider mb-1">Requests</p>
          <h3 className="text-4xl font-bold text-blue-500 drop-shadow-sm">{stats.total_requests.toLocaleString()}</h3>
        </div>

        {/* Guardrail Blocks */}
        <div className="glass-panel p-6 rounded-2xl relative overflow-hidden group hover:-translate-y-1 transition-transform">
          <div className="flex justify-between items-start mb-4">
            <div className="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center text-red-500 mb-4 shadow-inner">
              <ShieldAlert size={20} />
            </div>
          </div>
          <p className="text-on-surface-variant text-xs font-bold uppercase tracking-wider mb-1">Guardrail Blocks</p>
          <h3 className="text-4xl font-bold text-red-500 drop-shadow-sm">{stats.total_blocked.toLocaleString()}</h3>
        </div>

        {/* Avg Response Time */}
        <div className="glass-panel p-6 rounded-2xl relative overflow-hidden group hover:-translate-y-1 transition-transform">
          <div className="flex justify-between items-start mb-4">
            <div className="w-10 h-10 rounded-xl bg-orange-500/10 flex items-center justify-center text-orange-500 mb-4 shadow-inner">
              <Timer size={20} />
            </div>
          </div>
          <p className="text-on-surface-variant text-xs font-bold uppercase tracking-wider mb-1">Avg Response</p>
          <h3 className="text-4xl font-bold text-orange-500 drop-shadow-sm">{(stats.avg_latency || 0).toFixed(2)}s</h3>
        </div>

      </div>

      {/* Recent Activity Table */}
      <div className="glass-panel rounded-3xl overflow-hidden border border-outline-variant/30">
        <div className="p-6 border-b border-outline-variant/30 flex justify-between items-center bg-white/40">
          <h3 className="text-xl font-bold text-on-surface">Recent Intelligence Queries</h3>
          <button className="text-sm font-semibold text-primary hover:text-primary-focus flex items-center gap-1 transition-colors">
            View all logs <ChevronRight size={16} />
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-container-low/50 text-on-surface-variant text-xs uppercase tracking-wider">
                <th className="px-6 py-4 font-semibold">User Query</th>
                <th className="px-6 py-4 font-semibold">Intent</th>
                <th className="px-6 py-4 font-semibold">Status</th>
                <th className="px-6 py-4 font-semibold">Latency</th>
                <th className="px-6 py-4 font-semibold">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/20">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-primary/5 transition-colors">
                  <td className="px-6 py-4 text-sm font-medium text-on-surface max-w-md truncate">
                    {log.original_query || 'Unknown'}
                  </td>
                  <td className="px-6 py-4 text-sm text-on-surface-variant">
                    <span className="px-2 py-1 rounded-md bg-surface-variant text-xs font-semibold">{log.intent || 'rag'}</span>
                  </td>
                  <td className="px-6 py-4 text-sm">
                    {log.blocked_by_guardrail ? (
                      <span className="text-error font-semibold flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-error"></span> Blocked</span>
                    ) : (
                      <span className="text-primary font-semibold flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span> Safe</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm font-mono text-on-surface-variant">
                    {(log.total_latency_ms || 0).toFixed(0)}ms
                  </td>
                  <td className="px-6 py-4 text-sm text-on-surface-variant">
                    {new Date(log.created_at + 'Z').toLocaleTimeString('vi-VN')}
                  </td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr>
                  <td colSpan="5" className="px-6 py-8 text-center text-on-surface-variant text-sm italic">
                    No recent activity found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
