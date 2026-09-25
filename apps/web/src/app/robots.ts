import type { MetadataRoute } from 'next';
import { SITE_URL as BASE } from '@/config/site';

export const dynamic = 'force-static';

export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: '*', allow: '/' },
    sitemap: `${BASE}/sitemap.xml`,
  };
}
