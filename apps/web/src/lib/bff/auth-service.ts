import { backendError, backendRequest, readJson } from '@/lib/bff/backend';
import {
  type LoginInput,
  type RegisterInput,
  type SessionUser,
  sessionUserSchema,
  tokenResponseSchema,
} from '@/lib/bff/contracts';
import { createSessionRecord, type SessionRecord } from '@/lib/session/session-cookie';

async function tokenResponse(response: Response) {
  const payload = await readJson(response);
  if (!response.ok) throw backendError(response.status, payload);
  return tokenResponseSchema.parse(payload);
}

export async function loginWithBackend(input: LoginInput): Promise<SessionRecord> {
  const response = await backendRequest('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(input),
  });
  const payload = await tokenResponse(response);
  return createSessionRecord({
    accessToken: payload.access_token,
    refreshToken: payload.refresh_token,
    user: payload.user,
  });
}

export async function registerWithBackend(input: RegisterInput): Promise<SessionRecord> {
  const response = await backendRequest('/api/v1/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(input),
  });
  const payload = await tokenResponse(response);
  return createSessionRecord({
    accessToken: payload.access_token,
    refreshToken: payload.refresh_token,
    user: payload.user,
  });
}

export async function refreshSession(record: SessionRecord): Promise<SessionRecord> {
  const response = await backendRequest('/api/v1/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ refresh_token: record.refreshToken }),
  });
  const payload = await tokenResponse(response);
  return createSessionRecord({
    accessToken: payload.access_token,
    refreshToken: payload.refresh_token,
    user: payload.user,
  });
}

export async function currentUser(record: SessionRecord): Promise<SessionUser> {
  const response = await backendRequest('/api/v1/auth/me', {
    method: 'GET',
    headers: { Accept: 'application/json' },
    accessToken: record.accessToken,
  });
  const payload = await readJson(response);
  if (!response.ok) throw backendError(response.status, payload);
  return sessionUserSchema.parse(payload);
}

export async function logoutFromBackend(record: SessionRecord): Promise<void> {
  await backendRequest('/api/v1/auth/logout', {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: record.refreshToken }),
    accessToken: record.accessToken,
  });
}
