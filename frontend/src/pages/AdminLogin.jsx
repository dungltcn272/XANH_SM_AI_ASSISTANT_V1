import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { 
  Lock, Mail, Eye, EyeOff, CheckCircle, ShieldCheck, 
  ArrowRight, FileText, BrainCircuit, Zap, Target, 
  MessageSquare, Users, Info
} from 'lucide-react';

function AdminLogin() {
  const { loginAsAdmin } = useAuth();
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);

  const handleAdminLogin = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      setError("Vui lòng nhập Username và Mật khẩu");
      return;
    }
    const success = await loginAsAdmin(email, password);
    if (success) {
      navigate('/admin');
    } else {
      setError("Đăng nhập Admin thất bại. Sai tài khoản hoặc mật khẩu.");
    }
  };

  return (
    <div className="min-h-screen bg-[#f2f9f8] text-[#1a2b3c] font-sans relative overflow-hidden flex flex-col">
      {/* Background Decor */}
      <div className="absolute top-[-20%] left-[-10%] w-[70%] h-[140%] bg-gradient-to-br from-[#00c897]/10 via-[#00c897]/5 to-transparent rounded-full blur-3xl pointer-events-none"></div>
      
      {/* Header Logo */}
      <header className="absolute top-0 left-0 w-full p-8 flex justify-between items-center z-10">
        <div className="flex items-center gap-2">
          <img src="/logo.svg" alt="Xanh SM Logo" className="h-8 w-auto object-contain" />
        </div>
      </header>

      <main className="flex-1 w-full max-w-7xl mx-auto flex flex-col lg:flex-row items-center justify-center p-6 lg:p-12 gap-12 lg:gap-24 z-10 pt-24">
        
        {/* Left Content */}
        <div className="flex-1 w-full flex flex-col pt-8 lg:pt-0">
          <h1 className="text-4xl lg:text-5xl font-extrabold leading-tight tracking-tight text-[#1a2b3c] mb-4">
            XANH SM RAG <br/>
            <span className="text-[#00c897]">Enterprise</span> AI Assistant
          </h1>
          <p className="text-[#4a5f73] text-base lg:text-lg mb-10 max-w-md">
            Nền tảng tìm kiếm, hiểu và khai thác tri thức nội bộ bằng AI dành cho đội ngũ Xanh SM.
          </p>

          {/* Stats Card */}
          <div className="bg-white/70 backdrop-blur-xl border border-white rounded-[2rem] p-6 shadow-[0_8px_30px_rgb(0,0,0,0.04)] w-full max-w-xl">
            <div className="flex items-center gap-2 text-[#00c897] font-bold mb-6">
              <ShieldCheck size={20} />
              <span>Hệ thống quản trị tri thức AI</span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100 flex flex-col">
                <div className="flex items-center gap-2 text-[#4a5f73] mb-3 text-xs font-semibold">
                  <div className="w-6 h-6 rounded-full bg-blue-50 text-blue-500 flex items-center justify-center"><FileText size={12}/></div>
                  Tài liệu nội bộ
                </div>
                <div className="text-2xl font-bold text-[#00c897]">1,248</div>
                <div className="text-[10px] text-gray-400 mt-1 font-medium">+12 tài liệu mới</div>
              </div>

              <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100 flex flex-col">
                <div className="flex items-center gap-2 text-[#4a5f73] mb-3 text-xs font-semibold">
                  <div className="w-6 h-6 rounded-full bg-green-50 text-[#00c897] flex items-center justify-center"><BrainCircuit size={12}/></div>
                  AI Model
                </div>
                <div className="text-xl font-bold text-[#00c897]">GPT-4o-Mini</div>
                <div className="text-[10px] text-gray-400 mt-1 font-medium">RAG Powered</div>
              </div>

              <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100 flex flex-col">
                <div className="flex items-center gap-2 text-[#4a5f73] mb-3 text-xs font-semibold">
                  <div className="w-6 h-6 rounded-full bg-yellow-50 text-yellow-500 flex items-center justify-center"><Zap size={12}/></div>
                  Thời gian phản hồi
                </div>
                <div className="text-2xl font-bold text-[#00c897]">3.1s</div>
                <div className="text-[10px] text-gray-400 mt-1 font-medium">Trung bình</div>
              </div>

              <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100 flex flex-col">
                <div className="flex items-center gap-2 text-[#4a5f73] mb-3 text-xs font-semibold">
                  <div className="w-6 h-6 rounded-full bg-purple-50 text-purple-500 flex items-center justify-center"><Target size={12}/></div>
                  Độ chính xác
                </div>
                <div className="text-2xl font-bold text-[#00c897]">99%</div>
                <div className="text-[10px] text-gray-400 mt-1 font-medium">+3.6% so với tuần trước</div>
              </div>

              <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100 flex flex-col">
                <div className="flex items-center gap-2 text-[#4a5f73] mb-3 text-xs font-semibold">
                  <div className="w-6 h-6 rounded-full bg-cyan-50 text-cyan-500 flex items-center justify-center"><MessageSquare size={12}/></div>
                  Truy vấn hôm nay
                </div>
                <div className="text-2xl font-bold text-[#00c897]">5,824</div>
                <div className="text-[10px] text-gray-400 mt-1 font-medium">+18% so với hôm qua</div>
              </div>

              <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100 flex flex-col">
                <div className="flex items-center gap-2 text-[#4a5f73] mb-3 text-xs font-semibold">
                  <div className="w-6 h-6 rounded-full bg-orange-50 text-orange-500 flex items-center justify-center"><Users size={12}/></div>
                  Người dùng HĐ
                </div>
                <div className="text-2xl font-bold text-[#00c897]">142</div>
                <div className="text-[10px] text-gray-400 mt-1 font-medium flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-[#00c897]"></span> Online</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Content - Login Form */}
        <div className="w-full max-w-[440px] relative">
          <div className="bg-white rounded-[2rem] shadow-[0_20px_60px_rgba(0,0,0,0.06)] p-10 pt-14 border border-gray-50 relative z-10">
            
            {/* Top overlapping badge */}
            <div className="absolute -top-8 left-1/2 -translate-x-1/2 w-16 h-16 bg-white rounded-full flex items-center justify-center shadow-md">
              <div className="w-12 h-12 rounded-full bg-[#00c897] flex items-center justify-center text-white">
                <Lock size={20} />
              </div>
            </div>

            <div className="text-center mb-10">
              <h2 className="text-2xl font-bold text-[#1a2b3c] flex items-center justify-center gap-2 mb-2">
                Đăng nhập hệ thống
                <ShieldCheck size={20} className="text-[#00c897]" />
              </h2>
              <p className="text-[#7a8b9c] text-sm">Chỉ dành cho quản trị viên</p>
            </div>

            <form onSubmit={handleAdminLogin} className="space-y-6">
              {error && <div className="text-red-500 text-sm text-center bg-red-50 p-2 rounded-lg">{error}</div>}
              
              <div className="space-y-2">
                <label className="text-sm font-bold text-[#1a2b3c]">Tài khoản (Admin) / Email</label>
                <div className="relative">
                  <div className="absolute left-4 top-1/2 -translate-y-1/2 text-[#7a8b9c]">
                    <Mail size={18} />
                  </div>
                  <input 
                    type="text" 
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="admin@gmail.com"
                    className="w-full pl-11 pr-11 py-3.5 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#00c897]/20 focus:border-[#00c897] transition-all text-[#1a2b3c]"
                  />
                  {email && (
                    <div className="absolute right-4 top-1/2 -translate-y-1/2 text-[#00c897]">
                      <CheckCircle size={18} />
                    </div>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-bold text-[#1a2b3c]">Mật khẩu</label>
                <div className="relative">
                  <div className="absolute left-4 top-1/2 -translate-y-1/2 text-[#7a8b9c]">
                    <Lock size={18} />
                  </div>
                  <input 
                    type={showPassword ? "text" : "password"} 
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full pl-11 pr-11 py-3.5 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#00c897]/20 focus:border-[#00c897] transition-all text-[#1a2b3c]"
                  />
                  <button 
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-[#7a8b9c] hover:text-[#00c897] transition-colors"
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              <div className="flex justify-end">
                <a href="#" className="text-sm font-bold text-[#00c897] hover:underline">Quên mật khẩu?</a>
              </div>

              <button 
                type="submit"
                className="w-full py-4 bg-[#00c897] hover:bg-[#00b386] text-white rounded-xl font-bold flex items-center justify-center gap-2 transition-all shadow-[0_8px_20px_rgba(0,200,151,0.25)] hover:shadow-[0_8px_25px_rgba(0,200,151,0.35)]"
              >
                <Lock size={18} /> Truy cập hệ thống <ArrowRight size={18} />
              </button>

              <div className="bg-[#f2f9f8] p-3 rounded-xl flex items-center justify-center gap-2 text-xs text-[#4a5f73] mt-4 border border-[#00c897]/10">
                <Info size={14} className="text-[#00c897]" /> Hệ thống chỉ dành cho quản trị viên được ủy quyền.
              </div>
            </form>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="w-full max-w-7xl mx-auto p-6 flex flex-col md:flex-row justify-between items-center text-xs text-[#7a8b9c] z-10 gap-2">
        <div className="flex items-center gap-2 font-medium">
          <ShieldCheck size={14} /> Bảo mật doanh nghiệp • Dữ liệu của bạn được bảo vệ tuyệt đối
        </div>
        <div>
          © 2026 Xanh SM. All rights reserved.
        </div>
      </footer>
    </div>
  );
}

export default AdminLogin;
