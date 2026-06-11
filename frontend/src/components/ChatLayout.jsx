import { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import 'regenerator-runtime/runtime';
import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useSearchParams } from 'react-router-dom';
import { User, Loader2, Link2, Plus, Mic, MicOff, Send, Car, Key, Tag, Newspaper, ShieldCheck, CheckCheck, Gift, Info, X, Sparkles, PencilLine, Image as ImageIcon, ThumbsUp, ThumbsDown } from 'lucide-react';
import { api } from '../api';
import { useAuth } from '../AuthContext';

const stripNode = (props) => {
  const rest = { ...props };
  delete rest.node;
  return rest;
};

const MessageCard = ({ icon, title, desc, image, link, index }) => {
  const IconComponent = useMemo(() => {
    switch (icon) {
      case 'car': return Car;
      case 'bike': return Car; // Bike icon would be better if available
      case 'gift': return Gift;
      case 'news': return Newspaper;
      case 'info': return Info;
      default: return Info;
    }
  }, [icon]);

  const CardWrapper = link ? 'a' : 'div';
  const wrapperProps = link ? {
    href: link,
    target: "_blank",
    rel: "noopener noreferrer",
    className: "flex items-center gap-4 p-4 my-2 bg-white/50 dark:bg-white/5 border border-outline-variant/20 rounded-2xl hover:bg-[#00c897]/5 transition-all group cursor-pointer"
  } : {
    className: "flex items-center gap-4 p-4 my-2 bg-white/50 dark:bg-white/5 border border-outline-variant/20 rounded-2xl transition-all"
  };

  return (
    <CardWrapper {...wrapperProps}>
      {image ? (
        <img
          src={image}
          alt={title || "Hình ảnh Xanh SM"}
          className="w-16 h-16 rounded-xl object-cover border border-outline-variant/20 bg-surface-container-high shrink-0"
          loading="lazy"
        />
      ) : (
        <div className={`w-12 h-12 rounded-xl bg-[#00c897]/10 flex items-center justify-center text-[#00c897] shrink-0 ${link ? 'group-hover:bg-[#00c897] group-hover:text-white' : ''} transition-all`}>
          <IconComponent size={24} />
        </div>
      )}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="w-5 h-5 rounded-full bg-[#00c897] text-white text-[10px] font-bold flex items-center justify-center shrink-0">
            {index}
          </span>
          <h4 className="font-bold text-sm text-on-surface truncate">{title}</h4>
        </div>
        <p className="text-xs text-on-surface-variant/80 line-clamp-2 leading-relaxed">
          {desc}
        </p>
      </div>
      {link && (
        <div className="text-[#00c897] opacity-0 group-hover:opacity-100 transition-opacity">
          <Plus size={16} className="rotate-45" />
        </div>
      )}
    </CardWrapper>
  );
};

export default function ChatLayout() {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [imageBase64, setImageBase64] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const fileInputRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [pipelineStep, setPipelineStep] = useState(null);
  
  // Feedback States
  const [feedbackModalOpen, setFeedbackModalOpen] = useState(false);
  const [feedbackMessageId, setFeedbackMessageId] = useState(null);
  const [feedbackRating, setFeedbackRating] = useState(null);
  const [feedbackTags, setFeedbackTags] = useState([]);
  const [feedbackComment, setFeedbackComment] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);
  const [submittedReviews, setSubmittedReviews] = useState({});

  const handleReviewClick = async (messageId, rating) => {
    if (!messageId) return;
    if (rating === 'up') {
      try {
        await api.submitReview({ message_id: messageId, rating: 'up' });
        setSubmittedReviews(prev => ({ ...prev, [messageId]: 'up' }));
      } catch(e) {
        console.error("Failed to submit review", e);
      }
    } else {
      setFeedbackMessageId(messageId);
      setFeedbackRating('down');
      setFeedbackTags([]);
      setFeedbackComment('');
      setFeedbackModalOpen(true);
    }
  };

  const submitDownReview = async () => {
    if (!feedbackMessageId) return;
    try {
      setSubmittingReview(true);
      await api.submitReview({
        message_id: feedbackMessageId,
        rating: 'down',
        reason_tags: feedbackTags,
        comment: feedbackComment
      });
      setSubmittedReviews(prev => ({ ...prev, [feedbackMessageId]: 'down' }));
      setFeedbackModalOpen(false);
    } catch(e) {
      console.error(e);
      alert('Gửi đánh giá thất bại');
    } finally {
      setSubmittingReview(false);
    }
  };

  const [searchParams, setSearchParams] = useSearchParams();
  const activeConversationId = searchParams.get('c');
  const currentConvIdRef = useRef(activeConversationId);
  const lastProcessedActiveConvIdRef = useRef(undefined);
  const messagesEndRef = useRef(null);

  const {
    transcript,
    listening,
    resetTranscript,
    browserSupportsSpeechRecognition
  } = useSpeechRecognition();

  const [recordingTime, setRecordingTime] = useState(0);
  const timerRef = useRef(null);

  const [isEditingVoiceText, setIsEditingVoiceText] = useState(false);
  const [voiceLanguage] = useState('vi-VN');

  useEffect(() => {
    if (listening && !isEditingVoiceText) {
      setTimeout(() => setRecordingTime(0), 0);
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [listening, isEditingVoiceText]);

  const formatRecordingTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  useEffect(() => {
    if (transcript && !isEditingVoiceText) {
      setTimeout(() => setInput(transcript), 0);
    }
  }, [transcript, isEditingVoiceText]);

  const handleVoiceInput = () => {
    if (listening) {
      SpeechRecognition.stopListening();
    } else {
      resetTranscript();
      setIsEditingVoiceText(false);
      SpeechRecognition.startListening({ language: voiceLanguage, continuous: true });
    }
  };

  const toggleEditingVoiceText = () => {
    if (!isEditingVoiceText) {
      SpeechRecognition.stopListening();
      setIsEditingVoiceText(true);
    } else {
      setIsEditingVoiceText(false);
      SpeechRecognition.startListening({ language: voiceLanguage, continuous: true });
    }
  };

  const cancelVoiceInput = () => {
    SpeechRecognition.stopListening();
    setTimeout(() => {
      resetTranscript();
      setInput('');
    }, 100);
  };

  const stopAndSendVoice = () => {
    // Stop recording first
    SpeechRecognition.stopListening();
    
    // We use a slightly longer delay to ensure the final transcript is captured and synced to 'input' state
    setTimeout(() => {
      // Use the transcript directly from the hook to avoid any state delay issues
      const finalContent = transcript.trim();
      if (finalContent) {
        // Trigger handle submit with the voice content
        handleSubmit(null, finalContent);
      }
      resetTranscript();
    }, 300);
  };

  const scrollToBottom = useCallback(() => {
    if (messages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages.length]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    if (activeConversationId !== lastProcessedActiveConvIdRef.current) {
      lastProcessedActiveConvIdRef.current = activeConversationId;
      currentConvIdRef.current = activeConversationId;
      if (activeConversationId) {
        // Load history
        api.getConversationMessages(activeConversationId).then(msgs => {
          const formatted = msgs.map(m => ({ 
            role: m.role, 
            content: m.content,
            created_at: m.created_at
          }));
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
    const currentImageBase64 = imageBase64;
    setInput('');
    setImageBase64(null);
    setImagePreview(null);
    const now = new Date().toISOString();
    setMessages(prev => [...prev, { role: 'user', content: userQuery, image: imagePreview, created_at: now }]);
    setLoading(true);

    try {
      const response = await api.chatStream(userQuery, currentConvIdRef.current, currentImageBase64);
      if (!response.ok) throw new Error('API Error');
      
      setMessages(prev => [...prev, { role: 'assistant', content: '', latency_ms: null, metrics: null, created_at: new Date().toISOString() }]);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let currentReply = '';
      let buffer = '';
      let sourcesObj = null;
      let metricsObj = null;

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
                  if (parsed.message_id) {
                    setMessages(prev => {
                      const newMsgs = [...prev];
                      newMsgs[newMsgs.length - 1].id = parsed.message_id;
                      return newMsgs;
                    });
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
          newMsgs.push({ role: 'assistant', content: 'Xin lỗi, hệ thống AI đang bận hoặc mất kết nối tới cơ sở dữ liệu. Vui lòng thử lại sau ít phút.', latency_ms: null, created_at: new Date().toISOString() });
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

  const formatTime = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        alert("Kích thước ảnh tối đa là 5MB.");
        return;
      }
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
        const base64String = reader.result.replace(/^data:image\/[a-z]+;base64,/, "");
        setImageBase64(base64String);
      };
      reader.readAsDataURL(file);
    }
  };

  const handlePaste = (e) => {
    if (e.clipboardData.files && e.clipboardData.files.length > 0) {
      const file = e.clipboardData.files[0];
      if (file.type.startsWith('image/')) {
        e.preventDefault();
        handleImageUpload({ target: { files: [file] } });
      }
    }
  };

  const clearImage = () => {
    setImageBase64(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const renderContent = (content) => {
    // Robust regex to handle optional colons, variable whitespace, and optional link
    const cardRegex = /:::card\s+\[icon:?\s*(.*?)\]\s+\[title:?\s*(.*?)\]\s+\[desc:?\s*(.*?)\](?:\s+\[image:?\s*(.*?)\])?(?:\s+\[link:?\s*(.*?)\])?\s+:::/g;
    const parts = [];
    let lastIndex = 0;
    let match;
    let cardIndex = 1;

    while ((match = cardRegex.exec(content)) !== null) {
      // Add text before card
      if (match.index > lastIndex) {
        parts.push(content.substring(lastIndex, match.index));
      }
      // Add card component
      parts.push(
        <MessageCard 
          key={`card-${cardIndex}`}
          icon={match[1]?.trim()}
          title={match[2]?.trim()}
          desc={match[3]?.trim()}
          image={match[4]?.trim()}
          link={match[5]?.trim()}
          index={cardIndex++}
        />
      );
      lastIndex = cardRegex.lastIndex;
    }
    // Add remaining text
    if (lastIndex < content.length) {
      parts.push(content.substring(lastIndex));
    }

    if (parts.length === 0) return (
      <ReactMarkdown 
        remarkPlugins={[remarkGfm]}
        components={markdownComponents}
      >
        {content}
      </ReactMarkdown>
    );

    return (
      <div className="flex flex-col">
        {parts.map((part, i) => (
          typeof part === 'string' ? (
            <ReactMarkdown 
              key={i}
              remarkPlugins={[remarkGfm]}
              components={markdownComponents}
            >
              {part}
            </ReactMarkdown>
          ) : part
        ))}
      </div>
    );
  };

  const markdownComponents = {
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
          <div className="w-full max-w-5xl flex flex-col gap-8">
            {messages.map((msg, idx) => {
              if (msg.role === 'assistant' && !msg.content && loading) return null;
              return (
                <div key={idx} className={`flex flex-col w-full ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  {/* Header info */}
                  <div className={`flex items-center gap-2 mb-2 px-1 text-[11px] font-bold text-on-surface-variant/50 select-none ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                    {msg.role === 'user' ? (
                      <>
                        <span>Bạn</span>
                        <span>•</span>
                        <span>{formatTime(msg.created_at)}</span>
                      </>
                    ) : (
                      <>
                        <span className="text-[#00c897]">Xanh SM</span>
                        <div className="px-1.5 py-0.5 rounded-md border border-[#00c897]/30 text-[#00c897] scale-75 origin-left flex items-center justify-center font-black">AI</div>
                        <span>•</span>
                        <span>{formatTime(msg.created_at)}</span>
                      </>
                    )}
                  </div>

                  <div className={`flex gap-3 w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'} items-start`}>
                    {msg.role !== 'user' && (
                      <div className="w-10 h-10 rounded-full bg-white dark:bg-white/10 flex items-center justify-center text-white shrink-0 shadow-md border border-[#00c897]/20 relative overflow-hidden group">
                        <img src="/Bot.png" alt="Xanh SM AI" className="w-7 h-7 object-contain group-hover:scale-110 transition-transform" />
                      </div>
                    )}
                    
                    <div className={`max-w-[85%] ${msg.role === 'user' ? 'order-1' : 'order-2'}`}>
                      <div className={`p-4 md:p-5 rounded-3xl text-sm md:text-base leading-relaxed transition-all duration-300 flex flex-col gap-4 ${
                        msg.role === 'user' 
                          ? 'bg-gradient-to-br from-[#00c897] to-[#009e79] text-white rounded-tr-none shadow-[0_4px_16px_rgba(0,200,151,0.15)] dark:shadow-[0_4px_16px_rgba(0,200,151,0.05)] border border-[#00c897]/20' 
                          : 'bg-white/88 dark:bg-white/5 backdrop-blur-md border border-white/40 dark:border-white/10 text-on-surface rounded-tl-none shadow-[0_8px_30px_rgba(0,0,0,0.04)] dark:shadow-[0_8px_30px_rgba(0,0,0,0.2)]'
                      }`}>
                        {msg.role === 'user' ? (
                          <div className="flex flex-col gap-2">
                            {msg.image && (
                              <img src={msg.image} alt="User upload" className="max-w-[200px] max-h-[200px] rounded-xl object-contain bg-black/20" />
                            )}
                            <p className="whitespace-pre-wrap font-medium">{msg.content}</p>
                          </div>
                        ) : (
                          <div className="prose prose-sm md:prose-base dark:prose-invert max-w-none">
                            {renderContent(msg.content)}
                          </div>
                        )}
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
                            <div className="flex gap-2 flex-wrap mt-1">
                              {uniqueSources.slice(0, 3).map((src, i) => (
                                <a key={i} href={src.url || '#'} target="_blank" rel="noopener noreferrer" 
                                   className="flex items-center gap-1 text-[10px] font-bold bg-surface-container-high/50 text-primary px-3 py-1.5 rounded-full border border-primary/20 hover:bg-primary hover:text-white transition-all max-w-[240px]">
                                  <Link2 size={10} className="shrink-0" />
                                  <span className="truncate">
                                    {src.source ? src.source.replace(/\.(md|html|txt)$/i, '').replace(/[-_]/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Tài liệu Xanh SM'}
                                  </span>
                                </a>
                              ))}
                            </div>
                          );
                        })()}

                        {/* Assistant Footer */}
                        {msg.role === 'assistant' && (
                          <div className="mt-2 pt-3 border-t border-outline-variant/10 flex items-center justify-between text-[10px] font-bold text-on-surface-variant/40">
                            <div className="flex items-center gap-1.5">
                              <span className="scale-110">⏱️</span>
                              <span>Tổng thời gian: {msg.latency_ms ? `${Math.round(msg.latency_ms)}ms` : 'N/A'}</span>
                            </div>
                            <div className="flex items-center gap-3">
                              {msg.id && (
                                <div className="flex items-center gap-2">
                                  <button 
                                    onClick={() => handleReviewClick(msg.id, 'up')}
                                    className={`hover:text-[#00c897] transition-colors p-1 rounded-md ${submittedReviews[msg.id] === 'up' ? 'text-[#00c897] bg-[#00c897]/10' : ''}`}
                                    title="Hữu ích"
                                    disabled={!!submittedReviews[msg.id]}
                                  >
                                    <ThumbsUp size={14} />
                                  </button>
                                  <button 
                                    onClick={() => handleReviewClick(msg.id, 'down')}
                                    className={`hover:text-red-500 transition-colors p-1 rounded-md ${submittedReviews[msg.id] === 'down' ? 'text-red-500 bg-red-50' : ''}`}
                                    title="Không hữu ích"
                                    disabled={!!submittedReviews[msg.id]}
                                  >
                                    <ThumbsDown size={14} />
                                  </button>
                                </div>
                              )}
                              <div className="flex items-center gap-1.5">
                                <span>Nguồn: Xanh SM Official</span>
                                <ShieldCheck size={12} className="text-[#00c897]" />
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                      
                      {msg.role === 'user' && (
                        <div className="flex justify-end mt-1.5 px-1">
                          <CheckCheck size={14} className="text-[#00c897]" />
                        </div>
                      )}
                    </div>

                    {msg.role === 'user' && (
                      user?.type === 'user' ? (
                        <div 
                          className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white text-sm font-black shadow-md uppercase border border-primary/20 shrink-0 order-2 overflow-hidden"
                          title={user.email}
                        >
                          {user.name ? user.name[0] : <User size={18} />}
                        </div>
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-surface-container-high flex items-center justify-center text-primary shrink-0 shadow-sm order-2 border border-primary/10">
                          <User size={20} />
                        </div>
                      )
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {showSpinner && (
          <div className="w-full max-w-5xl flex gap-3 mt-2 justify-start">
            <div className="w-10 h-10 rounded-full bg-white dark:bg-white/10 flex items-center justify-center text-white shrink-0 shadow-md border border-[#00c897]/20 relative overflow-hidden">
               <img src="/Bot.png" alt="Xanh SM AI" className="w-7 h-7 object-contain animate-bounce" />
            </div>
            <div className="p-4 rounded-3xl bg-white/88 dark:bg-white/5 backdrop-blur-md border border-white/40 dark:border-white/10 text-on-surface rounded-tl-none shadow-sm flex items-center gap-3 max-w-[85%]">
              <Loader2 className="animate-spin text-[#00c897]" size={20} />
              <div className="flex flex-col gap-2">
                <span className="text-on-surface-variant/60 italic text-sm font-medium">
                  {pipelineStep ? pipelineStep : 'Đang phân tích dữ liệu...'}
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
              className="glass-panel p-3 rounded-2xl text-left border border-white/10 dark:border-white/5 hover:border-[#00c897]/40 dark:hover:border-[#00c897]/40 hover:bg-[#00c897]/5 dark:hover:bg-[#00c897]/5 transition-all hover:-translate-y-0.5 group flex flex-col justify-between min-h-[100px] md:min-h-[120px] h-full shadow-sm"
            >
              <div className="w-8 h-8 rounded-lg bg-[#00c897]/10 flex items-center justify-center text-[#00c897] group-hover:bg-[#00c897] group-hover:text-white transition-colors shrink-0">
                <Car size={16} />
              </div>
              <div className="mt-1.5 md:mt-2 flex-grow">
                <h3 className="text-xs md:text-sm font-extrabold text-on-surface mb-0.5 truncate">Giá cước dịch vụ</h3>
                <p className="text-[10px] md:text-xs text-on-surface-variant/80 line-clamp-2 leading-relaxed font-medium">Xem bảng giá chi tiết cho từng loại dịch vụ</p>
              </div>
              <span className="text-[10px] md:text-xs font-extrabold text-[#00c897] mt-0.5 block select-none">Khám phá &rarr;</span>
            </button>

            {/* Card 2 */}
            <button 
              onClick={(e) => handleSubmit(e, "Chính sách thuê xe VinFast chạy dịch vụ trên Green SM Platform")} 
              className="glass-panel p-3 rounded-2xl text-left border border-white/10 dark:border-white/5 hover:border-blue-500/40 dark:hover:border-blue-500/40 hover:bg-blue-500/5 dark:hover:bg-blue-500/5 transition-all hover:-translate-y-0.5 group flex flex-col justify-between min-h-[100px] md:min-h-[120px] h-full shadow-sm"
            >
              <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-500 group-hover:bg-blue-500 group-hover:text-white transition-colors shrink-0">
                <Key size={16} />
              </div>
              <div className="mt-1.5 md:mt-2 flex-grow">
                <h3 className="text-xs md:text-sm font-extrabold text-on-surface mb-0.5 truncate">Thuê xe chạy dịch vụ</h3>
                <p className="text-[10px] md:text-xs text-on-surface-variant/80 line-clamp-2 leading-relaxed font-medium">Thông tin chi tiết về chính sách thuê xe điện VinFast</p>
              </div>
              <span className="text-[10px] md:text-xs font-extrabold text-blue-500 mt-0.5 block select-none">Tìm hiểu &rarr;</span>
            </button>

            {/* Card 3 */}
            <button 
              onClick={(e) => handleSubmit(e, "Chính sách ưu đãi và khuyến mãi sạc pin trạm V-GREEN")} 
              className="glass-panel p-3 rounded-2xl text-left border border-white/10 dark:border-white/5 hover:border-amber-500/40 dark:hover:border-amber-500/40 hover:bg-amber-500/5 dark:hover:bg-amber-500/5 transition-all hover:-translate-y-0.5 group flex flex-col justify-between min-h-[100px] md:min-h-[120px] h-full shadow-sm"
            >
              <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-500 group-hover:bg-amber-500 group-hover:text-white transition-colors shrink-0">
                <Tag size={16} />
              </div>
              <div className="mt-1.5 md:mt-2 flex-grow">
                <h3 className="text-xs md:text-sm font-extrabold text-on-surface mb-0.5 truncate">Ưu đãi & khuyến mãi</h3>
                <p className="text-[10px] md:text-xs text-on-surface-variant/80 line-clamp-2 leading-relaxed font-medium">Các chương trình ưu đãi mới nhất hiện nay</p>
              </div>
              <span className="text-[10px] md:text-xs font-extrabold text-amber-500 mt-0.5 block select-none">Xem ngay &rarr;</span>
            </button>

            {/* Card 4 */}
            <button 
              onClick={(e) => handleSubmit(e, "Cập nhật các tin tức và sự kiện mới nhất từ Xanh SM")} 
              className="glass-panel p-3 rounded-2xl text-left border border-white/10 dark:border-white/5 hover:border-purple-500/40 dark:hover:border-purple-500/40 hover:bg-purple-500/5 dark:hover:bg-purple-500/5 transition-all hover:-translate-y-0.5 group flex flex-col justify-between min-h-[100px] md:min-h-[120px] h-full shadow-sm"
            >
              <div className="w-8 h-8 rounded-lg bg-purple-500/10 flex items-center justify-center text-purple-500 group-hover:bg-purple-500 group-hover:text-white transition-colors shrink-0">
                <Newspaper size={16} />
              </div>
              <div className="mt-1.5 md:mt-2 flex-grow">
                <h3 className="text-xs md:text-sm font-extrabold text-on-surface mb-0.5 truncate">Tin tức Xanh SM</h3>
                <p className="text-[10px] md:text-xs text-on-surface-variant/80 line-clamp-2 leading-relaxed font-medium">Cập nhật tin tức, sự kiện và thông báo mới nhất</p>
              </div>
              <span className="text-[10px] md:text-xs font-extrabold text-purple-500 mt-0.5 block select-none">Đọc ngay &rarr;</span>
            </button>
          </div>
        )}

        {(listening || isEditingVoiceText) ? (
          /* Advanced Voice UI Overlay - Compact & Elegant */
          <div className="w-full max-w-4xl mx-auto glass-panel p-4 md:p-6 rounded-[28px] md:rounded-[32px] shadow-[0_20px_60px_rgba(0,0,0,0.06)] flex flex-col gap-3 md:gap-4 border-white/60 bg-white/95 dark:bg-[#0c1618]/95 backdrop-blur-3xl animate-in fade-in slide-in-from-bottom-4 duration-500 pointer-events-auto">
            
            <div className="flex flex-col md:flex-row items-center md:items-start gap-3 md:gap-6 text-center md:text-left">
              {/* Status & Timer Section - More Compact */}
              <div className="flex flex-row md:flex-col items-center gap-3 md:gap-2 shrink-0">
                <div className="w-12 h-12 md:w-16 md:h-16 rounded-full bg-[#00c897]/5 flex items-center justify-center text-[#00c897] relative border border-[#00c897]/10">
                  {listening && !isEditingVoiceText && (
                    <div className="absolute inset-0 rounded-full bg-[#00c897]/10 animate-ping"></div>
                  )}
                  <Mic className="w-6 h-6 md:w-8 md:h-8" strokeWidth={2.5} />
                </div>
                <div className="flex flex-col items-start md:items-center">
                  <span className="text-[9px] md:text-xs font-bold text-on-surface-variant/60 uppercase tracking-widest">Đang nghe...</span>
                  <span className="text-base md:text-lg font-black text-on-surface font-mono">{formatRecordingTime(recordingTime)}</span>
                </div>
              </div>

              {/* Transcription Display Section */}
              <div className="flex-1 flex flex-col gap-2 md:gap-3 w-full">
                <div className="flex items-center justify-center md:justify-start gap-2 text-[#00c897] text-[10px] md:text-xs font-bold">
                  <Sparkles size={14} fill="currentColor" className="animate-pulse" />
                  <span>Đang chuyển giọng nói thành văn bản...</span>
                </div>
                
                <div className="min-h-[50px] md:min-h-[60px] w-full">
                  {isEditingVoiceText ? (
                    <textarea
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      className="w-full bg-transparent border-none focus:ring-0 text-lg md:text-2xl font-bold text-on-surface p-0 resize-none outline-none placeholder:opacity-20 text-center md:text-left"
                      autoFocus
                      rows={2}
                    />
                  ) : (
                    <p className="text-lg md:text-2xl font-bold text-on-surface leading-snug break-words text-center md:text-left">
                      {input || <span className="opacity-20 italic font-medium text-lg">Hãy nói điều gì đó...</span>}
                      {listening && <span className="inline-block w-0.5 h-5 md:w-0.5 md:h-6 bg-[#00c897] ml-1 animate-pulse align-middle"></span>}
                    </p>
                  )}
                </div>

                {/* Animated Waveform - Lower height, more bars */}
                <div className="flex items-center gap-0.5 h-5 md:h-7 overflow-hidden w-full opacity-40">
                  {[...Array(window.innerWidth < 768 ? 40 : 80)].map((_, i) => (
                    <div 
                      key={i} 
                      className="w-[3px] bg-[#00c897] rounded-full transition-all duration-150"
                      style={{ 
                        height: listening ? `${20 + (i % 10) * 8}%` : '3px',
                        animation: listening ? `waveform 0.5s ease-in-out infinite alternate ${i * 0.008}s` : 'none'
                      }}
                    ></div>
                  ))}
                  <style dangerouslySetInnerHTML={{ __html: `
                    @keyframes waveform {
                      from { height: 20%; }
                      to { height: 100%; }
                    }
                  `}} />
                </div>
              </div>
            </div>

            {/* Actions Footer - More Compact */}
            <div className="flex items-center justify-center md:justify-end pt-3 md:pt-4 border-t border-on-surface/5">
              <div className="flex items-center gap-2 md:gap-3 w-full md:w-auto">
                <button 
                  onClick={toggleEditingVoiceText}
                  className={`flex-1 md:flex-none flex items-center justify-center gap-1.5 px-3 md:px-4 py-2 rounded-xl font-bold text-[11px] md:text-xs transition-all active:scale-95 ${
                    isEditingVoiceText 
                      ? 'bg-[#00c897]/10 text-[#00c897] border border-[#00c897]/20' 
                      : 'text-on-surface-variant hover:bg-surface-variant/50 border border-transparent'
                  }`}
                >
                  <PencilLine size={14} /> {isEditingVoiceText ? "Xong" : "Chỉnh sửa"}
                </button>
                <button 
                  onClick={cancelVoiceInput}
                  className="flex-1 md:flex-none flex items-center justify-center gap-1.5 px-3 md:px-5 py-2 rounded-xl border border-red-500/10 text-red-500 font-bold text-[11px] md:text-xs hover:bg-red-500/5 transition-all active:scale-95"
                >
                  <X size={14} strokeWidth={3} /> Hủy
                </button>
                <button 
                  onClick={stopAndSendVoice}
                  className="flex-1 md:flex-none flex items-center justify-center gap-2 px-5 md:px-7 py-2 rounded-xl bg-[#00c897] text-white font-black text-[11px] md:text-xs hover:brightness-105 shadow-lg shadow-[#00c897]/10 transition-all active:scale-95"
                >
                  <Send size={14} fill="white" /> Gửi
                </button>
              </div>
            </div>
          </div>
        ) : (
          /* Standard Input Box */
          <div className="w-full max-w-5xl glass-panel p-3 rounded-3xl shadow-[0_20px_50px_rgba(0,108,80,0.15)] flex flex-col gap-2 group border-white/20 dark:border-white/10 focus-within:border-[#00c897]/50 focus-within:ring-2 focus-within:ring-[#00c897]/10 transition-all bg-white/80 dark:bg-[#0c1618]/80 backdrop-blur-xl pointer-events-auto">
            {imagePreview && (
              <div className="relative w-20 h-20 mb-2 ml-2">
                <img src={imagePreview} alt="Preview" className="w-full h-full object-cover rounded-xl border border-[#00c897]/30 shadow-sm" />
                <button 
                  onClick={clearImage}
                  className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 shadow-md"
                >
                  <X size={12} />
                </button>
              </div>
            )}
            <textarea 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              onPaste={handlePaste}
              className="w-full bg-transparent border-none focus:ring-0 text-on-surface placeholder:text-on-surface-variant/60 font-bold px-2 py-1 resize-none max-h-32 min-h-[48px] outline-none text-sm" 
              placeholder="Hỏi Xanh SM bất cứ điều gì..." 
              rows={1}
            />
            
            <div className="flex items-center justify-between border-t border-outline-variant/10 pt-2 shrink-0">
              <div className="flex items-center gap-2 min-w-0 flex-1 mr-2">
                <input 
                  type="file" 
                  accept="image/*" 
                  ref={fileInputRef} 
                  onChange={handleImageUpload} 
                  className="hidden" 
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="w-8 h-8 rounded-full flex items-center justify-center text-on-surface-variant dark:text-white/60 hover:text-[#00c897] hover:bg-surface-variant/50 dark:hover:bg-white/10 transition-all active:scale-95 shrink-0"
                  title="Tải ảnh lên"
                >
                  <ImageIcon size={16} />
                </button>

                {/* Horizontally scrollable suggestion pills */}

                <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-0.5 min-w-0 select-none">
                  <button 
                    onClick={(e) => handleSubmit(e, "Giá cước Xanh Car và Xanh Bike ở các khu vực")}
                    className="px-2.5 py-1 rounded-full bg-[#00c897]/10 hover:bg-[#00c897]/20 text-on-surface-variant dark:text-white/80 hover:text-[#00c897] text-[10px] font-bold transition-all border border-[#00c897]/20 whitespace-nowrap shrink-0 flex items-center gap-1 active:scale-95"
                  >
                    <span>🚗</span> Giá cước
                  </button>
                  <button 
                    onClick={(e) => handleSubmit(e, "Chính sách ưu đãi và khuyến mãi sạc pin trạm V-GREEN")}
                    className="px-2.5 py-1 rounded-full bg-[#00c897]/10 hover:bg-[#00c897]/20 text-on-surface-variant dark:text-white/80 hover:text-[#00c897] text-[10px] font-bold transition-all border border-[#00c897]/20 whitespace-nowrap shrink-0 flex items-center gap-1 active:scale-95"
                  >
                    <span>⚡</span> Ưu đãi
                  </button>
                  <button 
                    onClick={(e) => handleSubmit(e, "Chính sách thuê xe VinFast chạy dịch vụ trên Green SM Platform")}
                    className="px-2.5 py-1 rounded-full bg-[#00c897]/10 hover:bg-[#00c897]/20 text-on-surface-variant dark:text-white/80 hover:text-[#00c897] text-[10px] font-bold transition-all border border-[#00c897]/20 whitespace-nowrap shrink-0 flex items-center gap-1 active:scale-95"
                  >
                    <span>🔑</span> Thuê xe
                  </button>
                  <button 
                    onClick={(e) => handleSubmit(e, "Chính sách mua xe 0 đồng, thuê xe tự lái và ưu đãi sạc pin trạm V-GREEN cho xe VF 5, VF 6")}
                    className="px-2.5 py-1 rounded-full bg-[#00c897]/10 hover:bg-[#00c897]/20 text-on-surface-variant dark:text-white/80 hover:text-[#00c897] text-[10px] font-bold transition-all border border-[#00c897]/20 whitespace-nowrap shrink-0 flex items-center gap-1 active:scale-95"
                  >
                    <span>⚡</span> Xe điện
                  </button>
                </div>
              </div>
              
              <div className="flex items-center gap-1.5 shrink-0">
                {browserSupportsSpeechRecognition && (
                  <button
                    onClick={handleVoiceInput}
                    className={`w-8 h-8 rounded-full flex items-center justify-center transition-all active:scale-95 ${
                      listening 
                        ? 'bg-red-500 text-white shadow-lg animate-pulse' 
                        : 'text-on-surface-variant dark:text-white/60 hover:text-[#00c897] hover:bg-surface-variant/50 dark:hover:bg-white/10'
                    }`}
                    title={listening ? "Dừng ghi âm" : "Nhập liệu bằng giọng nói"}
                  >
                    {listening ? <MicOff size={16} /> : <Mic size={16} />}
                  </button>
                )}
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
        )}
        
        <span className="text-[10px] text-on-surface-variant/60 flex items-center gap-1 select-none font-bold">
          <ShieldCheck size={12} /> Thông tin của bạn được bảo mật và chỉ sử dụng để hỗ trợ.
        </span>
      </div>

      {/* Feedback Modal */}
      {feedbackModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="bg-white dark:bg-surface-container-high rounded-2xl w-full max-w-md overflow-hidden shadow-2xl border border-outline-variant/20 flex flex-col scale-in-95 duration-200">
            <div className="p-5 border-b border-outline-variant/20 flex items-center justify-between bg-surface-container/30">
              <h3 className="font-bold text-lg text-on-surface">Đóng góp ý kiến</h3>
              <button 
                onClick={() => setFeedbackModalOpen(false)}
                className="p-2 text-on-surface-variant hover:bg-surface-variant rounded-full transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            
            <div className="p-5 space-y-5">
              <p className="text-sm text-on-surface-variant">Xin lỗi vì câu trả lời chưa đáp ứng mong đợi của bạn. Hãy cho chúng tôi biết lý do (chọn nhiều):</p>
              
              <div className="flex flex-wrap gap-2">
                {['Không đúng thực tế', 'Thiếu thông tin', 'Sai ngữ cảnh', 'Lỗi hiển thị', 'Lạc đề', 'Lý do khác'].map(tag => (
                  <button
                    key={tag}
                    onClick={() => {
                      if (feedbackTags.includes(tag)) setFeedbackTags(feedbackTags.filter(t => t !== tag));
                      else setFeedbackTags([...feedbackTags, tag]);
                    }}
                    className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all border ${
                      feedbackTags.includes(tag) 
                        ? 'bg-primary text-white border-primary shadow-md' 
                        : 'bg-transparent text-on-surface-variant border-outline-variant/40 hover:border-primary/50'
                    }`}
                  >
                    {tag}
                  </button>
                ))}
              </div>
              
              <div className="space-y-2">
                <label className="text-xs font-bold text-on-surface-variant uppercase tracking-wider">Bình luận thêm (không bắt buộc)</label>
                <textarea
                  value={feedbackComment}
                  onChange={e => setFeedbackComment(e.target.value)}
                  placeholder="Góp ý của bạn sẽ giúp Xanh SM AI thông minh hơn..."
                  className="w-full bg-surface-container/50 border border-outline-variant/30 rounded-xl p-3 text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none h-24"
                ></textarea>
              </div>
            </div>
            
            <div className="p-5 border-t border-outline-variant/20 bg-surface-container/30 flex justify-end gap-3">
              <button 
                onClick={() => setFeedbackModalOpen(false)}
                className="px-4 py-2 font-semibold text-sm text-on-surface-variant hover:bg-surface-variant rounded-xl transition-colors"
              >
                Hủy
              </button>
              <button 
                onClick={submitDownReview}
                disabled={submittingReview || (feedbackTags.length === 0 && !feedbackComment.trim())}
                className="px-6 py-2 font-bold text-sm bg-primary text-white rounded-xl shadow-md hover:shadow-lg hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
              >
                {submittingReview && <Loader2 size={16} className="animate-spin" />}
                Gửi Đánh Giá
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
