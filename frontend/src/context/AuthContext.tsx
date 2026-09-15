/** Auth context for dashboard. */

import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';

interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  is_admin: boolean;
  country: string | null;
  language: string;
  name?: string | null;
}

interface AuthContextValue {
  user: User | null;
  isAdmin: boolean;
  isAuthenticated: boolean;
  token: string | null;
  isLoading: boolean;
  login: (accessToken: string, userData: {
    id: string;
    email: string;
    full_name: string | null;
    role: string;
    language: string;
    [key: string]: unknown;
  }) => Promise<void>;
  logout: () => void;
  updateUser: (data: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const login = useCallback(async (accessToken: string, userData: {
    id: string;
    email: string;
    full_name: string | null;
    role: string;
    language: string;
    [key: string]: unknown;
  }) => {
    setIsLoading(true);
    try {
      setToken(accessToken);
      setUser({
        id: userData.id,
        email: userData.email,
        full_name: userData.full_name,
        role: userData.role,
        is_admin: userData.role === 'admin',
        country: (userData.country as string | null) ?? null,
        language: userData.language,
        name: userData.full_name,
      });
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
  }, []);

  const updateUser = useCallback((data: Partial<User>) => {
    setUser((prev) => (prev ? { ...prev, ...data } : prev));
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAdmin: user?.is_admin ?? false,
        isAuthenticated: user !== null,
        token,
        isLoading,
        login,
        logout,
        updateUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return value;
}
