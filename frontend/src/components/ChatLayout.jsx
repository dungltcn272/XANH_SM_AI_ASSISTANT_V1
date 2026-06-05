import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useSearchParams } from 'react-router-dom';
import { User, Loader2, Link2, PlusCircle, Mic, ArrowUp, Car, Key, BatteryCharging, ChevronRight, Truck } from 'lucide-react';
import { api } from '../api';
import { useAuth } from '../AuthContext';

const stripNode = (props) => {
  const rest = { ...props };
  delete rest.node;
  return rest;
};

const XanhSMIcon = ({ className = "w-6 h-6" }) => (
  <img 
    src="/icon.svg" 
    alt="Xanh SM" 
    className={`object-contain ${className}`}
  />
);
export default function ChatLayout() {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [pipelineStep, setPipelineStep] = useState(null);
  
  const [searchParams, setSearchParams] = useSearchParams();
  const activeConversationId = searchParams.get('c');
  const currentConvIdRef = useRef(activeConversationId);
  const lastProcessedActiveConvIdRef = useRef(undefined);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (activeConversationId !== lastProcessedActiveConvIdRef.current) {
      lastProcessedActiveConvIdRef.current = activeConversationId;
      currentConvIdRef.current = activeConversationId;
      if (activeConversationId) {
        // Load history
        api.getConversationMessages(activeConversationId).then(msgs => {
          const formatted = msgs.map(m => ({ role: m.role, content: m.content }));
          setMessages(formatted);
        }).catch(console.error);
      } else {
        // New conversation
        setTimeout(() => {
          setMessages([]);
        }, 0);
      }
    }
  }, [activeConversationId]);

  const handleSubmit = async (e, directQuery = null) => {
    e?.preventDefault();
    const query = (typeof directQuery === 'string' ? directQuery : input).trim();
    if (!query || loading) return;

    const userQuery = query;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userQuery }]);
    setLoading(true);

    try {
      const response = await api.chatStream(userQuery, currentConvIdRef.current);
      if (!response.ok) throw new Error('API Error');
      
      setMessages(prev => [...prev, { role: 'assistant', content: '', latency_ms: null, metrics: null }]);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let currentReply = '';
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        
        // SSE messages are separated by double newlines
        let boundary = buffer.indexOf('\n\n');
        while (boundary !== -1) {
          const chunk = buffer.slice(0, boundary);
          buffer = buffer.slice(boundary + 2);
          
          const lines = chunk.split('\n');
          let textDataParts = [];
          let isStep = false;
          let isMetrics = false;
          let sourcesObj = null;
          let metricsObj = null;

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6); // remove 'data: '
              if (data === '[DONE]') continue;
              
              if (data.trim().startsWith('{')) {
                try {
                  const parsed = JSON.parse(data);
                  
                  let handledAsMetadata = false;

                  if (parsed.error) {
                    textDataParts.push(parsed.error);
                    handledAsMetadata = true;
                  } 
                  if (parsed.conversation_id) {
                    currentConvIdRef.current = parsed.conversation_id;
                    lastProcessedActiveConvIdRef.current = parsed.conversation_id;
                    setSearchParams({ c: parsed.conversation_id }, { replace: true });
                    isStep = true; 
                    handledAsMetadata = true;
                  } 
                  if (parsed.step) {
                    setPipelineStep(parsed.step);
                    isStep = true;
                    handledAsMetadata = true;
                  } 
                  if (parsed.metrics) {
                    metricsObj = parsed.metrics;
                    isMetrics = true;
                    handledAsMetadata = true;
                  } 
                  if (parsed.sources) {
                    sourcesObj = parsed.sources;
                    handledAsMetadata = true;
                  } 
                  
                  if (!handledAsMetadata) {
                    textDataParts.push(data);
                  }
                } catch(e) {
                  console.error("JSON parse error:", e);
                  textDataParts.push(data);
                }
              } else {
                textDataParts.push(data);
              }
            }
          }
          
          const textData = textDataParts.join('\n');
          
          if (!isStep && !isMetrics && textData.length > 0) {
             currentReply += textData;
             setPipelineStep(null);
          }
          
          setMessages(prev => {
            const newMsgs = [...prev];
            newMsgs[newMsgs.length - 1].content = currentReply;
            if (sourcesObj) {
              newMsgs[newMsgs.length - 1].sources = sourcesObj;
            }
            // Store metrics if received
            if (metricsObj) {
              newMsgs[newMsgs.length - 1].metrics = metricsObj;
              newMsgs[newMsgs.length - 1].latency_ms = metricsObj.total_latency_ms;
            }
            return newMsgs;
          });

          
          boundary = buffer.indexOf('\n\n');
        }
      }
      
      // Mark loading complete when stream finishes
      setLoading(false);
      setPipelineStep(null);
      window.dispatchEvent(new Event('refresh-conversations'));
    } catch (error) {
      console.error('Chat stream error:', error);
      setMessages(prev => {
        const newMsgs = [...prev];
        const lastMsg = newMsgs.length > 0 ? newMsgs[newMsgs.length - 1] : null;
        if (lastMsg && lastMsg.role === 'assistant' && lastMsg.content === '') {
          lastMsg.content = 'Xin lỗi, hệ thống AI đang bận hoặc mất kết nối tới cơ sở dữ liệu. Vui lòng thử lại sau ít phút.';
        } else if (!lastMsg || lastMsg.role === 'user') {
          newMsgs.push({ role: 'assistant', content: 'Xin lỗi, hệ thống AI đang bận hoặc mất kết nối tới cơ sở dữ liệu. Vui lòng thử lại sau ít phút.', latency_ms: null });
        }
        return newMsgs;
      });
      setLoading(false);
      setPipelineStep(null);
      window.dispatchEvent(new Event('refresh-conversations'));
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const lastMsg = messages[messages.length - 1];
  const showSpinner = loading && (!lastMsg || lastMsg.role !== 'assistant' || !lastMsg.content);

  return (
    <div className="relative flex-1 min-h-0 flex flex-col items-center pt-2 md:pt-8 pb-24 md:pb-32 px-4 md:px-16 overflow-y-auto w-full">
      
      {/* Empty State Hero */}
      {messages.length === 0 && (
        <div className="w-full max-w-4xl text-center flex flex-col items-center gap-3 md:gap-8 relative mt-2 md:mt-12 mb-2 md:mb-8">
          <div className="relative z-10">
            <div className="w-12 h-12 md:w-24 md:h-24 mb-2 md:mb-6 rounded-xl md:rounded-3xl bg-gradient-to-tr from-primary/20 to-secondary/20 flex items-center justify-center glass shadow-xl mx-auto border-2 border-primary/20 animate-pulse">
              <XanhSMIcon className="w-6 h-6 md:w-12 md:h-12" />
            </div>
            <h1 className="text-xl md:text-4xl font-bold text-on-surface max-w-3xl leading-tight">
              Chào mừng bạn đến với <span className="text-primary font-extrabold">Xanh SM AI</span>.<br className="hidden md:block" />
              Hôm nay bạn muốn khám phá điều gì?
            </h1>
            <div className="mt-2 md:mt-4 w-32 h-1 bg-gradient-to-r from-transparent via-primary/40 to-transparent mx-auto rounded-full"></div>
          </div>

          {/* Desktop Grid Layout (Large Screens) */}
          <div className="hidden md:grid grid-cols-3 gap-6 w-full mt-12 relative z-10">
            <button 
              onClick={(e) => handleSubmit(e, "Giá cước các dịch vụ Xanh SM Taxi, Xanh SM Luxury và xe máy Xanh SM Bike mới nhất là bao nhiêu?")} 
              className="glass-panel p-6 rounded-2xl text-left hover:border-primary/50 transition-all hover:-translate-y-1 group flex flex-col items-start gap-0"
            >
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-primary mb-4 group-hover:bg-primary group-hover:text-white transition-colors shrink-0">
                <Car size={20} />
              </div>
              <div>
                <h3 className="text-xl font-bold text-on-surface mb-2">Giá cước Di chuyển</h3>
                <p className="text-sm text-on-surface-variant">Tra cứu bảng giá cước chi tiết của các dịch vụ taxi điện và xe máy điện Xanh SM.</p>
              </div>
            </button>

            <button 
              onClick={(e) => handleSubmit(e, "Quy định vận chuyển của xe bán tải điện VinFast EC Van và dịch vụ giao hàng Xanh Express như thế nào?")} 
              className="glass-panel p-6 rounded-2xl text-left hover:border-primary/50 transition-all hover:-translate-y-1 group flex flex-col items-start gap-0"
            >
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-primary mb-4 group-hover:bg-primary group-hover:text-white transition-colors shrink-0">
                <Truck size={20} />
              </div>
              <div>
                <h3 className="text-xl font-bold text-on-surface mb-2">Giao hàng & Xe Van điện</h3>
                <p className="text-sm text-on-surface-variant">Tìm hiểu dịch vụ giao hàng siêu tốc và xe Van chở hàng cồng kềnh tới 580kg.</p>
              </div>
            </button>

            <button 
              onClick={(e) => handleSubmit(e, "Chính sách mua xe 0 đồng, thuê xe tự lái và ưu đãi sạc pin trạm V-GREEN cho xe VF 5, VF 6 là gì?")} 
              className="glass-panel p-6 rounded-2xl text-left hover:border-primary/50 transition-all hover:-translate-y-1 group flex flex-col items-start gap-0"
            >
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-primary mb-4 group-hover:bg-primary group-hover:text-white transition-colors shrink-0">
                <BatteryCharging size={20} />
              </div>
              <div>
                <h3 className="text-xl font-bold text-on-surface mb-2">Chính sách VF 5 & VF 6</h3>
                <p className="text-sm text-on-surface-variant">Khám phá ưu đãi sạc pin trạm V-GREEN, chương trình mua xe 0 đồng, thuê xe chạy dịch vụ.</p>
              </div>
            </button>
          </div>

          {/* Mobile Stack Layout (Sleek, Compact, No Space Wasted) */}
          <div className="flex md:hidden flex-col gap-2.5 w-full mt-4 relative z-10 px-1">
            <button 
              onClick={(e) => handleSubmit(e, "Giá cước các dịch vụ Xanh SM Taxi, Xanh SM Luxury và xe máy Xanh SM Bike mới nhất là bao nhiêu?")} 
              className="glass-panel py-3 px-4 rounded-xl flex items-center justify-between gap-3 text-left w-full border border-primary/10 hover:bg-primary/5 active:scale-[0.99] transition-all shadow-sm bg-white/70 dark:bg-transparent"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary shrink-0">
                  <Car size={16} />
                </div>
                <div className="min-w-0">
                  <h4 className="text-sm font-bold text-on-surface truncate">Giá cước Di chuyển</h4>
                  <p className="text-xs text-on-surface-variant/80 truncate">Bảng giá cước taxi Xanh SM & Xanh SM Bike...</p>
                </div>
              </div>
              <ChevronRight size={14} className="text-on-surface-variant/40 shrink-0" />
            </button>

            <button 
              onClick={(e) => handleSubmit(e, "Quy định vận chuyển của xe bán tải điện VinFast EC Van và dịch vụ giao hàng Xanh Express như thế nào?")} 
              className="glass-panel py-3 px-4 rounded-xl flex items-center justify-between gap-3 text-left w-full border border-primary/10 hover:bg-primary/5 active:scale-[0.99] transition-all shadow-sm bg-white/70 dark:bg-transparent"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary shrink-0">
                  <Truck size={16} />
                </div>
                <div className="min-w-0">
                  <h4 className="text-sm font-bold text-on-surface truncate">Giao hàng & Xe Van điện</h4>
                  <p className="text-xs text-on-surface-variant/80 truncate">Dịch vụ Xanh Express & xe Van chở hàng...</p>
                </div>
              </div>
              <ChevronRight size={14} className="text-on-surface-variant/40 shrink-0" />
            </button>

            <button 
              onClick={(e) => handleSubmit(e, "Chính sách mua xe 0 đồng, thuê xe tự lái và ưu đãi sạc pin trạm V-GREEN cho xe VF 5, VF 6 là gì?")} 
              className="glass-panel py-3 px-4 rounded-xl flex items-center justify-between gap-3 text-left w-full border border-primary/10 hover:bg-primary/5 active:scale-[0.99] transition-all shadow-sm bg-white/70 dark:bg-transparent"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary shrink-0">
                  <BatteryCharging size={16} />
                </div>
                <div className="min-w-0">
                  <h4 className="text-sm font-bold text-on-surface truncate">Chính sách VF 5 & VF 6</h4>
                  <p className="text-xs text-on-surface-variant/80 truncate">Mua xe 0đ, trạm sạc V-GREEN, thuê xe...</p>
                </div>
              </div>
              <ChevronRight size={14} className="text-on-surface-variant/40 shrink-0" />
            </button>
          </div>
        </div>
      )}

      {/* Messages List */}
      <div className="w-full max-w-4xl flex flex-col gap-4">
        {messages.map((msg, idx) => {
          if (msg.role === 'assistant' && !msg.content && loading) return null;
          return (
            <div key={idx} className={`flex gap-3 w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'} items-start`}>
            {msg.role !== 'user' && (
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white shrink-0 shadow-lg">
                <XanhSMIcon />
              </div>
            )}
            
            <div className={`max-w-[85%] ${msg.role === 'user' ? 'order-1' : 'order-2'}`}>
              <div className={`p-4 rounded-2xl text-base leading-relaxed ${
                msg.role === 'user' 
                  ? 'bg-primary text-white rounded-br-sm shadow-md' 
                  : 'bg-surface-container-lowest border border-outline-variant text-on-surface rounded-bl-sm shadow-sm'
              }`}>
                {msg.role === 'user' ? (
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                ) : (
                  <div className="prose prose-sm md:prose-base dark:prose-invert max-w-none">
                    <ReactMarkdown 
                      remarkPlugins={[remarkGfm]}
                      components={{
                        ol: (props) => <ol className="list-decimal pl-5 my-2 ml-4" {...stripNode(props)} />,
                        ul: (props) => <ul className="list-disc pl-5 my-2 ml-4" {...stripNode(props)} />,
                        li: (props) => <li className="my-1" {...stripNode(props)} />,
                        table: (props) => (
                          <div className="overflow-x-auto my-4 w-full border border-primary/20 rounded-xl shadow-sm">
                            <table className="w-full text-sm text-left m-0" {...stripNode(props)} />
                          </div>
                        ),
                        thead: (props) => <thead className="text-xs uppercase bg-primary/10 text-primary" {...stripNode(props)} />,
                        th: (props) => <th className="px-6 py-4 font-bold border-b border-primary/10 m-0" {...stripNode(props)} />,
                        td: (props) => <td className="px-6 py-4 border-b border-surface-variant/50 m-0" {...stripNode(props)} />,
                        tr: (props) => <tr className="hover:bg-surface-container-high/30 transition-colors m-0" {...stripNode(props)} />,
                        a: (props) => (
                          <a 
                            className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-semibold italic underline transition-all"
                            target="_blank"
                            rel="noopener noreferrer"
                            {...stripNode(props)}
                          />
                        ),

                        img: (props) => (
                          <div className="my-4 flex flex-col items-center">
                            <img 
                              className="max-h-[320px] object-contain rounded-2xl border border-primary/10 shadow-md hover:scale-[1.01] transition-transform cursor-zoom-in bg-black/20"
                              alt={props.alt || "Hình ảnh từ Xanh SM"}
                              onClick={() => window.open(props.src, '_blank')}
                              {...stripNode(props)}
                            />
                            {props.alt && (
                              <span className="text-xs text-on-surface-variant/60 italic mt-2 text-center">
                                {props.alt}
                              </span>
                            )}
                          </div>
                        )
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                )}
              </div>

              {/* Citations / Sources */}
              {msg.sources && msg.sources.length > 0 && (() => {
                const uniqueSources = [];
                const seenSources = new Set();
                for (const src of msg.sources) {
                  const normalizedSource = (src.source || '').toLowerCase().trim();
                  if (normalizedSource && !seenSources.has(normalizedSource)) {
                    seenSources.add(normalizedSource);
                    uniqueSources.push(src);
                  }
                }
                return (
                  <div className="flex gap-2 flex-wrap mt-2">
                    {uniqueSources.slice(0, 3).map((src, i) => (
                      <a key={i} href={src.url || '#'} target="_blank" rel="noopener noreferrer" 
                         className="flex items-center gap-1 text-xs font-medium bg-surface-container-high text-primary px-3 py-1.5 rounded-full border border-primary/20 hover:bg-primary hover:text-white transition-colors">
                        <Link2 size={12} />
                        {src.source ? src.source.replace(/\.(md|html|txt)$/i, '').replace(/[-_]/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Tài liệu Xanh SM'}
                      </a>
                    ))}
                  </div>
                );
              })()}

              {/* Image Gallery from Chunk Sources removed */}
              
              {/* Response Time / Latency - for assistant messages only */}
              {msg.role === 'assistant' && msg.latency_ms && (
                <div className="text-xs text-on-surface-variant italic mt-2 flex items-center gap-1">
                  <span>⏱️</span>
                  <span>Phản hồi: {msg.latency_ms.toFixed(0)}ms</span>
                </div>
              )}
            </div>

            {msg.role === 'user' && (
              user?.type === 'user' ? (
                <div 
                  className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white text-sm font-bold shadow-md uppercase border border-primary/20 shrink-0 order-2"
                  title={user.email}
                >
                  {user.name ? user.name[0] : <User size={18} />}
                </div>
              ) : (
                <div className="w-10 h-10 rounded-xl bg-surface-container-high flex items-center justify-center text-primary shrink-0 shadow-sm order-2 border border-primary/10">
                  <User size={20} />
                </div>
              )
            )}
          </div>
          );
        })}

        {showSpinner && (
          <div className="flex gap-4 w-full justify-start">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white shrink-0 shadow-lg">
              <XanhSMIcon />
            </div>
            <div className="p-4 rounded-2xl bg-surface-container-lowest border border-outline-variant text-on-surface rounded-bl-sm shadow-sm flex items-center gap-3 max-w-[85%]">
              <Loader2 className="animate-spin text-primary" size={20} />
              <div className="flex flex-col gap-2">
                <span className="text-on-surface-variant italic">
                  {pipelineStep ? pipelineStep : 'Đang phân tích...'}
                </span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Floating Chat Input */}
      <div className="fixed bottom-8 left-0 md:left-72 right-0 px-4 md:px-0 flex justify-center z-50">
        <div className="w-full max-w-3xl glass-panel p-2 rounded-3xl shadow-[0_20px_50px_rgba(0,108,80,0.15)] flex items-end gap-2 group border-primary/10 focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20 transition-all bg-white/80 dark:bg-transparent">
          <button className="w-12 h-12 flex items-center justify-center text-on-surface-variant hover:text-primary transition-colors shrink-0">
            <PlusCircle size={24} />
          </button>
          
          <textarea 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-grow bg-transparent border-none focus:ring-0 text-on-surface placeholder:text-on-surface-variant font-medium py-3 px-0 resize-none max-h-32 min-h-[48px] outline-none" 
            placeholder="Hỏi Xanh SM bất cứ điều gì..." 
            rows={1}
          />
          
          <div className="flex items-center gap-1 px-2 shrink-0 pb-1">
            <button className="w-10 h-10 flex items-center justify-center text-on-surface-variant hover:text-primary transition-colors">
              <Mic size={20} />
            </button>
            <button 
              onClick={handleSubmit}
              disabled={!input.trim() || loading}
              className={`w-10 h-10 rounded-full flex items-center justify-center shadow-lg transition-all ${
                input.trim() && !loading 
                  ? 'bg-gradient-to-br from-primary to-secondary text-white hover:brightness-110 active:scale-95' 
                  : 'bg-surface-variant text-on-surface-variant/50 cursor-not-allowed'
              }`}
            >
              <ArrowUp size={20} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
