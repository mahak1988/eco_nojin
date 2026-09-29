import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ListBlock } from '@/components/ListBlock';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { StateSlot } from '@/components/ui/StateSlot';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { apiGet } from '@/lib/api/client';
import {
  type Agrovoc,
  type CitationIndex,
  type DatasetCatalog,
  type ModelCards,
  type ZenodoStatus,
} from '../evidence/contracts';

const CITATIONS_PATH = '/api/v1/science/citations/index';
const DATASETS_PATH = '/api/v1/science/datasets';
const MODEL_CARDS_PATH = '/api/v1/science/model-cards';
const AGROVOC_PATH = '/api/v1/science/agrovoc';
const ZENODO_PATH = '/api/v1/science/zenodo/status';

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.integrity');

  return {
    title: t('metaTitle'),
    description: t('metaDescription'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/references`,
      title: t('metaTitle'),
      description: t('metaDescription'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/references'),
      languages: languageAlternates('/references'),
    },
  };
}

export default async function ReferencesPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  const t = await getTranslations('public.integrity');
  const common = await getTranslations('common');
  const statusLine = await getTranslations('statusLine');
  const market = await getTranslations('market.template');
  const nf = new Intl.NumberFormat(locale);

  const [citations, datasets, modelCards, agrovoc, zenodo] = await Promise.all([
    apiGet<CitationIndex>(CITATIONS_PATH),
    apiGet<DatasetCatalog>(DATASETS_PATH),
    apiGet<ModelCards>(MODEL_CARDS_PATH),
    apiGet<Agrovoc>(AGROVOC_PATH),
    apiGet<ZenodoStatus>(ZENODO_PATH),
  ]);

  const results = [citations, datasets, modelCards, agrovoc, zenodo];
  const answered = results.filter((result) => result.ok).length;
  const state = (() => {
    if (answered === results.length) return 'ready' as const;
    if (answered === 0) {
      return results.every((result) => !result.ok && result.status === 0)
        ? ('offline' as const)
        : ('error' as const);
    }
    return 'partial' as const;
  })();

  const rows = [
    { id: 'citations', path: CITATIONS_PATH, result: citations },
    { id: 'datasets', path: DATASETS_PATH, result: datasets },
    { id: 'model-cards', path: MODEL_CARDS_PATH, result: modelCards },
    { id: 'agrovoc', path: AGROVOC_PATH, result: agrovoc },
    { id: 'zenodo', path: ZENODO_PATH, result: zenodo },
  ];

  const items = citations.ok ? citations.data.items : [];
  const datasetRows = datasets.ok ? datasets.data.datasets : [];
  const cardRows = modelCards.ok ? (modelCards.data.cards ?? []) : [];

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 pb-16 pt-8">
        <header>
          <h1 className="display text-3xl font-bold text-balance text-ink sm:text-4xl">
            {t('metaTitle')}
          </h1>
          <p className="mt-3 max-w-2xl text-sm text-ink-soft">{t('metaDescription')}</p>
        </header>

        <section className="card mt-6 p-5">
          <h2 className="field-label">{t('claimTitle')}</h2>
          <p className="mt-2 text-sm text-ink-soft">{t('claimBody')}</p>
        </section>

        <section className="mt-6" aria-labelledby="reference-sources">
          <h2 id="reference-sources" className="field-label">
            {t('traceabilityTitle')}
          </h2>
          <p className="mt-2 text-sm text-ink-soft">{t('traceabilityBody')}</p>
          <div className="mt-3">
            <StateSlot
              state={state}
              density="compact"
              labels={{
                loading: common('retry'),
                empty: statusLine('noData'),
                error: statusLine('unavailable'),
                partial: market('unavailableTitle'),
                offline: statusLine('unavailable'),
              }}
              detail={`${answered}/${results.length}`}
            >
              <ul className="grid gap-2">
                {rows.map((row) => (
                  <li
                    key={row.id}
                    className="card flex flex-wrap items-center justify-between gap-3 p-4"
                  >
                    <span className="num font-mono text-xs text-ink">{row.path}</span>
                    <span className="flex items-center gap-3">
                      <span className="num text-xs text-ink-soft">
                        {row.result.ok ? statusLine('realData') : statusLine('unavailable')}
                      </span>
                      <ProvenanceStamp source={row.path} verified={row.result.ok} />
                      <StatusDot
                        state={row.result.ok ? 'ok' : 'down'}
                        label={row.result.ok ? common('live') : statusLine('unavailable')}
                      />
                    </span>
                  </li>
                ))}
              </ul>
            </StateSlot>
          </div>
        </section>

        {items.length > 0 ? (
          <section className="mt-8" aria-labelledby="reference-citations">
            <h2 id="reference-citations" className="field-label">
              {CITATIONS_PATH}
            </h2>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full text-sm">
                <caption className="sr-only">{t('traceabilityTitle')}</caption>
                <thead>
                  <tr className="border-b border-line text-ink-soft">
                    <th scope="col" className="num py-2 pe-4 text-start font-medium">
                      slug
                    </th>
                    <th scope="col" className="py-2 pe-4 text-start font-medium">
                      name
                    </th>
                    <th scope="col" className="py-2 text-start font-medium">
                      reference
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={item.slug} className="border-b border-line/50 align-top">
                      <td className="num py-2 pe-4 font-mono text-xs text-ink">{item.slug}</td>
                      <td className="py-2 pe-4 text-xs text-ink-soft">
                        {locale === 'fa'
                          ? (item.name_fa ?? item.name_en)
                          : (item.name_en ?? item.name_fa)}
                      </td>
                      <td className="num py-2 text-xs text-ink-soft">
                        {item.reference ?? statusLine('noData')}
                        {item.doi ? ` · ${item.doi}` : ''}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ) : null}

        {datasetRows.length > 0 ? (
          <section className="mt-8" aria-labelledby="reference-datasets">
            <h2 id="reference-datasets" className="field-label">
              {DATASETS_PATH}
            </h2>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full text-sm">
                <caption className="sr-only">{t('traceabilityTitle')}</caption>
                <thead>
                  <tr className="border-b border-line text-ink-soft">
                    <th scope="col" className="py-2 pe-4 text-start font-medium">
                      name
                    </th>
                    <th scope="col" className="py-2 pe-4 text-start font-medium">
                      source
                    </th>
                    <th scope="col" className="py-2 pe-4 text-start font-medium">
                      status
                    </th>
                    <th scope="col" className="py-2 text-start font-medium">
                      requires
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {datasetRows.map((dataset) => (
                    <tr key={dataset.id} className="border-b border-line/50 align-top">
                      <td className="py-2 pe-4 text-ink">{dataset.name}</td>
                      <td className="py-2 pe-4 text-xs text-ink-soft">
                        {dataset.source} · {dataset.license}
                      </td>
                      <td className="py-2 pe-4 text-xs">
                        <StatusDot
                          state={dataset.status === 'live' ? 'ok' : 'warn'}
                          label={dataset.status}
                        />
                      </td>
                      <td className="py-2 text-xs text-ink-soft">{dataset.requires}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ) : null}

        <section className="mt-8 grid gap-4 sm:grid-cols-2">
          <Card density="compact">
            <h3 className="field-label">{t('modelCardsTitle')}</h3>
            <p className="num mt-2 text-2xl font-semibold text-ink">
              {modelCards.ok
                ? nf.format(modelCards.data.count ?? cardRows.length)
                : statusLine('unavailable')}
            </p>
            <p className="mt-1 text-sm text-ink-soft">{t('modelCardsBody')}</p>
            <div className="mt-3">
              <ProvenanceStamp source={MODEL_CARDS_PATH} verified={modelCards.ok} />
            </div>
          </Card>
          <Card density="compact">
            <h3 className="field-label">{t('agrovocTitle')}</h3>
            <p className="num mt-2 text-2xl font-semibold text-ink">
              {agrovoc.ok && agrovoc.data.stats.total !== undefined
                ? nf.format(Number(agrovoc.data.stats.total))
                : statusLine('unavailable')}
            </p>
            <p className="mt-1 text-sm text-ink-soft">{t('agrovocBody')}</p>
            <div className="mt-3">
              <ProvenanceStamp source={AGROVOC_PATH} verified={agrovoc.ok} />
            </div>
          </Card>
          <Card density="compact">
            <h3 className="field-label">{ZENODO_PATH}</h3>
            <p className="mt-2 text-sm text-ink">
              {zenodo.ok ? zenodo.data.status : statusLine('unavailable')}
            </p>
            <div className="mt-3">
              <ProvenanceStamp source={ZENODO_PATH} verified={zenodo.ok} />
            </div>
          </Card>
          <Card density="compact">
            <h3 className="field-label">{t('noExternalTitle')}</h3>
            <p className="mt-1 text-sm text-ink-soft">{t('noExternalBody')}</p>
            <div className="mt-3">
              <ProvenanceStamp source={t('noExternalTitle')} verified={false} />
            </div>
          </Card>
        </section>

        <div className="mt-8 grid gap-4">
          <ListBlock
            title={t('aspirationTitle')}
            items={t.raw('aspirationItems') as string[]}
            tone="clay"
          />
          <ListBlock title={common('nextLabel')} items={[]} tone="moss">
            <p className="text-sm text-ink-soft">{t('contractBody')}</p>
          </ListBlock>
        </div>
      </div>
    </main>
  );
}
