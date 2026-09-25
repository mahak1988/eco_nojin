import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';
import { currentUser, refreshSession } from '@/lib/bff/auth-service';
import { BffError, errorResponse } from '@/lib/bff/backend';
import { readSession, readSessionId, replaceSession } from '@/lib/session/session-cookie';

export async function GET(request: NextRequest): Promise<NextResponse> {
  const current = await readSession(request);
  if (!current) {
    return NextResponse.json({ user: null });
  }

  try {
    const user = await currentUser(current);
    return NextResponse.json({ user });
  } catch (error) {
    if (error instanceof BffError && error.status === 401) {
      try {
        const currentId = await readSessionId(request);
        if (!currentId) return NextResponse.json({ user: null }, { status: 401 });
        const session = await refreshSession(current);
        const response = NextResponse.json({ user: session.user });
        await replaceSession(response, currentId, session);
        return response;
      } catch (refreshError) {
        return errorResponse(refreshError);
      }
    }
    return errorResponse(error);
  }
}
