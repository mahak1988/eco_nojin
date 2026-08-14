import '../styles/globals.css';
import { I18nProvider } from '../lib/i18n-context';
import LocaleAttributeSync from '../components/LocaleAttributeSync';
import type { Metadata, Viewport } from 'next';

export const metadata: Metadata = {
  title: 'Eco Nojin | HyDroMa',
  description: 'Intelligent platform for ecosystem restoration and smart agriculture',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'Eco Nojin',
  },
  icons: {
    icon: [
      { url: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
      { url: '/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
    ],
    apple: [
      { url: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
    ],
  },
};

export const viewport: Viewport = {
  themeColor: '#15803d',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // lang/dir below are SSR defaults. After hydration, LocaleAttributeSync
  // (client) sets them from the persisted/selected locale — see
  // lib/i18n-context.tsx. suppressHydrationWarning prevents React from
  // flagging the runtime attribute change.
  return (
    <html lang="en" dir="ltr" suppressHydrationWarning>
      <head>
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#15803d" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="Eco Nojin" />
      </head>
      <body>
        <I18nProvider>
          <LocaleAttributeSync />
          {children}
        </I18nProvider>
      </body>
    </html>
  );
}
