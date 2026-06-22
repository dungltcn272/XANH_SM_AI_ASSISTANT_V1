import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight, Server, Database, Layers, BrainCircuit, Activity, Cpu, ArrowRight, CheckCircle2, MessageSquare, MapPin, Zap } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const mockChartData = [
  { time: '10:00', latency: 45, requests: 120 },
  { time: '10:05', latency: 52, requests: 150 },
  { time: '10:10', latency: 38, requests: 180 },
  { time: '10:15', latency: 65, requests: 220 },
  { time: '10:20', latency: 48, requests: 170 },
  { time: '10:25', latency: 42, requests: 140 },
];

const slides = [
  {
    id: 1,
    title: "Xanh SM AI Assistant",
    subtitle: "Enterprise-Grade Conversational System",
    icon: <Server className="w-16 h-16 text-emerald-400 mx-auto mb-4" />,
    content: (
      <div className="space-y-6 text-left">
        <p className="text-xl text-gray-300 text-center">Một trợ lý ảo đa năng tích hợp nhiều phân hệ động.</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
          <div className="bg-gray-800/50 p-4 rounded-xl border border-gray-700 flex flex-col items-center text-center">
            <div className="bg-blue-900/50 p-3 rounded-full mb-3"><Layers className="text-blue-400" /></div>
            <h3 className="text-emerald-400 font-bold mb-2">Frontend</h3>
            <p className="text-sm text-gray-400">React 19, Tailwind CSS<br/>Framer Motion</p>
          </div>
          <div className="bg-gray-800/50 p-4 rounded-xl border border-gray-700 flex flex-col items-center text-center">
            <div className="bg-green-900/50 p-3 rounded-full mb-3"><Server className="text-green-400" /></div>
            <h3 className="text-emerald-400 font-bold mb-2">Backend</h3>
            <p className="text-sm text-gray-400">FastAPI, Python<br/>SQLAlchemy</p>
          </div>
          <div className="bg-gray-800/50 p-4 rounded-xl border border-gray-700 flex flex-col items-center text-center">
            <div className="bg-yellow-900/50 p-3 rounded-full mb-3"><Database className="text-yellow-400" /></div>
            <h3 className="text-emerald-400 font-bold mb-2">Databases</h3>
            <p className="text-sm text-gray-400">PostgreSQL (RDBMS)<br/>Qdrant (Vector DB)</p>
          </div>
          <div className="bg-gray-800/50 p-4 rounded-xl border border-gray-700 flex flex-col items-center text-center">
            <div className="bg-purple-900/50 p-3 rounded-full mb-3"><Cpu className="text-purple-400" /></div>
            <h3 className="text-emerald-400 font-bold mb-2">Infra</h3>
            <p className="text-sm text-gray-400">Railway, Vercel<br/>Docker Compose</p>
          </div>
        </div>
      </div>
    )
  },
  {
    id: 2,
    title: "Unified NLU Orchestrator",
    subtitle: "Bộ não định tuyến thông minh với LLM",
    icon: <BrainCircuit className="w-16 h-16 text-purple-400 mx-auto mb-4" />,
    content: (
      <div className="mt-4 flex flex-col items-center">
        {/* Flowchart UI */}
        <div className="flex items-center gap-4 mb-8 w-full max-w-4xl justify-center">
          <div className="bg-gray-800 p-4 rounded-lg border border-gray-600 text-center w-32">
            <MessageSquare className="mx-auto mb-2 text-gray-400" />
            <span className="text-sm font-bold">User Input</span>
          </div>
          <ArrowRight className="text-purple-500" />
          <div className="bg-purple-900/50 p-5 rounded-xl border-2 border-purple-500 text-center w-48 shadow-[0_0_15px_rgba(168,85,247,0.4)]">
            <BrainCircuit className="mx-auto mb-2 text-purple-400" size={32} />
            <span className="font-bold text-purple-200">LLM Router</span>
            <p className="text-xs text-purple-300 mt-1">Intent & Slot Filling</p>
          </div>
          <ArrowRight className="text-purple-500" />
          <div className="flex flex-col gap-3">
            <div className="bg-blue-900/40 border border-blue-500 p-2 rounded w-40 text-center text-sm font-bold text-blue-300 flex items-center justify-center gap-2">
              <Layers size={16}/> RAG Pipeline
            </div>
            <div className="bg-orange-900/40 border border-orange-500 p-2 rounded w-40 text-center text-sm font-bold text-orange-300 flex items-center justify-center gap-2">
              <MapPin size={16}/> Food Pipeline
            </div>
            <div className="bg-green-900/40 border border-green-500 p-2 rounded w-40 text-center text-sm font-bold text-green-300 flex items-center justify-center gap-2">
              <MessageSquare size={16}/> Smalltalk
            </div>
          </div>
        </div>
        <p className="text-gray-400 text-center max-w-2xl">
          Thay vì dùng nhiều mô hình nhỏ, hệ thống dùng 1 prompt cực mạnh để phân loại ngữ cảnh, bóc tách `Location`, `Budget`, `Category` hoặc truy vấn tìm kiếm chỉ trong 1 lần gọi (Zero-shot Routing).
        </p>
      </div>
    )
  },
  {
    id: 3,
    title: "Hybrid RAG Pipeline",
    subtitle: "Tối ưu độ chính xác và độ phủ",
    icon: <Layers className="w-16 h-16 text-blue-400 mx-auto mb-4" />,
    content: (
      <div className="flex flex-col items-center w-full">
        <div className="flex flex-col md:flex-row items-center justify-center gap-4 w-full mb-6">
          <div className="bg-gray-800 border border-gray-600 p-3 rounded-lg text-center w-40">
            <span className="text-blue-400 font-bold block text-sm">1. Semantic Cache</span>
            <span className="text-xs text-gray-400">Trả lời ngay ~5ms</span>
          </div>
          <ArrowRight className="hidden md:block text-gray-500" />
          <div className="bg-indigo-900/30 border border-indigo-500 p-3 rounded-lg text-center w-48">
            <span className="text-indigo-400 font-bold block text-sm">2. Hybrid Search</span>
            <span className="text-xs text-gray-400">Qdrant (Dense) + BM25 (Sparse)</span>
          </div>
          <ArrowRight className="hidden md:block text-gray-500" />
          <div className="bg-purple-900/30 border border-purple-500 p-3 rounded-lg text-center w-40">
            <span className="text-purple-400 font-bold block text-sm">3. Reranker</span>
            <span className="text-xs text-gray-400">Cohere Cross-Encoder</span>
          </div>
          <ArrowRight className="hidden md:block text-gray-500" />
          <div className="bg-pink-900/30 border border-pink-500 p-3 rounded-lg text-center w-40">
            <span className="text-pink-400 font-bold block text-sm">4. Synthesis</span>
            <span className="text-xs text-gray-400">LLM Stream & Citations</span>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4 w-full max-w-3xl mt-4">
          <div className="bg-gray-800/50 p-4 rounded-xl">
            <CheckCircle2 className="text-emerald-500 mb-2 inline-block mr-2" size={18}/>
            <span className="font-bold text-gray-200">Sparse Search (Từ khoá)</span>
            <p className="text-sm text-gray-400 mt-1">Tìm chính xác các mã lỗi, tên riêng, thuật ngữ đặc thù.</p>
          </div>
          <div className="bg-gray-800/50 p-4 rounded-xl">
            <CheckCircle2 className="text-emerald-500 mb-2 inline-block mr-2" size={18}/>
            <span className="font-bold text-gray-200">Dense Search (Ngữ nghĩa)</span>
            <p className="text-sm text-gray-400 mt-1">Hiểu được ý định dù người dùng dùng từ đồng nghĩa.</p>
          </div>
        </div>
      </div>
    )
  },
  {
    id: 4,
    title: "Food Pipeline (Heuristic Core)",
    subtitle: "Luồng hoạt động Rule-based (Khởi động lạnh)",
    icon: <Database className="w-16 h-16 text-yellow-400 mx-auto mb-4" />,
    content: (
      <div className="text-left w-full max-w-4xl mx-auto">
        <div className="flex flex-col md:flex-row items-stretch gap-6">
          <div className="flex-1 bg-gray-800/50 p-5 rounded-xl border border-gray-700 relative">
            <div className="absolute top-[-12px] left-4 bg-yellow-500 text-black text-xs font-bold px-3 py-1 rounded">PHASE 1: RETRIEVAL</div>
            <div className="mt-4 space-y-4 text-sm text-gray-300">
              <div className="flex items-center gap-3 bg-gray-900/50 p-3 rounded">
                <MapPin className="text-yellow-500" size={24}/>
                <div>
                  <span className="font-bold block text-yellow-400">Geo-Filtering</span>
                  Tính toán Haversine Formula loại bỏ các quán quá xa bán kính cho phép.
                </div>
              </div>
              <div className="flex items-center gap-3 bg-gray-900/50 p-3 rounded">
                <Layers className="text-yellow-500" size={24}/>
                <div>
                  <span className="font-bold block text-yellow-400">BM25 Scoring</span>
                  Chấm điểm Keyword Matching trên Tên món, Mô tả, Ingredient Tags.
                </div>
              </div>
            </div>
          </div>
          
          <div className="flex items-center justify-center"><ArrowRight className="text-gray-500" size={32}/></div>

          <div className="flex-1 bg-gray-800/50 p-5 rounded-xl border border-gray-700 relative">
            <div className="absolute top-[-12px] left-4 bg-orange-500 text-white text-xs font-bold px-3 py-1 rounded">PHASE 2: RANKING</div>
            <div className="mt-4 text-sm text-gray-300">
              <p className="mb-2">Tính tổng điểm từ 10 tiêu chí trọng số:</p>
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-orange-900/20 p-2 border border-orange-500/30 rounded text-center">Gần xa (16%)</div>
                <div className="bg-orange-900/20 p-2 border border-orange-500/30 rounded text-center">Phí ship (10%)</div>
                <div className="bg-orange-900/20 p-2 border border-orange-500/30 rounded text-center">ETA (8%)</div>
                <div className="bg-orange-900/20 p-2 border border-orange-500/30 rounded text-center">Lịch sử (15%)</div>
              </div>
              <div className="mt-3 bg-red-900/30 border border-red-500/50 p-2 rounded text-xs text-red-200">
                <Zap size={14} className="inline mr-1"/> Exponential Penalty (x1.5) nếu sai Category!
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  },
  {
    id: 5,
    title: "Food Pipeline (ML-Ready)",
    subtitle: "Kiến trúc cắm-và-chạy cho Deep Learning",
    icon: <Cpu className="w-16 h-16 text-red-400 mx-auto mb-4" />,
    content: (
      <div className="text-left w-full max-w-4xl mx-auto flex gap-6 mt-4">
        <div className="w-1/3 flex flex-col justify-center">
          <div className="bg-gray-800 border-l-4 border-red-500 p-4 rounded-r-lg shadow-lg mb-4 opacity-70 relative">
            <div className="absolute top-2 right-2 text-xs text-gray-500">Heuristic</div>
            <h4 className="font-bold text-gray-300 mb-1">Rule-based Score</h4>
            <div className="h-2 bg-gray-700 rounded w-full"><div className="h-2 bg-gray-500 rounded w-3/4"></div></div>
          </div>
          <div className="flex justify-center mb-4"><ArrowRight className="text-red-500 rotate-90" size={24}/> Override</div>
          <div className="bg-red-900/20 border-l-4 border-red-500 p-4 rounded-r-lg shadow-[0_0_20px_rgba(239,68,68,0.2)] relative">
            <div className="absolute top-2 right-2 text-xs text-red-400 font-bold">ML Model</div>
            <h4 className="font-bold text-white mb-1">XGBoost Score</h4>
            <div className="h-2 bg-gray-700 rounded w-full"><div className="h-2 bg-red-500 rounded w-[90%]"></div></div>
          </div>
        </div>
        <div className="w-2/3 space-y-4">
          <div className="bg-gray-800/80 p-5 rounded-xl border border-gray-700">
            <h4 className="text-red-400 font-bold text-lg mb-2 flex items-center gap-2"><Activity size={20}/> Learning-to-Rank (XGBoost)</h4>
            <p className="text-gray-400 text-sm">Hệ thống tự động phát hiện file model ML. Khi có dữ liệu thật (click, order), XGBoost sẽ tính toán ra xác suất mua hàng thay vì điểm Rule-based tĩnh.</p>
          </div>
          <div className="bg-gray-800/80 p-5 rounded-xl border border-gray-700">
            <h4 className="text-indigo-400 font-bold text-lg mb-2 flex items-center gap-2"><Layers size={20}/> Two-Tower Vector Retrieval</h4>
            <p className="text-gray-400 text-sm">Dễ dàng đổi từ BM25 sang `vector_search` (Qdrant) để bắt ngữ nghĩa ngầm (Ví dụ: "chè" = "món giải nhiệt mùa hè").</p>
          </div>
          <div className="bg-gray-800/80 p-5 rounded-xl border border-gray-700">
            <h4 className="text-orange-400 font-bold text-lg mb-2 flex items-center gap-2"><Zap size={20}/> Bandit Explorer</h4>
            <p className="text-gray-400 text-sm">Epsilon-Greedy (10%) đẩy ngẫu nhiên các quán mới lên Top để phá vỡ "bong bóng lọc" và thu thập dữ liệu khám phá.</p>
          </div>
        </div>
      </div>
    )
  },
  {
    id: 6,
    title: "System Monitoring",
    subtitle: "Giám sát & Đo lường tự động",
    icon: <Activity className="w-16 h-16 text-cyan-400 mx-auto mb-4" />,
    content: (
      <div className="flex flex-col md:flex-row items-center gap-8 w-full max-w-4xl mx-auto mt-4">
        <div className="w-full md:w-1/2 h-64 bg-gray-800/50 p-4 rounded-xl border border-cyan-900/50">
          <h4 className="text-cyan-400 text-sm font-bold text-center mb-4">Mô phỏng System Latency & Requests</h4>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={mockChartData}>
              <XAxis dataKey="time" stroke="#4b5563" fontSize={12} />
              <YAxis stroke="#4b5563" fontSize={12} />
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px', color: '#fff' }} />
              <Line type="monotone" dataKey="latency" stroke="#06b6d4" strokeWidth={3} dot={{ r: 4 }} name="Latency (ms)" />
              <Line type="monotone" dataKey="requests" stroke="#8b5cf6" strokeWidth={3} dot={{ r: 4 }} name="Requests/min" />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="w-full md:w-1/2 space-y-4">
          <div className="bg-gray-800/60 p-4 rounded-xl border-l-4 border-cyan-500">
            <h3 className="text-white font-bold mb-1">Traceability (Ghi vết)</h3>
            <p className="text-gray-400 text-sm">Gắn `trace_id` cho mọi suy luận của hệ thống, giúp Admin Dashboard phân tích dễ dàng điểm thắt nút.</p>
          </div>
          <div className="bg-gray-800/60 p-4 rounded-xl border-l-4 border-teal-500">
            <h3 className="text-white font-bold mb-1">Background Benchmarking</h3>
            <p className="text-gray-400 text-sm">Tiến trình nền chạy tự động bộ Ragas (Context Precision/Recall) không giới hạn timeout.</p>
          </div>
          <div className="bg-gray-800/60 p-4 rounded-xl border-l-4 border-sky-500">
            <h3 className="text-white font-bold mb-1">User Metrics Dashboard</h3>
            <p className="text-gray-400 text-sm">Đo lường mức độ hài lòng thực tế (Thumbs Up/Down) đối với từng phản hồi RAG và Food Card.</p>
          </div>
        </div>
      </div>
    )
  }
];

export default function TechPresentation() {
  const [current, setCurrent] = useState(0);

  const handleNext = () => {
    if (current < slides.length - 1) setCurrent(current + 1);
  };

  const handlePrev = () => {
    if (current > 0) setCurrent(current - 1);
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col items-center justify-center overflow-hidden font-sans relative">
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-emerald-900/20 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-900/20 rounded-full blur-[120px] pointer-events-none"></div>

      <div className="w-full max-w-6xl px-8 relative z-10">
        <AnimatePresence mode="wait">
          <motion.div
            key={current}
            initial={{ opacity: 0, x: 50, scale: 0.95 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: -50, scale: 0.95 }}
            transition={{ duration: 0.6, type: "spring", bounce: 0.3 }}
            className="bg-gray-900/60 backdrop-blur-xl border border-gray-800 shadow-2xl rounded-3xl p-12 min-h-[550px] flex flex-col justify-center"
          >
            <div className="flex-1 flex flex-col justify-center">
              <motion.div 
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.2, duration: 0.5 }}
                className="text-center mb-8"
              >
                {slides[current].icon}
                <h1 className="text-3xl md:text-4xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-gray-100 to-gray-400 tracking-tight">
                  {slides[current].title}
                </h1>
                <p className="text-lg text-gray-500 mt-2 font-medium">{slides[current].subtitle}</p>
              </motion.div>

              <motion.div 
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.4, duration: 0.5 }}
                className="w-full flex justify-center"
              >
                {slides[current].content}
              </motion.div>
            </div>

          </motion.div>
        </AnimatePresence>

        <div className="flex justify-between items-center mt-8 px-4">
          <button
            onClick={handlePrev}
            disabled={current === 0}
            className={`flex items-center gap-2 px-6 py-3 rounded-full font-semibold transition-all ${
              current === 0 
                ? 'opacity-30 cursor-not-allowed bg-gray-800 text-gray-500' 
                : 'bg-gray-800 hover:bg-gray-700 text-white shadow-lg hover:shadow-gray-900/50 active:scale-95'
            }`}
          >
            <ChevronLeft size={20} /> Trước
          </button>
          
          <div className="flex gap-3">
            {slides.map((_, idx) => (
              <div 
                key={idx} 
                onClick={() => setCurrent(idx)}
                className={`h-2 rounded-full transition-all duration-500 cursor-pointer ${idx === current ? 'w-8 bg-emerald-500' : 'w-2 bg-gray-700 hover:bg-gray-500'}`}
              />
            ))}
          </div>

          <button
            onClick={handleNext}
            disabled={current === slides.length - 1}
            className={`flex items-center gap-2 px-6 py-3 rounded-full font-semibold transition-all ${
              current === slides.length - 1 
                ? 'opacity-30 cursor-not-allowed bg-gray-800 text-gray-500' 
                : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-900/20 active:scale-95'
            }`}
          >
            Tiếp <ChevronRight size={20} />
          </button>
        </div>
      </div>
    </div>
  );
}
