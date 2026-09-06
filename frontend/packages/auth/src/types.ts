export type Role = 'admin' | 'scientist' | 'farmer' | 'citizen' | 'guest';

export type User = {
  id: string;
  email: string;
  full_name?: string;
  role: Role;
  locale?: string;
  avatar_url?: string;
};

export type AuthSession = {
  user: User;
  token: string;
  expires_at: string;
};

export type AuthState = {
  session: AuthSession | null;
  status: 'idle' | 'authenticating' | 'authenticated' | 'error';
  error: string | null;
};