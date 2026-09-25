import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';
import { loginWithBackend } from '@/lib/bff/auth-service';
import { assertBffRequest, errorResponse } from '@/lib/bff/backend';
import { loginSchema } from '@/lib/bff/contracts';
import { issueSession, setSessionCookie } from '@/lib/session/session-cookie';

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    assertBffRequest(request);
    const input = loginSchema.parse(await request.json());
    const session = await loginWithBackend(input);
    const response = NextResponse.json({ user: session.user });
    await setSessionCookie(response, await issueSession(session));
    return response;
  } catch (error) {
    return errorResponse(error);
  }
}
