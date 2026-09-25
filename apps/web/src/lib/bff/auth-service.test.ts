import { afterEach, describe, expect, it, vi } from 'vitest';
import { createSessionRecord } from '@/lib/session/session-cookie';
import { loginWithBackend, refreshSession } from './auth-service';
import type { SessionUser } from './contracts';

const user: SessionUser = {
  id: 'user-1',
  email: 'farmer@example.com',
  full_name: 'Test Farmer',
  role: 'farmer',
  language: 'fa',
  is_email_verified: true,
  is_active: true,
  created_at: new Date().toISOString(),
};

function tokenResponse() {
  return new Response(
    JSON.stringify({
      access_token: 'new-access',
      refresh_token: 'new-refresh',
      user,
    }),
    { status: 200, headers: { 'Content-Type': 'application/json' } },
  );
}

describe('BFF auth service', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it('stores backend login tokens in a server session record', async () => {
    vi.stubEnv('API_PROXY_TARGET', 'http://backend.test');
    const fetchMock = vi.fn(async () => tokenResponse());
    vi.stubGlobal('fetch', fetchMock);

    const session = await loginWithBackend({ email: user.email, password: 'password123' });

    expect(session.accessToken).toBe('new-access');
    expect(session.refreshToken).toBe('new-refresh');
    expect(fetchMock).toHaveBeenCalledWith(
      'http://backend.test/api/v1/auth/login',
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it('rotates the stored refresh token', async () => {
    vi.stubEnv('API_PROXY_TARGET', 'http://backend.test');
    const current = createSessionRecord({
      accessToken: 'old-access',
      refreshToken: 'old-refresh',
      user,
    });
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => tokenResponse()),
    );

    const refreshed = await refreshSession(current);

    expect(refreshed.accessToken).toBe('new-access');
    expect(refreshed.refreshToken).toBe('new-refresh');
  });
});
