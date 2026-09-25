import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ListBlock } from '@/components/ListBlock';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

const TITLES: Record<string, string> = { fa: 'گزارش شفافیت', en: 'Transparency Report' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'گزارش سالانه از منبع زنده منتشر نشده است؛ بنابراین هیچ عدد، نمودار یا سالی نمایش داده نمی‌شود.',
  en: 'The annual report is not served from a live source, so no figure, chart or year is shown.',
};

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  return {
    title: TITLES[locale] ?? TITLES.en,
    description: DESCRIPTIONS[locale] ?? DESCRIPTIONS.en,
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/trust/report`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/trust/report`,
      languages: {
        fa: `${BASE_URL}/fa/trust/report`,
        en: `${BASE_URL}/en/trust/report`,
      },
    },
  };
}

export default async function ReportPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('trust');
  const common = await getTranslations('common');
  const status = await getTranslations('statusLine');
  const template = await getTranslations('market.template');
  const title = TITLES[locale] ?? TITLES.en;

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('lead')}</p>

        <div className="mt-6 flex flex-wrap items-center gap-4">
          <StatusDot state="down" label={status('unavailable')} />
          <ProvenanceStamp
            source={template('source')}
            label={template('source')}
            verified={false}
            method={template('method')}
          />
        </div>

        <Card density="cozy" className="mt-6">
          <h2 className="font-semibold text-ink">{template('unavailableTitle')}</h2>
          <p className="mt-2 text-sm text-ink-soft">{template('unavailableDescription')}</p>
        </Card>

        <div className="mt-6 grid gap-4">
          <ListBlock title={common('limits')} items={t.raw('limits') as string[]} tone="clay" />
          <ListBlock title={common('next')} items={t.raw('next') as string[]} tone="moss" />
        </div>
      </div>
    </main>
  );
}
