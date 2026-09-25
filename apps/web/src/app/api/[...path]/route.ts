import { type NextRequest, NextResponse } from 'next/server';
import { refreshSession } from '@/lib/bff/auth-service';
import { assertBffRequest, backendRequest, errorResponse } from '@/lib/bff/backend';
import {
  clearSessionCookie,
  readSession,
  readSessionId,
  replaceSession,
  type SessionRecord,
} from '@/lib/session/session-cookie';

export const dynamic = 'force-dynamic';

type RouteContext = { params: Promise<{ path: string[] }> };

const forwardedHeaders = [
  'accept',
  'accept-language',
  'content-type',
  'if-match',
  'if-none-match',
  'x-idempotency-key',
  'x-request-id',
];

function requestHeaders(request: NextRequest, session: SessionRecord | null): Headers {
  const headers = new Headers();
  for (const name of forwardedHeaders) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  if (session) headers.set('Authorization', `Bearer ${session.accessToken}`);
  return headers;
}

function proxyResponse(upstream: Response): NextResponse {
  const headers = new Headers();
  for (const name of ['content-type', 'content-disposition', 'x-request-id']) {
    const value = upstream.headers.get(name);
    if (value) headers.set(name, value);
  }
  headers.set('Cache-Control', 'private, no-store');
  return new NextResponse(upstream.body, { status: upstream.status, headers });
}

async function handle(request: NextRequest, context: RouteContext): Promise<NextResponse> {
  try {
    assertBffRequest(request);
    const { path } = await context.params;
    if (path[0] === 'v1' && path[1] === 'auth') {
      return NextResponse.json({ error: 'Not found' }, { status: 404 });
    }

    const encodedPath = path.map((segment) => encodeURIComponent(segment)).join('/');
    const target = `/api/${encodedPath}${request.nextUrl.search}`;
    const body =
      request.method === 'GET' || request.method === 'HEAD'
        ? undefined
        : await request.arrayBuffer();
    const sessionId = await readSessionId(request);
    let session = await readSession(request);
    let refreshed = false;
    let upstream = await backendRequest(target, {
      method: request.method,
      headers: requestHeaders(request, session),
      body: body?.byteLength ? body : undefined,
    });

    if (upstream.status === 401 && session) {
      try {
        session = await refreshSession(session);
        refreshed = true;
        upstream = await backendRequest(target, {
          method: request.method,
          headers: requestHeaders(request, session),
          body: body?.byteLength ? body : undefined,
        });
      } catch {
        const response = NextResponse.json({ error: 'Session expired' }, { status: 401 });
        await clearSessionCookie(response, sessionId);
        return response;
      }
    }

    const response = proxyResponse(upstream);
    if (refreshed && sessionId && session) await replaceSession(response, sessionId, session);
    return response;
  } catch (error) {
    return errorResponse(error);
  }
}

export const GET = handle;
export const POST = handle;
export const PUT = handle;
export const PATCH = handle;
export const DELETE = handle;
