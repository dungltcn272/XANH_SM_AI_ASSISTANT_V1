import { useState, useRef, useEffect } from 'react';
import { TerminalIcon, Network, Play, DatabaseZap, Loader2 } from 'lucide-react';
import { api } from '../api';
import mermaid from 'mermaid';

// Initialize mermaid
mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  securityLevel: 'loose',
  themeVariables: {
    background: '#0b121e',
    primaryColor: '#2DCCD3',
    lineColor: '#2DCCD3'
  }
});

function MermaidDiagram({ chart }) {
  const elementRef = useRef(null);
  
  useEffect(() => {
    if (elementRef.current) {
      elementRef.current.removeAttribute('data-processed');
      elementRef.current.innerHTML = '<div className="text-white/40 animate-pulse text-sm">Rendering diagram...</div>';
      
      const renderId = 'mermaid-chart-' + Math.floor(Math.random() * 100000);
      try {
        mermaid.render(renderId, chart).then(({ svg }) => {
          if (elementRef.current) {
            elementRef.current.innerHTML = svg;
          }
        }).catch(err => {
          console.error("Mermaid render error:", err);
          // Suppress error display, clear diagram
          if (elementRef.current) {
            elementRef.current.innerHTML = '';
          }
        });
      } catch (e) {
        console.error("Mermaid exception:", e);
      }
    }
  }, [chart]);
  
  return <div ref={elementRef} className="flex justify-center items-center p-6 bg-[#0b121e] rounded-2xl border border-white/5 shadow-inner min-h-[220px]" />;
}

export default function AgentCrawler() {
  const [logs, setLogs] = useState([]);
  const [runningCrawler, setRunningCrawler] = useState(false);
  const [runningIngest, setRunningIngest] = useState(false);
  const [activeStep, setActiveStep] = useState(null); // 'Discovery', 'Crawl', 'Classification', 'Extraction', 'DocumentBuilder', 'Storage', 'Complete'
  const terminalRef = useRef(null);

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs]);

  const getMermaidChart = (step) => {
    const steps = ["Discovery", "Crawl", "Classification", "Extraction", "DocumentBuilder", "Storage"];
    
    let chart = `graph LR
      classDef active fill:#2DCCD3,stroke:#fff,stroke-width:2px,color:#fff;
      classDef completed fill:#10b981,stroke:#fff,stroke-width:1px,color:#fff;
      classDef inactive fill:#1a2333,stroke:#2DCCD3,stroke-width:1px,color:#8fa0b5;
      
      D["Discovery Agent"]
      C["Crawl Agent"]
      CL["Classification Agent"]
      E["Extraction Agent"]
      DB["Document Builder"]
      S["Storage Agent"]
      
      D --> C --> CL --> E --> DB --> S
    `;
    
    let activeIndex = steps.indexOf(step);
    if (step === "Complete") activeIndex = steps.length;
    
    steps.forEach((s, idx) => {
      let nodeKey = "";
      if (s === "Discovery") nodeKey = "D";
      else if (s === "Crawl") nodeKey = "C";
      else if (s === "Classification") nodeKey = "CL";
      else if (s === "Extraction") nodeKey = "E";
      else if (s === "DocumentBuilder") nodeKey = "DB";
      else if (s === "Storage") nodeKey = "S";
      
      if (idx < activeIndex) {
        chart += `\n      class ${nodeKey} completed;`;
      } else if (idx === activeIndex) {
        chart += `\n      class ${nodeKey} active;`;
      } else {
        chart += `\n      class ${nodeKey} inactive;`;
      }
    });
    
    return chart;
  };

  const startAgentCrawler = async () => {
    if (runningCrawler || runningIngest) return;
    
    setRunningCrawler(true);
    setActiveStep(null);
    setLogs(["[SYSTEM] Khởi chạy AI Agentic Crawler cho Green SM Platform..."]);
    
    try {
      const response = await api.runAgentCrawler();
      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        
        for (let i = 0; i < lines.length - 1; i++) {
          const line = lines[i];
          if (line.startsWith('data: ')) {
            const dataStr = line.substring(6);
            if (dataStr === '[DONE]') {
              continue;
            }
            
            try {
              const data = JSON.parse(dataStr);
              if (data.step) {
                // Check if it's an agent step marker
                if (data.step.startsWith('[AGENT_STEP]')) {
                  const stepName = data.step.replace('[AGENT_STEP]', '').strip || data.step.split('[AGENT_STEP]')[-1] || data.step.replace('[AGENT_STEP]', '').trim();
                  setActiveStep(stepName);
                  setLogs(prev => [...prev, `[SYSTEM_AGENT] >>> BƯỚC HOẠT ĐỘNG: ${stepName} <<<`]);
                } else {
                  setLogs(prev => [...prev, data.step]);
                }
              }
              if (data.error) {
                setLogs(prev => [...prev, `[ERROR] ${data.error}`]);
              }
            } catch (e) {
              // String fallback
              if (dataStr.startsWith('[AGENT_STEP]')) {
                const stepName = dataStr.replace('[AGENT_STEP]', '').trim();
                setActiveStep(stepName);
                setLogs(prev => [...prev, `[SYSTEM_AGENT] >>> BƯỚC HOẠT ĐỘNG: ${stepName} <<<`]);
              } else {
                setLogs(prev => [...prev, dataStr]);
              }
            }
          }
        }
        buffer = lines[lines.length - 1];
      }
    } catch (err) {
      setLogs(prev => [...prev, `[ERROR] System Error: ${err.message}`]);
    } finally {
      setRunningCrawler(false);
    }
  };

  const startPlatformIngestion = async () => {
    if (runningCrawler || runningIngest) return;
    
    setRunningIngest(true);
    setLogs(["[SYSTEM] Khởi chạy nạp cơ sở dữ liệu cho chuyên mục Platform (data/platform)..."]);
    
    try {
      const response = await api.runPlatformIngestion();
      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        
        for (let i = 0; i < lines.length - 1; i++) {
          const line = lines[i];
          if (line.startsWith('data: ')) {
            const dataStr = line.substring(6);
            if (dataStr === '[DONE]') {
              continue;
            }
            
            try {
              const data = JSON.parse(dataStr);
              if (data.step) {
                setLogs(prev => [...prev, data.step]);
              }
              if (data.error) {
                setLogs(prev => [...prev, `[ERROR] ${data.error}`]);
              }
            } catch (e) {
              setLogs(prev => [...prev, dataStr]);
            }
          }
        }
        buffer = lines[lines.length - 1];
      }
    } catch (err) {
      setLogs(prev => [...prev, `[ERROR] System Error: ${err.message}`]);
    } finally {
      setRunningIngest(false);
    }
  };

  return (
    <div className="flex flex-col h-full overflow-y-auto p-4 md:p-8">
      <header className="mb-8">
        <h1 className="text-4xl font-black bg-clip-text text-transparent bg-gradient-to-r from-primary to-secondary mb-2">
          Agent Crawler (Thử nghiệm)
        </h1>
        <p className="text-on-surface-variant">AI-powered Agentic Discovery, Quality Filtering, and Knowledge Extraction for Green SM Platform.</p>
      </header>

      {/* Visual Flow Diagram */}
      <section className="mb-8 w-full">
        <div className="glass-panel p-6 rounded-2xl border border-outline-variant/30 flex flex-col gap-3">
          <h2 className="text-lg font-bold text-on-surface flex items-center gap-2">
            <Network size={20} className="text-primary" />
            Sơ đồ Trạng thái Agentic Knowledge Builder
          </h2>
          <p className="text-xs text-on-surface-variant">Biểu diễn các Agent đang chạy. Node màu vàng lục là hoàn tất, xanh lam sáng là đang xử lý.</p>
          <MermaidDiagram chart={getMermaidChart(activeStep)} />
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 flex-1">
        
        {/* Actions Panel */}
        <div className="lg:col-span-1 flex flex-col gap-6">
          <div className="glass-panel p-6 rounded-2xl border border-outline-variant/30 flex flex-col gap-4">
            <h2 className="text-xl font-bold text-on-surface flex items-center gap-2 mb-1">
              <span className="w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold">1</span>
              AI Agentic Crawler
            </h2>
            <p className="text-sm text-on-surface-variant mb-2">
              Khám phá đệ quy, cào Playwright và sử dụng LLM gpt-4o-mini để làm sạch specs/giá bán, loại bỏ form đặt cọc rỗng, giữ lại link ảnh và tự động lưu.
            </p>
            <button 
              onClick={startAgentCrawler} 
              disabled={runningCrawler || runningIngest}
              className={`w-full py-4 rounded-xl font-bold shadow-md transition-all flex justify-center items-center gap-3 ${
                (runningCrawler || runningIngest) 
                  ? 'bg-surface-variant text-on-surface-variant cursor-not-allowed' 
                  : 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white hover:shadow-lg hover:scale-[1.02] active:scale-95'
              }`}
            >
              {runningCrawler ? <Loader2 className="animate-spin" size={20} /> : <Play size={20} />}
              {runningCrawler ? 'Agent Đang Chạy...' : 'Start Agent Crawler'}
            </button>
          </div>

          <div className="glass-panel p-6 rounded-2xl border border-outline-variant/30 flex flex-col gap-4">
            <h2 className="text-xl font-bold text-on-surface flex items-center gap-2 mb-1">
              <span className="w-8 h-8 rounded-full bg-secondary/20 text-secondary flex items-center justify-center font-bold">2</span>
              Ingest Platform Data
            </h2>
            <p className="text-sm text-on-surface-variant mb-2">
              Chỉ đồng bộ các tệp tri thức đã cào sạch trong `data/platform/` vào Vector DB (Qdrant) và SQL. Không nạp lại các thư mục khác.
            </p>
            <button 
              onClick={startPlatformIngestion} 
              disabled={runningCrawler || runningIngest}
              className={`w-full py-4 rounded-xl font-bold shadow-md transition-all flex justify-center items-center gap-3 ${
                (runningCrawler || runningIngest) 
                  ? 'bg-surface-variant text-on-surface-variant cursor-not-allowed' 
                  : 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white hover:shadow-lg hover:scale-[1.02] active:scale-95'
              }`}
            >
              {runningIngest ? <Loader2 className="animate-spin" size={20} /> : <DatabaseZap size={20} />}
              {runningIngest ? 'Đang Nạp Platform...' : 'Ingest Platform Data'}
            </button>
          </div>
        </div>

        {/* Terminal Logs */}
        <section className="lg:col-span-2 w-full h-full min-h-[450px] flex flex-col">
          <div className="bg-[#0b121e] rounded-2xl overflow-hidden border border-outline-variant/30 shadow-2xl flex-1 flex flex-col">
            <div className="flex items-center px-4 py-3 bg-white/5 border-b border-white/10 shrink-0">
              <div className="flex gap-2 mr-4">
                <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
                <div className="w-3 h-3 rounded-full bg-yellow-500/80"></div>
                <div className="w-3 h-3 rounded-full bg-green-500/80"></div>
              </div>
              <div className="flex items-center gap-2 text-white/50 text-xs font-mono">
                <TerminalIcon size={14} />
                <span>agent_pipeline_orchestrator.log</span>
              </div>
            </div>
            
            <div 
              ref={terminalRef}
              className="p-6 overflow-y-auto font-mono text-xs flex-1 bg-[#05090f] text-green-300"
              style={{ scrollBehavior: 'smooth' }}
            >
              {logs.length === 0 ? (
                 <div className="text-white/20 italic">Nhấn nút "Start Agent Crawler" để chạy hệ thống thử nghiệm...</div>
              ) : (
                logs.map((log, i) => {
                  let colorClass = 'text-green-400';
                  if (log.includes('[ERROR]')) colorClass = 'text-red-400';
                  if (log.includes('[WARNING]')) colorClass = 'text-yellow-400';
                  if (log.includes('[SYSTEM_AGENT]')) colorClass = 'text-cyan-400 font-bold';
                  if (log.includes('[SYSTEM]')) colorClass = 'text-blue-400';
                  
                  return (
                    <div key={i} className={`mb-1.5 ${colorClass}`}>
                      {log}
                    </div>
                  );
                })
              )}
              {(runningCrawler || runningIngest) && (
                <div className="flex items-center gap-2 mt-4 text-white/50">
                  <span className="animate-pulse">_</span>
                </div>
              )}
            </div>
          </div>
        </section>

      </div>
    </div>
  );
}
