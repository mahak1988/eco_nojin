import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';
import { refreshSession } from '@/lib/bff/auth-service';
import { assertBffRequest, BffError, errorResponse } from '@/lib/bff/backend';
import { readSession, readSessionId, replaceSession } from '@/lib/session/session-cookie';

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    assertBffRequest(request);
    const current = await readSession(request);
    const currentId = await readSessionId(request);
    if (!current || !currentId) throw new BffError(401, 'No active session');
    const session = await refreshSession(current);
    const response = NextResponse.json({ user: session.user });
    await replaceSession(response, currentId, session);
    return response;
  } catch (error) {
    return errorResponse(error);
  }
}
