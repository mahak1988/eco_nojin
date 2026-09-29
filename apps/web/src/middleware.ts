import { type NextRequest, NextResponse } from 'next/server';
import createMiddleware from 'next-intl/middleware';
import { routing } from './i18n/routing';

const handleIntl = createMiddleware(routing);

/** Paths that never carry a locale prefix and never produce a public response. */
const PRIVATE_PATHS = /^\/(api|health|ready)(\/|$)/;

/**
 * Adds the private-response headers the BFF owes its callers.
 *
 * `PWA_AND_OFFLINE.md` sets a release gate: a response carrying private data, a
 * `Set-Cookie`, or `no-store` semantics must not be storable. The BFF route
 * handlers were answering without a `Cache-Control` header at all, so the
 * guarantee existed only in the service worker matcher and not on the wire — a
 * shared cache between the reader and the next reader could hold a session
 * payload. `no-store` is set here rather than in each handler so a new BFF route
 * cannot forget it.
 *
 * These paths were previously outside the middleware matcher entirely, which is
 * why the headers were missing; the matcher now includes them and delegates the
 * locale handling to the paths that actually need it.
 */
export default function middleware(request: NextRequest) {
  if (PRIVATE_PATHS.test(request.nextUrl.pathname)) {
    const response = NextResponse.next();
    response.headers.set('Cache-Control', 'no-store, max-age=0');
    response.headers.set('Pragma', 'no-cache');
    return response;
  }
  return handleIntl(request);
}

export const config = {
  // Locale pages plus the private paths, whose responses need the headers above.
  matcher: ['/((?!_next|_vercel|.*\\..*).*)'],
};
