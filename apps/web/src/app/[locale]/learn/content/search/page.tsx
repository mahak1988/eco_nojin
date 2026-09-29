import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';
import { fetchResource, ResourcePage, resourceLabels } from '@/components/ResourcePage';
import { NoJsSearch } from '@/components/surface/NoJsSearch';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';

const SLUG = 'learning-learn-content-search';
const ROUTE = '/learn/content/search';
/** The declared contract. A dynamic segment is resolved from the route params. */
const PATH = '/api/v1/content/search';

/**
 * Generated from the page catalogue — do not hand-edit.
 *
 * Entry `learning-learn-content-search`, domain `learning`. Source of truth: `services/api_gateway/routers/content_public.py`.
 * The endpoint is the declared contract; the page renders one of the five
 * required states and never a fabricated value.
 */
type Payload = Record<string, unknown>;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('pageMeta.learning-learn-content-search');
  return {
    title: meta('title'),
    description: meta('description'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}${ROUTE}`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, ROUTE),
      languages: languageAlternates(ROUTE),
    },
  };
}

export default async function Page({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { locale } = await params;
  const meta = await getTranslations('pageMeta.learning-learn-content-search');
  const labels = await resourceLabels();
  const searchCopy = await getTranslations('search');
  const endpoint = PATH;
  // A real <form method="get"> on the page, so the search works with
  // JavaScript disabled: submitting it re-navigates to this URL with ?q=…, and
  // the term is read here and forwarded to the gateway. `required: true` — the gateway rejects a request without one, so the empty state is the honest first render.
  const resolved = await searchParams;
  const raw = resolved?.q;
  const term = (Array.isArray(raw) ? raw[0] : raw)?.trim() ?? '';
  const searched = term.length > 0 ? endpoint + (term ? `?q=${encodeURIComponent(term)}` : '') : '';
  const result = await fetchResource<Payload>(searched);

  return (
    <ResourcePage<Payload>
      slug={SLUG}
      locale={locale}
      title={meta('title')}
      description={meta('description')}
      path={searched}
      result={result}
      mode="rows"
      rowsKey={'searchs'}
      rowKey={(row) => String(row.id ?? JSON.stringify(row).slice(0, 24))}
      labels={labels}
    >
      {({ state }) => (
        <NoJsSearch
          name="q"
          path={`${searched}`}
          value={term}
          emptyResult={
            state === 'empty' && term.length > 0 ? searchCopy('noResults', { term }) : undefined
          }
          id="search-learning-learn-content-search"
        />
      )}
    </ResourcePage>
  );
}
