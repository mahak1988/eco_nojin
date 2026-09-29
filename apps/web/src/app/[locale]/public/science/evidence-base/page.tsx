import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
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

type CitationIndex = {
  count: number;
  items: CitationItem[];
};

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('pageMeta.public-science-evidence-base');
  return {
    title: meta('title'),
    description: meta('description'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/public/science/evidence-base`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/public/science/evidence-base'),
      languages: languageAlternates('/public/science/evidence-base'),
    },
  };
}

export default async function EvidenceBasePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);

  const _meta = await getTranslations('pageMeta.public-science-evidence-base');
  const t = await getTranslations('public.science.evidenceBase');
  const common = await getTranslations('common');
  const status = await getTranslations('statusLine');

  const citations = await apiGet<CitationIndex>(CITATIONS_PATH);
  const items = citations.ok ? citations.data.items : [];
  const state = toDataState(CITATIONS_PATH, citations, items.length);

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="display text-4xl font-bold text-ink">{t('title')}</h1>
          <ProvenanceStamp
            source={CITATIONS_PATH}
            label={t('provenanceLabel')}
            verified={citations.ok}
            method={CITATIONS_PATH}
          />
        </div>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('lead')}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <FivePart
          headingLevel={2}
          title={t('whatTitle')}
          lead={t('whatLead')}
          what={t('whatDesc')}
          audience={t('audience')}
          evidence={t.raw('evidenceItems') as string[]}
          limits={t.raw('limitsItems') as string[]}
          next={t.raw('nextItems') as string[]}
          evidenceLabel={common('evidenceLabel')}
          limitsLabel={common('limitsLabel')}
          nextLabel={common('nextLabel')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('evidenceCatalog')}</h2>
        <DataStateCard
          state={state}
          emptyTitle={t('emptyTitle')}
          emptyDescription={t('emptyDesc')}
        />
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
                    <p className="mt-1 flex items-center gap-2 text-xs text-ink-soft">
                      <span>DOI</span>
                      {item.doi ? (
                        <code className="font-mono">{item.doi}</code>
                      ) : (
                        <StatusDot state="warn" label={status('unavailable')} />
                      )}
                    </p>
                    {item.note ? <p className="mt-1 text-xs text-ink-soft">{item.note}</p> : null}
                  </div>
                  <ProvenanceStamp
                    source={item.reference}
                    verified={Boolean(item.doi)}
                    method={item.slug}
                    label={item.doi ? item.doi : undefined}
                  />
                </div>
              </Card>
            ))}
          </div>
        ) : null}
        <SourceFooter state={state} />
      </section>
    </main>
  );
}
