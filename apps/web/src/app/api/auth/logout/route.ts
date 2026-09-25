import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';
import { logoutFromBackend } from '@/lib/bff/auth-service';
import { assertBffRequest, errorResponse } from '@/lib/bff/backend';
import { clearSessionCookie, readSession, readSessionId } from '@/lib/session/session-cookie';

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    assertBffRequest(request);
    const session = await readSession(request);
    const sessionId = await readSessionId(request);
    if (session) {
      await logoutFromBackend(session).catch(() => undefined);
    }
    const response = NextResponse.json({ success: true });
    await clearSessionCookie(response, sessionId);
    return response;
  } catch (error) {
    return errorResponse(error);
  }
}
