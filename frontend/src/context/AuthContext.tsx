import React, { createContext, useContext, useEffect, useState } from 'react';

export interface AuthUser {
  name: string;
  email: string;
  role: string;
  plan: string;
}

interface AuthCtx {
  user: AuthUser | null;
  loading: boolean;
  /** ورود واقعی از طریق GoTrue (Supabase) — پروکسی بک‌اند */
  login: (email: string, password: string) => Promise<AuthUser>;
  /** ثبت‌نام واقعی — در صورت فعال بودن تأیید ایمیل، پیام تأیید برمی‌گردد */
  register: (data: {
    name: string;
    email: string;
    role: string;
    password: string;
  }) => Promise<AuthUser>;
  logout: () => void;
}

const Ctx = createContext<AuthCtx | null>(null);

const TOKEN_KEY = 'eco_token';
const USER_KEY = 'eco_user';

async function postJson(url: string, body: unknown) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return (await res.json()) as Record<string, unknown>;
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const raw = localStorage.getItem(USER_KEY);
    if (raw) {
      try {
        setUser(JSON.parse(raw) as AuthUser);
      } catch {
        localStorage.removeItem(USER_KEY);
      }
    }
    setLoading(false);
  }, []);

  const persist = (u: AuthUser, token?: string) => {
    setUser(u);
    localStorage.setItem(USER_KEY, JSON.stringify(u));
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  };

  const login: AuthCtx['login'] = async (email, password) => {
    const res = await postJson('/api/v1/auth/login', { email, password });
    if (res.status !== 'ok' || !res.access_token) {
      throw new Error(String(res.error ?? 'ورود ناموفق — ایمیل یا رمز عبور نادرست است'));
    }
    const u: AuthUser = {
      name: String(res.email ?? email.split('@')[0]),
      email: String(res.email ?? email),
      role: 'farmer',
      plan: 'free',
    };
    persist(u, String(res.access_token));
    return u;
  };

  const register: AuthCtx['register'] = async (data) => {
    const res = await postJson('/api/v1/auth/register', {
      email: data.email,
      password: data.password,
    });
    if (res.status !== 'ok') {
      throw new Error(String(res.error ?? 'ثبت‌نام ناموفق'));
    }
    const confirmed = Boolean(res.confirmed);
    const u: AuthUser = { name: data.name, email: data.email, role: data.role, plan: 'free' };
    persist(u, confirmed ? undefined : undefined);
    if (!confirmed) {
      throw new Error('حساب ساخته شد؛ لینک تأیید به ایمیل ارسال شد. پس از تأیید وارد شوید.');
    }
    return u;
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(TOKEN_KEY);
  };

  return <Ctx.Provider value={{ user, loading, login, register, logout }}>{children}</Ctx.Provider>;
};

export function useAuth() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
