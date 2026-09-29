import type { Metadata, Viewport } from 'next';
import { notFound } from 'next/navigation';
import { hasLocale, NextIntlClientProvider } from 'next-intl';
import { getMessages, setRequestLocale } from 'next-intl/server';
import { Providers } from '@/components/Providers';
import { OfflineProvider } from '@/components/providers/OfflineProvider';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { OfflineBanner } from '@/components/ui/OfflineBanner';
import { WebVitals } from '@/components/WebVitals';
import { isRtl, routing } from '@/i18n/routing';
import '../globals.css';
import { SITE_URL as BASE_URL } from '@/config/site';

/**
 * Script font sheets, one per locale that reads a script the three families in
 * `globals.css` do not carry.
 *
 * These rules used to live in `globals.css`, where every page in all fourteen
 * locales downloaded them: `Noto Sans SC` alone is 97 `@font-face` rules with
 * disjoint `unicode-range`s, 18.7 kB brotli of rule text that a page in `de`
 * can never use. They are in `public/styles/fonts/<locale>.css` now, and this
 * layout links the one file the current locale needs — ten of the fourteen
 * locales get no extra request at all.
 *
 * A `<link>` rather than an `import`: CSS imports are resolved at build time,
 * so a static import in this layout would put all four sheets in the one
 * stylesheet every locale loads, which is the thing being fixed. The cost is a
 * second render-blocking request on four locales out of fourteen; the preload
 * scanner starts it in the same batch as `globals.css` (both `<link>`s are in
 * this `<head>`), and `font-display: swap` means the extra request delays which
 * face is chosen, never legibility. No `preload` hint is added: the link is
 * already in the first bytes of the document, and preloading a stylesheet that
 * is also linked buys nothing but a second HTML element to keep in step.
 *
 * Cascade order is irrelevant here — these files contain only `@font-face`
 * rules, which do not participate in the cascade — so React's `precedence`
 * float is deliberately not used.
 */
const SCRIPT_FONT_SHEET: Partial<Record<(typeof routing.locales)[number], string>> = {
  hi: '/styles/fonts/hi.css',
  bn: '/styles/fonts/bn.css',
  zh: '/styles/fonts/zh.css',
  ur: '/styles/fonts/ur.css',
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#f6f5ef' },
    { media: '(prefers-color-scheme: dark)', color: '#0e1a1e' },
  ],
};

// Every page is bound to live backend data, so nothing is prerendered at build time.
export const dynamic = 'force-dynamic';

async function getLocaleMetadata(locale: string): Promise<Metadata> {
  const messages = await getMessages();
  const localeUrl = `${BASE_URL}/${locale}`;

  // The title template and the root description used to be Persian literals, so
  // every locale's `<title>` ended in `· هیدروما نوژین` and every locale's
  // fallback description was Persian — visible to a reader of `/zh/public/why` as
  // a correct page heading followed by a Persian document description. Both now
  // come from the catalogue, which every locale fills in.
  const brandName =
    typeof messages.brand?.name === 'string' && messages.brand.name
      ? messages.brand.name
      : 'Hydroma Nojin';
  const brandDescription =
    typeof messages.brand?.description === 'string' && messages.brand.description
      ? messages.brand.description
      : undefined;

  return {
    metadataBase: new URL(BASE_URL),
    title: {
      default: brandName,
      template: `%s · ${brandName}`,
    },
    description: brandDescription,
    applicationName: 'Eco Nojin',
    formatDetection: { telephone: false },
    alternates: {
      canonical: localeUrl,
      languages: Object.fromEntries(routing.locales.map((loc) => [loc, `${BASE_URL}/${loc}`])),
    },
    openGraph: {
      type: 'website',
      locale,
      url: localeUrl,
      siteName: 'Eco Nojin',
      title: messages.brand?.name ?? 'HyDroMa / هیدروما نوژین',
      description: 'مدیریت هوشمند مَنظر برای احیای آب، خاک و معیشت',
      images: [
        {
          url: `${BASE_URL}/og-image.png`,
          width: 1200,
          height: 630,
          alt: 'Eco Nojin - Smart Landscape Management',
        },
      ],
    },
    twitter: {
      card: 'summary_large_image',
      title: messages.brand?.name ?? 'Eco Nojin',
      description: 'Smart landscape management for restoring water, soil and livelihoods',
      images: [`${BASE_URL}/og-image.png`],
    },
    robots: {
      index: true,
      follow: true,
    },
  };
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  if (!hasLocale(routing.locales, locale)) return {};
  setRequestLocale(locale);
  return getLocaleMetadata(locale);
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!hasLocale(routing.locales, locale)) notFound();
  setRequestLocale(locale);
  const messages = await getMessages();

  const skipLabel =
    typeof messages.a11y?.skipToContent === 'string'
      ? messages.a11y.skipToContent
      : 'Skip to main content';

  const scriptFontSheet = SCRIPT_FONT_SHEET[locale as (typeof routing.locales)[number]];

  return (
    <html lang={locale} dir={isRtl(locale) ? 'rtl' : 'ltr'}>
      <head>
        {/*
          Only `x-default` belongs here. A layout cannot know the path it is
          rendering, so a per-locale cluster emitted from this level advertised
          the *home* page as the alternate for every deep URL — 240 of the 241
          pages were declaring their translations as `/{locale}`. Each page now
          supplies its own cluster through `languageAlternates`, and
          `check-page-meta.mjs` fails if a page hand-writes a two-locale one.
        */}
        <link rel="alternate" hrefLang="x-default" href={BASE_URL} />
        {scriptFontSheet ? <link rel="stylesheet" href={scriptFontSheet} /> : null}
      </head>
      <body className="flex min-h-dvh flex-col">
        <a href="#main-content" className="skip-link">
          {skipLabel}
        </a>
        <div id="main-content" tabIndex={-1}>
          <OfflineBanner />
          <OfflineProvider>
            <WebVitals />
            <ErrorBoundary>
              <Providers>
                <NextIntlClientProvider messages={messages}>{children}</NextIntlClientProvider>
              </Providers>
            </ErrorBoundary>
          </OfflineProvider>
        </div>
      </body>
    </html>
  );
}
