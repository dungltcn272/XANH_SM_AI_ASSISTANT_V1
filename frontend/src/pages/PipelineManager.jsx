import { useEffect, useRef } from 'react';
import mermaid from 'mermaid';
import { Network } from 'lucide-react';

const mermaidCode = `
graph TD
    A([User Input]):::input
    A --> B[API Gateway & Guardrails]
    
    B -- Từ chối --> C[Chặn nội dung vi phạm]:::error
    B -- Hợp lệ --> D[Intent Classifier & Slot Filling]
    
    D -- Small-talk / Cước phí --> E[Task Agent / Phản hồi nhanh]
    D -- Câu hỏi nghiệp vụ --> F[Query Expansion & Rewrite]
    
    classDef input fill:#00c897,color:#fff,stroke-width:0px;
    classDef error fill:#ff4444,color:#fff,stroke-width:0px;
    
    classDef default fill:#1e293b,color:#fff,stroke:#475569,stroke-width:1px;
    linkStyle default stroke:#64748b,stroke-width:2px;
`;

export default function PipelineManager() {
  const mermaidRef = useRef(null);

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: true,
      theme: 'dark',
      securityLevel: 'loose',
      fontFamily: 'Inter, sans-serif'
    });
    
    if (mermaidRef.current) {
      mermaid.contentLoaded();
    }
  }, []);

  return (
    <div className="max-w-[1600px] mx-auto w-full h-[calc(100vh-100px)] flex flex-col p-4 md:p-8">
      {/* Header */}
      <div className="mb-8 flex justify-between items-end shrink-0">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="inline-block w-3 h-3 rounded-full bg-primary animate-pulse shadow-[0_0_10px_#00c897]"></span>
            <span className="text-primary text-xs font-bold tracking-widest uppercase">System Architecture</span>
          </div>
          <h2 className="text-3xl md:text-4xl font-bold text-on-surface">Pipeline Manager</h2>
          <p className="text-lg text-on-surface-variant mt-2 max-w-2xl">
            Sơ đồ luồng xử lý NLU-Gateway và RAG Pipeline của hệ thống Xanh SM AI.
          </p>
        </div>
      </div>

      <div className="flex-1 glass-panel rounded-3xl border border-outline-variant/30 overflow-hidden flex flex-col relative bg-[#0b121e]">
        <div className="p-4 border-b border-white/10 flex items-center gap-3 bg-white/5 shrink-0">
          <Network className="text-primary" size={24} />
          <h3 className="font-bold text-white text-lg">RAG Pipeline Flowchart</h3>
        </div>
        
        <div className="flex-1 overflow-auto flex items-center justify-center p-8">
          <div 
            ref={mermaidRef} 
            className="mermaid text-center transform scale-110 md:scale-125 lg:scale-150 transition-transform origin-center"
          >
            {mermaidCode}
          </div>
        </div>
      </div>
    </div>
  );
}
