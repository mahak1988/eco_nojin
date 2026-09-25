import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { SiteNav } from '@/components/SiteNav';
import { type DotState, StatusDot } from '@/components/StatusDot';
import { apiGet } from '@/lib/api/client';

export const dynamic = 'force-dynamic';

type CitationIndex = { count: number; items: { slug: string; reference: string | null }[] };
type DatasetCatalog = { count: number; live: number; datasets: { status: string }[] };
type ZenodoStatus = { configured: boolean; status: string };

const EVIDENCE_SOURCES = [
  '/api/v1/science/citations/index',
  '/api/v1/science/datasets',
  '/api/v1/science/zenodo/status',
] as const;

export default async function EvidencePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();
  const common = await getTranslations('common');
  const statusLine = await getTranslations('statusLine');
  const statusPage = await getTranslations('statusPage');
  const nf = new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en');

  const [citations, datasets, zenodo] = await Promise.all([
    apiGet<CitationIndex>('/api/v1/science/citations/index'),
    apiGet<DatasetCatalog>('/api/v1/science/datasets'),
    apiGet<ZenodoStatus>('/api/v1/science/zenodo/status'),
  ]);

  const reachable = [citations, datasets, zenodo].filter((result) => result.ok).length;
  const state: DotState =
    reachable === 0 ? 'down' : reachable === EVIDENCE_SOURCES.length ? 'ok' : 'warn';
  const items = citations.ok ? citations.data.items.slice(0, 8) : [];

  return (
    <main id="main">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 py-10">
        <FivePart
          title={t('evidence.title')}
          lead={t('evidence.lead')}
          what={t('evidence.what')}
          audience={t('evidence.audience')}
          evidence={t.raw('evidence.evidence') as string[]}
          limits={t.raw('evidence.limits') as string[]}
          next={t.raw('evidence.next') as string[]}
        />

        <section className="mt-10" aria-labelledby="evidence-sources">
          <h2 id="evidence-sources" className="field-label">
            {statusPage('endpoint')}
          </h2>
          <div className="mt-3 flex flex-wrap items-center gap-4">
            <StatusDot
              state={state}
              label={state === 'down' ? statusLine('unavailable') : statusLine('realData')}
            />
          </div>

          <ul className="mt-4 grid gap-3">
            <li className="card flex items-center justify-between gap-3 p-4 text-sm">
              <span className="font-mono text-xs text-ink">/api/v1/science/citations/index</span>
              <span className={citations.ok ? 'text-forest' : 'text-copper'}>
                {citations.ok ? nf.format(citations.data.count) : statusLine('unavailable')}
              </span>
            </li>
            <li className="card flex items-center justify-between gap-3 p-4 text-sm">
              <span className="font-mono text-xs text-ink">/api/v1/science/datasets</span>
              <span className={datasets.ok ? 'text-forest' : 'text-copper'}>
                {datasets.ok
                  ? `${nf.format(datasets.data.live)} / ${nf.format(datasets.data.count)}`
                  : statusLine('unavailable')}
              </span>
            </li>
            <li className="card flex items-center justify-between gap-3 p-4 text-sm">
              <span className="font-mono text-xs text-ink">/api/v1/science/zenodo/status</span>
              <span className={zenodo.ok ? 'text-forest' : 'text-copper'}>
                {zenodo.ok ? zenodo.data.status : statusLine('unavailable')}
              </span>
            </li>
          </ul>
        </section>

        {items.length > 0 && (
          <section className="mt-10" aria-labelledby="evidence-citations">
            <h2 id="evidence-citations" className="field-label">
              {common('evidence')}
            </h2>
            <ul className="mt-3 divide-y divide-line rounded-[var(--radius-card)] border border-line bg-surface">
              {items.map((item) => (
                <li
                  key={item.slug}
                  className="flex items-baseline justify-between gap-4 px-4 py-3 text-sm"
                >
                  <span className="font-mono text-xs text-ink">{item.slug}</span>
                  <span className="text-ink-soft">{item.reference ?? statusLine('noData')}</span>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </main>
  );
}
