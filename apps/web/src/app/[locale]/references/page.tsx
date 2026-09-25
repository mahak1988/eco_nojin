import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ListBlock } from '@/components/ListBlock';
import { SiteNav } from '@/components/SiteNav';
import { type DotState, StatusDot } from '@/components/StatusDot';
import { SITE_URL as BASE_URL } from '@/config/site';
import { apiGet } from '@/lib/api/client';

const CITATIONS_PATH = '/api/v1/science/citations/index';
const DATASETS_PATH = '/api/v1/science/datasets';
const ZENODO_PATH = '/api/v1/science/zenodo/status';

type CitationIndex = {
  count: number;
  items: {
    slug: string;
    name_en: string | null;
    name_fa: string | null;
    reference: string | null;
    doi: string | null;
  }[];
};

type DatasetCatalog = {
  count: number;
  live: number;
  datasets: {
    id: string;
    name: string;
    domain: string;
    source: string;
    status: string;
    requires: string;
    license: string;
  }[];
};

type ZenodoStatus = { configured: boolean; status: string };

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('evidence');
  return {
    title: t('title'),
    description: t('lead'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/references`,
      title: t('title'),
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/references`,
      languages: {
        fa: `${BASE_URL}/fa/references`,
        en: `${BASE_URL}/en/references`,
      },
    },
  };
}

export default async function ReferencesPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();
  const common = await getTranslations('common');
  const statusLine = await getTranslations('statusLine');
  const statusPage = await getTranslations('statusPage');
  const nf = new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en');

  const [citations, datasets, zenodo] = await Promise.all([
    apiGet<CitationIndex>(CITATIONS_PATH),
    apiGet<DatasetCatalog>(DATASETS_PATH),
    apiGet<ZenodoStatus>(ZENODO_PATH),
  ]);

  const reachable = [citations, datasets, zenodo].filter((result) => result.ok).length;
  const state: DotState = reachable === 0 ? 'down' : reachable === 3 ? 'ok' : 'warn';
  const items = citations.ok ? citations.data.items : [];
  const datasetRows = datasets.ok ? datasets.data.datasets : [];

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <FivePart
          title={t('evidence.title')}
          lead={t('evidence.lead')}
          what={t('evidence.what')}
          audience={t('evidence.audience')}
          evidence={t.raw('evidence.evidence') as string[]}
          limits={t.raw('evidence.limits') as string[]}
          next={t.raw('evidence.next') as string[]}
        />

        <section className="mt-10" aria-labelledby="reference-sources">
          <h2 id="reference-sources" className="field-label">
            {statusPage('endpoint')}
          </h2>
          <div className="mt-3 flex flex-wrap items-center gap-4">
            <StatusDot
              state={state}
              label={state === 'down' ? statusLine('unavailable') : statusLine('realData')}
            />
          </div>

          <ul className="mt-4 grid gap-3">
            <li className="card flex flex-wrap items-center justify-between gap-3 p-4 text-sm">
              <span className="font-mono text-xs text-ink">{CITATIONS_PATH}</span>
              <span className={citations.ok ? 'text-forest' : 'text-copper'}>
                {citations.ok
                  ? `${common('total')}: ${nf.format(citations.data.count)}`
                  : statusLine('unavailable')}
              </span>
            </li>
            <li className="card flex flex-wrap items-center justify-between gap-3 p-4 text-sm">
              <span className="font-mono text-xs text-ink">{DATASETS_PATH}</span>
              <span className={datasets.ok ? 'text-forest' : 'text-copper'}>
                {datasets.ok
                  ? `${common('total')}: ${nf.format(datasets.data.count)}`
                  : statusLine('unavailable')}
              </span>
            </li>
            <li className="card flex flex-wrap items-center justify-between gap-3 p-4 text-sm">
              <span className="font-mono text-xs text-ink">{ZENODO_PATH}</span>
              <span className={zenodo.ok && zenodo.data.configured ? 'text-forest' : 'text-copper'}>
                {zenodo.ok ? zenodo.data.status : statusLine('unavailable')}
              </span>
            </li>
          </ul>
        </section>

        {items.length > 0 && (
          <section className="mt-10" aria-labelledby="reference-citations">
            <h2 id="reference-citations" className="field-label">
              {statusPage('label')}
            </h2>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-line text-ink-soft">
                    <th className="py-2 pe-4 text-start font-medium">{statusPage('label')}</th>
                    <th className="py-2 pe-4 text-start font-medium">{statusPage('service')}</th>
                    <th className="py-2 text-start font-medium">{statusPage('result')}</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={item.slug} className="border-b border-line/50 align-top">
                      <td className="py-2 pe-4 font-mono text-xs text-ink">{item.slug}</td>
                      <td className="py-2 pe-4 text-xs text-ink-soft">
                        {locale === 'fa'
                          ? (item.name_fa ?? item.name_en)
                          : (item.name_en ?? item.name_fa)}
                      </td>
                      <td className="py-2 text-xs text-ink-soft">
                        {item.reference ?? statusLine('noData')}
                        {item.doi ? ` · ${item.doi}` : ''}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {datasetRows.length > 0 && (
          <section className="mt-10" aria-labelledby="reference-datasets">
            <h2 id="reference-datasets" className="field-label">
              {statusPage('service')}
            </h2>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-line text-ink-soft">
                    <th className="py-2 pe-4 text-start font-medium">{statusPage('label')}</th>
                    <th className="py-2 pe-4 text-start font-medium">{statusPage('service')}</th>
                    <th className="py-2 pe-4 text-start font-medium">{statusPage('state')}</th>
                    <th className="py-2 text-start font-medium">{statusPage('result')}</th>
                  </tr>
                </thead>
                <tbody>
                  {datasetRows.map((dataset) => (
                    <tr key={dataset.id} className="border-b border-line/50 align-top">
                      <td className="py-2 pe-4 text-ink">{dataset.name}</td>
                      <td className="py-2 pe-4 text-xs text-ink-soft">
                        {dataset.source} · {dataset.license}
                      </td>
                      <td
                        className={`py-2 pe-4 text-xs ${
                          dataset.status === 'live' ? 'text-forest' : 'text-copper'
                        }`}
                      >
                        {dataset.status}
                      </td>
                      <td className="py-2 text-xs text-ink-soft">{dataset.requires}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        <div className="mt-6 grid gap-4">
          <ListBlock
            title={common('limitsLabel')}
            items={t.raw('evidence.limits') as string[]}
            tone="clay"
          />
          <ListBlock
            title={common('nextLabel')}
            items={t.raw('evidence.next') as string[]}
            tone="moss"
          />
        </div>
      </div>
    </main>
  );
}
