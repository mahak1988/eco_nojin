import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { SITE_URL as BASE_URL } from '@/config/site';
import { apiGet } from '@/lib/api/client';
import { DataStateCard, SourceFooter, toDataState } from '../../data-states';

const CITATIONS_PATH = '/api/v1/science/citations/index';

type CitationItem = {
  slug: string;
  name_fa: string;
  name_en: string;
  reference: string;
  citation: string;
  doi: string | null;
  note: string;
};

type CitationIndex = { count: number; items: CitationItem[] };

const TITLES: Record<string, string> = { fa: 'بازبینی همکاران', en: 'Peer Review' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'مرجع علمی ثبت‌شده برای هر مدل؛ سابقهٔ داوری منتشرشده‌ای وجود ندارد',
  en: 'Registered scientific reference per model; no published review record exists',
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
      url: `${BASE_URL}/${locale}/public/science/peer-review`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/science/peer-review`,
      languages: {
        fa: `${BASE_URL}/fa/public/science/peer-review`,
        en: `${BASE_URL}/en/public/science/peer-review`,
      },
    },
  };
}

export default async function PeerReviewPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const template = await getTranslations('market.template');
  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  const citations = await apiGet<CitationIndex>(CITATIONS_PATH);
  const items = citations.ok ? citations.data.items : [];
  const state = toDataState(CITATIONS_PATH, citations, items.length);

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={CITATIONS_PATH}
          label={title}
          verified={citations.ok}
          method={CITATIONS_PATH}
        >
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{CITATIONS_PATH}</h2>
        <DataStateCard state={state} />
        {state.kind === 'ready' ? (
          <div className="grid gap-4">
            {items.map((item) => (
              <Card key={item.slug} density="compact">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h3 className="font-medium text-ink">
                      {locale === 'fa' ? item.name_fa : item.name_en}
                    </h3>
                    <p className="mt-1 text-sm text-ink-soft">{item.reference}</p>
                    {item.note ? <p className="mt-1 text-xs text-ink-soft">{item.note}</p> : null}
                  </div>
                  <ProvenanceStamp
                    source={item.reference}
                    verified={Boolean(item.doi)}
                    method={item.slug}
                  />
                </div>
              </Card>
            ))}
          </div>
        ) : null}
        <SourceFooter state={state} />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{template('status')}</h2>
        <Card density="cozy">
          <h3 className="text-sm font-medium text-ink">{template('unavailableTitle')}</h3>
          <p className="mt-1 text-sm text-ink-soft">{template('unavailableDescription')}</p>
        </Card>
      </section>
    </main>
  );
}
