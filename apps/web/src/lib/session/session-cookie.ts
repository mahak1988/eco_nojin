import type { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import type { SessionUser } from '@/lib/bff/contracts';
import { getPublicAppUrl, getSessionTtlSeconds } from '@/lib/config/server-env';
import {
  createStoredSession,
  deleteStoredSession,
  getStoredSession,
  replaceStoredSession,
} from '@/lib/session/store';

const sessionRecordSchema = z.object({
  version: z.literal(1),
  accessToken: z.string().min(1),
  refreshToken: z.string().min(1),
  user: z.object({
    id: z.string().min(1),
    email: z.email(),
    full_name: z.string().nullable().optional(),
    role: z.string().min(1),
    language: z.string().nullable().optional(),
    phone: z.string().nullable().optional(),
    country: z.string().nullable().optional(),
    city: z.string().nullable().optional(),
    avatar_url: z.url().nullable().optional(),
    is_email_verified: z.boolean(),
    is_active: z.boolean(),
    created_at: z.string(),
  }),
  createdAt: z.number().int().positive(),
  expiresAt: z.number().int().positive(),
});

export type SessionRecord = z.infer<typeof sessionRecordSchema>;

export function createSessionRecord(tokens: {
  accessToken: string;
  refreshToken: string;
  user: SessionUser;
}): SessionRecord {
  const now = Date.now();
  return sessionRecordSchema.parse({
    version: 1,
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
    user: tokens.user,
    createdAt: now,
    expiresAt: now + getSessionTtlSeconds() * 1000,
  });
}

export function sessionCookieName(): string {
  return getPublicAppUrl().protocol === 'https:' ? '__Host-eco_session' : 'eco_session';
}

export async function issueSession(record: SessionRecord): Promise<string> {
  return createStoredSession(record);
}

export async function readSessionId(request: NextRequest): Promise<string | null> {
  return request.cookies.get(sessionCookieName())?.value ?? null;
}

export async function readSession(request: NextRequest): Promise<SessionRecord | null> {
  const id = await readSessionId(request);
  return id ? getStoredSession(id) : null;
}

export async function setSessionCookie(response: NextResponse, id: string): Promise<void> {
  const secure = getPublicAppUrl().protocol === 'https:';
  response.cookies.set({
    name: sessionCookieName(),
    value: id,
    httpOnly: true,
    secure,
    sameSite: 'lax',
    path: '/',
    maxAge: getSessionTtlSeconds(),
  });
}

export async function replaceSession(
  response: NextResponse,
  id: string,
  record: SessionRecord,
): Promise<void> {
  await replaceStoredSession(id, record);
  await setSessionCookie(response, id);
}

export async function clearSessionCookie(
  response: NextResponse,
  id?: string | null,
): Promise<void> {
  if (id) await deleteStoredSession(id);
  const secure = getPublicAppUrl().protocol === 'https:';
  response.cookies.set({
    name: sessionCookieName(),
    value: '',
    httpOnly: true,
    secure,
    sameSite: 'lax',
    path: '/',
    maxAge: 0,
  });
}
