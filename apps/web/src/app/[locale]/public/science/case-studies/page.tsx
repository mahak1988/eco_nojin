import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { canonicalFor, languageAlternates } from '@/config/alternates';
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

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('pageMeta.public-science-case-studies');
  return {
    title: meta('title'),
    description: meta('description'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/public/science/case-studies`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/public/science/case-studies'),
      languages: languageAlternates('/public/science/case-studies'),
    },
  };
}

export default async function CaseStudiesPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  const meta = await getTranslations('pageMeta.public-science-case-studies');
  const status = await getTranslations('statusLine');
  const template = await getTranslations('market.template');
  const common = await getTranslations('common');
  const title = meta('title');
  const description = meta('description');

  const citations = await apiGet<CitationIndex>(CITATIONS_PATH);
  const items = citations.ok ? citations.data.items : [];
  const state = toDataState(CITATIONS_PATH, citations, items.length);

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
          <ProvenanceStamp
            source={CITATIONS_PATH}
            label={title}
            verified={citations.ok}
            method={CITATIONS_PATH}
          />
        </div>
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
                    <p className="mt-1 text-xs text-ink-soft">{item.citation}</p>
                    {item.note ? <p className="mt-1 text-xs text-ink-soft">{item.note}</p> : null}
                  </div>
                  <ProvenanceStamp
                    source={item.reference}
                    verified={Boolean(item.doi)}
                    method={item.slug}
                    label={item.doi ?? status('unavailable')}
                  />
                </div>
              </Card>
            ))}
          </div>
        ) : null}
        <SourceFooter state={state} />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{common('limits')}</h2>
        <Card density="compact">
          <h3 className="text-sm font-medium text-ink">{template('unavailableTitle')}</h3>
          <p className="mt-1 text-sm text-ink-soft">{template('unavailableDescription')}</p>
        </Card>
      </section>
    </main>
  );
}
