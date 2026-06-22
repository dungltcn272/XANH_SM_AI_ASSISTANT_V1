import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight, Keyboard, RotateCcw } from 'lucide-react';

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

  // Executive-focused slide tabs
  const getActiveTab = (index) => {
    if (index === 0) return 'Tầm nhìn';
    if (index === 1) return 'Giá trị';
    if (index === 2) return 'Hiệu quả';
    if (index === 3) return 'Khác biệt';
    if (index === 4) return 'Lợi thế';
    if (index === 5 || index === 6) return 'Giải pháp';
    if (index === 7) return 'Triển khai';
    if (index === 8) return 'Nâng cấp';
    return 'Cảm ơn';
  };

  const getTabsList = (index) => {
    if (index === 0 || index === 1 || index === 2) return ['Tầm nhìn', 'Giá trị', 'Hiệu quả', 'Giải pháp'];
    if (index === 3) return ['Tầm nhìn', 'Giá trị', 'Khác biệt', 'Giải pháp'];
    if (index === 4) return ['Tầm nhìn', 'Giá trị', 'Lợi thế', 'Giải pháp'];
    if (index === 5 || index === 6) return ['Tầm nhìn', 'Giá trị', 'Hiệu quả', 'Giải pháp'];
    if (index === 7) return ['Giá trị', 'Giải pháp', 'Triển khai', 'Nâng cấp'];
    if (index === 8) return ['Giải pháp', 'Triển khai', 'Nâng cấp', 'Cảm ơn'];
    return ['Triển khai', 'Nâng cấp', 'Cảm ơn'];
  };

  const navigateToTab = (tabName) => {
    const targetMap = {
      'Tầm nhìn': 0,
      'Giá trị': 1,
      'Hiệu quả': 2,
      'Khác biệt': 3,
      'Lợi thế': 4,
      'Giải pháp': 5,
      'Triển khai': 7,
      'Nâng cấp': 8,
      'Cảm ơn': 9
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
                {/* SLIDE 0: TẦM NHÌN CHIẾN LƯỢC */}
                {currentSlide === 0 && (
                  <div className="grid grid-cols-[0.92fr_1.08fr] gap-[54px] items-center">
                    <div className="space-y-4 max-w-[680px]">
                      <div className="inline-flex items-center gap-2 px-[18px] py-[11px] rounded-full bg-[#00b386]/12 text-[#008c72] font-black tracking-widest text-[17px] uppercase">
                        Giải Pháp Đột Phá Doanh Nghiệp
                      </div>
                      <h1 className="text-[76px] font-black leading-[1.1] text-[#071735]">
                        Tối Ưu Trải Nghiệm<br />
                        <span className="text-[#00b386]">Bán Hàng & CSKH</span>
                      </h1>
                      <p className="text-[24px] font-semibold leading-[1.48] text-[#314967] max-w-[620px]">
                        Hệ thống trợ lý ảo đa nhiệm thế hệ mới cho Xanh SM: Tự động hóa hỗ trợ khách hàng, tối ưu hóa điểm chạm và tăng trưởng doanh thu bán chéo dịch vụ.
                      </p>
                      <div className="flex flex-wrap gap-3 mt-4 max-w-[640px]">
                        <div className="inline-flex items-center gap-2.5 px-[18px] py-[12px] border border-[#00b386]/22 bg-white text-[#123257] text-[18px] font-extrabold rounded-[18px] shadow-sm">
                          ✅ Độ trung thực 99%
                        </div>
                        <div className="inline-flex items-center gap-2.5 px-[18px] py-[12px] border border-[#00b386]/22 bg-white text-[#123257] text-[18px] font-extrabold rounded-[18px] shadow-sm">
                          🎯 Chính xác 90%
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-3 max-w-[640px]" style={{ marginTop: '12px' }}>
                        <div className="inline-flex items-center gap-2.5 px-[18px] py-[12px] border border-[#00b386]/22 bg-white text-[#123257] text-[18px] font-extrabold rounded-[18px] shadow-sm">
                          🛡️ Bảo mật & Tin cậy
                        </div>
                        <div className="inline-flex items-center gap-2.5 px-[18px] py-[12px] border border-[#00b386]/22 bg-white text-[#123257] text-[18px] font-extrabold rounded-[18px] shadow-sm">
                          🚀 RAG & Food NLU
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
                        style={{ left: '32%', transform: 'translateX(-50%)' }}
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

                {/* SLIDE 1: GIÁ TRỊ DOANH NGHIỆP */}
                {currentSlide === 1 && (
                  <div className="space-y-4">
                    <div>
                      <h2 className="text-[54px] font-black leading-tight text-[#071735]">
                        Giải quyết các <span className="text-[#00b386]">bài toán cốt lõi</span>
                      </h2>
                      <p className="text-[22px] font-semibold text-[#415b7d] mt-1 max-w-[1200px]">
                        Một nền tảng trợ lý thông minh duy nhất giúp giải quyết triệt để các thách thức về chi phí nhân sự, giữ chân khách hàng và khai thác tối đa doanh số chéo.
                      </p>
                    </div>
                    <div className="grid grid-cols-4 gap-[16px] pt-2">
                      {[
                        { img: '/knowledge_search.png', t: 'Tự Động Hóa CSKH FAQ', d: 'Trả lời tức thì 90% thắc mắc của khách hàng về chính sách, chuyến đi và giá cước.' },
                        { img: '/deep_research.png', t: 'Hỗ Trợ Đại Lý & Tài Xế', d: 'Tra cứu thông tin chính sách, luật, vận hành nội bộ nhanh chóng cho nhân sự.' },
                        { img: '/vehicle_expert.png', t: 'Chuyên Gia Tư Vấn Dịch Vụ', d: 'Giải đáp tường tận về các dòng xe VinFast, gói thuê xe và chính sách ưu đãi thành viên.' },
                        { img: '/pricing_assistant.png', t: 'Minh Bạch Giá Cước', d: 'Tự động tính toán, giải thích chi tiết cơ chế giá cước động theo thời gian thực.' },
                        { img: '/news_digest.png', t: 'Báo Cáo Tin Tức Tự Động', d: 'Cập nhật nhanh tin tức thị trường xe điện, khuyến mãi tuần cho khách hàng.' },
                        { img: '/food_recommendation.png', t: 'Bán Chéo Food & Địa Điểm', d: 'Tự động gợi ý quán ăn, món ngon quanh vị trí và kích thích đặt xe/đồ ăn.' },
                        { img: '/policy_support.png', t: 'Xử Lý Khiếu Nại 24/7', d: 'Tự động ghi nhận thông tin, phân loại sự cố và hướng dẫn khách hàng xử lý nhanh.' },
                        { img: '/data_analytics.png', t: 'Đo Lường Chất Lượng', d: 'Phân tích dữ liệu hội thoại để tìm ra điểm nghẽn dịch vụ và cải tiến tức thì.' }
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

                {/* SLIDE 2: HIỆU QUẢ KINH DOANH */}
                {currentSlide === 2 && (
                  <div className="space-y-6">
                    <div>
                      <h2 className="text-[60px] font-black leading-tight text-[#071735]">
                        Hiệu quả vận hành & <span className="text-[#00b386]">Tối ưu Chi phí</span>
                      </h2>
                      <p className="text-[26px] font-semibold text-[#415b7d] mt-[16px] max-w-[1120px]">
                        Được kiểm chứng qua các bộ chỉ số vận hành thực tế. Không chỉ là công nghệ, đây là công cụ thúc đẩy hiệu suất kinh doanh trực tiếp.
                      </p>
                    </div>
                    <div className="grid grid-cols-[1.1fr_0.9fr] gap-6 items-stretch pt-2">
                      <div className="border border-[#094a70]/14 rounded-[24px] bg-white p-[30px] shadow-[0_28px_90px_rgba(8,45,77,0.22)] flex flex-col justify-between">
                        <div>
                          <h3 className="text-[#071735] text-[38px] font-black leading-[1.14]">Hiệu Quả Chuyển Đổi Thực Tế</h3>
                          <p className="text-[#344e70] text-[24px] font-semibold mt-[18px] leading-[1.52]">
                            Tối ưu hóa quy trình tư vấn tự động hóa giúp giải phóng áp lực cho tổng đài viên, đồng thời cá nhân hóa trải nghiệm ăn uống và di chuyển của từng khách hàng.
                          </p>
                        </div>
                        <div className="grid grid-cols-2 gap-5 mt-6">
                          <div className="border border-[#00b386]/18 bg-white p-5 rounded-[20px] shadow-sm">
                            <b className="block text-[#071735] text-[34px] font-black leading-tight">Guardrails</b>
                            <span className="block text-[#3d5574] text-[18px] font-semibold mt-[4px] leading-[1.4]">Chặn đứng &gt;99% các câu hỏi tấn công (Prompt Injection) & độc hại.</span>
                          </div>
                          <div className="border border-[#00b386]/18 bg-white p-5 rounded-[20px] shadow-sm">
                            <b className="block text-[#071735] text-[40px] font-black leading-none">99%</b>
                            <span className="block text-[#3d5574] text-[18px] font-semibold mt-[8px] leading-[1.4]">Tỉ lệ phản hồi trung thực (Faithfulness) trên tập kiểm thử.</span>
                          </div>
                          <div className="border border-[#00b386]/18 bg-white p-5 rounded-[20px] shadow-sm">
                            <b className="block text-[#071735] text-[40px] font-black leading-none">~5s</b>
                            <span className="block text-[#3d5574] text-[18px] font-semibold mt-[8px] leading-[1.4]">Thời gian phản hồi toàn bộ Pipeline (NLU + RAG + LLM) cho truy vấn phức tạp.</span>
                          </div>
                          <div className="border border-[#00b386]/18 bg-white p-5 rounded-[20px] shadow-sm">
                            <b className="block text-[#008c72] text-[40px] font-black leading-none">90%</b>
                            <span className="block text-[#3d5574] text-[18px] font-semibold mt-[8px] leading-[1.4]">Tỉ lệ trả lời chính xác (Correctness) trên toàn bộ domain.</span>
                          </div>
                        </div>
                      </div>
                      <div className="border border-[#094a70]/14 rounded-[24px] bg-white p-5 shadow-[0_28px_90px_rgba(8,45,77,0.22)] flex items-center justify-center overflow-hidden">
                        <img className="max-w-full max-h-[460px] object-contain rounded-[22px] shadow-[0_18px_60px_rgba(0,70,98,0.18)]" src="/food_recommend.png" alt="Food recommendation demo" />
                      </div>
                    </div>
                  </div>
                )}

                {/* SLIDE 3: KIẾN TRÚC CÔNG NGHỆ (Gộp NLU, Pipeline, Memory) */}
                {currentSlide === 3 && (
                  <div className="space-y-6">
                    <div>
                      <h2 className="text-[60px] font-black leading-tight text-[#071735]">
                        Kiến trúc <span className="text-[#00b386]">AI Assistant Pipeline</span> tinh gọn
                      </h2>
                      <p className="text-[26px] font-semibold text-[#415b7d] mt-[16px] max-w-[1120px]">
                        Một hệ thống duy nhất xử lý thông minh: NLU đọc ý định khách hàng, Multi-agent Pipeline điều phối RAG/Food, và Memory lưu giữ ngữ cảnh xuyên suốt.
                      </p>
                    </div>
                    <div className="grid grid-cols-3 gap-5 pt-2">
                      <div className="border border-[#094a70]/14 rounded-[24px] bg-white p-6 shadow-[0_16px_36px_rgba(13,64,100,0.1)] flex flex-col justify-between min-h-[220px]">
                        <div className="w-[46px] h-[46px] rounded-xl bg-gradient-to-br from-[#00b386] to-[#1cc7f2] text-white flex items-center justify-center font-black text-[20px]">1</div>
                        <div className="mt-4 flex-grow">
                          <h3 className="text-[#071735] text-[28px] font-black leading-[1.2]">Parallel NLU</h3>
                          <p className="text-[#405a7a] text-[20px] font-semibold mt-2 leading-[1.4]">Phân tích đa luồng song song: bóc tách Intent, trích xuất Slot và nhận diện Missing-info siêu tốc.</p>
                        </div>
                      </div>
                      <div className="border border-[#094a70]/14 rounded-[24px] bg-white p-6 shadow-[0_16px_36px_rgba(13,64,100,0.1)] flex flex-col justify-between min-h-[220px]">
                        <div className="w-[46px] h-[46px] rounded-xl bg-gradient-to-br from-[#00b386] to-[#1cc7f2] text-white flex items-center justify-center font-black text-[20px]">2</div>
                        <div className="mt-4 flex-grow">
                          <h3 className="text-[#071735] text-[28px] font-black leading-[1.2]">Hybrid RAG & Food</h3>
                          <p className="text-[#405a7a] text-[20px] font-semibold mt-2 leading-[1.4]">Kết hợp Sparse/Dense Retrieval và Agentic Routing để gợi ý quán ăn, xe cộ chuẩn xác 90%.</p>
                        </div>
                      </div>
                      <div className="border border-[#094a70]/14 rounded-[24px] bg-white p-6 shadow-[0_16px_36px_rgba(13,64,100,0.1)] flex flex-col justify-between min-h-[220px]">
                        <div className="w-[46px] h-[46px] rounded-xl bg-gradient-to-br from-[#00b386] to-[#1cc7f2] text-white flex items-center justify-center font-black text-[20px]">3</div>
                        <div className="mt-4 flex-grow">
                          <h3 className="text-[#071735] text-[28px] font-black leading-[1.2]">Context Memory</h3>
                          <p className="text-[#405a7a] text-[20px] font-semibold mt-2 leading-[1.4]">Ghi nhớ sở thích, ngữ cảnh phiên chat giúp Assistant luôn đưa ra phản hồi mang tính cá nhân hóa.</p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* SLIDE 5: VỊ THẾ XANH SM TRÊN BẢN ĐỒ AI */}
                {currentSlide === 4 && (
                  <div className="space-y-4">
                    <div>
                      <h2 className="text-[54px] font-black leading-tight text-[#071735]">
                        Bản đồ AI Assistant & <span className="text-[#00b386]">Sức Mạnh Cốt Lõi</span>
                      </h2>
                      <p className="text-[24px] font-semibold text-[#415b7d] mt-[10px] max-w-[1120px]">
                        Xanh SM AI đang dẫn đầu mảng <b>Enterprise Knowledge AI</b> (95/100 điểm), vượt xa các đối thủ về độ tin cậy, chống Hallucination và khả năng quản trị tri thức.
                      </p>
                    </div>
                    
                    <div className="grid grid-cols-[1fr_1.5fr] gap-8 mt-8">
                      {/* Left: AI Landscape */}
                      <div className="border border-[#094a70]/11 rounded-[24px] bg-white shadow-[0_28px_90px_rgba(8,45,77,0.22)] p-8 flex flex-col">
                        <h3 className="text-[#071735] text-[28px] font-black mb-6 border-b border-slate-100 pb-4">Điểm Đánh Giá Kiến Trúc AI</h3>
                        <div className="space-y-6 flex-grow justify-center flex flex-col">
                          {[
                            { name: 'Knowledge Assistant', xanh: 95, grab: 100 },
                            { name: 'Customer Support AI', xanh: 90, grab: 95 },
                            { name: 'Enterprise RAG & Eval', xanh: 95, grab: 80 },
                            { name: 'Hallucination Control', xanh: 90, grab: 60 }
                          ].map(item => (
                            <div key={item.name}>
                              <div className="flex justify-between text-[20px] font-bold text-[#071735] mb-2">
                                <span>{item.name}</span>
                              </div>
                              <div className="flex items-center gap-4">
                                <div className="text-[16px] font-bold w-[120px] text-[#00b386]">Xanh SM: {item.xanh}</div>
                                <div className="flex-1 h-4 bg-slate-100 rounded-full overflow-hidden">
                                  <div className="h-full bg-[#00b386] rounded-full" style={{ width: `${item.xanh}%` }}></div>
                                </div>
                              </div>
                              <div className="flex items-center gap-4 mt-2">
                                <div className="text-[16px] font-bold w-[120px] text-[#00a5cf]">Grab: {item.grab}</div>
                                <div className="flex-1 h-4 bg-slate-100 rounded-full overflow-hidden">
                                  <div className="h-full bg-[#00a5cf] rounded-full" style={{ width: `${item.grab}%` }}></div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Right: What we are better at */}
                      <div className="border border-[#094a70]/11 rounded-[24px] bg-white shadow-[0_28px_90px_rgba(8,45,77,0.22)] p-8">
                        <h3 className="text-[#00b386] text-[32px] font-black mb-6 flex items-center gap-3">
                          🏆 Điểm Xanh SM Đang Vượt Trội 
                        </h3>
                        <ul className="space-y-6 text-[20px] text-[#405a7a] font-medium leading-[1.6]">
                          <li className="flex gap-4">
                            <span className="text-[#00b386] text-[28px] mt-1">●</span>
                            <div>
                              <strong className="text-[#071735] text-[24px] block mb-1">Kiến trúc RAG Tiêu chuẩn Doanh nghiệp</strong>
                              Xanh SM sở hữu luồng Hybrid Retrieval kết hợp Reranker và Context Expansion mạnh mẽ hơn hầu hết Chatbot CSKH hiện tại của Grab/Uber.
                            </div>
                          </li>
                          <li className="flex gap-4">
                            <span className="text-[#00b386] text-[28px] mt-1">●</span>
                            <div>
                              <strong className="text-[#071735] text-[24px] block mb-1">Kiểm soát Hallucination & Trích dẫn minh bạch</strong>
                              Hệ thống có độ chính xác (Faithfulness) chạm ngưỡng 99%. Trả lời hoàn toàn dựa trên tài liệu Xanh SM, cho phép truy vết (Tracing) rõ ràng, ngược lại với mô hình "Hộp đen suy luận" của Grab.
                            </div>
                          </li>
                          <li className="flex gap-4">
                            <span className="text-[#00b386] text-[28px] mt-1">●</span>
                            <div>
                              <strong className="text-[#071735] text-[24px] block mb-1">Đánh Giá Bằng RAGAS</strong>
                              Xanh SM AI được tích hợp hệ thống Evaluation tự động theo thời gian thực (Correctness, Faithfulness). Đây là tiêu chuẩn vàng mà đa số AI trên thị trường chưa publish.
                            </div>
                          </li>
                        </ul>
                      </div>
                    </div>
                  </div>
                )}

                {/* SLIDE 6: PHÂN TÍCH KHOẢNG CÁCH */}
                {currentSlide === 5 && (
                  <div className="space-y-4">
                    <div>
                      <h2 className="text-[54px] font-black leading-tight text-[#071735]">
                        Cuộc Đua Tới <span className="text-[#00b386]">AI Concierge</span>
                      </h2>
                      <p className="text-[24px] font-semibold text-[#415b7d] mt-[10px] max-w-[1120px]">
                        Xanh SM đang nằm ở bước <b>Knowledge Assistant</b>. Để bắt kịp hệ sinh thái của Grab, chúng ta cần chuyển mình thành <b>Life Assistant / Action Agent</b>.
                      </p>
                    </div>

                    <div className="grid grid-cols-[1.5fr_1fr] gap-8 mt-8">
                      {/* Left: What Grab is better at */}
                      <div className="border border-[#094a70]/11 rounded-[24px] bg-white shadow-[0_28px_90px_rgba(8,45,77,0.22)] p-8">
                        <h3 className="text-[#e11d48] text-[32px] font-black mb-6 flex items-center gap-3">
                          📉 Những Điểm Grab Bỏ Xa Xanh SM
                        </h3>
                        <ul className="space-y-6 text-[20px] text-[#405a7a] font-medium leading-[1.6]">
                          <li className="flex gap-4">
                            <span className="text-[#e11d48] text-[28px] mt-1">●</span>
                            <div>
                              <strong className="text-[#071735] text-[24px] block mb-1">Thiếu Dữ Liệu Hành Vi & Cá Nhân Hóa Sâu</strong>
                              Grab sở hữu hàng trăm triệu giao dịch đa dịch vụ (ăn uống, đi lại, thanh toán). AI Recommendation của họ ăn đứt mọi startup nhờ lịch sử này. (Grab: 100 vs Xanh: 50).
                            </div>
                          </li>
                          <li className="flex gap-4">
                            <span className="text-[#e11d48] text-[28px] mt-1">●</span>
                            <div>
                              <strong className="text-[#071735] text-[24px] block mb-1">Chưa Trở Thành "Agent Thực Chiến" Đa Bước</strong>
                              Grab AI có thể nhận lệnh: <i className="text-slate-500">"Tổ chức sinh nhật 10 người, ngân sách 3 triệu"</i> &rarr; Tự tìm quán &rarr; Đặt bàn &rarr; Gọi xe trong 1 cuộc trò chuyện duy nhất. Xanh SM vẫn là dạng "Hỏi - Đáp - Tool Calling đơn giản".
                            </div>
                          </li>
                          <li className="flex gap-4">
                            <span className="text-[#e11d48] text-[28px] mt-1">●</span>
                            <div>
                              <strong className="text-[#071735] text-[24px] block mb-1">Giao Tiếp Đa Phương Thức (Voice Native)</strong>
                              Grab đã hỗ trợ Voice Notes và thao tác bằng giọng nói xuyên suốt. Chúng ta hiện chưa có hệ sinh thái Voice-First thực sự trơn tru.
                            </div>
                          </li>
                        </ul>
                      </div>

                      {/* Right: Path to victory */}
                      <div className="border border-[#094a70]/11 rounded-[24px] bg-[#e1fff7] shadow-[0_28px_90px_rgba(8,45,77,0.22)] p-8 flex flex-col justify-center border-l-[8px] border-l-[#00b386]">
                        <h3 className="text-[#071735] text-[32px] font-black mb-6">Chiến Lược Bứt Phá 🚀</h3>
                        <div className="space-y-5 text-[22px] font-bold text-[#405a7a]">
                          <div className="flex items-center gap-3">
                            <span className="w-10 h-10 rounded-full bg-white flex items-center justify-center text-[#00b386] border border-[#00b386]">1</span>
                            Hoàn thiện Food Recommendation Engine
                          </div>
                          <div className="flex justify-center my-2 text-[#00b386]">↓</div>
                          <div className="flex items-center gap-3">
                            <span className="w-10 h-10 rounded-full bg-white flex items-center justify-center text-[#00b386] border border-[#00b386]">2</span>
                            Tích hợp Preference Memory Dài Hạn
                          </div>
                          <div className="flex justify-center my-2 text-[#00b386]">↓</div>
                          <div className="flex items-center gap-3">
                            <span className="w-10 h-10 rounded-full bg-white flex items-center justify-center text-[#00b386] border border-[#00b386]">3</span>
                            Phát triển Multi-Agent Planning
                          </div>
                          <div className="mt-8 pt-6 border-t border-[#00b386]/30 text-[20px] text-[#071735] leading-[1.6]">
                            Chỉ cần hoàn thành luồng này, Xanh SM sẽ tiến thẳng từ mốc <b>60 điểm</b> lên <b>90 điểm</b> AI Concierge, tạo thế đối trọng sòng phẳng với Grab!
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* SLIDE 7: NÂNG CẤP HỆ SINH THÁI */}
                {currentSlide === 6 && (
                  <div className="space-y-6">
                    <div>
                      <h2 className="text-[60px] font-black leading-tight text-[#071735]">
                        Tầm nhìn <span className="text-[#00b386]">Nâng Cấp Hệ Sinh Thái</span>
                      </h2>
                      <p className="text-[26px] font-semibold text-[#415b7d] mt-[16px] max-w-[1120px]">
                        Xanh SM AI Assistant liên tục mở rộng tiện ích nhằm mang lại trải nghiệm tối ưu nhất cho Đối tác Tài xế và Nhà hàng, thúc đẩy doanh số và hiệu suất.
                      </p>
                    </div>

                    <div className="grid grid-cols-2 gap-8 pt-4">
                      {/* Cột Tài xế */}
                      <div className="border border-[#094a70]/14 rounded-[24px] bg-white p-[30px] shadow-[0_16px_36px_rgba(13,64,100,0.1)]">
                        <div className="flex items-center gap-4 mb-6">
                          <div className="w-[60px] h-[60px] rounded-2xl bg-gradient-to-br from-[#00b386] to-[#10cdb1] flex items-center justify-center text-white text-[32px]">🚘</div>
                          <h3 className="text-[#071735] text-[34px] font-black leading-[1.2]">Đối tác Tài xế (Drivers)</h3>
                        </div>
                        <ul className="space-y-4">
                          <li className="flex gap-4">
                            <span className="text-[#00b386] text-[24px]">✓</span>
                            <div>
                              <strong className="text-[#071735] text-[20px]">Trợ Lý Rảnh Tay (Voice-First):</strong>
                              <p className="text-[#405a7a] text-[18px] mt-1">Hỏi doanh thu, kiểm tra thưởng, báo cáo sự cố bằng giọng nói, không cần chạm màn hình.</p>
                            </div>
                          </li>
                          <li className="flex gap-4">
                            <span className="text-[#00b386] text-[24px]">✓</span>
                            <div>
                              <strong className="text-[#071735] text-[20px]">Tối Ưu Hóa Trạm Sạc V-GREEN:</strong>
                              <p className="text-[#405a7a] text-[18px] mt-1">Gợi ý trạm sạc gần nhất có trụ trống và giá tối ưu theo thời gian thực.</p>
                            </div>
                          </li>
                          <li className="flex gap-4">
                            <span className="text-[#00b386] text-[24px]">✓</span>
                            <div>
                              <strong className="text-[#071735] text-[20px]">Heatmap & Điều Hướng:</strong>
                              <p className="text-[#405a7a] text-[18px] mt-1">Dự báo điểm nóng nhu cầu cao để điều phối xe, tối đa hóa thu nhập.</p>
                            </div>
                          </li>
                        </ul>
                      </div>

                      {/* Cột Nhà hàng */}
                      <div className="border border-[#094a70]/14 rounded-[24px] bg-white p-[30px] shadow-[0_16px_36px_rgba(13,64,100,0.1)]">
                        <div className="flex items-center gap-4 mb-6">
                          <div className="w-[60px] h-[60px] rounded-2xl bg-gradient-to-br from-[#ff9900] to-[#ffb84d] flex items-center justify-center text-white text-[32px]">🍜</div>
                          <h3 className="text-[#071735] text-[34px] font-black leading-[1.2]">Cửa hàng (Merchants)</h3>
                        </div>
                        <ul className="space-y-4">
                          <li className="flex gap-4">
                            <span className="text-[#ff9900] text-[24px]">✓</span>
                            <div>
                              <strong className="text-[#071735] text-[20px]">Dự Báo Nhu Cầu & Tồn Kho:</strong>
                              <p className="text-[#405a7a] text-[18px] mt-1">Phân tích thời tiết, sự kiện để dự báo đơn hàng, tối ưu nhập nguyên liệu.</p>
                            </div>
                          </li>
                          <li className="flex gap-4">
                            <span className="text-[#ff9900] text-[24px]">✓</span>
                            <div>
                              <strong className="text-[#071735] text-[20px]">Tự Động Trả Lời Đánh Giá:</strong>
                              <p className="text-[#405a7a] text-[18px] mt-1">Tạo phản hồi chuẩn mực, cá nhân hóa cho từng review, tiết kiệm CSKH.</p>
                            </div>
                          </li>
                          <li className="flex gap-4">
                            <span className="text-[#ff9900] text-[24px]">✓</span>
                            <div>
                              <strong className="text-[#071735] text-[20px]">Đề Xuất Khuyến Mãi:</strong>
                              <p className="text-[#405a7a] text-[18px] mt-1">Gợi ý tạo combo flash sale vào khung giờ thấp điểm nhằm kích cầu.</p>
                            </div>
                          </li>
                        </ul>
                      </div>
                    </div>
                  </div>
                )}

                {/* SLIDE 8: CẢM ƠN */}
                {currentSlide === 7 && (
                  <div className="flex flex-col items-center justify-center h-full text-center space-y-8">
                    <img src="/logo.svg" alt="Green SM" className="h-[120px] mb-4 drop-shadow-xl" />
                    <h1 className="text-[86px] font-black leading-[1.1] text-[#071735]">
                      Cảm ơn quý vị đã lắng nghe!
                    </h1>
                    <p className="text-[32px] font-semibold leading-[1.48] text-[#314967] max-w-[800px]">
                      Xanh SM AI Assistant - Cùng kiến tạo tương lai dịch vụ xanh và thông minh.
                    </p>
                    <button 
                      onClick={() => setCurrentSlide(0)} 
                      className="inline-flex items-center gap-3 px-[32px] py-[24px] rounded-full bg-gradient-to-r from-[#00b386] to-[#10cdb1] text-white shadow-[0_18px_42px_rgba(0,179,134,0.28)] hover:scale-105 active:scale-95 transition-all text-[26px] font-black mt-8"
                    >
                      <RotateCcw size={28} /> Trở về trang đầu
                    </button>
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
              
              
              
              
              
              {currentSlide !== 0 && currentSlide !== 6 && currentSlide !== 7 && (
                <span>Giải Pháp Trợ Lý Ảo Thông Minh Xanh SM</span>
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
