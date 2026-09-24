import type { Metadata, Viewport } from 'next';
import { notFound } from 'next/navigation';
import { hasLocale, NextIntlClientProvider } from 'next-intl';
import { getMessages, setRequestLocale } from 'next-intl/server';
import { isRtl, routing } from '@/i18n/routing';
import '../globals.css';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

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

  const localeUrl = `${BASE_URL}/${locale}`;

  const metadata: Metadata = {
    title: {
      default: messages.brand?.name ?? 'HyDroMa / هیدروما نوژین',
      template: '%s · هیدروما نوژین',
    },
    description: 'مدیریت هوشمند مَنظر برای احیای آب، خاک و معیشت',
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

  return (
    <html lang={locale} dir={isRtl(locale) ? 'rtl' : 'ltr'}>
      <head>
        <link rel="alternate" hrefLang="x-default" href={BASE_URL} />
        {routing.locales.map((loc) => (
          <link key={loc} rel="alternate" hrefLang={loc} href={`${BASE_URL}/${loc}`} />
        ))}
      </head>
      <body className="flex min-h-dvh flex-col">
        <NextIntlClientProvider messages={messages}>{children}</NextIntlClientProvider>
      </body>
    </html>
  );
}
