import createMiddleware from 'next-intl/middleware';
import { routing } from './i18n/routing';

export default createMiddleware(routing);

export const config = {
  // Skip API proxy, Next internals and static assets.
  matcher: ['/((?!api|_next|_vercel|.*\\..*).*)'],
};
