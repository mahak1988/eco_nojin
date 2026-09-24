'use client';

import { useEffect, useState } from 'react';
import { LocaleSwitcher } from '@/components/LocaleSwitcher';
import { Link } from '@/i18n/navigation';

interface Translations {
  cover: {
    subtitle: string;
    slogan: string;
    quote: string;
    enterPublic: string;
    enterMarketplace: string;
    languageLabel: string;
  };
  common: {
    machineTranslatedNotice: string;
  };
}

interface CoverPageProps {
  locale: string;
  t: Translations;
  meta: { machineTranslated: boolean; fallbackLocale: string | null };
}

const colors = [
  'text-water',
  'text-forest',
  'text-copper',
  'text-ink',
  'text-amber',
  'text-emerald',
];

export default function CoverPageClient({ locale, t, meta }: CoverPageProps) {
  const [colorIndex, setColorIndex] = useState(0);

  // Cycle colors every 2 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setColorIndex((prev) => (prev + 1) % colors.length);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <main className="min-h-dvh w-full flex flex-col items-center justify-center px-4 relative overflow-hidden">
      {/* Animated background */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute inset-0 bg-gradient-to-br from-surface via-surface-2 to-water/10" />
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-water/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-forest/20 rounded-full blur-3xl animate-pulse delay-1000" />
        <div className="absolute top-1/2 left-1/2 w-72 h-72 bg-copper/15 rounded-full blur-3xl animate-pulse delay-2000" />
      </div>

      <div className="contour w-full max-w-none text-center flex-1 flex flex-col items-center justify-center relative z-10">
        <header className="flex items-center justify-between gap-4 w-full px-6 py-6">
          <span className="font-semibold tracking-tight text-ink animate-fade-in-down">
            هیدروما نوژین
          </span>
          <LocaleSwitcher current={locale} label={t.cover.languageLabel} />
        </header>

        <section className="w-full px-6 pb-16 pt-10 flex-1 flex flex-col items-center justify-center">
          <h1
            className={`display text-5xl font-bold leading-tight sm:text-6xl ${colors[colorIndex]} animate-fade-in`}
          >
            هیدروما نوژین
          </h1>

          <p className="mt-4 max-w-2xl text-lg text-ink-soft mx-auto animate-fade-in-up delay-200">
            {t.cover.subtitle}
          </p>

          <p className="mt-6 max-w-2xl text-base text-ink mx-auto animate-fade-in-up delay-400">
            {t.cover.slogan}
          </p>

          <blockquote className="mt-8 max-w-2xl border-s-2 border-water/60 ps-4 text-sm text-ink-soft mx-auto animate-fade-in-up delay-600">
            {t.cover.quote}
          </blockquote>

          {meta.machineTranslated && (
            <p className="mt-4 inline-block rounded-full border border-line px-3 py-1 text-xs text-ink-soft animate-fade-in-up delay-800">
              {t.common.machineTranslatedNotice}
            </p>
          )}

          <div className="mt-10 flex flex-wrap gap-3 justify-center animate-fade-in-up delay-1000">
            <Link
              href="/home"
              className="rounded-[var(--radius-card)] bg-water px-5 py-3 text-sm font-semibold text-white hover:opacity-90 hover:scale-105 transition-all duration-300 shadow-lg shadow-water/30"
            >
              {t.cover.enterPublic}
            </Link>
            <Link
              href="/market"
              className="rounded-[var(--radius-card)] border border-line px-5 py-3 text-sm text-ink hover:bg-surface hover:scale-105 transition-all duration-300"
            >
              {t.cover.enterMarketplace}
            </Link>
          </div>
        </section>
      </div>

      <style jsx>{`
        @keyframes fade-in-down {
          from { opacity: 0; transform: translateY(-20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes fade-in-up {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes fade-in {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        .animate-fade-in-down { animation: fade-in-down 0.6s ease-out forwards; }
        .animate-fade-in-up { animation: fade-in-up 0.6s ease-out forwards; opacity: 0; }
        .animate-fade-in { animation: fade-in 0.8s ease-out forwards; }
        .delay-200 { animation-delay: 200ms; }
        .delay-400 { animation-delay: 400ms; }
        .delay-600 { animation-delay: 600ms; }
        .delay-800 { animation-delay: 800ms; }
        .delay-1000 { animation-delay: 1000ms; }
        .delay-2000 { animation-delay: 2000ms; }
      `}</style>
    </main>
  );
}
