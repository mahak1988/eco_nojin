import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { PwaUpdatePanel } from '@/components/system/PwaUpdatePanel';
import { type RecoveryLinkItem, RecoveryLinks } from '@/components/system/RecoveryLinks';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import {
  LIVE_LABEL_KEY,
  METRIC_LABEL_KEY,
  RESULT_LABEL_KEY,
  STATE_LABEL_KEY,
  SYSTEM_PWA_UPDATE_ROUTE,
  UNAVAILABLE_LABEL_KEY,
} from '@/lib/domains/registry';

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return {
    title: t(SYSTEM_PWA_UPDATE_ROUTE.headingKey),
    description: t('offline.description'),
    robots: { index: false, follow: false },
    alternates: {
      canonical: canonicalFor(locale, '/system/pwa-update'),
      languages: languageAlternates('/system/pwa-update'),
    },
  };
}

export default async function PwaUpdatePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  const recovery: RecoveryLinkItem[] = [
    {
      href: '/system',
      label: t('statusPage.service'),
      detail: t('statusPage.subtitle'),
      token: '/system',
    },
    {
      href: '/offline',
      label: t('offline.title'),
      detail: t('offline.description'),
      token: '/offline',
    },
    { href: '/help', label: t('public.channels.title'), token: '/help' },
  ];

  return (
    <main id="main" className="mx-auto max-w-4xl px-6 py-12">
      <header>
        <span className="chip num font-mono">system/pwa-update</span>
        <h1 className="display mt-3 text-3xl font-bold text-ink sm:text-4xl">
          {t(SYSTEM_PWA_UPDATE_ROUTE.headingKey)}
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-ink-soft">{t('offline.description')}</p>
        <p className="num mt-2 text-xs text-ink-faint">
          <code>src/app/sw.ts</code> · <code>skipWaiting: true</code> ·{' '}
          <code>clientsClaim: true</code>
        </p>
      </header>

      <PwaUpdatePanel
        locale={locale}
        labels={{
          metric: t(METRIC_LABEL_KEY),
          state: t(STATE_LABEL_KEY),
          result: t(RESULT_LABEL_KEY),
          rows: t('statusPage.rows'),
          live: t(LIVE_LABEL_KEY),
          unavailable: t(UNAVAILABLE_LABEL_KEY),
          planned: t('common.planned'),
          error: t('common.error'),
        }}
      />

      <div className="mt-8">
        <RecoveryLinks
          links={recovery}
          heading={t('common.nextLabel')}
          headingId="pwa-recovery"
          viewLabel={t('common.view')}
        />
      </div>
    </main>
  );
}
