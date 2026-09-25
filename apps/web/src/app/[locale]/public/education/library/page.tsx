import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';
import { DataStateCard, SourceFooter, toDataState } from '../../data-states';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

const CONTENT_SEARCH_PATH = '/api/v1/content/search';

type ContentHit = {
  id: string;
  title: string;
  category: string;
  language: string;
  published_at: string | null;
  snippet: string;
};

type ContentSearch = {
  query: string;
  count: number;
  results: ContentHit[];
};

const TITLES: Record<string, string> = { fa: 'کتابخانه آموزشی', en: 'Education Library' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'جستجو در محتوای منتشرشدهٔ آموزشی',
  en: 'Search the published learning content',
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
      url: `${BASE_URL}/${locale}/public/education/library`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/education/library`,
      languages: {
        fa: `${BASE_URL}/fa/public/education/library`,
        en: `${BASE_URL}/en/public/education/library`,
      },
    },
  };
}

export default async function LibraryPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { locale } = await params;
  const query = await searchParams;
  setRequestLocale(locale);
  const template = await getTranslations('market.template');
  const learn = await getTranslations('learn');
  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  // The gateway publishes no unfiltered content listing: `q` is required by the
  // registered route, so the page searches it directly instead of faking a catalogue.
  const raw = query.q;
  const term = (Array.isArray(raw) ? raw[0] : raw)?.trim() ?? '';
  const search = term
    ? await apiGet<ContentSearch>(`${CONTENT_SEARCH_PATH}?q=${encodeURIComponent(term)}&limit=20`)
    : null;
  const results = search?.ok ? search.data.results : [];
  const state = search ? toDataState(CONTENT_SEARCH_PATH, search, results.length) : null;

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={CONTENT_SEARCH_PATH}
          label={title}
          verified={search ? search.ok : false}
          method={CONTENT_SEARCH_PATH}
        >
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <Card density="cozy">
          <form className="space-y-4" action="" method="get">
            <div>
              <label htmlFor="library-query" className="block text-sm text-ink-soft mb-1">
                {CONTENT_SEARCH_PATH}
              </label>
              <input
                id="library-query"
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
    </main>
  );
}
