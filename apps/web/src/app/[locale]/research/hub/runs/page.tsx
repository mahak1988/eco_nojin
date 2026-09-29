import type { Metadata } from 'next';
import Link from 'next/link';
import { getTranslations } from 'next-intl/server';

import { fetchResource, ResourcePage, resourceLabels } from '@/components/ResourcePage';
import { type Column } from '@/components/ui/DataTable';
import { canonicalFor, languageAlternates } from '@/config/alternates';

/**
 * Research hub - runs feed.
 *
 * Hand-authored entry `research-research-hub-runs`, domain `research`. Source of
 * truth: `services/api_gateway/routers/hydroma_hub.py`. The surface is hand-built
 * because the catalogue entry declares `POST` (the generator's page-shaped rule
 * only accepts `GET`) while the gateway also serves `GET /api/v1/hub/runs`.
 *
 * That `GET` is keyed by an anonymous client key (`user_key`), so the feed is
 * only requested when the address carries one; without a key the page says so
 * and sends nothing rather than guessing. With a key it renders exactly what the
 * gateway returned - the five data states come from the shared `ResourcePage`
 * layer and no fixture path exists anywhere in this file.
 */
const SLUG = 'research-research-hub-runs';
const ROUTE = '/research/hub/runs';
/** The declared contract path (the `user_key` query parameter is added at request time). */
const PATH = '/api/v1/hub/runs';

/**
 * Response of `GET /api/v1/hub/runs`: `{ ok, count, runs[] }`. Only the scalar
 * run fields are shown; `inputs` and `outputs` are nested documents and are
 * deliberately left out of the table rather than flattened by guesswork.
 */
type Payload = Record<string, unknown>;

const RUN_COLUMNS: Column<Payload>[] = [
  { key: 'id', header: 'id' },
  { key: 'model_id', header: 'model id' },
  { key: 'title', header: 'title' },
  { key: 'shared', header: 'shared' },
  { key: 'created_at', header: 'created at' },
];

// The feed is read live per request; nothing about it is prerendered.
export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('pageMeta.research-research-hub-runs');
  return {
    title: meta('title'),
    description: meta('description'),
    // A keyed run feed is never public; keep the surface out of the index.
    robots: { index: false, follow: false },
    alternates: {
      canonical: canonicalFor(locale, ROUTE),
      languages: languageAlternates(ROUTE),
    },
  };
}

export default async function HubRunsPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { locale } = await params;
  const query = await searchParams;
  const meta = await getTranslations('pageMeta.research-research-hub-runs');

  const rawKey = query.user_key;
  const userKey = (Array.isArray(rawKey) ? rawKey[0] : rawKey)?.trim() ?? '';

  if (userKey === '') {
    // No key, no request: the contract requires one, and there is nothing to
    // show without it. The explanatory copy lives under `pages.research.hubRuns`.
    const hubRuns = await getTranslations('pages.research.hubRuns');
    const sharedFeed = await getTranslations('pageMeta.research-research-hub-shared');
    const statusPage = await getTranslations('statusPage');

    return (
      <div>
        <header>
          <h1 className="display text-4xl font-bold text-ink">{meta('title')}</h1>
          <p className="mt-3 max-w-2xl text-ink-soft">{meta('description')}</p>
        </header>
        <section className="card mt-6 p-5">
          <p className="text-sm text-ink">{hubRuns('noKey')}</p>
          <p className="mt-2 text-sm text-ink-soft">{hubRuns('keyHint')}</p>
          <p className="num mt-3 text-xs text-ink-faint">
            {statusPage('endpoint')}: {PATH}
          </p>
          <p className="mt-3 text-sm">
            <Link
              href={`/${locale}/research/hub/shared`}
              className="underline decoration-dotted underline-offset-4 transition-micro hover:text-ink"
            >
              {sharedFeed('title')}
            </Link>
          </p>
        </section>
      </div>
    );
  }

  const labels = await resourceLabels();
  const endpoint = `${PATH}?user_key=${encodeURIComponent(userKey)}`;
  const result = await fetchResource<Payload>(endpoint);

  return (
    <ResourcePage<Payload>
      slug={SLUG}
      locale={locale}
      title={meta('title')}
      description={meta('description')}
      // The stamp names the contract path; the key is request metadata and is
      // not echoed into the visible surface.
      path={PATH}
      result={result}
      mode="rows"
      rowsKey="runs"
      columns={RUN_COLUMNS}
      rowKey={(row) => String(row.id ?? JSON.stringify(row).slice(0, 24))}
      labels={labels}
    />
  );
}
