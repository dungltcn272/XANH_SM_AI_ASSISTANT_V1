import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { Bot, Mail, Eye, EyeOff, ArrowRight, User as UserIcon, Car, Leaf, Zap, Lock } from 'lucide-react';
import { GoogleLogin } from '@react-oauth/google';
import { api } from '../api';

function Login() {
  const { login, setToken } = useAuth();
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);

  // Parallax effect
  useEffect(() => {
    const handleMouseMove = (e) => {
      const moveX = (e.clientX - window.innerWidth / 2) * 0.01;
      const moveY = (e.clientY - window.innerHeight / 2) * 0.01;
      
      const aurora = document.querySelector('.aurora-bg');
      const cinematic = document.querySelector('.cinematic-bg');
      
      if (aurora) aurora.style.transform = `translate(${moveX}px, ${moveY}px)`;
      if (cinematic) cinematic.style.transform = `scale(1.05) translate(${moveX * -0.5}px, ${moveY * -0.5}px)`;
    };
    
    document.addEventListener('mousemove', handleMouseMove);
    return () => document.removeEventListener('mousemove', handleMouseMove);
  }, []);

  const handleGuestLogin = () => {
    login({ type: 'guest' });
    navigate('/');
  };

  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      const data = await api.authGoogle(credentialResponse.credential);
      setToken(data.access_token);
      login({ type: data.role || 'user', name: data.name, email: data.email });
      navigate('/');
    } catch (err) {
      console.error(err);
      setError("Đăng nhập thất bại");
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen overflow-hidden bg-background font-sans text-on-surface w-full relative">
      <div className="absolute inset-0 bg-gradient-to-tr from-primary/20 to-secondary/20 aurora-bg transition-transform duration-200"></div>
      
      <main className="w-full max-w-[480px] px-6 md:px-0 z-10">
        <div className="glass-panel p-6 md:p-12 rounded-2xl flex flex-col items-center">
          
          <header className="text-center mb-10 w-full">
            <div className="mb-6 flex justify-center">
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center shadow-lg">
                <Bot className="text-white" size={32} />
              </div>
            </div>
            <h1 className="text-3xl font-bold bg-gradient-to-br from-primary to-secondary bg-clip-text text-transparent mb-2">
              Xanh SM RAG
            </h1>
            <p className="text-on-surface-variant/70 text-lg">Chào mừng bạn quay lại</p>
          </header>

          <form className="w-full space-y-6" onSubmit={(e) => e.preventDefault()}>
            {error && <div className="text-red-500 text-sm text-center bg-red-50 p-2 rounded">{error}</div>}
            
            <div className="relative group">
              <input 
                className="w-full bg-white/40 border border-white/60 rounded-xl px-4 pt-6 pb-2 text-on-surface focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all peer" 
                id="email" 
                placeholder=" " 
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
              />
              <label 
                className="absolute left-4 top-2 text-on-surface-variant/70 text-xs font-semibold transition-all peer-placeholder-shown:text-base peer-placeholder-shown:top-4 peer-focus:text-xs peer-focus:top-2" 
                htmlFor="email"
              >
                Email
              </label>
              <div className="absolute right-4 top-4 text-on-surface-variant/40">
                <Mail size={20} />
              </div>
            </div>

            <div className="relative group">
              <input 
                className="w-full bg-white/40 border border-white/60 rounded-xl px-4 pt-6 pb-2 text-on-surface focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all peer" 
                id="password" 
                placeholder=" " 
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={e => setPassword(e.target.value)}
              />
              <label 
                className="absolute left-4 top-2 text-on-surface-variant/70 text-xs font-semibold transition-all peer-placeholder-shown:text-base peer-placeholder-shown:top-4 peer-focus:text-xs peer-focus:top-2" 
                htmlFor="password"
              >
                Mật khẩu
              </label>
              <div 
                className="absolute right-4 top-4 text-on-surface-variant/40 cursor-pointer hover:text-primary transition-colors"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </div>
            </div>

            <div className="flex justify-end -mt-2">
              <a className="text-xs font-semibold text-primary hover:underline transition-all" href="#">Quên mật khẩu?</a>
            </div>

            <div className="space-y-4 pt-2">
              <button 
                className="w-full py-3 rounded-full bg-gradient-to-r from-primary to-secondary text-white font-bold shadow-md flex items-center justify-center gap-2 group hover:shadow-lg transition-all" 
                type="submit"
              >
                <span>Đăng nhập</span>
                <ArrowRight className="group-hover:translate-x-1 transition-transform" size={20} />
              </button>
              
              <div className="flex justify-center my-4">
                 <GoogleLogin
                    onSuccess={handleGoogleSuccess}
                    onError={() => setError('Đăng nhập Google thất bại')}
                    useOneTap
                 />
              </div>

              <button 
                className="w-full py-3 rounded-full border border-primary/30 text-primary font-medium hover:bg-white/40 transition-all flex items-center justify-center gap-2" 
                type="button"
                onClick={handleGuestLogin}
              >
                <span>Tiếp tục dưới dạng Khách (Guest)</span>
                <UserIcon size={20} />
              </button>
            </div>
          </form>

          <footer className="mt-12 text-center">
            <p className="text-xs font-semibold text-on-surface-variant/60 uppercase tracking-widest mb-4">ĐỐI TÁC CỦA HỆ SINH THÁI XANH</p>
            <div className="flex items-center justify-center gap-6 opacity-40 grayscale hover:grayscale-0 transition-all duration-500">
              <Car size={28} />
              <Leaf size={28} />
              <Zap size={28} />
            </div>
          </footer>
        </div>

        <div className="mt-8 flex justify-center items-center gap-4 text-on-surface-variant/50">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
            <span className="text-xs font-semibold">Hệ thống AI ổn định</span>
          </div>
          <div className="w-px h-3 bg-on-surface-variant/20"></div>
          <div className="flex items-center gap-2">
            <Lock size={14} />
            <span className="text-xs font-semibold">Mã hóa 256-bit</span>
          </div>
        </div>
      </main>
    </div>
  );
}

export default Login;
