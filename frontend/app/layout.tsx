import type { Metadata, Viewport } from "next";
import { I18nProvider } from "../lib/i18n-context";
import { FontLanguageProvider } from '../components/FontLanguageProvider';
import SwRegister from '../components/SwRegister';
import Navigation from '../components/Navigation';

import { ThemeProvider } from "../lib/theme-context";
import { AuthProvider } from "../lib/auth-context";
import { FarmProvider } from "../lib/farm-context";
import { Providers } from "./providers";
import { CommandPalette } from "@/components/site/CommandPalette";
import { SkipLink } from "../components/SkipLink";
import "./globals.css";
import LocaleAttributeSync from '../components/LocaleAttributeSync';

export const metadata: Metadata = {
  title: "Eco Nojin - Intelligent Platform for Ecosystem Restoration",
  description: "Democratizing access to agricultural science for 2.5 billion farmers",
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#f9fafb' },
    { media: '(prefers-color-scheme: dark)', color: '#0a0f1c' },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fa" dir="rtl" data-scroll-behavior="smooth" suppressHydrationWarning>
      <head>
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="apple-touch-icon" href="/icon.svg" />
        <link rel="manifest" href="/manifest.json" />
      </head>
      <body>
        <FontLanguageProvider>
          <SwRegister />
          <ThemeProvider>
            <AuthProvider>
              <FarmProvider>
                <I18nProvider>
                  <LocaleAttributeSync />
                  <Providers>
                    <SkipLink />
                    <Navigation />
                    <div id="main-content" tabIndex={-1} style={{ outline: 'none' }}>
                      {children}
                    </div>
                  </Providers>
                  <CommandPalette />
                </I18nProvider>
              </FarmProvider>
            </AuthProvider>
          </ThemeProvider>
        </FontLanguageProvider>
      </body>
    </html>
  );
}