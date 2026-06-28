/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useState, useEffect } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api/v1';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const savedToken = localStorage.getItem('access_token');
    const savedType = localStorage.getItem('auth_type');
    const savedUserId = localStorage.getItem('user_id');
    const savedEmail = localStorage.getItem('email');
    const savedName = localStorage.getItem('name');
    const savedRole = localStorage.getItem('user_role');
    const savedAvatarUrl = localStorage.getItem('avatar_url');

    if (savedToken && savedType) {
      return {
        token: savedToken,
        type: savedType,
        id: savedUserId,
        email: savedEmail,
        name: savedName,
        role: savedRole,
        avatar_url: savedAvatarUrl
      };
    }
    return null;
  });

  const [loading, setLoading] = useState(() => {
    const savedToken = localStorage.getItem('access_token');
    const savedType = localStorage.getItem('auth_type');
    return !(savedToken && savedType);
  });

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
        name: data.name,
        avatar_url: data.avatar_url
      });
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('auth_type', 'user');
      localStorage.setItem('user_id', data.user_id);
      localStorage.setItem('email', data.email);
      localStorage.setItem('name', data.name);
      if (data.avatar_url) {
        localStorage.setItem('avatar_url', data.avatar_url);
      } else {
        localStorage.removeItem('avatar_url');
      }
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

  const loginAsAdmin = async (username, password) => {
    try {
      const res = await fetch(`${API_BASE}/auth/admin-login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      if (!res.ok) throw new Error('Admin login failed');
      const data = await res.json();
      
      setUser({
        token: data.access_token,
        type: 'user',
        role: data.role,
        id: data.user_id,
        email: data.email,
        name: data.name,
        avatar_url: data.avatar_url
      });
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('auth_type', 'user');
      localStorage.setItem('user_role', data.role);
      localStorage.setItem('user_id', data.user_id);
      localStorage.setItem('email', data.email);
      localStorage.setItem('name', data.name);
      if (data.avatar_url) {
        localStorage.setItem('avatar_url', data.avatar_url);
      } else {
        localStorage.removeItem('avatar_url');
      }
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

  useEffect(() => {
    if (!user) {
      const timer = setTimeout(() => {
        loginAsGuest().finally(() => setLoading(false));
      }, 0);
      return () => clearTimeout(timer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, loginWithGoogle, loginAsGuest, loginAsAdmin, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

