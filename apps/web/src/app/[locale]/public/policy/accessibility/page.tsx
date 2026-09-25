import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ListBlock } from '@/components/ListBlock';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

const TITLES: Record<string, string> = {
  fa: 'بیانیه دسترس‌پذیری',
  en: 'Accessibility Statement',
};
const DESCRIPTIONS: Record<string, string> = {
  fa: 'تعهد به WCAG 2.2 AA و وضعیت انطباق',
  en: 'Commitment to WCAG 2.2 AA and conformance status',
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
      url: `${BASE_URL}/${locale}/public/policy/accessibility`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/policy/accessibility`,
      languages: {
        fa: `${BASE_URL}/fa/public/policy/accessibility`,
        en: `${BASE_URL}/en/public/policy/accessibility`,
      },
    },
  };
}

export default async function AccessibilityPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('accessibility');
  const template = await getTranslations('market.template');
  const common = await getTranslations('common');
  const status = await getTranslations('statusLine');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <h1 className="display text-4xl font-bold text-ink">{t('title')}</h1>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('lead')}</p>
        <div className="mt-3 max-w-2xl text-sm text-ink-soft">{t('what')}</div>
        <div className="mt-3 max-w-2xl text-sm text-ink-soft">{t('audience')}</div>

        <div className="mt-6 grid gap-4">
          <ListBlock
            title={common('evidence')}
            items={t.raw('evidence') as string[]}
            tone="neutral"
          />
          <ListBlock title={common('limits')} items={t.raw('limits') as string[]} tone="clay" />
          <ListBlock title={common('next')} items={t.raw('next') as string[]} tone="moss" />
        </div>

        <section className="mt-8">
          <div className="flex flex-wrap items-center gap-4">
            <StatusDot state="down" label={status('unavailable')} />
            <ProvenanceStamp
              source={template('source')}
              label={template('source')}
              verified={false}
              method={template('method')}
            />
          </div>
          <Card density="cozy" className="mt-4">
            <h2 className="font-semibold text-ink">{template('unavailableTitle')}</h2>
            <p className="mt-2 text-sm text-ink-soft">{template('unavailableDescription')}</p>
          </Card>
        </section>
      </div>
    </main>
  );
}
