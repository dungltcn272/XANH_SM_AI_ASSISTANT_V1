import { useState, useEffect } from 'react';
import { ChevronDown, Zap, Database, Activity, ArrowUpRight, ArrowDownRight, MessageSquare, ShieldAlert, ChevronRight, Server, Cpu, Bot, RefreshCw } from 'lucide-react';
import { AreaChart, Area, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { api } from '../api';

const emptySeries = Array.from({ length: 24 }, (_, i) => ({ time: `${String(i).padStart(2, '0')}:00`, value: 0 }));

const intentDataMock = [];

const safetyDataMock = [
  { name: 'Passed', value: 0, color: '#00c897' },
  { name: 'Blocked', value: 0, color: '#f59e0b' },
  { name: 'Error', value: 0, color: '#ef4444' },
];



export default function CommandCenter() {
  const [stats, setStats] = useState({
    total_requests: 0,
    avg_latency: 0,
    total_cost: 0,
    cache_hit_rate: 0,
    total_blocked: 0,
    total_errors: 0
  });
  
  const [intentData, setIntentData] = useState(intentDataMock);
  const [safetyData, setSafetyData] = useState(safetyDataMock);
  
  const [liveActivityFeed, setLiveActivityFeed] = useState([]);
  const [timeseries, setTimeseries] = useState({
    queries: emptySeries,
    cache: emptySeries,
    latency: emptySeries,
    cost: emptySeries,
  });
  const [health, setHealth] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const s = await api.getDbStats();
          if (s) {
          setStats({
            total_requests: s.total_requests || 0,
            avg_latency: s.avg_latency || 0,
            total_cost: s.total_cost || 0,
            cache_hit_rate: s.cache_hit_rate || 0,
            total_blocked: s.total_blocked || 0,
            total_errors: s.total_errors || 0
          });
          if (s.intentData) setIntentData(s.intentData);
          if (s.safetyData) setSafetyData(s.safetyData);
          if (s.timeseries) setTimeseries(s.timeseries);
        }
        const l = await api.getAdminLogs();
        if (l) setLiveActivityFeed(l.slice(0, 5)); // Take top 5 as per design
        const h = await api.getSystemHealth();
        if (h) setHealth(h);
      } catch (err) {
        console.error(err);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="max-w-[1600px] mx-auto w-full text-[#f8f9ff]">
      
      {/* Top Header */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center mb-8 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wide">Command Center</h1>
          <p className="text-sm text-[#94a3b8] mt-1">Real-time overview of your AI system performance and health</p>
        </div>
        
        <div className="flex flex-wrap items-center gap-6">
          {/* Health Stats */}
          <div className="flex items-center gap-6 text-sm border-l border-[#1e293b] pl-6">
            <div className="flex flex-col">
              <span className="text-[#94a3b8] text-xs">API Health</span>
              <div className={`flex items-center gap-1.5 font-medium ${health?.status === 'operational' ? 'text-[#00c897]' : 'text-[#f59e0b]'}`}>
                <div className={`w-2 h-2 rounded-full ${health?.status === 'operational' ? 'bg-[#00c897]' : 'bg-[#f59e0b]'} animate-pulse`}></div>
                {health?.status === 'operational' ? 'Healthy' : 'Checking'}
              </div>
            </div>
            <div className="flex flex-col">
              <span className="text-[#94a3b8] text-xs">System Health</span>
              <div className="flex items-center gap-1.5 font-medium text-[#00c897]">
                <span className="text-[#00c897]">{(health?.score ?? 0).toFixed(1)}%</span>
              </div>
            </div>
          </div>
          
          {/* User Profile */}
          <div className="flex items-center gap-3 border-l border-[#1e293b] pl-6 cursor-pointer">
            <div className="w-9 h-9 rounded-full bg-[#1e293b] flex items-center justify-center font-bold text-[#f8f9ff]">
              A
            </div>
            <div className="hidden md:block">
              <p className="text-sm font-semibold text-white leading-tight">Admin</p>
              <p className="text-[10px] text-[#94a3b8]">Super Admin</p>
            </div>
            <ChevronDown size={14} className="text-[#64748b]" />
          </div>
        </div>
      </div>

      {/* 4 KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        {/* Card 1 */}
        <div className="glass-panel p-5 rounded-xl border border-[#1e293b]/60 flex flex-col justify-between h-36 relative overflow-hidden">
          <div className="flex items-start gap-3 mb-2 relative z-10">
            <div className="w-8 h-8 rounded-lg bg-[#00c897]/10 flex items-center justify-center text-[#00c897]">
              <MessageSquare size={16} />
            </div>
            <div>
              <p className="text-sm font-medium text-[#e2e8f0]">Total Queries</p>
              <h3 className="text-3xl font-bold text-white mt-1">{stats.total_requests.toLocaleString()}</h3>
            </div>
          </div>
          <div className="flex justify-between items-end relative z-10 mt-auto">
            <p className="text-xs font-medium text-[#00c897] flex items-center gap-1">
              <ArrowUpRight size={12} /> Live <span className="text-[#64748b] font-normal">from DB</span>
            </p>
          </div>
          <div className="absolute bottom-0 left-0 right-0 h-16 opacity-50 z-0">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timeseries.queries}>
                 <Area type="monotone" dataKey="value" stroke="#00c897" strokeWidth={2} fill="transparent" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Card 2 */}
        <div className="glass-panel p-5 rounded-xl border border-[#1e293b]/60 flex flex-col justify-between h-36 relative overflow-hidden">
          <div className="flex items-start gap-3 mb-2 relative z-10">
            <div className="w-8 h-8 rounded-lg bg-[#3b82f6]/10 flex items-center justify-center text-[#3b82f6]">
              <Zap size={16} />
            </div>
            <div>
              <p className="text-sm font-medium text-[#e2e8f0]">Cache Hit Rate</p>
              <h3 className="text-3xl font-bold text-white mt-1">{stats.cache_hit_rate.toFixed(1)}%</h3>
            </div>
          </div>
          <div className="flex justify-between items-end relative z-10 mt-auto">
            <p className="text-xs font-medium text-[#00c897] flex items-center gap-1">
              <ArrowUpRight size={12} /> Live <span className="text-[#64748b] font-normal">from DB</span>
            </p>
          </div>
          <div className="absolute bottom-0 left-0 right-0 h-16 opacity-50 z-0">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timeseries.cache}>
                 <Area type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} fill="transparent" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Card 3 */}
        <div className="glass-panel p-5 rounded-xl border border-[#1e293b]/60 flex flex-col justify-between h-36 relative overflow-hidden">
          <div className="flex items-start gap-3 mb-2 relative z-10">
            <div className="w-8 h-8 rounded-lg bg-[#8b5cf6]/10 flex items-center justify-center text-[#8b5cf6]">
              <Activity size={16} />
            </div>
            <div>
              <p className="text-sm font-medium text-[#e2e8f0]">Avg Latency</p>
              <h3 className="text-3xl font-bold text-white mt-1">{stats.avg_latency.toFixed(0)} <span className="text-lg text-[#94a3b8] font-normal">ms</span></h3>
            </div>
          </div>
          <div className="flex justify-between items-end relative z-10 mt-auto">
            <p className="text-xs font-medium text-[#00c897] flex items-center gap-1">
              <ArrowDownRight size={12} /> Live <span className="text-[#64748b] font-normal">from DB</span>
            </p>
          </div>
          <div className="absolute bottom-0 left-0 right-0 h-16 opacity-50 z-0">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timeseries.latency}>
                 <Area type="monotone" dataKey="value" stroke="#8b5cf6" strokeWidth={2} fill="transparent" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Card 4 */}
        <div className="glass-panel p-5 rounded-xl border border-[#1e293b]/60 flex flex-col justify-between h-36 relative overflow-hidden">
          <div className="flex items-start gap-3 mb-2 relative z-10">
            <div className="w-8 h-8 rounded-lg bg-[#00c897]/10 flex items-center justify-center text-[#00c897]">
              <Database size={16} />
            </div>
            <div>
              <p className="text-sm font-medium text-[#e2e8f0]">Total Cost (USD)</p>
              <h3 className="text-3xl font-bold text-white mt-1">${stats.total_cost.toFixed(4)}</h3>
            </div>
          </div>
          <div className="flex justify-between items-end relative z-10 mt-auto">
            <p className="text-xs font-medium text-[#ef4444] flex items-center gap-1">
              <ArrowUpRight size={12} /> Live <span className="text-[#64748b] font-normal">from DB</span>
            </p>
          </div>
          <div className="absolute bottom-0 left-0 right-0 h-16 opacity-50 z-0">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timeseries.cost}>
                 <Area type="monotone" dataKey="value" stroke="#00c897" strokeWidth={2} fill="transparent" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* System Health */}
      <div className="glass-panel rounded-xl border border-[#1e293b]/60 bg-[#0f1520]/80 mb-6 px-5 py-4">
        <div className="flex flex-col xl:flex-row xl:items-center gap-5">
          <div className="w-full xl:w-56 shrink-0">
            <p className="text-[10px] font-bold uppercase tracking-wider text-[#64748b]">System Health</p>
            <div className="flex items-end gap-2 mt-1">
              <span className="text-3xl font-bold text-[#00c897]">{(health?.score ?? 0).toFixed(1)}%</span>
            </div>
            <div className="flex items-center gap-1.5 mt-1 text-xs text-[#94a3b8]">
              <span className={`w-2 h-2 rounded-full ${(health?.status || 'degraded') === 'operational' ? 'bg-[#00c897]' : 'bg-[#f59e0b]'}`}></span>
              {health?.status === 'operational' ? 'All systems operational' : 'Some services need attention'}
            </div>
          </div>

          <div className="hidden xl:block flex-1 h-12">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timeseries.latency}>
                <Area type="monotone" dataKey="value" stroke="#00c897" strokeWidth={2} fill="transparent" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 w-full xl:w-auto">
            {(health?.services || [
              { name: 'LLM API', status: 'down', detail: 'loading' },
              { name: 'Vector DB', status: 'down', detail: 'loading' },
              { name: 'Database', status: 'down', detail: 'loading' },
              { name: 'Semantic Cache', status: 'down', detail: 'loading' },
              { name: 'Crawlers', status: 'down', detail: 'loading' },
            ]).map((service) => {
              const Icon = service.name === 'LLM API' ? Bot : service.name === 'Vector DB' ? Server : service.name === 'Database' ? Database : service.name === 'Crawlers' ? RefreshCw : Cpu;
              const ok = service.status === 'healthy';
              return (
                <div key={service.name} className="rounded-lg border border-[#1e293b] bg-[#0b1220] px-3 py-2 min-w-32">
                  <div className="flex items-center gap-2 text-xs font-semibold text-[#cbd5e1]">
                    <Icon size={14} className={ok ? 'text-[#00c897]' : 'text-[#f59e0b]'} />
                    {service.name}
                  </div>
                  <div className="mt-1 flex items-center gap-1.5 text-[11px]">
                    <span className={`w-1.5 h-1.5 rounded-full ${ok ? 'bg-[#00c897]' : 'bg-[#f59e0b]'}`}></span>
                    <span className={ok ? 'text-[#00c897]' : 'text-[#f59e0b]'}>{ok ? 'Healthy' : 'Check'}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Middle Row Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        
        {/* Intent Distribution */}
        <div className="glass-panel p-6 rounded-xl border border-[#1e293b]/60 h-[340px] flex flex-col bg-[#0f1520]/80">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h3 className="text-base font-bold text-white">Intent Distribution</h3>
              <p className="text-xs text-[#64748b]">Distribution of queries by intent</p>
            </div>
          </div>
          <div className="flex-1 flex flex-col gap-5 justify-center">
            {intentData.map((item, idx) => (
              <div key={idx} className="flex items-center gap-4">
                <div className="w-36 text-xs text-[#94a3b8] truncate font-medium">{item.name}</div>
                <div className="flex-1 h-2 bg-[#1e293b] rounded-full overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${stats.total_requests > 0 ? (item.value / stats.total_requests) * 100 : 0}%`, backgroundColor: item.color }}></div>
                </div>
                <div className="w-24 text-right flex items-center justify-end gap-2">
                  <span className="text-sm font-semibold text-[#f8f9ff]">{item.value.toLocaleString()}</span>
                  <span className="text-[10px] text-[#64748b]">({stats.total_requests > 0 ? ((item.value / stats.total_requests) * 100).toFixed(1) : 0}%)</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Safety Monitoring */}
        <div className="glass-panel p-6 rounded-xl border border-[#1e293b]/60 h-[340px] flex flex-col bg-[#0f1520]/80">
          <div className="mb-4">
            <h3 className="text-base font-bold text-white">Safety & Guardrail Monitoring</h3>
            <p className="text-xs text-[#64748b]">Query safety evaluation</p>
          </div>
          <div className="flex-1 flex items-center justify-between">
            <div className="w-[180px] h-[180px] relative shrink-0">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={safetyData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={85}
                    paddingAngle={2}
                    dataKey="value"
                    stroke="none"
                  >
                    {safetyData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span className="text-2xl font-bold text-white">{stats.total_requests.toLocaleString()}</span>
                <span className="text-[10px] text-[#64748b]">Total</span>
              </div>
            </div>
            <div className="flex-1 flex flex-col gap-5 pl-8">
              {safetyData.map((item, idx) => (
                <div key={idx} className="flex items-start gap-3">
                  <div className="w-2.5 h-2.5 rounded-sm mt-1" style={{ backgroundColor: item.color }}></div>
                  <div className="flex flex-col">
                    <span className="text-xs text-[#94a3b8] font-medium">{item.name}</span>
                    <div className="flex items-baseline gap-1.5">
                      <span className="text-sm font-bold text-[#f8f9ff]">{item.value.toLocaleString()}</span>
                      <span className="text-[10px] font-medium text-[#64748b]">({stats.total_requests > 0 ? ((item.value/stats.total_requests)*100).toFixed(1) : 0}%)</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="flex justify-between items-center mt-4 border-t border-[#1e293b] pt-4">
            <span className="text-xs font-medium text-[#94a3b8]">Guardrail Block Rate</span>
            <span className="text-sm font-bold text-[#f59e0b]">{stats.total_requests > 0 ? ((stats.total_blocked / stats.total_requests)*100).toFixed(1) : 0}%</span>
          </div>
        </div>

      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 gap-6">
        
        {/* Live Activity Feed */}
        <div className="glass-panel rounded-xl border border-[#1e293b]/60 overflow-hidden flex flex-col bg-[#0f1520]/80">
          <div className="p-5 flex items-center gap-3">
            <h3 className="text-base font-bold text-white">Live Activity Feed</h3>
            <span className="bg-[#00c897]/10 text-[#00c897] text-[10px] font-bold px-2 py-0.5 rounded border border-[#00c897]/20 tracking-wider">LIVE</span>
            <p className="text-xs text-[#64748b] ml-auto">Real-time system activities</p>
          </div>
          <div className="overflow-x-auto border-t border-[#1e293b]/50">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="text-[#475569] text-[10px] font-bold uppercase tracking-wider border-b border-[#1e293b]">
                  <th className="px-5 py-3 w-24">TIME</th>
                  <th className="px-5 py-3 w-16">TYPE</th>
                  <th className="px-5 py-3">QUERY / EVENT</th>
                  <th className="px-5 py-3 w-28">INTENT</th>
                  <th className="px-5 py-3 w-28">STATUS</th>
                  <th className="px-5 py-3 w-24">LATENCY</th>
                  <th className="px-5 py-3 w-32">MODEL</th>
                  <th className="px-5 py-3 w-32">USER / SOURCE</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1e293b]/50">
                {liveActivityFeed.map((row, idx) => (
                  <tr key={idx} className="hover:bg-[#1e293b]/30 transition-colors">
                    <td className="px-5 py-3.5 text-[11px] text-[#94a3b8] font-mono">{row.time}</td>
                    <td className="px-5 py-3.5">
                      <div className="w-6 h-6 rounded bg-[#1e293b]/50 flex items-center justify-center">
                        {row.type === 'chat' && <MessageSquare size={12} className="text-[#00c897]" />}
                        {row.type === 'zap' && <Zap size={12} className="text-[#3b82f6]" />}
                        {row.type === 'shield' && <ShieldAlert size={12} className="text-[#f59e0b]" />}
                        {row.type === 'database' && <Database size={12} className="text-[#8b5cf6]" />}
                      </div>
                    </td>
                    <td className="px-5 py-3.5 text-sm text-[#e2e8f0]">{row.query}</td>
                    <td className="px-5 py-3.5">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                        row.intent === 'RAG' ? 'border-[#00c897]/30 text-[#00c897]' :
                        row.intent === 'Food' ? 'border-[#3b82f6]/30 text-[#3b82f6]' :
                        row.intent === 'Sensitive' ? 'border-[#f59e0b]/30 text-[#f59e0b]' :
                        'border-[#8b5cf6]/30 text-[#8b5cf6]'
                      }`}>{row.intent}</span>
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-1.5 text-[11px] font-medium">
                        <div className={`w-1.5 h-1.5 rounded-full ${row.status === 'Success' ? 'bg-[#00c897]' : 'bg-[#f59e0b]'}`}></div>
                        <span className={row.status === 'Success' ? 'text-[#00c897]' : 'text-[#f59e0b]'}>{row.status}</span>
                      </div>
                    </td>
                    <td className="px-5 py-3.5 text-[11px] text-[#94a3b8] font-mono">{row.latency}</td>
                    <td className="px-5 py-3.5 text-xs text-[#94a3b8]">{row.model}</td>
                    <td className="px-5 py-3.5 text-xs text-[#94a3b8]">{row.source}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="p-3 border-t border-[#1e293b]/50 flex justify-center bg-[#0a0f16]/50">
            <button className="text-xs font-medium text-[#64748b] hover:text-[#00c897] transition-colors flex items-center gap-1">
              View All Activities <ChevronRight size={14} />
            </button>
          </div>
        </div>



      </div>

    </div>
  );
}
