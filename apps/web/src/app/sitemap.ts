import type { MetadataRoute } from 'next';
import { locales } from '@/i18n/routing';

const BASE = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

export const dynamic = 'force-static';

/**
 * Per-locale sitemap — one entry per route × 14 locales, each with an
 * hreflang alternate block (master plan §۰.5).
 */
export default function sitemap(): MetadataRoute.Sitemap {
  const routes = [
    '',
    '/home',
    '/about',
    '/statements',
    '/platform',
    '/services',
    '/evidence',
    '/learn',
    '/ai',
    '/trust',
    '/developers',
    '/legal',
    '/accessibility',
    '/hydroma',
    '/market',
    '/status',
  ];
  return locales.flatMap((locale) =>
    routes.map((route) => ({
      url: `${BASE}/${locale}${route}`,
      lastModified: new Date(),
      changeFrequency: 'daily' as const,
      priority: route === '' ? 1 : 0.7,
      alternates: {
        languages: Object.fromEntries(locales.map((alt) => [alt, `${BASE}/${alt}${route}`])),
      },
    })),
  );
}
