import React, { createContext, useContext, useEffect, useState } from 'react';

export interface AuthUser {
  name: string; email: string; role: string; plan: string;
}

interface AuthCtx {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<AuthUser>;
  register: (data: { name: string; email: string; role: string }) => Promise<AuthUser>;
  logout: () => void;
}

const Ctx = createContext<AuthCtx | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const raw = localStorage.getItem('eco_user');
    if (raw) { try { setUser(JSON.parse(raw)); } catch { /* ignore */ } }
    setLoading(false);
  }, []);

  const persist = (u: AuthUser) => { setUser(u); localStorage.setItem('eco_user', JSON.stringify(u)); };

  const login: AuthCtx['login'] = async (email, password) => {
    await new Promise(r => setTimeout(r, 900));
    if (!email.includes('@') || password.length < 6) throw new Error('ایمیل یا رمز عبور معتبر نیست');
    const u: AuthUser = { name: email.split('@')[0], email, role: 'farmer', plan: 'free' };
    persist(u); return u;
  };

  const register: AuthCtx['register'] = async (data) => {
    await new Promise(r => setTimeout(r, 1100));
    const u: AuthUser = { name: data.name, email: data.email, role: data.role, plan: 'free' };
    persist(u); return u;
  };

  const logout = () => { setUser(null); localStorage.removeItem('eco_user'); };

  return <Ctx.Provider value={{ user, loading, login, register, logout }}>{children}</Ctx.Provider>;
};

export function useAuth() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
