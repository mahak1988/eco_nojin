import { NextRequest, NextResponse } from 'next/server';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { SessionUser } from '@/lib/bff/contracts';
import {
  clearSessionCookie,
  createSessionRecord,
  issueSession,
  readSession,
  readSessionId,
  sessionCookieName,
  setSessionCookie,
} from './session-cookie';

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

describe('session cookie', () => {
  beforeEach(() => {
    vi.stubEnv('REDIS_URL', '');
    vi.stubEnv('SESSION_TTL_SECONDS', '3600');
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it('stores an opaque session identifier in the cookie', async () => {
    const record = createSessionRecord({ accessToken: 'access', refreshToken: 'refresh', user });
    const id = await issueSession(record);
    const response = NextResponse.json({ ok: true });
    await setSessionCookie(response, id);
    const value = response.cookies.get(sessionCookieName())?.value;
    expect(value).toBe(id);
    expect(value).not.toContain('access');
    const request = new NextRequest('http://localhost:3001', {
      headers: { cookie: `${sessionCookieName()}=${value}` },
    });
    expect((await readSession(request))?.user.id).toBe(user.id);
  });

  it('deletes the server session when cleared', async () => {
    const id = await issueSession(
      createSessionRecord({ accessToken: 'access', refreshToken: 'refresh', user }),
    );
    const response = NextResponse.json({ ok: true });
    await clearSessionCookie(response, id);
    expect(response.cookies.get(sessionCookieName())?.value).toBe('');
    const request = new NextRequest('http://localhost:3001', {
      headers: { cookie: `${sessionCookieName()}=${id}` },
    });
    expect(await readSessionId(request)).toBe(id);
    expect(await readSession(request)).toBeNull();
  });
});
