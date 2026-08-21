"use client";
import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { api } from './api-client';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  language: string;
  phone?: string;
  country?: string;
  city?: string;
  avatar_url?: string;
  is_email_verified: boolean;
  is_active: boolean;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (data: any) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  updateUser: (data: Partial<User>) => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const savedToken = localStorage.getItem('auth_token');
    const savedUser = localStorage.getItem('auth_user');
    if (savedToken && savedUser) {
      try {
        const u = JSON.parse(savedUser);
        setUser(u);
        setToken(savedToken);
        // Sync language to localStorage for i18n
        if (u.language) {
          localStorage.setItem('locale', u.language);
        }
      } catch (e) {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
      }
    }
    setLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    const res = await api.post<any>('/api/v1/auth/login', { email, password });
    if (res.success && res.data) {
      localStorage.setItem('auth_token', res.data.access_token);
      localStorage.setItem('auth_user', JSON.stringify(res.data.user));
      setToken(res.data.access_token);
      setUser(res.data.user);
      if (res.data.user.language) {
        localStorage.setItem('locale', res.data.user.language);
      }
      return { success: true };
    }
    return { success: false, error: res.error };
  };

  const register = async (data: any) => {
    const res = await api.post<any>('/api/v1/auth/register', data);
    if (res.success && res.data) {
      localStorage.setItem('auth_token', res.data.access_token);
      localStorage.setItem('auth_user', JSON.stringify(res.data.user));
      setToken(res.data.access_token);
      setUser(res.data.user);
      if (res.data.user.language) {
        localStorage.setItem('locale', res.data.user.language);
      }
      return { success: true };
    }
    return { success: false, error: res.error };
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
    setToken(null);
    setUser(null);
  };

  const updateUser = (data: Partial<User>) => {
    if (user) {
      const updated = { ...user, ...data };
      setUser(updated);
      localStorage.setItem('auth_user', JSON.stringify(updated));
      if (data.language) {
        localStorage.setItem('locale', data.language);
      }
    }
  };

  return (
    <AuthContext.Provider value={{
      user, token, loading, login, register, logout, updateUser,
      isAuthenticated: !!user && !!token,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}