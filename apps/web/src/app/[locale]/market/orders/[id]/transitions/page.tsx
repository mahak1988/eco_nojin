import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';
import { fetchResource, ResourcePage, resourceLabels } from '@/components/ResourcePage';
import { type Column } from '@/components/ui/DataTable';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';

const SLUG = 'marketplace-market-orders-order-transitions';
const ROUTE = '/market/orders/{order_id}/transitions';
/**
 * `GET /api/v1/commerce/orders/{order_id}/transitions` —
 * `services/commerce/routers/commerce.py:271`. The handler declares
 * `response_model=list[str]` and returns the bare list, so there is no envelope
 * key to name and `rowsKey` is left undefined: `readRows` then takes the payload
 * itself. Declaring a key here would render the empty state over a 200.
 */
const PATH = '/api/v1/commerce/orders/{order_id}/transitions';

type Payload = string[];

/**
 * The transitions the order state machine currently allows.
 *
 * The commerce spine publishes this alongside the order document, and it is the
 * list a command form needs before it can offer anything: a transition the
 * machine does not allow is a 400, so rendering one regardless would be a page
 * offering an action the gateway refuses. This page therefore reports the
 * allowed set and offers nothing.
 *
 * The column is declared rather than inferred, because the payload is a list of
 * strings: `inferColumns` reads `Object.keys` off the first row, and on a string
 * that yields character indices rather than fields, which would render a table
 * with no readable header and no cell text.
 */
export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}): Promise<Metadata> {
  const { locale, id } = await params;
  const t = await getTranslations('market.orderTransitions');
  return {
    title: t('title'),
    description: t('lead'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/market/orders/${id}/transitions`,
      title: t('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, ROUTE),
      languages: languageAlternates(ROUTE),
    },
    robots: { index: false, follow: true },
  };
}

export default async function OrderTransitionsPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale, id } = await params;
  const t = await getTranslations('market.orderTransitions');
  const labels = await resourceLabels();
  const endpoint = PATH.replace('{order_id}', encodeURIComponent(id));
  const result = await fetchResource<Payload>(endpoint);

  const columns: Column<Payload[number]>[] = [
    { key: 'transition', header: t('transition'), render: (row) => row },
  ];

  // `commerce.py:271` returns a bare `list[str]` — no envelope and no
  // `rowsKey`, because the array *is* the rows. So the row type is `string`,
  // which is `Payload[number]`; declaring `ResourcePage<Payload>` typed the row
  // as `string[]` and rejected the columns.
  return (
    <ResourcePage<string, Payload>
      slug={SLUG}
      locale={locale}
      title={t('title')}
      description={t('lead')}
      path={endpoint}
      result={result}
      mode="rows"
      columns={columns}
      rowKey={(row) => String(row)}
      labels={labels}
    >
      <p className="text-sm text-[var(--color-ink-soft)]">{t('note')}</p>
    </ResourcePage>
  );
}
