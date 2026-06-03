import { createContext, useContext, useState, useEffect } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null); // { token, type: 'user'|'guest', ...info }
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check localStorage on mount
    const savedToken = localStorage.getItem('access_token');
    const savedType = localStorage.getItem('auth_type');
    const savedUserId = localStorage.getItem('user_id');
    const savedEmail = localStorage.getItem('email');
    const savedName = localStorage.getItem('name');

    if (savedToken && savedType) {
      setUser({
        token: savedToken,
        type: savedType,
        id: savedUserId,
        email: savedEmail,
        name: savedName
      });
      setLoading(false);
    } else {
      loginAsGuest().finally(() => setLoading(false));
    }
  }, []);

  const loginWithGoogle = async (credential) => {
    try {
      const res = await fetch(`${API_BASE}/auth/google`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: credential })
      });
      if (!res.ok) throw new Error('Login failed');
      const data = await res.json();
      
      setUser({
        token: data.access_token,
        type: 'user',
        id: data.user_id,
        email: data.email,
        name: data.name
      });
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('auth_type', 'user');
      localStorage.setItem('user_id', data.user_id);
      localStorage.setItem('email', data.email);
      localStorage.setItem('name', data.name);
      return true;
    } catch (e) {
      console.error(e);
      return false;
    }
  };

  const loginAsGuest = async () => {
    try {
      const res = await fetch(`${API_BASE}/auth/guest`, {
        method: 'POST'
      });
      if (!res.ok) throw new Error('Guest login failed');
      const data = await res.json();
      
      setUser({
        token: data.access_token,
        type: 'guest',
        id: data.guest_id
      });
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('auth_type', 'guest');
      localStorage.setItem('user_id', data.guest_id);
      return true;
    } catch (e) {
      console.error(e);
      return false;
    }
  };

  const logout = async () => {
    localStorage.clear();
    setUser(null);
    setLoading(true);
    try {
      await loginAsGuest();
    } catch (e) {
      console.error("Failed to automatically login as guest after logout:", e);
    }
    setLoading(false);
  };

  return (
    <AuthContext.Provider value={{ user, loading, loginWithGoogle, loginAsGuest, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
