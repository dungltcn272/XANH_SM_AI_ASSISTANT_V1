import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight, Keyboard, RotateCcw } from 'lucide-react';

export default function SlideShow() {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [direction, setDirection] = useState(0); // -1 for left/prev, 1 for right/next
  const [scale, setScale] = useState(1);
  const [activeDialog, setActiveDialog] = useState(null);

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
  const ALL_TABS = [
    'Tầm nhìn',
    'Hiện trạng',
    'Hiệu quả',
    'Kiến trúc',
    'Cơ hội',
    'Khoảng cách',
    'Nâng cấp',
    'Lời kết'
  ];

  const getActiveTab = (index) => {
    return ALL_TABS[index] || ALL_TABS[0];
  };

  const getTabsList = (index) => {
    let start = index - 1;
    if (start < 0) start = 0;
    if (start + 4 > ALL_TABS.length) start = ALL_TABS.length - 4;
    return ALL_TABS.slice(start, start + 4);
  };

  const navigateToTab = (tabName) => {
    const targetIndex = ALL_TABS.indexOf(tabName);
    if (targetIndex !== -1) {
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
                        Một nền tảng trợ lý thông minh duy nhất giúp giải quyết triệt để các thách thức về chi phí nhân sự, giữ chân khách hàng và khai thác tối đa doanh số chéo. Click vào các thẻ để xem ví dụ thực tế.
                      </p>
                    </div>
                    <div className="grid grid-cols-4 gap-[16px] pt-2">
                      {[
                        { 
                          img: '/knowledge_search.png', t: 'Tự Động Hóa CSKH FAQ', d: 'Trả lời tức thì 90% thắc mắc của khách hàng về chính sách, chuyến đi và giá cước.',
                          dialog: { user: 'Cho mình hỏi giá cước xe VF8 sân bay Nội Bài về Cầu Giấy là bao nhiêu? Có bị tính phí cầu đường không?', ai: 'Dạ, giá cước VF8 chặng sân bay Nội Bài - Cầu Giấy hiện dao động từ 300.000đ - 350.000đ. Khách hàng sẽ cần thanh toán thêm phí cầu đường khoảng 15.000đ ạ.' }
                        },
                        { 
                          img: '/deep_research.png', t: 'Hỗ Trợ Đại Lý & Tài Xế', d: 'Tra cứu thông tin chính sách, luật, vận hành nội bộ nhanh chóng cho nhân sự.',
                          dialog: { user: 'Quy trình xử lý khách hàng quên đồ trên xe như thế nào?', ai: 'Dạ, tài xế cần báo cáo ngay trên app Driver, chọn mục "Khách quên đồ" -> điền thông tin và chụp ảnh hiện vật -> Giao nộp tại trạm điều hành gần nhất trong 24h.' }
                        },
                        { 
                          img: '/vehicle_expert.png', t: 'Chuyên Gia Tư Vấn Dịch Vụ', d: 'Giải đáp tường tận về các dòng xe VinFast, gói thuê xe và chính sách ưu đãi thành viên.',
                          dialog: { user: 'Gói thuê xe 1 ngày đi Mộc Châu cho gia đình 4 người thì xe nào phù hợp?', ai: 'Dạ, cho hành trình đi tỉnh như Mộc Châu, gia đình 4 người nên chọn VF8. Gói thuê VF8 1 ngày đi tỉnh hiện đang là 1.500.000đ/ngày (Giới hạn 200km).' }
                        },
                        { 
                          img: '/pricing_assistant.png', t: 'Minh Bạch Giá Cước', d: 'Tự động tính toán, giải thích chi tiết cơ chế giá cước động theo thời gian thực.',
                          dialog: { user: 'Sao giá cước hôm nay từ Mỹ Đình về Hoàn Kiếm lại cao hơn hôm qua 50k thế?', ai: 'Dạ, hiện tại khu vực Hoàn Kiếm đang có sự kiện lớn dẫn tới nhu cầu đặt xe tăng vọt 300%. Hệ thống áp dụng phụ phí giờ cao điểm 50.000đ để thu hút thêm tài xế phục vụ ạ.' }
                        },
                        { 
                          img: '/news_digest.png', t: 'Báo Cáo Tin Tức Tự Động', d: 'Cập nhật nhanh tin tức thị trường xe điện, khuyến mãi tuần cho khách hàng.',
                          dialog: { user: 'Tin tức mới nhất cho bác tài!', ai: 'Dạ, tuần này Xanh SM đang hợp tác với VIB, giảm ngay 30% (Tối đa 50k) cho các chuyến đi thứ 6, thứ 7 ạ.' }
                        },
                        { 
                          img: '/food_recommendation.png', t: 'Bán Chéo Food & Địa Điểm', d: 'Tự động gợi ý quán ăn, món ngon quanh vị trí và kích thích đặt xe/đồ ăn.',
                          dialog: { user: 'Quanh Ngõ 67 Phùng Khoang có quán phở nào ngon, đang mở cửa mà có xe Xanh SM chờ sẵn không?', ai: 'Dạ, ngay phố Bát Đàn có Phở Gia Truyền đang mở cửa, cách vị trí của bạn 1.5km. Hiện có 5 xe Xanh SM đang chờ quanh quán. Bạn có muốn đặt xe luôn không?' }
                        },
                        { 
                          img: '/policy_support.png', t: 'Xử Lý Khiếu Nại 24/7', d: 'Tự động ghi nhận thông tin, phân loại sự cố và hướng dẫn khách hàng xử lý nhanh.',
                          dialog: { user: 'Tài xế đi nhầm đường làm tôi lỡ chuyến bay, tôi muốn khiếu nại!', ai: 'Dạ Xanh SM vô cùng xin lỗi. Hệ thống ghi nhận lộ trình có sai lệch. Chúng tôi đã hoàn 100% cước phí chuyến đi vào ví Xanh SM và gửi mã giảm 100k đền bù cho bạn ạ.' }
                        },
                        { 
                          img: '/data_analytics.png', t: 'Đo Lường Chất Lượng', d: 'Phân tích dữ liệu hội thoại để tìm ra điểm nghẽn dịch vụ và cải tiến tức thì.'
                        }
                      ].map((item, idx) => {
                        const hasDialog = !!item.dialog;
                        return (
                        <div 
                          key={idx} 
                          onClick={() => hasDialog && setActiveDialog(item)}
                          className={`flex flex-col min-h-[250px] border border-[#094a70]/13 rounded-[20px] overflow-hidden bg-white shadow-[0_16px_36px_rgba(13,64,100,0.1)] transition-all duration-300 ${hasDialog ? 'cursor-pointer hover:-translate-y-2 hover:shadow-[0_24px_50px_rgba(0,179,134,0.2)] group' : ''}`}
                        >
                          <div className="relative overflow-hidden h-[120px]">
                            <img className={`w-full h-full object-cover transition-transform duration-500 ${hasDialog ? 'group-hover:scale-105' : ''}`} src={item.img} alt={item.t} />
                            {hasDialog && (
                            <div className="absolute inset-0 bg-[#00b386]/0 group-hover:bg-[#00b386]/10 transition-colors duration-300 flex items-center justify-center">
                              <span className="opacity-0 group-hover:opacity-100 bg-[#00b386] text-white px-4 py-2 rounded-full font-bold text-[14px] shadow-lg transform translate-y-4 group-hover:translate-y-0 transition-all duration-300">Click xem ví dụ</span>
                            </div>
                            )}
                          </div>
                          <div className="p-4 flex-grow flex flex-col justify-between">
                            <h3 className={`text-[#071735] text-[22px] font-black leading-[1.15] transition-colors ${hasDialog ? 'group-hover:text-[#00b386]' : ''}`}>{item.t}</h3>
                            <p className="text-[#365071] text-[17px] font-semibold mt-[6px] leading-[1.4]">{item.d}</p>
                          </div>
                        </div>
                      )})}
                    </div>

                    <AnimatePresence>
                      {activeDialog && (
                        <motion.div 
                          initial={{ opacity: 0, scale: 0.95 }}
                          animate={{ opacity: 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.95 }}
                          transition={{ type: "spring", duration: 0.5, bounce: 0.3 }}
                          className="absolute inset-0 z-50 flex items-center justify-center bg-[#071735]/40 backdrop-blur-sm rounded-[28px]"
                          onClick={() => setActiveDialog(null)}
                        >
                          <div 
                            className="w-[800px] bg-white rounded-[24px] shadow-[0_40px_100px_rgba(0,0,0,0.2)] overflow-hidden border border-white"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <div className="flex items-center justify-between px-8 py-5 border-b border-slate-100 bg-slate-50/50">
                              <h3 className="text-[24px] font-black text-[#071735]">{activeDialog.t}</h3>
                              <button 
                                onClick={() => setActiveDialog(null)}
                                className="w-10 h-10 rounded-full bg-slate-200 text-slate-600 flex items-center justify-center hover:bg-rose-100 hover:text-rose-600 transition-colors font-bold text-[18px]"
                              >
                                ✕
                              </button>
                            </div>
                            <div className="p-8 space-y-6 bg-[linear-gradient(180deg,rgba(255,255,255,1),rgba(240,250,248,1))]">
                              {/* User Chat Bubble */}
                              <div className="flex gap-4 items-start">
                                <div className="w-[48px] h-[48px] rounded-full bg-slate-200 flex items-center justify-center text-[24px] shadow-sm flex-shrink-0">👤</div>
                                <div className="bg-white border border-slate-200 p-5 rounded-[20px] rounded-tl-none shadow-sm max-w-[85%]">
                                  <p className="text-[#071735] text-[18px] font-medium leading-[1.5]">{activeDialog.dialog.user}</p>
                                </div>
                              </div>
                              
                              {/* AI Chat Bubble */}
                              <div className="flex gap-4 items-start flex-row-reverse">
                                <div className="w-[48px] h-[48px] rounded-full bg-[#00b386] flex items-center justify-center text-[24px] shadow-sm flex-shrink-0">🤖</div>
                                <div className="bg-gradient-to-br from-[#00b386] to-[#10cdb1] text-white p-5 rounded-[20px] rounded-tr-none shadow-[0_12px_24px_rgba(0,179,134,0.2)] max-w-[85%]">
                                  <p className="text-white text-[18px] font-medium leading-[1.5]">{activeDialog.dialog.ai}</p>
                                </div>
                              </div>
                            </div>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                )}

                {/* SLIDE 2: HIỆU QUẢ KINH DOANH */}
                {currentSlide === 2 && (
                  <div className="space-y-6">
                    <div>
                      <h2 className="text-[60px] font-black leading-tight text-[#071735]">
                        Hiệu quả vận hành & <span className="text-[#00b386]">Tối ưu Chi phí</span>
                      </h2>
                      <p className="text-[24px] font-semibold text-[#415b7d] mt-[10px] max-w-[1120px]">
                        Đánh giá nghiêm túc dưới góc độ CTO/Head of AI Product: Xanh SM AI đang định hình rõ thế mạnh ở mảng Knowledge Assistant, sẵn sàng đối trọng với siêu ứng dụng Grab.
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
                  <div className="space-y-4 w-full">
                    <div className="text-center mb-10">
                      <div className="inline-flex items-center gap-2 px-[18px] py-[11px] rounded-full bg-[#00b386]/12 text-[#008c72] font-black tracking-widest text-[17px] uppercase mb-4 shadow-sm border border-[#00b386]/20">
                        Thực Trạng Thị Trường & Cơ Hội
                      </div>
                      <h2 className="text-[58px] font-black leading-tight text-[#071735]">
                        Cơ Hội Vàng Tại <span className="text-[#00b386]">Thị Trường Việt Nam</span>
                      </h2>
                      <p className="text-[22px] font-medium text-[#415b7d] mt-4 max-w-[1000px] mx-auto">
                        Thực tế tại Việt Nam hiện vẫn chưa có bất kỳ đối thủ nào phổ cập rộng rãi một AI Assistant đa năng cho hệ sinh thái. Chúng ta đang mở đường, không phải đang chạy theo!
                      </p>
                    </div>

                    <div className="grid grid-cols-4 gap-6 px-4">
                      {/* GRAB CARD */}
                      <div className="border border-[#00a5cf]/20 rounded-[32px] bg-gradient-to-b from-white to-[#f0f9ff]/50 shadow-[0_24px_50px_rgba(0,165,207,0.08)] p-8 flex flex-col relative overflow-hidden group hover:-translate-y-2 hover:shadow-[0_34px_60px_rgba(0,165,207,0.15)] transition-all duration-300">
                        <div className="absolute -right-10 -top-10 w-40 h-40 bg-[#00a5cf]/5 rounded-full blur-2xl group-hover:bg-[#00a5cf]/10 transition-colors"></div>
                        <div className="flex items-center justify-between mb-8">
                          <a href="https://www.grab.com/my/press/others/grab-unveils-13-ai-powered-experiences-at-grabx-2026-as-southeast-asias-intelligent-everyday-guide/" target="_blank" rel="noreferrer" className="text-[#00a5cf] text-[38px] font-black hover:text-[#0082a3] flex items-center gap-2 drop-shadow-sm">
                            Grab <span className="text-[20px] bg-white/80 p-2 rounded-full shadow-sm">🔗</span>
                          </a>
                        </div>
                        <div className="space-y-6">
                          <div>
                            <p className="text-[14px] text-slate-400 uppercase font-bold tracking-widest mb-3">Có AI Assistant?</p>
                            <div className="inline-flex items-center gap-2.5 px-4 py-2.5 bg-[#00b386]/10 border border-[#00b386]/20 text-[#008c72] rounded-2xl font-bold shadow-sm"><span className="text-[22px]">✅</span> Có</div>
                          </div>
                          <div>
                            <p className="text-[14px] text-slate-400 uppercase font-bold tracking-widest mb-3">Đã rollout tại VN?</p>
                            <div className="inline-flex items-center gap-2.5 px-4 py-2.5 bg-rose-50 border border-rose-100 text-rose-600 rounded-2xl font-bold shadow-sm"><span className="text-[22px]">❌</span> Chưa (Sing)</div>
                          </div>
                          <div className="pt-2 border-t border-[#00a5cf]/10">
                            <p className="text-[14px] text-slate-400 uppercase font-bold tracking-widest mb-3">User VN thấy không?</p>
                            <div className="inline-flex items-center gap-2.5 px-5 py-3 bg-slate-100/80 border border-slate-200 text-slate-600 rounded-2xl font-bold shadow-inner"><span className="text-[22px] grayscale">🚫</span> Hoàn toàn không</div>
                          </div>
                        </div>
                      </div>

                      {/* UBER CARD */}
                      <div className="border border-slate-200 rounded-[32px] bg-gradient-to-b from-white to-slate-50/50 shadow-[0_24px_50px_rgba(0,0,0,0.04)] p-8 flex flex-col relative overflow-hidden group hover:-translate-y-2 hover:shadow-[0_34px_60px_rgba(0,0,0,0.08)] transition-all duration-300">
                        <div className="flex items-center justify-between mb-8">
                          <a href="https://techcrunch.com/2026/02/11/uber-eats-launches-ai-assistant-to-help-with-grocery-cart-creation/" target="_blank" rel="noreferrer" className="text-[#111827] text-[38px] font-black hover:text-[#374151] flex items-center gap-2 drop-shadow-sm">
                            Uber <span className="text-[20px] bg-white p-2 rounded-full shadow-sm border border-slate-100">🔗</span>
                          </a>
                        </div>
                        <div className="space-y-6">
                          <div>
                            <p className="text-[14px] text-slate-400 uppercase font-bold tracking-widest mb-3">Có AI Assistant?</p>
                            <div className="inline-flex items-center gap-2.5 px-4 py-2.5 bg-amber-50 border border-amber-200 text-amber-700 rounded-2xl font-bold shadow-sm"><span className="text-[22px]">⚠️</span> Có 1 phần</div>
                          </div>
                          <div>
                            <p className="text-[14px] text-slate-400 uppercase font-bold tracking-widest mb-3">Đã rollout tại VN?</p>
                            <div className="inline-flex items-center gap-2.5 px-4 py-2.5 bg-rose-50 border border-rose-100 text-rose-600 rounded-2xl font-bold shadow-sm"><span className="text-[22px]">❌</span> Không</div>
                          </div>
                          <div className="pt-2 border-t border-slate-200">
                            <p className="text-[14px] text-slate-400 uppercase font-bold tracking-widest mb-3">User VN thấy không?</p>
                            <div className="inline-flex items-center gap-2.5 px-5 py-3 bg-slate-100/80 border border-slate-200 text-slate-600 rounded-2xl font-bold shadow-inner"><span className="text-[22px] grayscale">🚫</span> Hoàn toàn không</div>
                          </div>
                        </div>
                      </div>

                      {/* LYFT CARD */}
                      <div className="border border-[#ec4899]/20 rounded-[32px] bg-gradient-to-b from-white to-[#fdf2f8]/60 shadow-[0_24px_50px_rgba(236,72,153,0.06)] p-8 flex flex-col relative overflow-hidden group hover:-translate-y-2 hover:shadow-[0_34px_60px_rgba(236,72,153,0.12)] transition-all duration-300">
                        <div className="absolute -left-10 -top-10 w-40 h-40 bg-[#ec4899]/5 rounded-full blur-2xl group-hover:bg-[#ec4899]/10 transition-colors"></div>
                        <div className="flex items-center justify-between mb-8 z-10 relative">
                          <a href="https://www.businessinsider.com/lyft-ai-tool-earnings-assistant-helps-drivers-find-rides-2026-5" target="_blank" rel="noreferrer" className="text-[#ec4899] text-[38px] font-black hover:text-[#be185d] flex items-center gap-2 drop-shadow-sm">
                            Lyft <span className="text-[20px] bg-white/80 p-2 rounded-full shadow-sm">🔗</span>
                          </a>
                        </div>
                        <div className="space-y-6 z-10 relative">
                          <div>
                            <p className="text-[14px] text-slate-400 uppercase font-bold tracking-widest mb-3">Có AI Assistant?</p>
                            <div className="inline-flex items-center gap-2.5 px-4 py-2.5 bg-amber-50 border border-amber-200 text-amber-700 rounded-2xl font-bold shadow-sm"><span className="text-[22px]">⚠️</span> Chỉ Driver AI</div>
                          </div>
                          <div>
                            <p className="text-[14px] text-slate-400 uppercase font-bold tracking-widest mb-3">Đã rollout tại VN?</p>
                            <div className="inline-flex items-center gap-2.5 px-4 py-2.5 bg-rose-50 border border-rose-100 text-rose-600 rounded-2xl font-bold shadow-sm"><span className="text-[22px]">❌</span> K.Hoạt Động</div>
                          </div>
                          <div className="pt-2 border-t border-[#ec4899]/10">
                            <p className="text-[14px] text-slate-400 uppercase font-bold tracking-widest mb-3">User VN thấy không?</p>
                            <div className="inline-flex items-center gap-2.5 px-5 py-3 bg-slate-100/80 border border-slate-200 text-slate-600 rounded-2xl font-bold shadow-inner"><span className="text-[22px] grayscale">🚫</span> Hoàn toàn không</div>
                          </div>
                        </div>
                      </div>

                      {/* SHOPEE CARD */}
                      <div className="border border-[#f97316]/20 rounded-[32px] bg-gradient-to-b from-white to-[#fff7ed]/80 shadow-[0_24px_50px_rgba(249,115,22,0.08)] p-8 flex flex-col relative overflow-hidden group hover:-translate-y-2 hover:shadow-[0_34px_60px_rgba(249,115,22,0.15)] transition-all duration-300">
                        <div className="flex items-center justify-between mb-8">
                          <a href="https://banhang.shopee.vn/edu/article/22401" target="_blank" rel="noreferrer" className="text-[#f97316] text-[38px] font-black hover:text-[#c2410c] flex items-center gap-2 drop-shadow-sm">
                            Shopee <span className="text-[20px] bg-white/80 p-2 rounded-full shadow-sm">🔗</span>
                          </a>
                        </div>
                        <div className="space-y-6">
                          <div>
                            <p className="text-[14px] text-slate-400 uppercase font-bold tracking-widest mb-3">Có AI Assistant?</p>
                            <div className="inline-flex items-center gap-2.5 px-4 py-2.5 bg-[#00b386]/10 border border-[#00b386]/20 text-[#008c72] rounded-2xl font-bold shadow-sm"><span className="text-[22px]">✅</span> Có</div>
                          </div>
                          <div>
                            <p className="text-[14px] text-slate-400 uppercase font-bold tracking-widest mb-3">Đã rollout tại VN?</p>
                            <div className="inline-flex items-center gap-2.5 px-4 py-2.5 bg-[#00b386]/10 border border-[#00b386]/20 text-[#008c72] rounded-2xl font-bold shadow-sm"><span className="text-[22px]">✅</span> Có (Cho Seller)</div>
                          </div>
                          <div className="pt-2 border-t border-[#f97316]/10">
                            <p className="text-[14px] text-slate-400 uppercase font-bold tracking-widest mb-3">Buyer VN thấy không?</p>
                            <div className="inline-flex items-center gap-2.5 px-5 py-3 bg-rose-50 border border-rose-100 text-rose-600 rounded-2xl font-bold shadow-sm"><span className="text-[22px]">❌</span> Không thấy</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* SLIDE 6: PHÂN TÍCH KHOẢNG CÁCH */}
                {currentSlide === 5 && (
                  <div className="space-y-4 w-full">
                    <div className="flex items-end justify-between mb-4 px-2">
                      <div>
                        <h2 className="text-[54px] font-black leading-tight text-[#071735]">
                          Khoảng Cách Tới <span className="text-[#00b386]">Action Agent Toàn Cầu</span>
                        </h2>
                        <p className="text-[22px] font-medium text-[#415b7d] mt-2 max-w-[900px]">
                          So với mô hình tham chiếu toàn cầu (Mỹ, Sing), Xanh SM vẫn còn thiếu những năng lực "Thực Chiến" đa tác vụ và can thiệp sâu vào hệ sinh thái.
                        </p>
                      </div>
                      <div className="px-5 py-3 rounded-[20px] bg-rose-50 border border-rose-100 text-rose-600 font-bold text-[18px] shadow-sm">
                        🚨 Cảnh báo tụt hậu
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-8 mt-6">
                      {/* GRAB SING CARD */}
                      <div className="border border-[#00a5cf]/15 rounded-[32px] bg-white shadow-[0_20px_50px_rgba(8,45,77,0.06)] p-8 flex flex-col relative group hover:shadow-[0_30px_70px_rgba(0,165,207,0.12)] hover:-translate-y-1 transition-all duration-300">
                        <div className="flex justify-between items-start border-b border-[#00a5cf]/10 pb-5 mb-6">
                          <div>
                            <a href="https://www.grab.com/my/press/others/grab-unveils-13-ai-powered-experiences-at-grabx-2026-as-southeast-asias-intelligent-everyday-guide/" target="_blank" rel="noreferrer" className="text-[#00a5cf] text-[34px] font-black flex items-center gap-2 hover:underline">Grab Sing <span className="text-[18px] bg-slate-50 p-2 rounded-full border border-slate-100">🔗</span></a>
                            <span className="inline-block mt-2 px-3 py-1 bg-slate-100 text-slate-500 rounded-lg text-[13px] font-black uppercase tracking-widest">Super App AI</span>
                          </div>
                        </div>
                        
                        <div className="flex-grow">
                          <h4 className="text-[16px] font-black text-[#071735] mb-4 flex items-center gap-3 uppercase tracking-wide">
                            <span className="w-2 h-6 bg-rose-500 rounded-full block"></span> Năng lực Xanh SM thiếu hụt
                          </h4>
                          <ul className="space-y-4 mb-8">
                            <li className="flex items-start gap-3 bg-rose-50/60 p-4 rounded-2xl border border-rose-100/50">
                               <span className="text-rose-500 font-black text-[20px] leading-none">×</span>
                               <span className="text-[#405a7a] font-medium leading-snug text-[17px]"><strong className="text-[#071735]">AI Concierge:</strong> Lập kế hoạch đa bước xuyên suốt hệ sinh thái.</span>
                            </li>
                            <li className="flex items-start gap-3 bg-rose-50/60 p-4 rounded-2xl border border-rose-100/50">
                               <span className="text-rose-500 font-black text-[20px] leading-none">×</span>
                               <span className="text-[#405a7a] font-medium leading-snug text-[17px]"><strong className="text-[#071735]">Voice & Shopping:</strong> Giao tiếp Voice Notes, ảnh giỏ hàng.</span>
                            </li>
                          </ul>
                        </div>
                        
                        <div className="bg-gradient-to-br from-[#f0f9ff] to-[#e0f2fe] rounded-[24px] p-6 border border-[#00a5cf]/15 mt-auto">
                          <h4 className="text-[15px] font-black text-[#00a5cf] mb-3 uppercase tracking-wider flex items-center gap-2">💡 Ví dụ thực tế</h4>
                          <p className="text-[#314967] text-[17px] font-medium bg-white p-3 rounded-xl border border-white/50 shadow-sm mb-3">Nhận lệnh: <i className="text-slate-500">"Tổ chức sinh nhật 10 người, ngân sách 3 triệu"</i></p>
                          <div className="text-[#0082a3] font-bold text-[18px] leading-snug flex items-start gap-2">
                            <span className="text-[20px] leading-none mt-0.5">⚡</span>
                            <span>Tự lọc menu &rarr; Đặt bàn &rarr; Gọi xe (Chỉ trong 1 lượt chat).</span>
                          </div>
                        </div>
                      </div>

                      {/* UBER US CARD */}
                      <div className="border border-slate-200 rounded-[32px] bg-white shadow-[0_20px_50px_rgba(8,45,77,0.06)] p-8 flex flex-col relative group hover:shadow-[0_30px_70px_rgba(0,0,0,0.08)] hover:-translate-y-1 transition-all duration-300">
                        <div className="flex justify-between items-start border-b border-slate-100 pb-5 mb-6">
                          <div>
                            <a href="https://techcrunch.com/2026/02/11/uber-eats-launches-ai-assistant-to-help-with-grocery-cart-creation/" target="_blank" rel="noreferrer" className="text-[#111827] text-[34px] font-black flex items-center gap-2 hover:underline">Uber US <span className="text-[18px] bg-slate-50 p-2 rounded-full border border-slate-100">🔗</span></a>
                            <span className="inline-block mt-2 px-3 py-1 bg-slate-100 text-slate-500 rounded-lg text-[13px] font-black uppercase tracking-widest">Ecosystem AI</span>
                          </div>
                        </div>
                        
                        <div className="flex-grow">
                          <h4 className="text-[16px] font-black text-[#071735] mb-4 flex items-center gap-3 uppercase tracking-wide">
                            <span className="w-2 h-6 bg-rose-500 rounded-full block"></span> Năng lực Xanh SM thiếu hụt
                          </h4>
                          <ul className="space-y-4 mb-8">
                            <li className="flex items-start gap-3 bg-rose-50/60 p-4 rounded-2xl border border-rose-100/50">
                               <span className="text-rose-500 font-black text-[20px] leading-none">×</span>
                               <span className="text-[#405a7a] font-medium leading-snug text-[17px]"><strong className="text-[#071735]">Commerce Action:</strong> Tự động hóa quá trình nhặt đồ mua sắm, ăn uống.</span>
                            </li>
                            <li className="flex items-start gap-3 bg-rose-50/60 p-4 rounded-2xl border border-rose-100/50">
                               <span className="text-rose-500 font-black text-[20px] leading-none">×</span>
                               <span className="text-[#405a7a] font-medium leading-snug text-[17px]"><strong className="text-[#071735]">Meal Planning:</strong> Trực tiếp lên thực đơn thay vì chỉ gợi ý nhà hàng.</span>
                            </li>
                          </ul>
                        </div>
                        
                        <div className="bg-gradient-to-br from-slate-50 to-slate-100 rounded-[24px] p-6 border border-slate-200 mt-auto">
                          <h4 className="text-[15px] font-black text-[#475569] mb-3 uppercase tracking-wider flex items-center gap-2">💡 Ví dụ thực tế</h4>
                          <a href="https://www.axios.com/2026/02/11/uber-eats-ai-grocery-cart-assistant" target="_blank" rel="noreferrer" className="block text-[#314967] text-[17px] font-medium bg-white p-3 rounded-xl border border-white/50 shadow-sm mb-3 hover:underline">Gửi ảnh danh sách đồ ăn / hàng tạp hóa cần mua</a>
                          <div className="text-[#111827] font-bold text-[18px] leading-snug flex items-start gap-2">
                            <span className="text-[20px] leading-none mt-0.5">⚡</span>
                            <span>AI tự nhận diện nét chữ/ảnh &rarr; Thêm trực tiếp sản phẩm vào giỏ hàng.</span>
                          </div>
                        </div>
                      </div>

                      {/* LYFT US CARD */}
                      <div className="border border-[#ec4899]/15 rounded-[32px] bg-white shadow-[0_20px_50px_rgba(8,45,77,0.06)] p-8 flex flex-col relative group hover:shadow-[0_30px_70px_rgba(236,72,153,0.12)] hover:-translate-y-1 transition-all duration-300">
                        <div className="flex justify-between items-start border-b border-[#ec4899]/10 pb-5 mb-6">
                          <div>
                            <a href="https://www.businessinsider.com/lyft-ai-tool-earnings-assistant-helps-drivers-find-rides-2026-5" target="_blank" rel="noreferrer" className="text-[#ec4899] text-[34px] font-black flex items-center gap-2 hover:underline">Lyft US <span className="text-[18px] bg-slate-50 p-2 rounded-full border border-slate-100">🔗</span></a>
                            <span className="inline-block mt-2 px-3 py-1 bg-slate-100 text-slate-500 rounded-lg text-[13px] font-black uppercase tracking-widest">Operational AI</span>
                          </div>
                        </div>
                        
                        <div className="flex-grow">
                          <h4 className="text-[16px] font-black text-[#071735] mb-4 flex items-center gap-3 uppercase tracking-wide">
                            <span className="w-2 h-6 bg-rose-500 rounded-full block"></span> Năng lực Xanh SM thiếu hụt
                          </h4>
                          <ul className="space-y-4 mb-8">
                            <li className="flex items-start gap-3 bg-rose-50/60 p-4 rounded-2xl border border-rose-100/50">
                               <span className="text-rose-500 font-black text-[20px] leading-none">×</span>
                               <span className="text-[#405a7a] font-medium leading-snug text-[17px]"><strong className="text-[#071735]">Earnings Assistant:</strong> AI phân tích sự kiện, giao thông để tối ưu thu nhập tài xế tự động.</span>
                            </li>
                          </ul>
                        </div>
                        
                        <div className="bg-gradient-to-br from-[#fdf2f8] to-[#fce7f3] rounded-[24px] p-6 border border-[#ec4899]/15 mt-auto">
                          <h4 className="text-[15px] font-black text-[#db2777] mb-3 uppercase tracking-wider flex items-center gap-2">💡 Ví dụ thực tế</h4>
                          <p className="text-[#314967] text-[17px] font-medium bg-white p-3 rounded-xl border border-white/50 shadow-sm mb-3">Dự báo Blackpink Concert chuẩn bị kết thúc lúc 10h tối.</p>
                          <div className="text-[#be185d] font-bold text-[18px] leading-snug flex items-start gap-2">
                            <span className="text-[20px] leading-none mt-0.5">⚡</span>
                            <span>Chỉ đường/Gợi ý tài xế di chuyển sớm đến vị trí cổng chính để đón khách.</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* SLIDE 7: NÂNG CẤP HỆ SINH THÁI */}
                {currentSlide === 6 && (
                  <div className="space-y-5">
                    <div>
                      <h2 className="text-[52px] font-black leading-tight text-[#071735]">
                        Lộ Trình <span className="text-[#00b386]">Nâng Cấp Hệ Sinh Thái</span>
                      </h2>
                      <p className="text-[22px] font-semibold text-[#415b7d] mt-[10px] max-w-[1120px]">
                        Trước khi tiến tới Action Agent toàn diện, chúng ta cần hoàn thiện vững chắc nền móng tri thức và ưu tiên giải quyết các pain-points cốt lõi của Tài xế & Nhà hàng.
                      </p>
                    </div>

                    {/* Giải thích nguyên nhân */}
                    <div className="border-l-[6px] border-amber-400 bg-amber-50/80 p-5 rounded-r-[20px] shadow-sm mb-2 flex gap-4 items-start">
                      <div className="text-[32px] leading-none">💡</div>
                      <div>
                        <strong className="text-[#92400e] text-[20px] block mb-1">Tại sao Xanh SM chưa vội vã triển khai Action Agent như Grab/Uber?</strong>
                        <p className="text-[#b45309] text-[17px] leading-snug font-medium">
                          <b className="text-[#92400e]">1. Rủi ro hệ thống:</b> Việc cho phép AI tự động gọi xe, thanh toán đòi hỏi Deep API Integration với độ bảo mật tuyệt đối. Chúng ta chọn ưu tiên an toàn (Guardrails 99%) thay vì vội vàng ra mắt tính năng tiềm ẩn lỗi.<br/>
                          <b className="text-[#92400e]">2. Xây móng vững chắc:</b> Cần làm chủ hoàn toàn lớp Knowledge Assistant (CSKH, Chính sách) trước khi dạy AI tự động hóa chuỗi hành động phức tạp.
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-6 pt-2">
                      {/* Cột Tài xế */}
                      <div className="border border-[#094a70]/14 rounded-[24px] bg-white p-6 shadow-[0_12px_30px_rgba(13,64,100,0.06)] relative overflow-hidden group hover:shadow-xl transition-all">
                        <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-[#00b386]/10 to-transparent rounded-bl-full"></div>
                        <div className="flex items-center gap-4 mb-5 relative z-10">
                          <div className="w-[50px] h-[50px] rounded-2xl bg-gradient-to-br from-[#00b386] to-[#10cdb1] flex items-center justify-center text-white text-[24px]">🚘</div>
                          <h3 className="text-[#071735] text-[28px] font-black leading-[1.2]">Driver AI (Tài xế)</h3>
                        </div>
                        <ul className="space-y-4 relative z-10">
                          <li className="flex gap-3">
                            <span className="text-[#00b386] text-[20px] font-black">✓</span>
                            <div>
                              <strong className="text-[#071735] text-[18px]">Trợ Lý Rảnh Tay (Voice-First):</strong>
                              <p className="text-[#405a7a] text-[16px] mt-1 leading-snug">Hỏi doanh thu, báo cáo sự cố bằng giọng nói, đảm bảo an toàn lái xe.</p>
                            </div>
                          </li>
                          <li className="flex gap-3">
                            <span className="text-[#00b386] text-[20px] font-black">✓</span>
                            <div>
                              <strong className="text-[#071735] text-[18px]">Tối Ưu Trạm Sạc V-GREEN:</strong>
                              <p className="text-[#405a7a] text-[16px] mt-1 leading-snug">Gợi ý trạm sạc gần nhất có trụ trống theo thời gian thực.</p>
                            </div>
                          </li>
                          <li className="flex gap-3">
                            <span className="text-[#00b386] text-[20px] font-black">✓</span>
                            <div>
                              <strong className="text-[#071735] text-[18px]">Heatmap & Điều Hướng:</strong>
                              <p className="text-[#405a7a] text-[16px] mt-1 leading-snug">Dự báo điểm nóng nhu cầu cao để điều phối xe, tối đa thu nhập.</p>
                            </div>
                          </li>
                        </ul>
                      </div>

                      {/* Cột Nhà hàng */}
                      <div className="border border-[#094a70]/14 rounded-[24px] bg-white p-6 shadow-[0_12px_30px_rgba(13,64,100,0.06)] relative overflow-hidden group hover:shadow-xl transition-all">
                        <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-[#ff9900]/10 to-transparent rounded-bl-full"></div>
                        <div className="flex items-center gap-4 mb-5 relative z-10">
                          <div className="w-[50px] h-[50px] rounded-2xl bg-gradient-to-br from-[#ff9900] to-[#ffb84d] flex items-center justify-center text-white text-[24px]">🍜</div>
                          <h3 className="text-[#071735] text-[28px] font-black leading-[1.2]">Seller AI (Cửa hàng)</h3>
                        </div>
                        <ul className="space-y-4 relative z-10">
                          <li className="flex gap-3">
                            <span className="text-[#ff9900] text-[20px] font-black">✓</span>
                            <div>
                              <strong className="text-[#071735] text-[18px]">Dự Báo Nhu Cầu & Tồn Kho:</strong>
                              <p className="text-[#405a7a] text-[16px] mt-1 leading-snug">Phân tích dữ liệu để dự báo lượng khách, tối ưu nhập nguyên liệu.</p>
                            </div>
                          </li>
                          <li className="flex gap-3">
                            <span className="text-[#ff9900] text-[20px] font-black">✓</span>
                            <div>
                              <strong className="text-[#071735] text-[18px]">Trả Lời Đánh Giá Tự Động:</strong>
                              <p className="text-[#405a7a] text-[16px] mt-1 leading-snug">Tạo phản hồi cá nhân hóa cho từng review, tiết kiệm 80% thời gian.</p>
                            </div>
                          </li>
                          <li className="flex gap-3">
                            <span className="text-[#ff9900] text-[20px] font-black">✓</span>
                            <div>
                              <strong className="text-[#071735] text-[18px]">Đề Xuất Khuyến Mãi Cục Bộ:</strong>
                              <p className="text-[#405a7a] text-[16px] mt-1 leading-snug">Gợi ý tạo combo flash sale vào khung giờ thấp điểm để kích cầu.</p>
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
