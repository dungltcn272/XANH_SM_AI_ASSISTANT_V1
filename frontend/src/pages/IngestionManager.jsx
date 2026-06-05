import { useState, useRef, useEffect } from 'react';
import { TerminalIcon, Globe, DatabaseZap, Loader2 } from 'lucide-react';
import { api } from '../api';

export default function IngestionManager() {
  const [logs, setLogs] = useState([]);
  const [runningCrawler, setRunningCrawler] = useState(false);
  const [runningIngest, setRunningIngest] = useState(false);
  const terminalRef = useRef(null);

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs]);

  const runCrawler = async () => {
    if (runningCrawler || runningIngest) return;
    
    setRunningCrawler(true);
    setLogs([]);
    
    try {
      const response = await api.runCrawler();
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
                setLogs(prev => [...prev, `[SYSTEM] ${data.step}`]);
              }
              if (data.error) {
                setLogs(prev => [...prev, `[ERROR] ${data.error}`]);
              }
            } catch {
              setLogs(prev => [...prev, dataStr]);
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

  const runIngestion = async () => {
    if (runningCrawler || runningIngest) return;
    
    setRunningIngest(true);
    setLogs([]);
    
    try {
      const response = await api.runIngestion();
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
                setLogs(prev => [...prev, `[SYSTEM] ${data.step}`]);
              }
              if (data.error) {
                setLogs(prev => [...prev, `[ERROR] ${data.error}`]);
              }
            } catch {
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
          Knowledge Ingestion
        </h1>
        <p className="text-on-surface-variant">Automated Web Crawling and Vector Database Ingestion Pipeline.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Actions Panel */}
        <div className="lg:col-span-1 flex flex-col gap-6">
          <div className="glass-panel p-6 rounded-2xl border border-outline-variant/30 flex flex-col gap-4">
            <h2 className="text-xl font-bold text-on-surface flex items-center gap-2 mb-2">
              <span className="w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center">1</span>
              Web Crawler
            </h2>
            <p className="text-sm text-on-surface-variant mb-2">
              Chạy script cào dữ liệu từ trang web Xanh SM (dựa trên urls.json). Tải HTML và chuyển đổi thành Markdown.
            </p>
            <button 
              onClick={runCrawler} 
              disabled={runningCrawler || runningIngest}
              className={`w-full py-4 rounded-xl font-bold shadow-md transition-all flex justify-center items-center gap-3 ${
                (runningCrawler || runningIngest) 
                  ? 'bg-surface-variant text-on-surface-variant cursor-not-allowed' 
                  : 'bg-gradient-to-r from-blue-500 to-indigo-500 text-white hover:shadow-lg hover:scale-[1.02] active:scale-95'
              }`}
            >
              {runningCrawler ? <Loader2 className="animate-spin" size={20} /> : <Globe size={20} />}
              {runningCrawler ? 'Đang Cào Dữ Liệu...' : 'Start Web Crawler'}
            </button>
          </div>

          <div className="glass-panel p-6 rounded-2xl border border-outline-variant/30 flex flex-col gap-4">
            <h2 className="text-xl font-bold text-on-surface flex items-center gap-2 mb-2">
              <span className="w-8 h-8 rounded-full bg-secondary/20 text-secondary flex items-center justify-center">2</span>
              Data Ingestion
            </h2>
            <p className="text-sm text-on-surface-variant mb-2">
              Cắt nhỏ dữ liệu (Chunking) bằng HeadingAwareSplitter và nạp (Embedding) song song Dense + Sparse vào Qdrant.
            </p>
            <button 
              onClick={runIngestion} 
              disabled={runningCrawler || runningIngest}
              className={`w-full py-4 rounded-xl font-bold shadow-md transition-all flex justify-center items-center gap-3 ${
                (runningCrawler || runningIngest) 
                  ? 'bg-surface-variant text-on-surface-variant cursor-not-allowed' 
                  : 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white hover:shadow-lg hover:scale-[1.02] active:scale-95'
              }`}
            >
              {runningIngest ? <Loader2 className="animate-spin" size={20} /> : <DatabaseZap size={20} />}
              {runningIngest ? 'Đang Nạp Dữ Liệu...' : 'Start Ingestion'}
            </button>
          </div>
        </div>

        {/* Terminal View */}
        <section className="lg:col-span-2 w-full h-full min-h-[600px] flex flex-col">
          <div className="bg-[#0b121e] rounded-2xl overflow-hidden border border-outline-variant/30 shadow-2xl flex-1 flex flex-col">
            <div className="flex items-center px-4 py-3 bg-white/5 border-b border-white/10 shrink-0">
              <div className="flex gap-2 mr-4">
                <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
                <div className="w-3 h-3 rounded-full bg-yellow-500/80"></div>
                <div className="w-3 h-3 rounded-full bg-green-500/80"></div>
              </div>
              <div className="flex items-center gap-2 text-white/50 text-xs font-mono">
                <TerminalIcon size={14} />
                <span>pipeline_orchestrator.sh</span>
              </div>
            </div>
            
            <div 
              ref={terminalRef}
              className="p-6 overflow-y-auto font-mono text-sm flex-1"
              style={{ scrollBehavior: 'smooth' }}
            >
              {logs.length === 0 ? (
                 <div className="text-white/30 italic">Nhấn nút bên trái để khởi động quá trình xử lý...</div>
              ) : (
                logs.map((log, i) => {
                  let colorClass = 'text-green-400';
                  if (log.includes('[ERROR]')) colorClass = 'text-red-400';
                  if (log.includes('[SYSTEM]') || log.includes('[INFO]')) colorClass = 'text-blue-400';
                  if (log.includes('[WARNING]')) colorClass = 'text-yellow-400';
                  
                  return (
                    <div key={i} className={`mb-2 ${colorClass}`}>
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
