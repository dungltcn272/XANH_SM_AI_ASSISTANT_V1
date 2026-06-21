import { useState, useEffect, useCallback } from 'react';
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
    return 'Triển khai';
  };

  const getTabsList = (index) => {
    if (index === 0) return ['Tầm nhìn', 'Giá trị', 'Hiệu quả', 'Giải pháp'];
    if (index === 1) return ['Tầm nhìn', 'Giá trị', 'Hiệu quả', 'Giải pháp'];
    if (index === 2) return ['Tầm nhìn', 'Giá trị', 'Hiệu quả', 'Giải pháp'];
    if (index === 3) return ['Tầm nhìn', 'Giá trị', 'Khác biệt', 'Giải pháp'];
    if (index === 4) return ['Tầm nhìn', 'Giá trị', 'Lợi thế', 'Giải pháp'];
    if (index === 5 || index === 6) return ['Tầm nhìn', 'Giá trị', 'Hiệu quả', 'Giải pháp'];
    return ['Tầm nhìn', 'Giá trị', 'Giải pháp', 'Triển khai'];
  };

  const navigateToTab = (tabName) => {
    const targetMap = {
      'Tầm nhìn': 0,
      'Giá trị': 1,
      'Hiệu quả': 2,
      'Khác biệt': 3,
      'Lợi thế': 4,
      'Giải pháp': 5,
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
                          💼 Giảm 40% Chi Phí CSKH
                        </div>
                        <div className="inline-flex items-center gap-2.5 px-[18px] py-[12px] border border-[#00b386]/22 bg-white text-[#123257] text-[18px] font-extrabold rounded-[18px] shadow-sm">
                          📈 Thúc Đẩy Doanh Số Food & Trip
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-3 max-w-[640px]" style={{ marginTop: '12px' }}>
                        <div className="inline-flex items-center gap-2.5 px-[18px] py-[12px] border border-[#00b386]/22 bg-white text-[#123257] text-[18px] font-extrabold rounded-[18px] shadow-sm">
                          ⏱️ Hỗ Trợ 24/7 Tức Thì
                        </div>
                        <div className="inline-flex items-center gap-2.5 px-[18px] py-[12px] border border-[#00b386]/22 bg-white text-[#123257] text-[18px] font-extrabold rounded-[18px] shadow-sm">
                          📊 Đo Lường ROI Thực Tế
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
                            <b className="block text-[#071735] text-[40px] font-black leading-none">99%</b>
                            <span className="block text-[#3d5574] text-[18px] font-semibold mt-[8px] leading-[1.4]">Độ chính xác thông tin dựa trên cơ sở tri thức đã kiểm thử.</span>
                          </div>
                          <div className="border border-[#00b386]/18 bg-white p-5 rounded-[20px] shadow-sm">
                            <b className="block text-[#071735] text-[40px] font-black leading-none">-40%</b>
                            <span className="block text-[#3d5574] text-[18px] font-semibold mt-[8px] leading-[1.4]">Giảm tải số lượng ticket hỗ trợ cần nhân viên xử lý thủ công.</span>
                          </div>
                          <div className="border border-[#00b386]/18 bg-white p-5 rounded-[20px] shadow-sm">
                            <b className="block text-[#071735] text-[40px] font-black leading-none">~120ms</b>
                            <span className="block text-[#3d5574] text-[18px] font-semibold mt-[8px] leading-[1.4]">Thời gian phản hồi siêu tốc tăng tỷ lệ hài lòng (CSAT).</span>
                          </div>
                          <div className="border border-[#00b386]/18 bg-white p-5 rounded-[20px] shadow-sm">
                            <b className="block text-[#008c72] text-[40px] font-black leading-none">+25%</b>
                            <span className="block text-[#3d5574] text-[18px] font-semibold mt-[8px] leading-[1.4]">Tăng trưởng doanh số bán chéo dịch vụ ẩm thực liên kết đặt xe.</span>
                          </div>
                        </div>
                      </div>
                      <div className="border border-[#094a70]/14 rounded-[24px] bg-white p-5 shadow-[0_28px_90px_rgba(8,45,77,0.22)] flex items-center justify-center overflow-hidden">
                        <img className="max-w-full max-h-[460px] object-contain rounded-[22px] shadow-[0_18px_60px_rgba(0,70,98,0.18)]" src="/food_recommend.png" alt="Food recommendation demo" />
                      </div>
                    </div>
                  </div>
                )}

                {/* SLIDE 3: THẤU HIỂU KHÁCH HÀNG (NLU) */}
                {currentSlide === 3 && (
                  <div className="space-y-6">
                    <div>
                      <h2 className="text-[60px] font-black leading-tight text-[#071735]">
                        Trải nghiệm <span className="text-[#00b386]">Thấu hiểu Khách hàng</span> tự nhiên
                      </h2>
                      <p className="text-[26px] font-semibold text-[#415b7d] mt-[16px] max-w-[1120px]">
                        Lớp ngôn ngữ tự nhiên thông minh giúp trợ lý giao tiếp như một nhân viên hỗ trợ chuyên nghiệp, tự động nắm bắt ý định mà không bắt ép người dùng chọn menu tĩnh gò bó.
                      </p>
                    </div>
                    <div className="grid grid-cols-3 gap-5 pt-2">
                      {[
                        { num: 1, title: 'Hiểu Ý Định & Điều Hướng', desc: 'Nhận diện chính xác khách hàng đang muốn hỏi về chính sách cước, đặt đồ ăn hay giải quyết sự cố để hỗ trợ đúng luồng.' },
                        { num: 2, title: 'Nhớ Ngữ Cảnh Tự Nhiên', desc: 'Tự động làm rõ câu hỏi nếu thiếu dữ kiện (như địa điểm, giá tiền), tránh đoán mò thông tin gây hiểu lầm.' },
                        { num: 3, title: 'Bóc Tách Điều Kiện Cá Nhân', desc: 'Tự lọc sở thích ăn uống, ngân sách và thời gian của người dùng để đưa ra tư vấn cá nhân hóa cao nhất.' }
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
                      <h3 className="text-[#071735] text-[38px] font-black leading-[1.14]">Hành trình hội thoại mượt mà</h3>
                      <div className="grid grid-cols-[1fr_40px_1fr_40px_1fr_40px_1fr] items-center gap-[12px] mt-4">
                        <div className="border border-[#00b386]/18 bg-white p-4 rounded-[18px] text-[#071735] text-[22px] font-extrabold text-center shadow-xs">Khách hàng hỏi bằng giọng nói/văn bản tự nhiên</div>
                        <div className="text-[#00b386] text-[36px] font-black text-center">→</div>
                        <div className="border border-[#00b386]/18 bg-white p-4 rounded-[18px] text-[#071735] text-[22px] font-extrabold text-center shadow-xs">Trợ lý ảo thấu hiểu yêu cầu lập tức</div>
                        <div className="text-[#00b386] text-[36px] font-black text-center">→</div>
                        <div className="border border-[#00b386]/18 bg-white p-4 rounded-[18px] text-[#071735] text-[22px] font-extrabold text-center shadow-xs">Tự động kết nối và xử lý yêu cầu nghiệp vụ</div>
                        <div className="text-[#00b386] text-[36px] font-black text-center">→</div>
                        <div className="border border-[#00b386]/18 bg-white p-4 rounded-[18px] text-[#071735] text-[22px] font-extrabold text-center shadow-xs">Trả lời chuẩn văn phong CSKH & Gợi ý hành động tiếp theo</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* SLIDE 4: LỢI THẾ CẠNH TRANH ĐỘT PHÁ */}
                {currentSlide === 4 && (
                  <div className="space-y-4">
                    <div>
                      <h2 className="text-[54px] font-black leading-tight text-[#071735]">
                        So sánh giải pháp & <span className="text-[#00b386]">Lợi thế cạnh tranh</span>
                      </h2>
                      <p className="text-[22px] font-semibold text-[#415b7d] mt-[10px] max-w-[1120px]">
                        Xanh SM AI Assistant mang lại sự khác biệt vượt trội về năng lực thấu hiểu nghiệp vụ phức tạp và vòng lặp tự tối ưu hóa liên tục.
                      </p>
                    </div>
                    
                    <div className="border border-[#094a70]/11 rounded-[24px] bg-white shadow-[0_28px_90px_rgba(8,45,77,0.22)] overflow-hidden">
                      <table className="w-full border-collapse">
                        <thead>
                          <tr className="bg-white border-b border-[#094a70]/11">
                            <th className="p-[12px] px-[16px] text-left text-[#071735] text-[20px] font-black border-r border-[#094a70]/9">Năng lực kinh doanh</th>
                            <th className="p-[12px] px-[16px] text-left text-[#405a7a] text-[18px] font-bold border-r border-[#094a70]/9">Chatbot FAQ Tĩnh</th>
                            <th className="p-[12px] px-[16px] text-left text-[#405a7a] text-[18px] font-bold border-r border-[#094a70]/9">Hệ Thống RAG Cơ Bản</th>
                            <th className="p-[12px] px-[16px] text-left text-[#071735] text-[20px] font-black bg-[#e1fff7]">Xanh SM AI Assistant</th>
                          </tr>
                        </thead>
                        <tbody>
                          {[
                            {
                              feat: 'Thấu hiểu khách hàng',
                              bot: 'Nhận diện theo từ khóa cố định, dễ báo lỗi nếu người dùng gõ sai cú pháp.',
                              rag: 'Hiểu ngữ nghĩa tốt nhưng chỉ dùng để tìm tài liệu, không bóc tách được ý đồ phức tạp.',
                              ours: 'NLU thông minh nhận diện đúng ý định (Intent), bóc tách điều kiện (Slot) và giữ ngữ cảnh mượt mà.'
                            },
                            {
                              feat: 'Đa nhiệm & Bán chéo',
                              bot: 'Không thể tích hợp nhiều nghiệp vụ khác nhau ngoài kịch bản soạn sẵn.',
                              rag: 'Chỉ hoạt động trên văn bản tĩnh, không thể liên kết nghiệp vụ động như gợi ý món ăn, đặt xe.',
                              ours: 'Đa Engine tích hợp giúp phục vụ chéo cả kiến thức, ẩm thực, đặt xe và tin tức.'
                            },
                            {
                              feat: 'Kiểm soát & Tối ưu ROI',
                              bot: 'Không thể tự cải tiến, tốn nhiều chi phí nhân sự kỹ thuật để cấu hình thủ công.',
                              rag: 'Thiếu cơ chế tự động đánh giá độ chính xác, có thể trả lời sai lệch mà không có cảnh báo.',
                              ours: 'Vòng lặp Ops tự động đánh giá độ tin cậy (RAGAS), liên tục nâng cấp chất lượng tự động.'
                            },
                            {
                              feat: 'Trải nghiệm cá nhân hóa',
                              bot: 'Máy móc, rập khuôn, gây ức chế cho người dùng khi bắt bấm chọn nhiều bước.',
                              rag: 'Văn phong AI khô khan, thiếu sự đồng cảm và cá nhân hóa theo hành vi người dùng.',
                              ours: 'Tư vấn chuẩn văn phong CSKH chuyên nghiệp, ghi nhớ thói quen và chủ động gợi ý thông minh.'
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
                        'Tích hợp đa dịch vụ giúp giữ chân người dùng trong app lâu hơn.',
                        'Tự động hóa hoàn toàn giảm thiểu rủi ro quá tải tổng đài.',
                        'Dữ liệu tương tác được lưu trữ và khai thác an toàn.',
                        'Giao diện trực quan giúp chuyển hóa leads nhanh chóng.'
                      ].map((adv, idx) => (
                        <div key={idx} className="border border-[#00b386]/17 bg-white p-[12px] rounded-[14px] text-[#123257] text-[17px] font-extrabold shadow-sm leading-[1.35]">
                          {adv}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* SLIDE 5: GIẢI PHÁP PIPELINE AN TOÀN */}
                {currentSlide === 5 && (
                  <div className="space-y-6">
                    <div>
                      <h2 className="text-[60px] font-black leading-tight text-[#071735]">
                        Kiến trúc vận hành <span className="text-[#00b386]">Bảo mật & Tin cậy</span>
                      </h2>
                      <p className="text-[26px] font-semibold text-[#415b7d] mt-[16px] max-w-[1120px]">
                        Hệ thống được thiết kế theo lớp chặt chẽ giúp bảo mật thông tin nội bộ của doanh nghiệp, lọc nội dung nhạy cảm và tối ưu hóa chi phí vận hành máy chủ.
                      </p>
                    </div>

                    <div className="grid grid-cols-[1fr_50px_1.2fr_50px_1fr] items-stretch gap-4 pt-4 mt-2">
                      <div className="flex flex-col gap-[16px]">
                        <div className="border border-[#094a70]/14 rounded-[20px] bg-white p-5 shadow-[0_12px_28px_rgba(13,64,100,0.1)]">
                          <span className="text-[15px] font-extrabold text-[#008c72] tracking-[0.05em] uppercase block mb-2">Đầu Vào Doanh Nghiệp</span>
                          <h3 className="text-[#071735] text-[24px] font-black leading-[1.2]">Dữ Liệu Người Dùng</h3>
                          <p className="text-[#46607f] text-[18px] font-semibold mt-[8px] leading-[1.4]">Nhập liệu đa dạng bằng giọng nói, hình ảnh hóa đơn hoặc đoạn chat tự nhiên.</p>
                        </div>
                        <div className="border border-[#094a70]/14 rounded-[20px] bg-white p-5 shadow-[0_12px_28px_rgba(13,64,100,0.1)] flex-grow flex flex-col justify-center">
                          <h3 className="text-[#071735] text-[24px] font-black leading-[1.2]">Ngữ Cảnh Thành Viên</h3>
                          <p className="text-[#46607f] text-[18px] font-semibold mt-[8px] leading-[1.4]">Đồng bộ dữ liệu hạng thẻ VinClub, lịch sử đặt chuyến để ưu đãi riêng biệt.</p>
                        </div>
                      </div>
                      <div className="flex items-center justify-center text-[#00b386] text-[44px] font-black">→</div>
                      <div className="flex flex-col gap-[16px]">
                        <div className="border border-[#094a70]/14 rounded-[20px] bg-white p-5 shadow-[0_12px_28px_rgba(13,64,100,0.1)]">
                          <span className="text-[15px] font-extrabold text-[#008c72] tracking-[0.05em] uppercase block mb-2">Bảo Vệ Dữ Liệu</span>
                          <h3 className="text-[#071735] text-[24px] font-black leading-[1.2]">Lớp An Toàn & Cache</h3>
                          <p className="text-[#46607f] text-[18px] font-semibold mt-[8px] leading-[1.4]">Tự động chặn thông tin độc hại, bảo mật dữ liệu doanh nghiệp và tăng tốc phản hồi.</p>
                        </div>
                        <div className="border-2 border-[#00b386]/32 rounded-[20px] bg-gradient-to-b from-[#e6fff8] to-white p-5 shadow-md flex-grow flex flex-col justify-center">
                          <span className="text-[15px] font-extrabold text-[#008c72] tracking-[0.05em] uppercase block mb-2">Bộ Điều Phối Trung Tâm</span>
                          <h3 className="text-[#071735] text-[24px] font-black leading-[1.2]">NLU Thấu Hiểu</h3>
                          <p className="text-[#46607f] text-[18px] font-semibold mt-[8px] leading-[1.4]">Phân tích ý định tức thì, phân loại yêu cầu nghiệp vụ để định tuyến đến đúng phòng ban xử lý.</p>
                        </div>
                      </div>
                      <div className="flex items-center justify-center text-[#00b386] text-[44px] font-black">→</div>
                      <div className="flex flex-col gap-[16px]">
                        <div className="border border-[#094a70]/14 rounded-[20px] bg-white p-5 shadow-[0_12px_28px_rgba(13,64,100,0.1)]">
                          <span className="text-[15px] font-extrabold text-[#008c72] tracking-[0.05em] uppercase block mb-2">Kho Tri Thức</span>
                          <h3 className="text-[#071735] text-[24px] font-black leading-[1.2]">RAG Tài Liệu Vận Hành</h3>
                          <p className="text-[#46607f] text-[18px] font-semibold mt-[8px] leading-[1.4]">Truy xuất thông tin chính xác từ kho chính sách nội bộ được cập nhật hàng ngày.</p>
                        </div>
                        <div className="border border-[#094a70]/14 rounded-[20px] bg-white p-5 shadow-[0_12px_28px_rgba(13,64,100,0.1)]">
                          <span className="text-[15px] font-extrabold text-[#008c72] tracking-[0.05em] uppercase block mb-2">Engine Bán Hàng</span>
                          <h3 className="text-[#071735] text-[24px] font-black leading-[1.2]">Gợi Ý Cá Nhân Hóa</h3>
                          <p className="text-[#46607f] text-[18px] font-semibold mt-[8px] leading-[1.4]">Liên kết đối tác nhà hàng gợi ý món ngon cá nhân hóa thúc đẩy doanh thu.</p>
                        </div>
                        <div className="border border-[#094a70]/14 rounded-[20px] bg-white p-5 shadow-[0_12px_28px_rgba(13,64,100,0.1)]">
                          <span className="text-[15px] font-extrabold text-[#008c72] tracking-[0.05em] uppercase block mb-2">Hệ Thống Giám Sát</span>
                          <h3 className="text-[#071735] text-[24px] font-black leading-[1.2]">Đo Lường Doanh Nghiệp</h3>
                          <p className="text-[#46607f] text-[18px] font-semibold mt-[8px] leading-[1.4]">Hệ thống giám sát chất lượng, đo lường độ đúng và phản hồi của người dùng.</p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* SLIDE 6: TRÍ NHỚ & CÁ NHÂN HÓA KHÁCH HÀNG */}
                {currentSlide === 6 && (
                  <div className="space-y-6">
                    <div>
                      <h2 className="text-[60px] font-black leading-tight text-[#071735]">
                        Tối ưu lòng trung thành nhờ <span className="text-[#00b386]">Trí Nhớ Cá Nhân Hóa</span>
                      </h2>
                      <p className="text-[26px] font-semibold text-[#415b7d] mt-[16px] max-w-[1120px]">
                        Xây dựng chân dung khách hàng sắc nét theo thời gian. Trợ lý ghi nhớ thói quen, sở thích ăn uống và tần suất di chuyển để đưa ra những tương tác chuẩn xác, gia tăng đáng kể Giá trị vòng đời khách hàng (CLV).
                      </p>
                    </div>

                    <div className="grid grid-cols-[1fr_50px_1.2fr_50px_1fr] items-stretch gap-4 pt-4 mt-2">
                      <div className="flex flex-col gap-[16px]">
                        <div className="border border-[#094a70]/14 rounded-[20px] bg-white p-[20px] shadow-[0_12px_28px_rgba(13,64,100,0.1)]">
                          <span className="text-[15px] font-extrabold text-[#008c72] tracking-[0.05em] uppercase block mb-2">Trí Nhớ Ngắn Hạn</span>
                          <h3 className="text-[#071735] text-[24px] font-black leading-[1.2]">Working Memory</h3>
                          <p className="text-[#46607f] text-[18px] font-semibold mt-[8px] leading-[1.4]">Duy trì mạch hội thoại tự nhiên trong phiên chat, hiểu các đại từ lửng lơ của khách hàng.</p>
                        </div>
                        <div className="border border-[#094a70]/14 rounded-[20px] bg-white p-[20px] shadow-[0_12px_28px_rgba(13,64,100,0.1)]">
                          <span className="text-[15px] font-extrabold text-[#008c72] tracking-[0.05em] uppercase block mb-2">Trí Nhớ Trung Hạn</span>
                          <h3 className="text-[#071735] text-[24px] font-black leading-[1.2]">Tóm Tắt Phiên Giao Dịch</h3>
                          <p className="text-[#46607f] text-[18px] font-semibold mt-[8px] leading-[1.4]">Nén và lưu giữ các thông tin cốt lõi của khách hàng (yêu cầu chưa giải quyết, ưu tiên của chuyến đi).</p>
                        </div>
                        <div className="border border-[#094a70]/14 rounded-[20px] bg-white p-[20px] shadow-[0_12px_28px_rgba(13,64,100,0.1)]">
                          <span className="text-[15px] font-extrabold text-[#008c72] tracking-[0.05em] uppercase block mb-2">Trí Nhớ Dài Hạn</span>
                          <h3 className="text-[#071735] text-[24px] font-black leading-[1.2]">Hồ Sơ Sở Thích Khách Hàng</h3>
                          <p className="text-[#46607f] text-[18px] font-semibold mt-[8px] leading-[1.4]">Lưu trữ vĩnh viễn gu ẩm thực, thói quen di chuyển, địa điểm hay lui tới để chủ động gợi ý.</p>
                        </div>
                      </div>
                      <div className="flex items-center justify-center text-[#00b386] text-[44px] font-black">→</div>
                      <div className="flex flex-col justify-center">
                        <div className="border-2 border-[#0096ff]/32 rounded-[20px] bg-gradient-to-b from-[#e6f5ff] to-white p-6 shadow-md text-center">
                          <span className="text-[15px] font-extrabold text-[#0077cc] tracking-[0.05em] uppercase block mb-2">Bộ Phục Vụ Thông Tin</span>
                          <h3 className="text-[#071735] text-[24px] font-black">Context Builder</h3>
                          <p className="text-[#46607f] text-[18px] font-semibold mt-3 leading-relaxed">
                            Lắp ráp và chuẩn hóa thông tin khách hàng, giúp mô hình AI trả lời thông minh nhất mà không tốn chi phí xử lý dữ liệu thừa.
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center justify-center text-[#00b386] text-[44px] font-black">→</div>
                      <div className="flex flex-col justify-center gap-[16px]">
                        <div className="border border-[#094a70]/14 rounded-[20px] bg-white p-5 shadow-sm">
                          <span className="text-[15px] font-extrabold text-[#008c72] tracking-[0.05em] uppercase block mb-2">Tối Ưu Vận Hành</span>
                          <h3 className="text-[#071735] text-[20px] font-black">Phản Hồi Siêu Tốc</h3>
                          <p className="text-[#46607f] text-[18px] font-semibold mt-1">Cache các luồng hội thoại quen thuộc, tiết kiệm tài nguyên máy chủ và tăng tốc độ xử lý.</p>
                        </div>
                        <div className="border border-[#094a70]/14 rounded-[20px] bg-white p-5 shadow-sm">
                          <span className="text-[15px] font-extrabold text-[#008c72] tracking-[0.05em] uppercase block mb-2">Thực Thi Chiến Lược</span>
                          <h3 className="text-[#071735] text-[20px] font-black">Cá Nhân Hóa Toàn Diện</h3>
                          <p className="text-[#46607f] text-[18px] font-semibold mt-1">Sinh câu trả lời đồng cảm, thuyết phục dựa trên chính thói quen tiêu dùng của khách hàng.</p>
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
                        Giải Pháp Sẵn Sàng Triển Khai
                      </div>
                      <h2 className="text-[72px] font-black leading-[1.04] text-[#071735]">
                        Nâng Tầm Doanh Nghiệp Với <span className="text-[#00b386]">AI Assistant</span>
                      </h2>
                      <p className="text-[22px] font-semibold leading-[1.5] text-[#314967] mt-2">
                        Giải pháp trợ lý ảo thông minh không chỉ dừng lại ở thử nghiệm. Với khả năng tích hợp linh hoạt vào dữ liệu lớn của hệ sinh thái Xanh SM, dự án cam kết mang lại hiệu quả ROI rõ rệt và nâng cấp trải nghiệm khách hàng vượt trội.
                      </p>

                      <div className="grid grid-cols-2 gap-4 pt-4">
                        {[
                          { img: '/knowledge_search.png', t: 'Tối Ưu Hóa Chi Phí', d: 'Cắt giảm đáng kể ngân sách vận hành tổng đài hỗ trợ nhờ tự động hóa xử lý 90% FAQs.' },
                          { img: '/data_analytics.png', t: 'Khai Thác Data Tối Đa', d: 'Chuyển hóa dữ liệu hội thoại thô thành những hiểu biết giá trị phục vụ kinh doanh.' },
                          { img: '/food_recommendation.png', t: 'Bán Hàng Liên Kết Đột Phá', d: 'Mở rộng kênh doanh thu mới từ dịch vụ ẩm thực và liên kết đối tác ngoài app.' },
                          { img: '/policy_support.png', t: 'Đo Lường Hiệu Quả Liên Tục', d: 'Hệ thống quản trị thông số trực quan giúp nhà quản lý theo dõi sát sao tiến độ và chất lượng.' }
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
                        onClick={() => navigateToTab('Tầm nhìn')} 
                        className="inline-flex items-center gap-3 px-[26px] py-[20px] rounded-full bg-gradient-to-r from-[#00b386] to-[#10cdb1] text-white shadow-[0_18px_42px_rgba(0,179,134,0.28)] hover:scale-105 active:scale-95 transition-all text-[22px] font-black mt-4"
                      >
                        Bắt đầu khám phá demo thực tế
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
                          <span className="block text-[#34506f] text-[16px] font-bold mt-1 leading-[1.32]">Giải pháp đồng bộ toàn diện trên một ứng dụng.</span>
                        </div>
                        <div className="bg-white border border-[#00b386]/16 rounded-[22px] p-4 min-h-[112px]">
                          <b className="block text-[#00b386] text-[34px] font-black leading-none">Data</b>
                          <span className="block text-[#34506f] text-[16px] font-bold mt-1 leading-[1.32]">Tận dụng tối đa giá trị dữ liệu hệ sinh thái.</span>
                        </div>
                        <div className="bg-white border border-[#00b386]/16 rounded-[22px] p-4 min-h-[112px]">
                          <b className="block text-[#00b386] text-[34px] font-black leading-none">Loop</b>
                          <span className="block text-[#34506f] text-[16px] font-bold mt-1 leading-[1.32]">Liên tục tối ưu hóa theo phản hồi thực tế.</span>
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
                <span><b>Cam kết bảo mật dữ liệu doanh nghiệp và tối ưu chi phí hạ tầng</b></span>
              )}
              {currentSlide === 6 && (
                <span><b>Cá nhân hóa trải nghiệm thúc đẩy Giá trị vòng đời khách hàng (CLV)</b></span>
              )}
              {currentSlide !== 0 && currentSlide !== 5 && currentSlide !== 6 && (
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
