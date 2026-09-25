'use client';

import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import type { LoginInput, RegisterInput, SessionUser } from '@/lib/bff/contracts';

type AuthResponse = {
  user: SessionUser | null;
};

type AuthContextValue = AuthResponse & {
  loading: boolean;
  login: (input: LoginInput) => Promise<void>;
  register: (input: RegisterInput) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

async function readAuthResponse(response: Response): Promise<AuthResponse> {
  const payload = (await response.json()) as AuthResponse & { error?: string };
  if (!response.ok) throw new Error(payload.error ?? 'Authentication request failed');
  return { user: payload.user };
}

async function requestAuth(path: string, init: RequestInit = {}): Promise<AuthResponse> {
  const headers = new Headers(init.headers);
  headers.set('Accept', 'application/json');
  if (init.body !== undefined) headers.set('Content-Type', 'application/json');
  if (init.method && init.method !== 'GET') headers.set('X-CSRF-Intent', '1');
  const response = await fetch(path, {
    ...init,
    headers,
    credentials: 'same-origin',
  });
  return readAuthResponse(response);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthResponse>({ user: null });
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      setState(await requestAuth('/api/auth/refresh', { method: 'POST' }));
    } catch {
      setState({ user: null });
    }
  }, []);

  useEffect(() => {
    void requestAuth('/api/auth/session')
      .then(setState)
      .catch(() => setState({ user: null }))
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (input: LoginInput) => {
    setState(await requestAuth('/api/auth/login', { method: 'POST', body: JSON.stringify(input) }));
  }, []);

  const register = useCallback(async (input: RegisterInput) => {
    setState(
      await requestAuth('/api/auth/signup', { method: 'POST', body: JSON.stringify(input) }),
    );
  }, []);

  const logout = useCallback(async () => {
    try {
      await requestAuth('/api/auth/logout', { method: 'POST' });
    } finally {
      setState({ user: null });
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ ...state, loading, login, register, logout, refresh }),
    [state, loading, login, register, logout, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used within AuthProvider');
  return value;
}
