import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';
import { fetchResource, ResourcePage, resourceLabels } from '@/components/ResourcePage';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';

const SLUG = 'marketplace-market-escrow-orders';
const ROUTE = '/market/escrow/orders';
/**
 * `GET /api/v1/commerce/orders` — `services/commerce/routers/commerce.py:145`.
 * The handler returns `{"orders": [...], "count": n}` (commerce.py:159-172), so the
 * rows key is `orders`. The list is buyer-scoped: `list_orders` falls back to the
 * authenticated user when `buyer_id` is absent, so a bare GET is already the
 * reader's own orders and no `buyer_id` is ever sent from the browser.
 */
const PATH = '/api/v1/commerce/orders';

type Payload = { orders?: Array<Record<string, unknown>>; count?: number };

/**
 * The escrow order index.
 *
 * This route is the static sibling of `/market/escrow/[id]`, and before it existed
 * the dynamic segment captured it: a reader asking for their escrow orders landed
 * on the payment-escrow record for a payment whose id happened to be the literal
 * string `orders`, which the gateway answers with a 404. A static segment is
 * matched ahead of a named dynamic one in the App Router, so this page now wins
 * that route and `escrow/[id]` serves only real payment ids.
 */
export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations('market.escrowOrders');
  return {
    title: t('title'),
    description: t('lead'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}${ROUTE}`,
      title: t('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, ROUTE),
      languages: languageAlternates(ROUTE),
    },
    robots: { index: false, follow: true },
  };
}

export default async function EscrowOrdersPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = await getTranslations('market.escrowOrders');
  const labels = await resourceLabels();
  const result = await fetchResource<Payload>(PATH);

  // The generic on `ResourcePage` is the *row* type, not the envelope.
  // `ResourcePageProps<T>` types `rowKey` and `columns` on `T`, and `readRows`
  // extracts `T[]` via `rowsKey`, so passing the envelope made `rowKey` receive
  // the envelope and `row.id` fail to resolve. `commerce.py:159-172` returns
  // `{count, orders}`, and each element of `orders` is a free-form order record,
  // which is what `Record<string, unknown>` states.
  return (
    <ResourcePage<Record<string, unknown>>
      slug={SLUG}
      locale={locale}
      title={t('title')}
      description={t('lead')}
      path={PATH}
      result={result}
      mode="rows"
      rowsKey="orders"
      rowKey={(row) => String(row.id ?? JSON.stringify(row).slice(0, 24))}
      labels={labels}
    >
      {({ state }) => (
        <p className="text-sm text-[var(--color-ink-soft)]">
          {state === 'error' ? t('authHint') : t('escrowByDefault')}
        </p>
      )}
    </ResourcePage>
  );
}
