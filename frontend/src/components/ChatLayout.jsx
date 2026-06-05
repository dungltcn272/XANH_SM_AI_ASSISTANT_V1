import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useSearchParams } from 'react-router-dom';
import { User, Loader2, Link2, Plus, Mic, Send, Car, Key, Tag, Newspaper } from 'lucide-react';
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
    if (messages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
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
    <div className="relative flex-1 min-h-0 flex flex-col w-full bg-transparent overflow-hidden">
      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-8px); }
        }
        .animate-float {
          animation: float 4s ease-in-out infinite;
        }
        .no-scrollbar::-webkit-scrollbar {
          display: none;
        }
        .no-scrollbar {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}</style>
      
      {/* Scrollable content container */}
      <div className="flex-1 overflow-y-auto w-full px-4 md:px-8 pt-6 pb-44 md:pb-52 no-scrollbar flex flex-col items-center">
        
        {/* Empty State Hero */}
        {messages.length === 0 && (
          <div className="w-full max-w-5xl flex flex-col items-center relative mt-2 mb-0 select-none">
            
            {/* Welcome Intro Section */}
            <div className="w-full flex flex-row items-center justify-between gap-4 sm:gap-6 md:gap-12 text-left">
              <div className="flex-1">
                <div className="flex items-center gap-1.5 text-xs text-primary dark:text-[#00c897] font-bold tracking-wider uppercase mb-2">
                  <span className="w-2 h-2 rounded-full bg-primary dark:bg-[#00c897] animate-pulse" />
                  Xanh SM AI Assistant
                </div>
                <h1 className="text-2xl md:text-4xl font-extrabold text-on-surface leading-tight">
                  Xin chào {user?.name ? (user.name.includes(' - ') ? user.name.split(' - ')[0].split(' ').pop() : user.name.split(' ').pop()) : 'bạn'} 👋 <br />
                  <span className="text-[#00c897]">Tôi có thể giúp gì cho bạn?</span>
                </h1>
                <p className="text-xs md:text-sm text-on-surface-variant/80 mt-2 max-w-lg leading-relaxed font-medium">
                  Tôi có thể giúp bạn tìm hiểu dịch vụ, giá cước, xe điện, ưu đãi và chính sách của Xanh SM.
                </p>
              </div>
              
              {/* Robot 3D Mascot Image */}
              <div className="w-28 h-28 sm:w-36 sm:h-36 md:w-[200px] md:h-[200px] lg:w-[220px] lg:h-[220px] xl:w-[240px] xl:h-[240px] flex items-center justify-center shrink-0 animate-float select-none">
                <img 
                  src="/Bot.png" 
                  alt="Xanh SM AI Mascot" 
                  className="w-full h-full object-contain filter drop-shadow-xl hover:scale-105 transition-transform duration-300 pointer-events-none"
                />
              </div>
            </div>
          </div>
        )}

        {/* Messages List */}
        {messages.length > 0 && (
          <div className="w-full max-w-5xl flex flex-col gap-4">
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
                    <div className={`p-4 rounded-2xl text-base leading-relaxed transition-all duration-300 ${
                      msg.role === 'user' 
                        ? 'bg-gradient-to-br from-[#00c897] to-[#009e79] text-white rounded-br-sm shadow-[0_4px_16px_rgba(0,200,151,0.15)] dark:shadow-[0_4px_16px_rgba(0,200,151,0.05)] border border-[#00c897]/20 hover:scale-[1.005]' 
                        : 'bg-white/85 dark:bg-[#0c1618]/85 backdrop-blur-md border border-outline-variant/20 dark:border-[#182a2d] text-on-surface rounded-bl-sm shadow-[0_4px_20px_rgba(0,0,0,0.02)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.12)] hover:scale-[1.005]'
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
                    
                    {/* Response Time / Latency */}
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
          </div>
        )}

        {showSpinner && (
          <div className="w-full max-w-5xl flex gap-3 mt-2 justify-start">
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

      {/* Floating Chat Input centered responsively using absolute */}
      <div className="absolute bottom-6 left-0 right-0 px-4 md:px-8 flex flex-col items-center gap-4 z-40 pointer-events-none">
        
        {/* Suggestion Cards Grid (displayed only on empty state, right above input box) */}
        {messages.length === 0 && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 w-full max-w-5xl relative z-10 pointer-events-auto mb-1">
            {/* Card 1 */}
            <button 
              onClick={(e) => handleSubmit(e, "Giá cước Xanh Car và Xanh Bike ở các khu vực")} 
              className="glass-panel p-3 rounded-2xl text-left border border-outline-variant/20 dark:border-[#182a2d] hover:border-[#00c897]/40 dark:hover:border-[#00c897]/40 hover:bg-[#00c897]/5 dark:hover:bg-[#00c897]/5 transition-all hover:-translate-y-0.5 group flex flex-col justify-between min-h-[100px] md:min-h-[120px] h-full bg-white/70 dark:bg-[#0c1618]/70 shadow-sm"
            >
              <div className="w-8 h-8 rounded-lg bg-[#00c897]/10 flex items-center justify-center text-[#00c897] group-hover:bg-[#00c897] group-hover:text-white transition-colors shrink-0">
                <Car size={16} />
              </div>
              <div className="mt-1.5 md:mt-2 flex-grow">
                <h3 className="text-xs md:text-sm font-extrabold text-on-surface mb-0.5 truncate">Giá cước dịch vụ</h3>
                <p className="text-[10px] md:text-xs text-on-surface-variant/80 line-clamp-2 leading-relaxed">Xem bảng giá chi tiết cho từng loại dịch vụ</p>
              </div>
              <span className="text-[10px] md:text-xs font-extrabold text-[#00c897] mt-0.5 block select-none">Khám phá &rarr;</span>
            </button>

            {/* Card 2 */}
            <button 
              onClick={(e) => handleSubmit(e, "Chính sách thuê xe VinFast chạy dịch vụ trên Green SM Platform")} 
              className="glass-panel p-3 rounded-2xl text-left border border-outline-variant/20 dark:border-[#182a2d] hover:border-blue-500/40 dark:hover:border-blue-500/40 hover:bg-blue-500/5 dark:hover:bg-blue-500/5 transition-all hover:-translate-y-0.5 group flex flex-col justify-between min-h-[100px] md:min-h-[120px] h-full bg-white/70 dark:bg-[#0c1618]/70 shadow-sm"
            >
              <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-500 group-hover:bg-blue-500 group-hover:text-white transition-colors shrink-0">
                <Key size={16} />
              </div>
              <div className="mt-1.5 md:mt-2 flex-grow">
                <h3 className="text-xs md:text-sm font-extrabold text-on-surface mb-0.5 truncate">Thuê xe chạy dịch vụ</h3>
                <p className="text-[10px] md:text-xs text-on-surface-variant/80 line-clamp-2 leading-relaxed">Thông tin chi tiết về chính sách thuê xe điện VinFast</p>
              </div>
              <span className="text-[10px] md:text-xs font-extrabold text-blue-500 mt-0.5 block select-none">Tìm hiểu &rarr;</span>
            </button>

            {/* Card 3 */}
            <button 
              onClick={(e) => handleSubmit(e, "Chính sách ưu đãi và khuyến mãi sạc pin trạm V-GREEN")} 
              className="glass-panel p-3 rounded-2xl text-left border border-outline-variant/20 dark:border-[#182a2d] hover:border-amber-500/40 dark:hover:border-amber-500/40 hover:bg-amber-500/5 dark:hover:bg-amber-500/5 transition-all hover:-translate-y-0.5 group flex flex-col justify-between min-h-[100px] md:min-h-[120px] h-full bg-white/70 dark:bg-[#0c1618]/70 shadow-sm"
            >
              <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-500 group-hover:bg-amber-500 group-hover:text-white transition-colors shrink-0">
                <Tag size={16} />
              </div>
              <div className="mt-1.5 md:mt-2 flex-grow">
                <h3 className="text-xs md:text-sm font-extrabold text-on-surface mb-0.5 truncate">Ưu đãi & khuyến mãi</h3>
                <p className="text-[10px] md:text-xs text-on-surface-variant/80 line-clamp-2 leading-relaxed">Các chương trình ưu đãi mới nhất hiện nay</p>
              </div>
              <span className="text-[10px] md:text-xs font-extrabold text-amber-500 mt-0.5 block select-none">Xem ngay &rarr;</span>
            </button>

            {/* Card 4 */}
            <button 
              onClick={(e) => handleSubmit(e, "Cập nhật các tin tức và sự kiện mới nhất từ Xanh SM")} 
              className="glass-panel p-3 rounded-2xl text-left border border-outline-variant/20 dark:border-[#182a2d] hover:border-purple-500/40 dark:hover:border-purple-500/40 hover:bg-purple-500/5 dark:hover:bg-purple-500/5 transition-all hover:-translate-y-0.5 group flex flex-col justify-between min-h-[100px] md:min-h-[120px] h-full bg-white/70 dark:bg-[#0c1618]/70 shadow-sm"
            >
              <div className="w-8 h-8 rounded-lg bg-purple-500/10 flex items-center justify-center text-purple-500 group-hover:bg-purple-500 group-hover:text-white transition-colors shrink-0">
                <Newspaper size={16} />
              </div>
              <div className="mt-1.5 md:mt-2 flex-grow">
                <h3 className="text-xs md:text-sm font-extrabold text-on-surface mb-0.5 truncate">Tin tức Xanh SM</h3>
                <p className="text-[10px] md:text-xs text-on-surface-variant/80 line-clamp-2 leading-relaxed">Cập nhật tin tức, sự kiện và thông báo mới nhất</p>
              </div>
              <span className="text-[10px] md:text-xs font-extrabold text-purple-500 mt-0.5 block select-none">Đọc ngay &rarr;</span>
            </button>
          </div>
        )}

        <div className="w-full max-w-5xl glass-panel p-3 rounded-3xl shadow-[0_20px_50px_rgba(0,108,80,0.15)] flex flex-col gap-2 group border-outline-variant/20 dark:border-[#182a2d] focus-within:border-[#00c897]/50 focus-within:ring-2 focus-within:ring-[#00c897]/10 transition-all bg-white/95 dark:bg-[#0c1618]/95 backdrop-blur-md pointer-events-auto">
          <textarea 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full bg-transparent border-none focus:ring-0 text-on-surface placeholder:text-on-surface-variant/60 font-medium px-2 py-1 resize-none max-h-32 min-h-[48px] outline-none text-sm" 
            placeholder="Hỏi Xanh SM bất cứ điều gì..." 
            rows={1}
          />
          
          <div className="flex items-center justify-between border-t border-outline-variant/10 pt-2 shrink-0">
            <div className="flex items-center gap-2 min-w-0 flex-1 mr-2">
              <button className="w-8 h-8 rounded-full flex items-center justify-center text-on-surface-variant dark:text-white/60 hover:text-[#00c897] hover:bg-surface-variant/50 dark:hover:bg-white/10 transition-colors shrink-0">
                <Plus size={16} />
              </button>
              
              {/* Horizontally scrollable suggestion pills */}
              <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-0.5 min-w-0 select-none">
                <button 
                  onClick={(e) => handleSubmit(e, "Giá cước Xanh Car và Xanh Bike ở các khu vực")}
                  className="px-2.5 py-1 rounded-full bg-surface-variant dark:bg-white/10 hover:bg-[#00c897]/10 text-on-surface-variant dark:text-white/80 hover:text-[#00c897] text-[10px] font-bold transition-all border border-outline-variant/10 dark:border-white/15 whitespace-nowrap shrink-0 flex items-center gap-1 active:scale-95"
                >
                  <span>🚗</span> Giá cước
                </button>
                <button 
                  onClick={(e) => handleSubmit(e, "Chính sách ưu đãi và khuyến mãi sạc pin trạm V-GREEN")}
                  className="px-2.5 py-1 rounded-full bg-surface-variant dark:bg-white/10 hover:bg-[#00c897]/10 text-on-surface-variant dark:text-white/80 hover:text-[#00c897] text-[10px] font-bold transition-all border border-outline-variant/10 dark:border-white/15 whitespace-nowrap shrink-0 flex items-center gap-1 active:scale-95"
                >
                  <span>⚡</span> Ưu đãi
                </button>
                <button 
                  onClick={(e) => handleSubmit(e, "Chính sách thuê xe VinFast chạy dịch vụ trên Green SM Platform")}
                  className="px-2.5 py-1 rounded-full bg-surface-variant dark:bg-white/10 hover:bg-[#00c897]/10 text-on-surface-variant dark:text-white/80 hover:text-[#00c897] text-[10px] font-bold transition-all border border-outline-variant/10 dark:border-white/15 whitespace-nowrap shrink-0 flex items-center gap-1 active:scale-95"
                >
                  <span>🔑</span> Thuê xe
                </button>
                <button 
                  onClick={(e) => handleSubmit(e, "Chính sách mua xe 0 đồng, thuê xe tự lái và ưu đãi sạc pin trạm V-GREEN cho xe VF 5, VF 6")}
                  className="px-2.5 py-1 rounded-full bg-surface-variant dark:bg-white/10 hover:bg-[#00c897]/10 text-on-surface-variant dark:text-white/80 hover:text-[#00c897] text-[10px] font-bold transition-all border border-outline-variant/10 dark:border-white/15 whitespace-nowrap shrink-0 flex items-center gap-1 active:scale-95"
                >
                  <span>⚡</span> Xe điện
                </button>
              </div>
            </div>
            
            <div className="flex items-center gap-1 shrink-0">
              <button className="w-8 h-8 rounded-full flex items-center justify-center text-on-surface-variant dark:text-white/60 hover:text-[#00c897] hover:bg-surface-variant/50 dark:hover:bg-white/10 transition-colors">
                <Mic size={16} />
              </button>
              <button 
                onClick={handleSubmit}
                disabled={!input.trim() || loading}
                className={`w-8 h-8 rounded-full flex items-center justify-center shadow-md transition-all ${
                  input.trim() && !loading 
                    ? 'bg-[#00c897] text-white hover:brightness-110 active:scale-95' 
                    : 'bg-surface-variant dark:bg-white/10 text-on-surface-variant/40 dark:text-white/30 cursor-not-allowed'
                }`}
              >
                <Send size={16} />
              </button>
            </div>
          </div>
        </div>
        
        <span className="text-[10px] text-on-surface-variant/60 flex items-center gap-1 select-none">
          <span>🔒</span> Thông tin của bạn được bảo mật và chỉ sử dụng để hỗ trợ.
        </span>
      </div>
    </div>
  );
}
