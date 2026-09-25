import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

const TITLES: Record<string, string> = { fa: 'تأثیر', en: 'Impact' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'شاخص‌های تأثیر پلتفرم',
  en: 'Platform impact metrics',
};

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
      url: `${BASE_URL}/${locale}/public/goals/impact`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/goals/impact`,
      languages: {
        fa: `${BASE_URL}/fa/public/goals/impact`,
        en: `${BASE_URL}/en/public/goals/impact`,
      },
    },
  };
}

export default async function ImpactPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.template');
  const status = await getTranslations('statusLine');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <h1 className="display text-4xl font-bold text-ink">{TITLES[locale] ?? TITLES.en}</h1>
        <div className="mt-6 flex flex-wrap items-center gap-4">
          <StatusDot state="down" label={status('unavailable')} />
          <ProvenanceStamp
            source={t('source')}
            label={t('source')}
            verified={false}
            method={t('method')}
          />
        </div>
        <Card density="cozy" className="mt-6">
          <h2 className="font-semibold text-ink">{t('unavailableTitle')}</h2>
          <p className="mt-2 text-sm text-ink-soft">{t('unavailableDescription')}</p>
        </Card>
        <div className="mt-6 grid gap-3 md:grid-cols-2">
          <div className="rounded-md border border-line p-4">
            <h3 className="font-medium text-ink">{t('contractTitle')}</h3>
            <p className="mt-1 text-sm text-ink-soft">{t('contractDescription')}</p>
          </div>
          <div className="rounded-md border border-line p-4">
            <h3 className="font-medium text-ink">{t('nextTitle')}</h3>
            <p className="mt-1 text-sm text-ink-soft">{t('nextDescription')}</p>
          </div>
        </div>
      </div>
    </main>
  );
}
