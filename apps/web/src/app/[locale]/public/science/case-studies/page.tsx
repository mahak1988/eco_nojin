import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

const CITATIONS_PATH = '/api/v1/science/citations/index';

type CitationIndex = { count: number };

const TITLES: Record<string, string> = { fa: 'مطالعات موردی', en: 'Case Studies' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'مطالعات موردی واقعی با مدل‌های هیدروما',
  en: 'Real-world case studies with HydroMa models',
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
      url: `${BASE_URL}/${locale}/public/science/case-studies`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/science/case-studies`,
      languages: {
        fa: `${BASE_URL}/fa/public/science/case-studies`,
        en: `${BASE_URL}/en/public/science/case-studies`,
      },
    },
  };
}

export default async function CaseStudiesPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('statusLine');
  const template = await getTranslations('market.template');
  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  // The gateway publishes no field case-study registry, so no case, outcome
  // figure or DOI is rendered here.
  const citations = await apiGet<CitationIndex>(CITATIONS_PATH);

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={CITATIONS_PATH}
          label={title}
          verified={citations.ok}
          method={template('method')}
        >
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{template('source')}</h2>
        <Card density="compact">
          <h3 className="text-sm font-medium text-ink">{template('unavailableTitle')}</h3>
          <p className="mt-1 text-sm text-ink-soft">{template('unavailableDescription')}</p>
          <p className="mt-3 text-xs text-ink-soft">
            {template('method')} · {t('unavailable')}
          </p>
        </Card>
        <p className="mt-6 text-xs text-ink-soft">{t('realData')}</p>
      </section>
    </main>
  );
}
