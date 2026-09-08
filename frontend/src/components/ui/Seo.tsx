import { useEffect } from 'react';

interface SeoProps {
  /** Full document title, e.g. "پلتفرم | اکو نوژین". */
  title: string;
  description?: string;
  /** Route path used for canonical + og:url (joined with the site origin). */
  path?: string;
  /** Optional JSON-LD object injected as a script tag (e.g. FAQPage). */
  jsonLd?: Record<string, unknown>;
}

const SITE_ORIGIN = 'https://econojin.org';

function upsertMeta(attr: 'name' | 'property', key: string, content: string): void {
  let tag = document.head.querySelector<HTMLMetaElement>(`meta[${attr}="${key}"]`);
  if (!tag) {
    tag = document.createElement('meta');
    tag.setAttribute(attr, key);
    document.head.appendChild(tag);
  }
  tag.setAttribute('content', content);
}

function upsertCanonical(href: string): void {
  let link = document.head.querySelector<HTMLLinkElement>('link[rel="canonical"]');
  if (!link) {
    link = document.createElement('link');
    link.setAttribute('rel', 'canonical');
    document.head.appendChild(link);
  }
  link.setAttribute('href', href);
}

/**
 * Per-page SEO: title, description, canonical and Open Graph tags.
 * Optional JSON-LD is injected with a data attribute so it can be cleaned up.
 */
export default function Seo({ title, description, path, jsonLd }: SeoProps) {
  useEffect(() => {
    document.title = title;

    if (description) {
      upsertMeta('name', 'description', description);
      upsertMeta('property', 'og:description', description);
    }
    upsertMeta('property', 'og:title', title);
    upsertMeta('property', 'og:type', 'website');
    upsertMeta('property', 'og:site_name', 'Eco Nojin');
    upsertMeta('property', 'og:image', `${SITE_ORIGIN}/og.png`);

    const url = `${SITE_ORIGIN}${path ?? window.location.pathname}`;
    upsertMeta('property', 'og:url', url);
    upsertCanonical(url);

    let script: HTMLScriptElement | null = null;
    if (jsonLd) {
      script = document.createElement('script');
      script.type = 'application/ld+json';
      script.setAttribute('data-seo-jsonld', 'true');
      script.textContent = JSON.stringify(jsonLd);
      document.head.appendChild(script);
    }

    return () => {
      script?.remove();
    };
  }, [title, description, path, jsonLd]);

  return null;
}
