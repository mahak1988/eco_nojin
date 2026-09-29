import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { apiGet } from '@/lib/api/client';
import { DataStateCard, SourceFooter, toDataState } from '../../data-states';

const CONTENT_SEARCH_PATH = '/api/v1/content/search';
const AGROVOC_PATH = '/api/v1/science/agrovoc';

type ContentHit = {
  id: string;
  title: string;
  category: string;
  language: string;
  published_at: string | null;
  snippet: string;
};

type ContentSearch = { query: string; count: number; results: ContentHit[] };

type AgrovocResult = { count: number | null; results: unknown[]; stats: Record<string, number> };

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('pageMeta.public-education-library-advanced');
  return {
    title: meta('title'),
    description: meta('description'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/public/education/library-advanced`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/public/education/library-advanced'),
      languages: languageAlternates('/public/education/library-advanced'),
    },
  };
}

export default async function LibraryAdvancedPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { locale } = await params;
  const query = await searchParams;
  setRequestLocale(locale);

  const meta = await getTranslations('pageMeta.public-education-library-advanced');
  const learn = await getTranslations('learn');
  const template = await getTranslations('market.template');
  const title = meta('title');
  const description = meta('description');

  // The registered search route accepts `q` and `limit` only; every filter shown
  // here is one the gateway actually applies.
  const raw = query.q;
  const term = (Array.isArray(raw) ? raw[0] : raw)?.trim() ?? '';
  const [search, agrovoc] = await Promise.all([
    term
      ? apiGet<ContentSearch>(`${CONTENT_SEARCH_PATH}?q=${encodeURIComponent(term)}&limit=50`)
      : Promise.resolve(null),
    apiGet<AgrovocResult>(AGROVOC_PATH),
  ]);
  const results = search?.ok ? search.data.results : [];
  const state = search ? toDataState(CONTENT_SEARCH_PATH, search, results.length) : null;
  const groups = agrovoc.ok ? Object.entries(agrovoc.data.stats) : [];
  const groupsState = toDataState(AGROVOC_PATH, agrovoc, groups.length);

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={CONTENT_SEARCH_PATH}
          label={title}
          verified={search ? search.ok : false}
          method={CONTENT_SEARCH_PATH}
        />
        <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <Card density="cozy">
          <form className="space-y-4" action="" method="get">
            <div>
              <label htmlFor="advanced-query" className="block text-sm text-ink-soft mb-1">
                {CONTENT_SEARCH_PATH}
              </label>
              <input
                id="advanced-query"
                name="q"
                type="text"
                defaultValue={term}
                className="w-full px-4 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-forest"
              />
            </div>
            <Button variant="primary" type="submit">
              {template('source')}
            </Button>
          </form>
        </Card>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{CONTENT_SEARCH_PATH}</h2>
        {!term ? (
          <Card density="compact">
            <h3 className="text-sm font-medium text-ink">{learn('emptyTitle')}</h3>
            <p className="mt-1 text-sm text-ink-soft">{learn('emptyDesc')}</p>
          </Card>
        ) : null}
        {state ? (
          <DataStateCard
            state={state}
            emptyTitle={learn('emptyTitle')}
            emptyDescription={learn('emptyDesc')}
          />
        ) : null}
        {state?.kind === 'ready' ? (
          <div className="grid gap-4">
            {results.map((hit) => (
              <Card key={hit.id} density="compact">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h3 className="font-medium text-ink">{hit.title}</h3>
                    <p className="mt-1 text-sm text-ink-soft">{hit.snippet}</p>
                    <p className="mt-1 text-xs text-ink-soft">
                      {hit.category} · {hit.language}
                    </p>
                  </div>
                  <ProvenanceStamp
                    source={CONTENT_SEARCH_PATH}
                    verified={Boolean(hit.published_at)}
                    timestamp={hit.published_at ?? undefined}
                    method={hit.category}
                  />
                </div>
              </Card>
            ))}
          </div>
        ) : null}
        {state ? <SourceFooter state={state} /> : null}
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{AGROVOC_PATH}</h2>
        <DataStateCard state={groupsState} />
        {groupsState.kind === 'ready' && agrovoc.ok ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {groups.map(([group, count]) => (
              <Card key={group} density="compact">
                <div className="num text-2xl font-semibold text-ink">{count}</div>
                <p className="mt-1 text-sm text-ink-soft">{group}</p>
                <div className="mt-2">
                  <ProvenanceStamp source={AGROVOC_PATH} verified method={group} />
                </div>
              </Card>
            ))}
          </div>
        ) : null}
        <SourceFooter state={groupsState} />
      </section>
    </main>
  );
}
