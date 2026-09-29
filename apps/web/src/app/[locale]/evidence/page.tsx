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
  ASPIRATIONS,
  type CitationIndex,
  type ContractRow,
  type DatasetCatalog,
  INTEGRITY_CONTRACTS,
  type ModelCards,
  type ZenodoStatus,
} from './contracts';

export const dynamic = 'force-dynamic';

const PATHS = {
  citations: '/api/v1/science/citations/index',
  datasets: '/api/v1/science/datasets',
  modelCards: '/api/v1/science/model-cards',
  agrovoc: '/api/v1/science/agrovoc',
  zenodo: '/api/v1/science/zenodo/status',
  validation: '/api/v1/hydroma/validation',
} as const;

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
      url: `${BASE_URL}/${locale}/evidence`,
      title: t('metaTitle'),
      description: t('metaDescription'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/evidence'),
      languages: languageAlternates('/evidence'),
    },
  };
}

export default async function EvidencePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  const t = await getTranslations('public.integrity');
  const common = await getTranslations('common');
  const statusLine = await getTranslations('statusLine');
  const market = await getTranslations('market.template');
  const nf = new Intl.NumberFormat(locale);

  const [citations, datasets, modelCards, agrovoc, zenodo, validation] = await Promise.all([
    apiGet<CitationIndex>(PATHS.citations),
    apiGet<DatasetCatalog>(PATHS.datasets),
    apiGet<ModelCards>(PATHS.modelCards),
    apiGet<Agrovoc>(PATHS.agrovoc),
    apiGet<ZenodoStatus>(PATHS.zenodo),
    apiGet<Record<string, unknown>>(PATHS.validation),
  ]);

  /**
   * The five states, decided once from the whole set rather than per card.
   *
   * A page that shows three live reads and two dead ones has not "succeeded
   * with a caveat" — it has a partial answer, and §4.5 is explicit that a
   * partial result must not present itself as a complete one.
   */
  const rows = [
    { id: 'citations', path: PATHS.citations, result: citations },
    { id: 'datasets', path: PATHS.datasets, result: datasets },
    { id: 'model-cards', path: PATHS.modelCards, result: modelCards },
    { id: 'agrovoc', path: PATHS.agrovoc, result: agrovoc },
    { id: 'zenodo', path: PATHS.zenodo, result: zenodo },
    { id: 'validation', path: PATHS.validation, result: validation },
  ];
  const results = rows.map((row) => row.result);
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

  const citationItems = citations.ok ? citations.data.items.slice(0, 8) : [];
  const datasetRows = datasets.ok ? datasets.data.datasets : [];
  const cardRows = modelCards.ok ? (modelCards.data.cards ?? []) : [];
  const agrovocStats = agrovoc.ok ? agrovoc.data.stats : null;

  const contractById = new Map(INTEGRITY_CONTRACTS.map((row) => [row.id, row]));

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

        <section className="card mt-6 p-5" aria-labelledby="evidence-rule">
          <h2 id="evidence-rule" className="field-label">
            {t('claimTitle')}
          </h2>
          <p className="mt-2 text-sm text-ink-soft">{t('claimBody')}</p>
        </section>

        <section className="mt-6" aria-labelledby="evidence-state">
          <h2 id="evidence-state" className="field-label">
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
                {INTEGRITY_CONTRACTS.map((contract: ContractRow) => {
                  const result = rows.find((row) => row.id === contract.id)?.result ?? null;
                  const answeredHere = result?.ok ?? false;
                  return (
                    <li
                      key={contract.id}
                      className="card flex flex-wrap items-center justify-between gap-3 p-4"
                    >
                      <span className="num font-mono text-xs text-ink">{contract.path}</span>
                      <span className="flex flex-wrap items-center gap-3">
                        <span className="num text-xs text-ink-faint">{contract.source}</span>
                        {contract.kind === 'absent' ? (
                          <>
                            <ProvenanceStamp
                              source={contract.path}
                              verified={false}
                              method={contract.id}
                            />
                            <StatusDot state="down" label={statusLine('unavailable')} />
                          </>
                        ) : (
                          <>
                            <ProvenanceStamp source={contract.path} verified={answeredHere} />
                            <StatusDot
                              state={answeredHere ? 'ok' : 'down'}
                              label={answeredHere ? common('live') : statusLine('unavailable')}
                            />
                          </>
                        )}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </StateSlot>
          </div>
        </section>

        <section className="mt-6 grid gap-4 sm:grid-cols-2" aria-labelledby="evidence-figures">
          <h2 id="evidence-figures" className="sr-only">
            {t('traceabilityTitle')}
          </h2>
          <Card density="compact">
            <h3 className="field-label">{PATHS.citations}</h3>
            <p className="num mt-2 text-3xl font-semibold text-ink">
              {citations.ok ? nf.format(citations.data.count) : statusLine('unavailable')}
            </p>
            <div className="mt-3">
              <ProvenanceStamp source={PATHS.citations} verified={citations.ok} />
            </div>
          </Card>
          <Card density="compact">
            <h3 className="field-label">{PATHS.datasets}</h3>
            <p className="num mt-2 text-3xl font-semibold text-ink">
              {datasets.ok
                ? `${nf.format(datasets.data.live)} / ${nf.format(datasets.data.count)}`
                : statusLine('unavailable')}
            </p>
            <div className="mt-3">
              <ProvenanceStamp source={PATHS.datasets} verified={datasets.ok} />
            </div>
          </Card>
          <Card density="compact">
            <h3 className="field-label">{PATHS.modelCards}</h3>
            <p className="num mt-2 text-3xl font-semibold text-ink">
              {modelCards.ok
                ? nf.format(modelCards.data.count ?? cardRows.length)
                : statusLine('unavailable')}
            </p>
            <p className="mt-1 text-xs text-ink-soft">{t('modelCardsBody')}</p>
            <div className="mt-3">
              <ProvenanceStamp source={PATHS.modelCards} verified={modelCards.ok} />
            </div>
          </Card>
          <Card density="compact">
            <h3 className="field-label">{PATHS.agrovoc}</h3>
            <p className="num mt-2 text-3xl font-semibold text-ink">
              {agrovocStats?.total !== undefined
                ? nf.format(Number(agrovocStats.total))
                : statusLine('unavailable')}
            </p>
            <p className="mt-1 text-xs text-ink-soft">{t('agrovocBody')}</p>
            <div className="mt-3">
              <ProvenanceStamp source={PATHS.agrovoc} verified={agrovoc.ok} />
            </div>
          </Card>
        </section>

        {state !== 'ready' ? (
          <section className="mt-6" aria-labelledby="evidence-partial">
            <Card density="compact">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h2 id="evidence-partial" className="field-label">
                  {market('unavailableTitle')}
                </h2>
                <StatusDot
                  state={state === 'error' ? 'down' : 'warn'}
                  label={answeredOf(answered, results.length)}
                />
              </div>
              <p className="mt-2 text-sm text-ink-soft">{market('unavailableDescription')}</p>
              <ul className="num mt-3 grid gap-1 text-xs text-ink-faint">
                {rows
                  .filter((row) => !row.result.ok)
                  .map((row) => (
                    <li key={row.path}>
                      {row.path} · {row.result.status || '—'} ·{' '}
                      {row.result.ok ? '' : row.result.error}
                    </li>
                  ))}
              </ul>
            </Card>
          </section>
        ) : null}

        {citationItems.length > 0 ? (
          <section className="mt-8" aria-labelledby="evidence-citations">
            <h2 id="evidence-citations" className="field-label">
              {t('traceabilityTitle')}
            </h2>
            <ul className="mt-3 divide-y divide-line rounded-[var(--radius-card)] border border-line">
              {citationItems.map((item) => (
                <li
                  key={item.slug}
                  className="flex flex-wrap items-baseline justify-between gap-4 px-4 py-3 text-sm"
                >
                  <span className="num font-mono text-xs text-ink">{item.slug}</span>
                  <span className="text-ink-soft">
                    {item.reference ?? statusLine('noData')}
                    {item.doi ? ` · ${item.doi}` : ''}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {datasetRows.length > 0 ? (
          <section className="mt-8" aria-labelledby="evidence-datasets">
            <h2 id="evidence-datasets" className="field-label">
              {PATHS.datasets}
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

        <section className="mt-8" aria-labelledby="evidence-aspiration">
          <h2 id="evidence-aspiration" className="field-label">
            {t('aspirationTitle')}
          </h2>
          <p className="mt-2 text-sm text-ink-soft">{t('aspirationLead')}</p>
          <ul className="mt-3 grid gap-2">
            {(t.raw('aspirationItems') as string[]).map((item) => (
              <li key={item} className="card p-4 text-sm text-ink">
                {item}
              </li>
            ))}
          </ul>
          <Card density="compact" className="mt-3">
            <h3 className="field-label">{t('contractTitle')}</h3>
            <p className="mt-1 text-sm text-ink-soft">{t('contractBody')}</p>
            <ul className="num mt-3 grid gap-1 text-xs text-ink-faint">
              {ASPIRATIONS.map((aspiration) => {
                const row = contractById.get(aspiration.id);
                return (
                  <li key={aspiration.id}>
                    {aspiration.contract} ·{' '}
                    {row?.source ?? 'services/api_gateway/routers/science.py'}
                  </li>
                );
              })}
            </ul>
          </Card>
        </section>

        <div className="mt-8 grid gap-4">
          <Card density="compact">
            <h2 className="field-label">{t('noExternalTitle')}</h2>
            <p className="mt-2 text-sm text-ink-soft">{t('noExternalBody')}</p>
          </Card>
          <ListBlock
            title={common('limitsLabel')}
            items={t.raw('aspirationItems') as string[]}
            tone="clay"
          />
        </div>
      </div>
    </main>
  );
}

/** `2/6`, in the reader's own digits. Used as the slot's status label. */
function answeredOf(answered: number, total: number): string {
  return `${answered}/${total}`;
}
