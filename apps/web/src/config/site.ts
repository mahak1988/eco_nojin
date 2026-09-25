/**
 * Canonical origin of the public site, shared by every page, layout and metadata
 * route. It is the single place allowed to read `NEXT_PUBLIC_SITE_URL`.
 */
export const SITE_URL_FALLBACK = 'https://app.eco-nojin.org';

function resolveSiteUrl(value: string | undefined): string {
  const configured = value?.trim();
  if (!configured) {
    return SITE_URL_FALLBACK;
  }
  return configured.replace(/\/+$/, '');
}

/** Absolute origin without a trailing slash, safe for `${SITE_URL}/path` joins. */
export const SITE_URL = resolveSiteUrl(process.env.NEXT_PUBLIC_SITE_URL);
