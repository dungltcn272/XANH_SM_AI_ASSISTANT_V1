import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight, Keyboard } from 'lucide-react';

export default function SlideShow() {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [direction, setDirection] = useState(0); // -1 for left/prev, 1 for right/next
  const [scale, setScale] = useState(1);

  const TOTAL_SLIDES = 8;

  // Dynamic scaling to fit 1920x1080 design in viewport
  useEffect(() => {
    const handleResize = () => {
      const targetWidth = 1920;
      const targetHeight = 1080;
      const windowWidth = window.innerWidth;
      const windowHeight = window.innerHeight;

      // Leave a tiny margin of 40px width and 80px height
      const scaleX = (windowWidth - 40) / targetWidth;
      const scaleY = (windowHeight - 80) / targetHeight;
      const newScale = Math.min(scaleX, scaleY);
      setScale(newScale);
    };

    window.addEventListener('resize', handleResize);
    handleResize(); // Trigger immediately on mount
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const nextSlide = useCallback(() => {
    if (currentSlide < TOTAL_SLIDES - 1) {
      setDirection(1);
      setCurrentSlide(prev => prev + 1);
    }
  }, [currentSlide]);

  const prevSlide = useCallback(() => {
    if (currentSlide > 0) {
      setDirection(-1);
      setCurrentSlide(prev => prev - 1);
    }
  }, [currentSlide]);

  // Handle keyboard interaction
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowRight') {
        e.preventDefault();
        nextSlide();
      } else if (e.key === 'ArrowLeft' || e.key === 'Backspace') {
        e.preventDefault();
        prevSlide();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [nextSlide, prevSlide]);

  const getActiveTab = (index) => {
    if (index === 0) return 'Tổng quan';
    if (index === 1) return 'Khám phá';
    if (index === 2) return 'Hiệu năng';
    if (index === 3) return 'NLU';
    if (index === 4) return 'Lợi thế';
    if (index === 5 || index === 6) return 'Kiến trúc';
    return 'Triển khai';
  };

  const getTabsList = (index) => {
    if (index === 0) return ['Tổng quan', 'Khám phá', 'Hiệu năng', 'Kiến trúc'];
    if (index === 1) return ['Tổng quan', 'Khám phá', 'Hiệu năng', 'Kiến trúc'];
    if (index === 2) return ['Tổng quan', 'Khám phá', 'Hiệu năng', 'Kiến trúc'];
    if (index === 3) return ['Tổng quan', 'Khám phá', 'NLU', 'Kiến trúc'];
    if (index === 4) return ['Tổng quan', 'Khám phá', 'Lợi thế', 'Kiến trúc'];
    if (index === 5 || index === 6) return ['Tổng quan', 'Khám phá', 'Hiệu năng', 'Kiến trúc'];
    return ['Tổng quan', 'Khám phá', 'Kiến trúc', 'Triển khai'];
  };

  const navigateToTab = (tabName) => {
    const targetMap = {
      'Tổng quan': 0,
      'Khám phá': 1,
      'Hiệu năng': 2,
      'NLU': 3,
      'Lợi thế': 4,
      'Kiến trúc': 5,
      'Triển khai': 7
    };
    const targetIndex = targetMap[tabName];
    if (targetIndex !== undefined) {
      setDirection(targetIndex > currentSlide ? 1 : -1);
      setCurrentSlide(targetIndex);
    }
  };

  // Animation settings for slide transition
  const slideVariants = {
    enter: (dir) => ({
      x: dir > 0 ? 1200 : -1200,
      opacity: 0,
      scale: 0.96
    }),
    center: {
      x: 0,
      opacity: 1,
      scale: 1,
      transition: {
        x: { type: 'spring', stiffness: 200, damping: 25 },
        opacity: { duration: 0.3 },
        scale: { duration: 0.3 }
      }
    },
    exit: (dir) => ({
      x: dir > 0 ? -1200 : 1200,
      opacity: 0,
      scale: 0.96,
      transition: {
        x: { type: 'spring', stiffness: 200, damping: 25 },
        opacity: { duration: 0.2 }
      }
    })
  };

  return (
    <div className="min-h-screen w-screen bg-[#cfeee9] flex flex-col items-center justify-center overflow-hidden font-sans select-none relative p-4">
      
      {/* Wrapper to center the scaled slide */}
      <div 
        className="flex items-center justify-center overflow-hidden"
        style={{
          width: '100%',
          height: '100%',
        }}
      >
        {/* Slide Container (Pixel-perfect 1920x1080 canvas scaled dynamically) */}
        <div 
          className="relative bg-white rounded-[28px] overflow-hidden shadow-[0_34px_100px_rgba(4,44,74,0.28)] flex flex-col justify-between p-[60px] pb-[80px]"
          style={{
            width: '1920px',
            height: '1080px',
            transform: `scale(${scale})`,
            transformOrigin: 'center center',
            flexShrink: 0,
            background: 'linear-gradient(90deg, rgba(255, 255, 255, 0.96) 0%, rgba(235, 251, 255, 0.76) 42%, rgba(235, 251, 255, 0.2) 100%), url("/bg_landing.png") center / cover no-repeat',
          }}
        >
          {/* Glow overlay circles matching the HTML design */}
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_18%_18%,rgba(255,255,255,0.82),transparent_28%)] bg-[radial-gradient(circle_at_78%_16%,rgba(0,198,242,0.18),transparent_32%)] bg-[linear-gradient(180deg,rgba(255,255,255,0.2),rgba(198,246,238,0.26))] pointer-events-none z-0" />
          
          {/* Frame border */}
          <div className="absolute inset-[46px] border border-white/58 rounded-[34px] pointer-events-none z-0" />

          {/* Topbar: Fixed, stays in place while contents animate */}
          <div className="relative z-10 flex items-center justify-between gap-8 mb-6">
            <img 
              className="h-[74px] w-auto cursor-pointer hover:opacity-85 transition-opacity" 
              src="/logo.svg" 
              alt="Green SM" 
              onClick={() => setCurrentSlide(0)} 
            />
            
            <div className="flex items-center gap-2.5 p-[10px] border border-white/76 rounded-full bg-white/42 backdrop-blur-[14px] shadow-[0_16px_38px_rgba(10,86,126,0.12)]">
              {getTabsList(currentSlide).map((tab) => {
                const isActive = getActiveTab(currentSlide) === tab;
                return (
                  <button
                    key={tab}
                    onClick={() => navigateToTab(tab)}
                    className={`min-w-[144px] text-center py-[18px] px-6 rounded-full font-extrabold text-[18px] transition-all duration-300 ${
                      isActive 
                        ? 'bg-[#00b386] text-white shadow-[0_14px_28px_rgba(0,179,134,0.28)]' 
                        : 'text-[#24415f] hover:bg-white/40'
                    }`}
                  >
                    {tab}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Slides Content Stage (Animated content swap) */}
          <div className="relative flex-grow z-10 flex flex-col justify-center">
            <AnimatePresence initial={false} custom={direction} mode="wait">
              <motion.div
                key={currentSlide}
                custom={direction}
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                className="w-full h-full flex flex-col justify-center"
              >
                {/* SLIDE 0: TỔNG QUAN / HERO */}
                {currentSlide === 0 && (
                  <div className="grid grid-cols-[0.92fr_1.08fr] gap-[54px] items-center">
                    <div className="space-y-6">
                      <div className="inline-flex items-center gap-2 px-[18px] py-[11px] rounded-full bg-[#00b386]/12 text-[#008c72] font-black tracking-widest text-[17px] uppercase">
                        AI Assistant
                      </div>
                      <h1 className="text-[110px] font-black leading-[1.05] text-[#071735]">
                        Xanh SM<br />
                        <span className="text-[#00b386]">AI Assistant</span>
                      </h1>
                      <p className="text-[30px] font-semibold leading-[1.48] text-[#314967] max-w-[800px]">
                        Một trợ lý hội thoại cho hệ sinh thái Xanh SM: hỏi đáp tri thức, hiểu ngôn ngữ tự nhiên, gợi ý theo ngữ cảnh và vận hành có đo lường.
                      </p>
                      <div className="flex flex-wrap gap-4 mt-8">
                        <div className="inline-flex items-center gap-2.5 px-[20px] py-[16px] border border-[#00b386]/22 bg-white text-[#123257] text-[20px] font-extrabold rounded-[18px] shadow-sm">
                          ✦ RAG Answer
                        </div>
                        <div className="inline-flex items-center gap-2.5 px-[20px] py-[16px] border border-[#00b386]/22 bg-white text-[#123257] text-[20px] font-extrabold rounded-[18px] shadow-sm">
                          ✦ Food Recommendation
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-4" style={{ marginTop: '16px' }}>
                        <div className="inline-flex items-center gap-2.5 px-[20px] py-[16px] border border-[#00b386]/22 bg-white text-[#123257] text-[20px] font-extrabold rounded-[18px] shadow-sm">
                          ✦ Eval & Ops
                        </div>
                        <div className="inline-flex items-center gap-2.5 px-[20px] py-[16px] border border-[#00b386]/22 bg-white text-[#123257] text-[20px] font-extrabold rounded-[18px] shadow-sm">
                          ✦ NLU Orchestrator
                        </div>
                      </div>
                    </div>
                    <div className="relative min-h-[740px]">
                      {/* Orbit Ring Background */}
                      <div 
                        className="absolute w-[590px] h-[590px] rounded-full border-2 border-white/78 bg-[radial-gradient(circle,rgba(0,179,134,0.2),rgba(255,255,255,0.12)_54%,transparent_68%)] shadow-[inset_0_0_60px_rgba(255,255,255,0.45),0_24px_80px_rgba(0,179,134,0.18)]"
                        style={{ left: '50%', top: '48%', transform: 'translate(-50%, -50%)' }}
                      />
                      
                      {/* Driver Bot Image */}
                      <img 
                        className="absolute bottom-[-180px] w-[1200px] max-w-none object-contain drop-shadow-[0_34px_42px_rgba(0,90,124,0.28)]" 
                        src="/driver_man.png" 
                        alt="AI Bot" 
                        style={{ left: '28%', transform: 'translateX(-50%)' }}
                      />

                      {/* Floating Cards */}
                      <div className="absolute px-5 py-[18px] w-[160px] h-[132px] border border-white/45 bg-white backdrop-blur-md rounded-[26px] shadow-[0_24px_52px_rgba(19,75,104,0.18)] text-[18px] font-extrabold text-[#071735] text-center flex flex-col items-center justify-center gap-1 left-[90px] top-[140px] rotate-[-6deg]">
                        <span className="text-[34px] leading-none">🚘</span> Xe điện
                      </div>
                      <div className="absolute px-5 py-[18px] w-[160px] h-[132px] border border-white/45 bg-white backdrop-blur-md rounded-[26px] shadow-[0_24px_52px_rgba(19,75,104,0.18)] text-[18px] font-extrabold text-[#071735] text-center flex flex-col items-center justify-center gap-1 right-[90px] top-[140px] rotate-[8deg]">
                        <span className="text-[34px] leading-none">📰</span> Tin tức
                      </div>
                      <div className="absolute px-5 py-[18px] w-[160px] h-[132px] border border-white/45 bg-white backdrop-blur-md rounded-[26px] shadow-[0_24px_52px_rgba(19,75,104,0.18)] text-[18px] font-extrabold text-[#071735] text-center flex flex-col items-center justify-center gap-1 left-[20px] bottom-[200px] rotate-[7deg]">
                        <span className="text-[34px] leading-none">🍜</span> Food AI
                      </div>
                      <div className="absolute px-5 py-[18px] w-[160px] h-[132px] border border-white/45 bg-white backdrop-blur-md rounded-[26px] shadow-[0_24px_52px_rgba(19,75,104,0.18)] text-[18px] font-extrabold text-[#071735] text-center flex flex-col items-center justify-center gap-1 right-[90px] bottom-[140px] rotate-[-5deg]">
                        <span className="text-[34px] leading-none">📊</span> Analytics
                      </div>
                      <div className="absolute px-5 py-[18px] w-[160px] h-[132px] border border-white/45 bg-white backdrop-blur-md rounded-[26px] shadow-[0_24px_52px_rgba(19,75,104,0.18)] text-[18px] font-extrabold text-[#071735] text-center flex flex-col items-center justify-center gap-1 left-[420px] bottom-[30px] rotate-[-4deg]">
                        <span className="text-[34px] leading-none">🛡️</span> Policy
                      </div>
                      <div className="absolute px-5 py-[18px] w-[160px] h-[132px] border border-white/45 bg-white backdrop-blur-md rounded-[26px] shadow-[0_24px_52px_rgba(19,75,104,0.18)] text-[18px] font-extrabold text-[#071735] text-center flex flex-col items-center justify-center gap-1 left-[370px] top-[40px] rotate-[4deg]">
                        <span className="text-[34px] leading-none">🔎</span> Search
                      </div>
                    </div>
                  </div>
                )}

                {/* SLIDE 1: KHÁM PHÁ KHẢ NĂNG */}
                {currentSlide === 1 && (
                  <div className="space-y-4">
                    <div>
                      <h2 className="text-[54px] font-black leading-tight text-[#071735]">
                        Khám phá <span className="text-[#00b386]">khả năng</span>
                      </h2>
                      <p className="text-[22px] font-semibold text-[#415b7d] mt-1 max-w-[1120px]">
                        Assistant không chỉ trả lời câu hỏi. Hệ thống gom nhiều năng lực vào một trải nghiệm thống nhất để người dùng hỏi bằng ngôn ngữ tự nhiên và nhận phản hồi đúng ngữ cảnh.
                      </p>
                    </div>
                    <div className="grid grid-cols-4 gap-[16px] pt-2">
                      {[
                        { img: '/knowledge_search.png', t: 'Knowledge Search', d: 'Tra cứu tri thức, chính sách, nội dung vận hành và tài liệu nội bộ.' },
                        { img: '/deep_research.png', t: 'Deep Research', d: 'Tổng hợp nhiều nguồn, giữ trích dẫn và lý do trả lời rõ ràng.' },
                        { img: '/vehicle_expert.png', t: 'Vehicle Expert', d: 'Hỏi đáp về dòng xe, dịch vụ, trải nghiệm di chuyển và hệ sinh thái.' },
                        { img: '/pricing_assistant.png', t: 'Pricing Assistant', d: 'Giải thích giá cước, ưu đãi và điều kiện áp dụng theo tình huống.' },
                        { img: '/news_digest.png', t: 'News Digest', d: 'Cập nhật tin tức, tóm tắt điểm đáng chú ý và biến động thị trường.' },
                        { img: '/food_recommendation.png', t: 'Food Recommendation', d: 'Gợi ý món/quán theo khẩu vị, vị trí, ngân sách và ngữ cảnh hội thoại.' },
                        { img: '/policy_support.png', t: 'Policy & Support', d: 'Hỗ trợ chính sách, điều khoản, câu hỏi thường gặp và CSKH.' },
                        { img: '/data_analytics.png', t: 'Data Analytics', d: 'Theo dõi chất lượng, trace, latency, feedback và tín hiệu cải thiện.' }
                      ].map((item, idx) => (
                        <div key={idx} className="flex flex-col min-h-[250px] border border-[#094a70]/13 rounded-[20px] overflow-hidden bg-white shadow-[0_16px_36px_rgba(13,64,100,0.1)] hover:translate-y-[-4px] transition-transform duration-300">
                          <img className="w-full h-[120px] object-cover" src={item.img} alt={item.t} />
                          <div className="p-4 flex-grow flex flex-col justify-between">
                            <h3 className="text-[#071735] text-[22px] font-black leading-[1.15]">{item.t}</h3>
                            <p className="text-[#365071] text-[17px] font-semibold mt-[6px] leading-[1.4]">{item.d}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* SLIDE 2: HIỆU NĂNG RAG & FOOD */}
                {currentSlide === 2 && (
                  <div className="space-y-6">
                    <div>
                      <h2 className="text-[60px] font-black leading-tight text-[#071735]">
                        Hiệu năng <span className="text-[#00b386]">RAG & Food</span>
                      </h2>
                      <p className="text-[26px] font-semibold text-[#415b7d] mt-[16px] max-w-[1120px]">
                        RAG answer và Food recommendation cùng chạy trong một assistant, cùng được trace, đánh giá và tối ưu theo dữ liệu vận hành.
                      </p>
                    </div>
                    <div className="grid grid-cols-[1.1fr_0.9fr] gap-6 items-stretch pt-2">
                      <div className="border border-[#094a70]/14 rounded-[24px] bg-white p-[30px] shadow-[0_28px_90px_rgba(8,45,77,0.22)] flex flex-col justify-between">
                        <div>
                          <h3 className="text-[#071735] text-[38px] font-black leading-[1.14]">Đo lường theo luồng thực tế</h3>
                          <p className="text-[#344e70] text-[24px] font-semibold mt-[18px] leading-[1.52]">
                            Eval tập trung vào độ bám tài liệu, độ đúng câu trả lời, tốc độ phản hồi và khả năng mở rộng domain. Food dùng cùng lớp NLU để hiểu khẩu vị, địa điểm, ngân sách và ràng buộc của người dùng.
                          </p>
                        </div>
                        <div className="grid grid-cols-2 gap-5 mt-6">
                          <div className="border border-[#00b386]/18 bg-white p-5 rounded-[20px] shadow-sm">
                            <b className="block text-[#071735] text-[40px] font-black leading-none">99%</b>
                            <span className="block text-[#3d5574] text-[18px] font-semibold mt-[8px] leading-[1.4]">Faithfulness trên bộ golden cases RAG đã kiểm thử.</span>
                          </div>
                          <div className="border border-[#00b386]/18 bg-white p-5 rounded-[20px] shadow-sm">
                            <b className="block text-[#071735] text-[40px] font-black leading-none">90%</b>
                            <span className="block text-[#3d5574] text-[18px] font-semibold mt-[8px] leading-[1.4]">Correctness mục tiêu cho câu hỏi chính sách, giá cước, xe và tin tức.</span>
                          </div>
                          <div className="border border-[#00b386]/18 bg-white p-5 rounded-[20px] shadow-sm">
                            <b className="block text-[#071735] text-[40px] font-black leading-none">~120ms</b>
                            <span className="block text-[#3d5574] text-[18px] font-semibold mt-[8px] leading-[1.4]">Fast-path/cache cho các câu hỏi phổ biến và guardrail nhẹ.</span>
                          </div>
                          <div className="border border-[#00b386]/18 bg-white p-5 rounded-[20px] shadow-sm">
                            <b className="block text-[#008c72] text-[40px] font-black leading-none">Food</b>
                            <span className="block text-[#3d5574] text-[18px] font-semibold mt-[8px] leading-[1.4]">Gợi ý có lý do, điều kiện cá nhân hóa và trace để debug.</span>
                          </div>
                        </div>
                      </div>
                      <div className="border border-[#094a70]/14 rounded-[24px] bg-white p-5 shadow-[0_28px_90px_rgba(8,45,77,0.22)] flex items-center justify-center overflow-hidden">
                        <img className="max-w-full max-h-[460px] object-contain rounded-[22px] shadow-[0_18px_60px_rgba(0,70,98,0.18)]" src="/food_recommend.png" alt="Food recommendation demo" />
                      </div>
                    </div>
                  </div>
                )}

                {/* SLIDE 3: NLU ORCHESTRATOR */}
                {currentSlide === 3 && (
                  <div className="space-y-6">
                    <div>
                      <h2 className="text-[60px] font-black leading-tight text-[#071735]">
                        NLU biến hệ thống thành <span className="text-[#00b386]">assistant hiểu người dùng</span>
                      </h2>
                      <p className="text-[26px] font-semibold text-[#415b7d] mt-[16px] max-w-[1120px]">
                        NLU là lớp đọc ý định, chuẩn hóa câu hỏi và điều phối domain. Nhờ lớp này, người dùng không cần nhớ cú pháp; họ chỉ cần nói tự nhiên, assistant tự hiểu cần hỏi RAG, gợi ý món ăn hay truy vấn thông tin khác.
                      </p>
                    </div>
                    <div className="grid grid-cols-3 gap-5 pt-2">
                      {[
                        { num: 1, title: 'Intent & Domain Routing', desc: 'Nhận diện câu hỏi chính sách, xe, giá cước, tin tức, food, missing-info hoặc câu hỏi ngoài phạm vi để chọn pipeline phù hợp.' },
                        { num: 2, title: 'Query Rewrite', desc: 'Viết lại câu hỏi mơ hồ thành truy vấn rõ nghĩa; nếu thiếu ngữ cảnh, NLU hỏi lại thay vì đoán hoặc gọi sai pipeline.' },
                        { num: 3, title: 'Slot Extraction', desc: 'Tách địa điểm, ngân sách, khẩu vị, món muốn ăn, loại xe, thời gian và các điều kiện người dùng nhắc tới.' }
                      ].map((nlu, idx) => (
                        <div key={idx} className="border border-[#094a70]/14 rounded-[24px] bg-white p-6 shadow-[0_16px_36px_rgba(13,64,100,0.1)] flex flex-col justify-between min-h-[220px]">
                          <div className="w-[46px] h-[46px] rounded-xl bg-gradient-to-br from-[#00b386] to-[#1cc7f2] text-white flex items-center justify-center font-black text-[20px]">
                            {nlu.num}
                          </div>
                          <div className="mt-4 flex-grow">
                            <h3 className="text-[#071735] text-[28px] font-black leading-[1.2]">{nlu.title}</h3>
                            <p className="text-[#405a7a] text-[20px] font-semibold mt-2 leading-[1.4]">{nlu.desc}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className="border border-[#094a70]/14 rounded-[24px] bg-white p-[30px] shadow-[0_28px_90px_rgba(8,45,77,0.22)] mt-[30px]">
                      <h3 className="text-[#071735] text-[38px] font-black leading-[1.14]">Nhanh hơn, mượt hơn, ít hỏi lại hơn</h3>
                      <div className="grid grid-cols-[1fr_40px_1fr_40px_1fr_40px_1fr] items-center gap-[12px] mt-4">
                        <div className="border border-[#00b386]/18 bg-white p-4 rounded-[18px] text-[#071735] text-[22px] font-extrabold text-center shadow-xs">Người dùng hỏi tự nhiên</div>
                        <div className="text-[#00b386] text-[36px] font-black text-center">→</div>
                        <div className="border border-[#00b386]/18 bg-white p-4 rounded-[18px] text-[#071735] text-[22px] font-extrabold text-center shadow-xs">NLU hiểu ý định và dữ kiện</div>
                        <div className="text-[#00b386] text-[36px] font-black text-center">→</div>
                        <div className="border border-[#00b386]/18 bg-white p-4 rounded-[18px] text-[#071735] text-[22px] font-extrabold text-center shadow-xs">Chọn RAG, Food hoặc hỏi làm rõ</div>
                        <div className="text-[#00b386] text-[36px] font-black text-center">→</div>
                        <div className="border border-[#00b386]/18 bg-white p-4 rounded-[18px] text-[#071735] text-[22px] font-extrabold text-center shadow-xs">Trả lời theo văn phong CSKH</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* SLIDE 4: SO SÁNH & LỢI THẾ */}
                {currentSlide === 4 && (
                  <div className="space-y-4">
                    <div>
                      <h2 className="text-[54px] font-black leading-tight text-[#071735]">
                        So sánh trực quan <span className="text-[#00b386]">& lợi thế</span>
                      </h2>
                      <p className="text-[22px] font-semibold text-[#415b7d] mt-[10px] max-w-[1120px]">
                        Điểm khác biệt không nằm ở một câu trả lời riêng lẻ, mà ở cách assistant hiểu ý định, chọn nguồn dữ liệu, giữ trace và cải thiện chất lượng qua từng phiên bản.
                      </p>
                    </div>
                    
                    <div className="border border-[#094a70]/11 rounded-[24px] bg-white shadow-[0_28px_90px_rgba(8,45,77,0.22)] overflow-hidden">
                      <table className="w-full border-collapse">
                        <thead>
                          <tr className="bg-white border-b border-[#094a70]/11">
                            <th className="p-[12px] px-[16px] text-left text-[#071735] text-[20px] font-black border-r border-[#094a70]/9">Năng lực</th>
                            <th className="p-[12px] px-[16px] text-left text-[#405a7a] text-[18px] font-bold border-r border-[#094a70]/9">Chatbot phổ thông</th>
                            <th className="p-[12px] px-[16px] text-left text-[#405a7a] text-[18px] font-bold border-r border-[#094a70]/9">RAG thông thường</th>
                            <th className="p-[12px] px-[16px] text-left text-[#071735] text-[20px] font-black bg-[#e1fff7]">Xanh SM AI Assistant</th>
                          </tr>
                        </thead>
                        <tbody>
                          {[
                            {
                              feat: 'Xử lý câu hỏi tự nhiên',
                              bot: 'Nhận diện theo từ khóa tĩnh, dễ sai lệch hoặc báo lỗi nếu người dùng gõ câu dài, nói lóng.',
                              rag: 'Hiểu ngữ nghĩa tốt nhưng chủ yếu dùng để tìm kiếm tài liệu thay vì bóc tách yêu cầu phức tạp.',
                              ours: 'NLU thông minh bóc tách chính xác ý định (intent), trích xuất điều kiện (slot) và nhớ ngữ cảnh hội thoại.'
                            },
                            {
                              feat: 'Đa nhiệm & Nghiệp vụ',
                              bot: 'Chỉ trả lời được kịch bản FAQ cố định, không lấy được dữ liệu động từ hệ thống.',
                              rag: 'Chỉ mạnh về đọc hiểu tài liệu văn bản, khó kết hợp logic nghiệp vụ (như gợi ý món ăn, giá cước).',
                              ours: 'Tích hợp Đa Engine (Kiến thức, Food Recommendation, Tin tức) để xử lý chéo nhiều luồng dịch vụ.'
                            },
                            {
                              feat: 'Kiểm soát & Vận hành',
                              bot: 'Hoạt động như "hộp đen", khi trả lời sai kỹ sư rất khó truy vết nguyên nhân để sửa chữa.',
                              rag: 'Có trích dẫn nguồn tài liệu nhưng thiếu hệ thống đánh giá chất lượng tự động (Eval) liên tục.',
                              ours: 'Vòng lặp Ops (Trace & Eval) ghi log mọi suy luận, giúp đo lường RAGAS và tự động cải tiến tức thì.'
                            },
                            {
                              feat: 'Trải nghiệm khách hàng',
                              bot: 'Giao tiếp rập khuôn, máy móc, thường bắt ép người dùng phải bấm chọn menu tĩnh.',
                              rag: 'Văn phong AI khô khan giống "bách khoa toàn thư", thiếu sự đồng cảm và cá nhân hóa.',
                              ours: 'Tư vấn chuẩn văn phong CSKH, cá nhân hóa theo profile và luôn định hướng rõ hành động kế tiếp.'
                            }
                          ].map((row, idx) => (
                            <tr key={idx} className="border-b border-[#094a70]/11 last:border-none">
                              <td className="p-[12px] px-[16px] font-black text-[#071735] text-[18px] border-r border-[#094a70]/9">{row.feat}</td>
                              <td className="p-[12px] px-[16px] font-medium text-[#405a7a] text-[17px] border-r border-[#094a70]/9 leading-[1.35]">{row.bot}</td>
                              <td className="p-[12px] px-[16px] font-medium text-[#405a7a] text-[17px] border-r border-[#094a70]/9 leading-[1.35]">{row.rag}</td>
                              <td className="p-[12px] px-[16px] font-extrabold text-[#071735] text-[17px] bg-[#e1fff7] leading-[1.35]">{row.ours}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    <div className="grid grid-cols-4 gap-3 mt-2">
                      {[
                        'Một assistant cho nhiều nhiệm vụ, không tách rời từng công cụ.',
                        'NLU làm lớp điều phối, giúp mở rộng domain nhanh hơn.',
                        'Eval/Ops gắn trực tiếp vào vòng phát triển sản phẩm.',
                        'UI mới hướng tới trải nghiệm demo mượt và dễ hiểu.'
                      ].map((adv, idx) => (
                        <div key={idx} className="border border-[#00b386]/17 bg-white p-[12px] rounded-[14px] text-[#123257] text-[17px] font-extrabold shadow-sm leading-[1.35]">
                          {adv}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* SLIDE 5: KIẾN TRÚC PIPELINE */}
                {currentSlide === 5 && (
                  <div className="space-y-6">
                    <div>
                      <h2 className="text-[60px] font-black leading-tight text-[#071735]">
                        Kiến trúc <span className="text-[#00b386]">AI Assistant Pipeline</span>
                      </h2>
                      <p className="text-[26px] font-semibold text-[#415b7d] mt-[16px] max-w-[1120px]">
                        Pipeline được thiết kế theo lớp: gateway bảo vệ đầu vào, NLU hiểu ý định, các engine xử lý domain và lớp ops/eval đóng vòng cải thiện chất lượng.
                      </p>
                    </div>

                    <div className="grid grid-cols-[1fr_50px_1.2fr_50px_1fr] items-stretch gap-4 pt-4 mt-2">
                      <div className="flex flex-col gap-[16px]">
                        <div className="border border-[#094a70]/14 rounded-[20px] bg-white p-5 shadow-[0_12px_28px_rgba(13,64,100,0.1)]">
                          <span className="text-[15px] font-extrabold text-[#008c72] tracking-[0.05em] uppercase block mb-2">Input</span>
                          <h3 className="text-[#071735] text-[24px] font-black leading-[1.2]">User Message</h3>
                          <p className="text-[#46607f] text-[18px] font-semibold mt-[8px] leading-[1.4]">Text, ảnh, voice, file upload và ngữ cảnh phiên chat.</p>
                        </div>
                        <div className="border border-[#094a70]/14 rounded-[20px] bg-white p-5 shadow-[0_12px_28px_rgba(13,64,100,0.1)] flex-grow flex flex-col justify-center">
                          <h3 className="text-[#071735] text-[24px] font-black leading-[1.2]">Session Context</h3>
                          <p className="text-[#46607f] text-[18px] font-semibold mt-[8px] leading-[1.4]">Lịch sử hội thoại, user profile, vị trí và trạng thái tác vụ.</p>
                        </div>
                      </div>
                      <div className="flex items-center justify-center text-[#00b386] text-[44px] font-black">→</div>
                      <div className="flex flex-col gap-[16px]">
                        <div className="border border-[#094a70]/14 rounded-[20px] bg-white p-5 shadow-[0_12px_28px_rgba(13,64,100,0.1)]">
                          <span className="text-[15px] font-extrabold text-[#008c72] tracking-[0.05em] uppercase block mb-2">Gateway</span>
                          <h3 className="text-[#071735] text-[24px] font-black leading-[1.2]">Safety & Cache</h3>
                          <p className="text-[#46607f] text-[18px] font-semibold mt-[8px] leading-[1.4]">Guardrail, semantic cache, chuẩn hóa input và quyết định fast-path.</p>
                        </div>
                        <div className="border-2 border-[#00b386]/32 rounded-[20px] bg-gradient-to-b from-[#e6fff8] to-white p-5 shadow-md flex-grow flex flex-col justify-center">
                          <span className="text-[15px] font-extrabold text-[#008c72] tracking-[0.05em] uppercase block mb-2">Orchestrator</span>
                          <h3 className="text-[#071735] text-[24px] font-black leading-[1.2]">Unified NLU</h3>
                          <p className="text-[#46607f] text-[18px] font-semibold mt-[8px] leading-[1.4]">Intent classification, query rewrite, slot extraction, missing-info clarification, domain routing và entity normalization.</p>
                        </div>
                      </div>
                      <div className="flex items-center justify-center text-[#00b386] text-[44px] font-black">→</div>
                      <div className="flex flex-col gap-[16px]">
                        <div className="border border-[#094a70]/14 rounded-[20px] bg-white p-5 shadow-[0_12px_28px_rgba(13,64,100,0.1)]">
                          <span className="text-[15px] font-extrabold text-[#008c72] tracking-[0.05em] uppercase block mb-2">RAG Engine</span>
                          <h3 className="text-[#071735] text-[24px] font-black leading-[1.2]">Hybrid Retrieval</h3>
                          <p className="text-[#46607f] text-[18px] font-semibold mt-[8px] leading-[1.4]">BM25 + vector search, reranking, table-aware chunks và answer synthesis.</p>
                        </div>
                        <div className="border border-[#094a70]/14 rounded-[20px] bg-white p-5 shadow-[0_12px_28px_rgba(13,64,100,0.1)]">
                          <span className="text-[15px] font-extrabold text-[#008c72] tracking-[0.05em] uppercase block mb-2">Food Engine</span>
                          <h3 className="text-[#071735] text-[24px] font-black leading-[1.2]">Recommendation</h3>
                          <p className="text-[#46607f] text-[18px] font-semibold mt-[8px] leading-[1.4]">Profile, retrieval, ranker, constraints và lý do gợi ý theo khẩu vị.</p>
                        </div>
                        <div className="border border-[#094a70]/14 rounded-[20px] bg-white p-5 shadow-[0_12px_28px_rgba(13,64,100,0.1)]">
                          <span className="text-[15px] font-extrabold text-[#008c72] tracking-[0.05em] uppercase block mb-2">Ops</span>
                          <h3 className="text-[#071735] text-[24px] font-black leading-[1.2]">Trace & Eval</h3>
                          <p className="text-[#46607f] text-[18px] font-semibold mt-[8px] leading-[1.4]">Log, latency, feedback, golden dataset và RAGAS evaluation.</p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* SLIDE 6: KIẾN TRÚC MEMORY */}
                {currentSlide === 6 && (
                  <div className="space-y-6">
                    <div>
                      <h2 className="text-[60px] font-black leading-tight text-[#071735]">
                        Kiến trúc <span className="text-[#00b386]">Memory & Cá nhân hóa</span>
                      </h2>
                      <p className="text-[26px] font-semibold text-[#415b7d] mt-[16px] max-w-[1120px]">
                        Giải quyết bài toán giới hạn Context Window bằng cách không nhồi nhét lịch sử thô. Phân tách trí nhớ thành đa tầng, kết hợp Context Builder để giữ prompt luôn tinh gọn, giảm latency và tối ưu cá nhân hóa.
                      </p>
                    </div>

                    <div className="grid grid-cols-[1fr_50px_1.2fr_50px_1fr] items-stretch gap-4 pt-4 mt-2">
                      <div className="flex flex-col gap-[16px]">
                        <div className="border border-[#094a70]/14 rounded-[20px] bg-white p-[20px] shadow-[0_12px_28px_rgba(13,64,100,0.1)]">
                          <span className="text-[15px] font-extrabold text-[#008c72] tracking-[0.05em] uppercase block mb-2">Short-term</span>
                          <h3 className="text-[#071735] text-[24px] font-black leading-[1.2]">Working Memory</h3>
                          <p className="text-[#46607f] text-[18px] font-semibold mt-[8px] leading-[1.4]">Giữ 5-10 lượt chat gần nhất để NLU hiểu đại từ (như "nó bao tiền?").</p>
                        </div>
                        <div className="border border-[#094a70]/14 rounded-[20px] bg-white p-[20px] shadow-[0_12px_28px_rgba(13,64,100,0.1)]">
                          <span className="text-[15px] font-extrabold text-[#008c72] tracking-[0.05em] uppercase block mb-2">Mid-term</span>
                          <h3 className="text-[#071735] text-[24px] font-black leading-[1.2]">Session Summary</h3>
                          <p className="text-[#46607f] text-[18px] font-semibold mt-[8px] leading-[1.4]">Nén phiên chat dài thành các insight có cấu trúc (mục tiêu, quyết định).</p>
                        </div>
                        <div className="border border-[#094a70]/14 rounded-[20px] bg-white p-[20px] shadow-[0_12px_28px_rgba(13,64,100,0.1)]">
                          <span className="text-[15px] font-extrabold text-[#008c72] tracking-[0.05em] uppercase block mb-2">Long-term</span>
                          <h3 className="text-[#071735] text-[24px] font-black leading-[1.2]">User Profile DB</h3>
                          <p className="text-[#46607f] text-[18px] font-semibold mt-[8px] leading-[1.4]">Nhớ vĩnh viễn sở thích, vị trí, thói quen để không phải hỏi lại nhiều lần.</p>
                        </div>
                      </div>
                      <div className="flex items-center justify-center text-[#00b386] text-[44px] font-black">→</div>
                      <div className="flex flex-col justify-center">
                        <div className="border-2 border-[#0096ff]/32 rounded-[20px] bg-gradient-to-b from-[#e6f5ff] to-white p-6 shadow-md text-center">
                          <span className="text-[15px] font-extrabold text-[#0077cc] tracking-[0.05em] uppercase block mb-2">Orchestrator</span>
                          <h3 className="text-[#071735] text-[24px] font-black">Context Builder</h3>
                          <p className="text-[#46607f] text-[18px] font-semibold mt-3 leading-relaxed">
                            Retrieval & lắp ráp các mảnh bộ nhớ liên quan kết hợp với RAG Document thành một Prompt động tinh gọn, giải phóng giới hạn Context Window.
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center justify-center text-[#00b386] text-[44px] font-black">→</div>
                      <div className="flex flex-col justify-center gap-[16px]">
                        <div className="border border-[#094a70]/14 rounded-[20px] bg-white p-5 shadow-sm">
                          <span className="text-[15px] font-extrabold text-[#008c72] tracking-[0.05em] uppercase block mb-2">Optimization</span>
                          <h3 className="text-[#071735] text-[20px] font-black">Prompt Caching</h3>
                          <p className="text-[#46607f] text-[18px] font-semibold mt-1">Tăng tốc độ phản hồi (Latency) bằng cách cache các cấu trúc prompt tĩnh (system prompt, rules).</p>
                        </div>
                        <div className="border border-[#094a70]/14 rounded-[20px] bg-white p-5 shadow-sm">
                          <span className="text-[15px] font-extrabold text-[#008c72] tracking-[0.05em] uppercase block mb-2">Execution</span>
                          <h3 className="text-[#071735] text-[20px] font-black">LLM Generation</h3>
                          <p className="text-[#46607f] text-[18px] font-semibold mt-1">Sinh câu trả lời chính xác, cá nhân hóa cao với lượng token tiêu thụ ít nhất.</p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* SLIDE 7: TRIỂN KHAI / KẾT LUẬN */}
                {currentSlide === 7 && (
                  <div className="grid grid-cols-[1.1fr_0.9fr] gap-[42px] items-center">
                    <div className="space-y-4">
                      <div className="inline-flex items-center gap-2 px-[18px] py-[11px] rounded-full bg-[#00b386]/12 text-[#008c72] font-black tracking-widest text-[16px] uppercase">
                        Kết luận triển khai
                      </div>
                      <h2 className="text-[72px] font-black leading-[1.04] text-[#071735]">
                        Một dự án <span className="text-[#00b386]">đáng triển khai</span> cho hệ sinh thái Xanh SM
                      </h2>
                      <p className="text-[22px] font-semibold leading-[1.5] text-[#314967] mt-2">
                        AI Assistant không chỉ trả lời câu hỏi. Khi được kết hợp với dữ liệu lớn từ hệ sinh thái Xanh SM, trợ lý có thể trở thành lớp giao tiếp thông minh giúp người dùng tra cứu, ra quyết định và sử dụng dịch vụ thuận tiện hơn mỗi ngày.
                      </p>

                      <div className="grid grid-cols-2 gap-4 pt-4">
                        {[
                          { img: '/knowledge_search.png', t: 'Thu hút người dùng', d: 'Biến trải nghiệm hỏi đáp thành một điểm chạm chủ động, dễ dùng và hữu ích hơn menu tĩnh.' },
                          { img: '/data_analytics.png', t: 'Tận dụng dữ liệu lớn', d: 'Khai thác dữ liệu chính sách, xe, ưu đãi, tin tức, hành vi và ngữ cảnh để cá nhân hóa câu trả lời.' },
                          { img: '/food_recommendation.png', t: 'Mở rộng tiện ích', d: 'Từ RAG sang Food Recommendation, Ops, Eval và các domain mới trong cùng một assistant.' },
                          { img: '/policy_support.png', t: 'Vận hành đo được', d: 'Trace, latency, feedback và evaluation giúp đội sản phẩm cải thiện chất lượng qua từng vòng lặp.' }
                        ].map((item, idx) => (
                          <div key={idx} className="flex gap-4 border border-[#00b386]/18 rounded-[22px] bg-white p-5 shadow-[0_18px_44px_rgba(13,64,100,0.12)]">
                            <img className="w-[62px] h-[62px] object-cover rounded-[18px] bg-[#ecfffb]" src={item.img} alt="" />
                            <div>
                              <h3 className="text-[#071735] text-[24px] font-black leading-[1.18]">{item.t}</h3>
                              <p className="text-[#405a7a] text-[18px] font-semibold mt-1 leading-[1.38]">{item.d}</p>
                            </div>
                          </div>
                        ))}
                      </div>

                      <button 
                        onClick={() => navigateToTab('Tổng quan')} 
                        className="inline-flex items-center gap-3 px-[26px] py-[20px] rounded-full bg-gradient-to-r from-[#00b386] to-[#10cdb1] text-white shadow-[0_18px_42px_rgba(0,179,134,0.28)] hover:scale-105 active:scale-95 transition-all text-[22px] font-black mt-4"
                      >
                        Sẵn sàng bước vào demo triển khai thực tế
                      </button>
                    </div>

                    <div className="relative min-h-[760px] border border-white/70 bg-gradient-to-b from-white to-[#dcfff8] rounded-[38px] shadow-[0_28px_90px_rgba(8,45,77,0.22)] overflow-hidden flex flex-col justify-between p-8">
                      <div className="absolute inset-[34px] border border-white/72 rounded-[30px] pointer-events-none" />

                      <div className="relative flex-grow">
                        {/* Bot is positioned absolute on top-right exactly like HTML */}
                        <img 
                          className="absolute z-2 right-[96px] top-[108px] w-[360px] object-contain drop-shadow-[0_34px_60px_rgba(4,50,82,0.24)]" 
                          src="/Bot.png" 
                          alt="Xanh SM AI Assistant" 
                        />
                        
                        <div className="absolute flex items-center gap-3 min-w-[198px] p-4 border border-white/78 bg-white backdrop-blur-md rounded-[26px] shadow-md text-[#071735] text-[18px] font-black left-[76px] top-[112px]">
                          <img className="w-[42px] h-[42px] object-cover rounded-xl" src="/vehicle_expert.png" alt="" />
                          Vehicle Expert
                        </div>

                        <div className="absolute flex items-center gap-3 min-w-[198px] p-4 border border-white/78 bg-white backdrop-blur-md rounded-[26px] shadow-md text-[#071735] text-[18px] font-black left-[96px] bottom-[198px]">
                          <img className="w-[42px] h-[42px] object-cover rounded-xl" src="/pricing_assistant.png" alt="" />
                          Pricing & Offer
                        </div>

                        <div className="absolute flex items-center gap-3 min-w-[198px] p-4 border border-white/78 bg-white backdrop-blur-md rounded-[26px] shadow-md text-[#071735] text-[18px] font-black right-[62px] bottom-[220px]">
                          <img className="w-[42px] h-[42px] object-cover rounded-xl" src="/deep_research.png" alt="" />
                          Deep Research
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-[14px] relative z-10">
                        <div className="bg-white border border-[#00b386]/16 rounded-[22px] p-4 min-h-[112px]">
                          <b className="block text-[#00b386] text-[34px] font-black leading-none">1</b>
                          <span className="block text-[#34506f] text-[16px] font-bold mt-1 leading-[1.32]">Assistant thống nhất cho nhiều nhu cầu.</span>
                        </div>
                        <div className="bg-white border border-[#00b386]/16 rounded-[22px] p-4 min-h-[112px]">
                          <b className="block text-[#00b386] text-[34px] font-black leading-none">Data</b>
                          <span className="block text-[#34506f] text-[16px] font-bold mt-1 leading-[1.32]">Hệ sinh thái dữ liệu là lợi thế cạnh tranh.</span>
                        </div>
                        <div className="bg-white border border-[#00b386]/16 rounded-[22px] p-4 min-h-[112px]">
                          <b className="block text-[#00b386] text-[34px] font-black leading-none">Loop</b>
                          <span className="block text-[#34506f] text-[16px] font-bold mt-1 leading-[1.32]">Eval/Ops/Feedback cải thiện liên tục.</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </motion.div>
            </AnimatePresence>
          </div>

          {/* Footer: Fixed position */}
          <div className="relative z-10 flex items-center justify-between border-t border-slate-200/50 pt-5 mt-6 text-[#42617e] text-[18px] font-bold">
            <div>
              {currentSlide === 0 && (
                <span><b>Demo:</b> <a href="https://rag-xanh-sm-v1.vercel.app" target="_blank" rel="noreferrer" className="underline hover:text-[#00b386]">rag-xanh-sm-v1.vercel.app</a></span>
              )}
              {currentSlide === 5 && (
                <span><b>Output:</b> câu trả lời nhất quán, có căn cứ, có thể debug</span>
              )}
              {currentSlide === 6 && (
                <span><b>Result:</b> Gợi ý món ăn thông minh hơn, nhớ vị trí, hiểu ngữ cảnh hội thoại mượt mà</span>
              )}
              {currentSlide !== 0 && currentSlide !== 5 && currentSlide !== 6 && (
                <span>Xanh SM AI Assistant Pitch Deck</span>
              )}
            </div>

            <div className="flex items-center gap-2">
              <span className="text-[16px] text-slate-500 font-extrabold mr-4">
                Slide {currentSlide + 1} / {TOTAL_SLIDES}
              </span>
              <div className="flex gap-1.5">
                {Array.from({ length: TOTAL_SLIDES }).map((_, idx) => (
                  <div 
                    key={idx}
                    onClick={() => {
                      setDirection(idx > currentSlide ? 1 : -1);
                      setCurrentSlide(idx);
                    }}
                    className={`h-2.5 rounded-full transition-all duration-300 cursor-pointer ${
                      idx === currentSlide ? 'w-8 bg-[#00b386]' : 'w-2.5 bg-slate-300 hover:bg-slate-400'
                    }`}
                  />
                ))}
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* Floating control helper widget for keyboard/mouse guidance */}
      <div className="flex gap-8 justify-center items-center mt-3 text-slate-500 text-xs font-semibold relative z-20">
        <div className="flex items-center gap-1.5"><Keyboard size={14} /> Dùng phím <b>Enter</b> / <b>Space</b> / <b>Mũi tên</b> để chuyển slide</div>
        <div className="flex gap-2">
          <button 
            onClick={prevSlide}
            disabled={currentSlide === 0}
            className="w-8 h-8 rounded-full border border-slate-300 flex items-center justify-center text-slate-600 bg-white hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed shadow-xs active:scale-95 transition-all"
          >
            <ChevronLeft size={16} />
          </button>
          <button 
            onClick={nextSlide}
            disabled={currentSlide === TOTAL_SLIDES - 1}
            className="w-8 h-8 rounded-full border border-slate-300 flex items-center justify-center text-slate-600 bg-white hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed shadow-xs active:scale-95 transition-all"
          >
            <ChevronRight size={16} />
          </button>
        </div>
      </div>

    </div>
  );
}
