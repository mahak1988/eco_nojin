import type { Metadata, Viewport } from "next";
import { I18nProvider } from "../lib/i18n-context";
import { FontLanguageProvider } from '../components/FontLanguageProvider';

import { ThemeProvider } from "../lib/theme-context";
import { AuthProvider } from "../lib/auth-context";
import { FarmProvider } from "../lib/farm-context";
import "./globals.css";

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
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="apple-touch-icon" href="/icon.svg" />
      </head>
      <body>
        <FontLanguageProvider>
        <ThemeProvider>
          <AuthProvider>
          <FarmProvider>
          <I18nProvider>
            {children}
          </I18nProvider>
          </FarmProvider>
        </AuthProvider>
        </ThemeProvider>
              </FontLanguageProvider>
      </body>
    </html>
  );
}
