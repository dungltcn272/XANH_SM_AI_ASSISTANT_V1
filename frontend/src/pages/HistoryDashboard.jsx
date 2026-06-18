import { useState } from 'react';
import RagLogView from './RagLogView';
import FoodLogView from './FoodLogView';
import BasicLogView from './BasicLogView';
import { Database, Zap, MessageSquare, RefreshCw } from 'lucide-react';

export default function HistoryDashboard() {
  const [activeTab, setActiveTab] = useState('rag'); // 'basic', 'rag', 'food'
  const [refreshCount, setRefreshCount] = useState(0);

  return (
    <div className="flex flex-col h-full bg-[#070b14]">
      {/* Header Tabs */}
      <div className="px-6 py-4 border-b border-[#1e293b] shrink-0 flex items-center justify-center gap-4">
        <button
          onClick={() => setActiveTab('basic')}
          className={`flex items-center gap-2 px-6 py-2.5 rounded-full font-bold text-sm transition-all ${
            activeTab === 'basic' 
              ? 'bg-[#3b82f6]/10 text-[#3b82f6] border border-[#3b82f6]/50 shadow-[0_0_15px_rgba(59,130,246,0.15)]' 
              : 'text-[#64748b] hover:text-[#94a3b8] hover:bg-[#1e293b]'
          }`}
        >
          <MessageSquare size={16} /> BASIC LOG
        </button>

        <button
          onClick={() => setActiveTab('rag')}
          className={`flex items-center gap-2 px-6 py-2.5 rounded-full font-bold text-sm transition-all ${
            activeTab === 'rag' 
              ? 'bg-[#00c897]/10 text-[#00c897] border border-[#00c897]/50 shadow-[0_0_15px_rgba(0,200,151,0.15)]' 
              : 'text-[#64748b] hover:text-[#94a3b8] hover:bg-[#1e293b]'
          }`}
        >
          <Database size={16} /> RAG LOG
        </button>

        <button
          onClick={() => setActiveTab('food')}
          className={`flex items-center gap-2 px-6 py-2.5 rounded-full font-bold text-sm transition-all ${
            activeTab === 'food' 
              ? 'bg-[#8b5cf6]/10 text-[#8b5cf6] border border-[#8b5cf6]/50 shadow-[0_0_15px_rgba(139,92,246,0.15)]' 
              : 'text-[#64748b] hover:text-[#94a3b8] hover:bg-[#1e293b]'
          }`}
        >
          <Zap size={16} /> FOOD LOG
        </button>

        <div className="ml-auto">
          <button 
            onClick={() => setRefreshCount(prev => prev + 1)}
            className="flex items-center gap-2 px-4 py-2 bg-[#1e293b]/50 text-[#94a3b8] hover:text-white rounded-lg border border-[#1e293b] hover:border-[#334155] font-medium transition-all text-sm"
          >
            <RefreshCw size={14} className="hover:animate-spin" /> Làm mới
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-hidden relative">
        {activeTab === 'basic' && <BasicLogView key={`basic-${refreshCount}`} />}
        {activeTab === 'rag' && <RagLogView key={`rag-${refreshCount}`} />}
        {activeTab === 'food' && <FoodLogView key={`food-${refreshCount}`} />}
      </div>
    </div>
  );
}
