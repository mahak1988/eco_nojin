import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';
import { fetchResource, ResourcePage, resourceLabels } from '@/components/ResourcePage';
import { NoJsSearch } from '@/components/surface/NoJsSearch';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';

const SLUG = 'hydroma-hydroma-carbon-credits-balance';
const ROUTE = '/hydroma/carbon/credits/balance';
/** The declared contract. A dynamic segment is resolved from the route params. */
const PATH = '/api/v1/carbon/credits/balance';

/**
 * Generated from the page catalogue — do not hand-edit.
 *
 * Entry `hydroma-hydroma-carbon-credits-balance`, domain `hydroma`. Source of truth: `services/api_gateway/routers/carbon.py`.
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
  const meta = await getTranslations('pageMeta.hydroma-hydroma-carbon-credits-balance');
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
  const meta = await getTranslations('pageMeta.hydroma-hydroma-carbon-credits-balance');
  const labels = await resourceLabels();
  const endpoint = PATH;
  // A real <form method="get"> on the page, so this works with JavaScript
  // disabled: submitting it re-navigates to this URL with the value, and the value
  // is read here and forwarded to the gateway. Kind: value ("address").
  // `required: true` — the gateway rejects a request without it, so without a form this page could only ever render an error.
  const resolved = await searchParams;
  const raw = resolved?.address;
  const term = (Array.isArray(raw) ? raw[0] : raw)?.trim() ?? '';
  const searched = term.length > 0 ? `${endpoint}?address=${encodeURIComponent(term)}` : '';
  const result = await fetchResource<Payload>(searched);

  return (
    <ResourcePage<Payload>
      slug={SLUG}
      locale={locale}
      title={meta('title')}
      description={meta('description')}
      path={searched}
      result={result}
      mode="record"
      rowsKey={undefined}
      rowKey={(row) => String(row.id ?? JSON.stringify(row).slice(0, 24))}
      labels={labels}
    >
      {({ state }) => (
        <NoJsSearch
          kind="value"
          name="address"
          path={`${searched}`}
          value={term}
          // The value kind has no "no results" message on purpose: an address
          // that matches nothing is not a failed search, and a reader who mistyped
          // a wallet address should be told the field was not found rather than
          // that a catalogue came up empty. The error state below carries that.
          id="query-hydroma-hydroma-carbon-credits-balance"
        />
      )}
    </ResourcePage>
  );
}
