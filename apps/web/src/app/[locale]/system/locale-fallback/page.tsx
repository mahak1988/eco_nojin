import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { StatusDot } from '@/components/StatusDot';
import { LocaleFallbackChain } from '@/components/system/LocaleFallbackChain';
import { LocaleSelector } from '@/components/system/LocaleSelector';
import { type RecoveryLinkItem, RecoveryLinks } from '@/components/system/RecoveryLinks';
import { RefreshStateButton } from '@/components/system/RefreshStateButton';
import { SITE_URL as BASE_URL } from '@/config/site';
import {
  LIVE_LABEL_KEY,
  METRIC_LABEL_KEY,
  RESULT_LABEL_KEY,
  STATE_LABEL_KEY,
  UNAVAILABLE_LABEL_KEY,
} from '@/lib/domains/registry';
import { getLocaleFallbackReport } from './catalogue';

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
    title: t('cover.languageLabel'),
    description: t('statusPage.subtitle'),
    robots: { index: false, follow: false },
    alternates: {
      canonical: `${BASE_URL}/${locale}/system/locale-fallback`,
      languages: {
        fa: `${BASE_URL}/fa/system/locale-fallback`,
        en: `${BASE_URL}/en/system/locale-fallback`,
      },
    },
  };
}

export default async function LocaleFallbackPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  const report = await getLocaleFallbackReport(locale);
  const notice = report.machineTranslated ? t('common.machineTranslatedNotice') : null;

  const recovery: RecoveryLinkItem[] = [
    {
      href: '/system',
      label: t('statusPage.service'),
      detail: t('statusPage.subtitle'),
      token: '/system',
    },
    { href: '/system/pwa-update', label: t('public.channels.webPwa'), token: '/system/pwa-update' },
    { href: '/help', label: t('public.channels.title'), token: '/help' },
  ];

  return (
    <main id="main" className="mx-auto max-w-4xl px-6 py-12">
      <header>
        <span className="chip num font-mono">system/locale-fallback</span>
        <h1 className="display mt-3 text-3xl font-bold text-ink sm:text-4xl">
          {t('cover.languageLabel')}
        </h1>
        <p className="num mt-2 max-w-2xl text-xs text-ink-soft">
          {t('market.template.source')}: <code>src/lib/i18n/messages.ts</code> ·{' '}
          <code>{locale} → en</code>
        </p>
        <div className="mt-4 flex flex-wrap items-center gap-4">
          <StatusDot
            state={report.machineTranslated ? 'warn' : 'ok'}
            label={report.machineTranslated ? t('common.planned') : t(LIVE_LABEL_KEY)}
          />
          <span className="num text-xs text-ink-faint">
            {report.current} → en
            {report.fallbackLocale ? ` · ${report.fallbackLocale}` : null}
          </span>
        </div>
      </header>

      <section className="card mt-6 p-5" aria-labelledby="locale-selector-heading">
        <h2 id="locale-selector-heading" className="field-label">
          {t('cover.languageLabel')}
        </h2>
        <LocaleSelector
          current={locale}
          label={t('cover.languageLabel')}
          actionLabel={t('common.view')}
        />
      </section>

      <div className="mt-6">
        <LocaleFallbackChain
          merge={report.merge}
          origin={report.origin}
          steps={report.steps}
          coverage={report.coverage.map((row) => ({
            locale: row.locale,
            ownKeys: row.ownKeys,
            effectiveKeys: row.effectiveKeys,
            fromEnglish: row.fromEnglish,
            current: row.locale === report.current,
          }))}
          notice={notice}
          labels={{
            metric: t(METRIC_LABEL_KEY),
            state: t(STATE_LABEL_KEY),
            result: t(RESULT_LABEL_KEY),
            total: t('common.total'),
            language: t('cover.languageLabel'),
            unavailable: t(UNAVAILABLE_LABEL_KEY),
          }}
        />
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <RefreshStateButton label={t('common.retry')} />
        <span className="num text-xs text-ink-faint">{report.origin}</span>
      </div>

      <div className="mt-6">
        <RecoveryLinks
          links={recovery}
          heading={t('common.nextLabel')}
          headingId="locale-fallback-recovery"
          viewLabel={t('common.view')}
        />
      </div>
    </main>
  );
}
