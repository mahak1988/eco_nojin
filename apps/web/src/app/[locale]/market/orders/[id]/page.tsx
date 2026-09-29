import type { Metadata } from 'next';
import Link from 'next/link';
import { getTranslations } from 'next-intl/server';
import { fetchResource, ResourcePage, resourceLabels } from '@/components/ResourcePage';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';

const SLUG = 'marketplace-market-orders-order';
/** The route directory is `[id]`; the gateway parameter is `order_id`. */
const ROUTE = '/market/orders/{order_id}';
/**
 * `GET /api/v1/commerce/orders/{order_id}` — `services/commerce/routers/commerce.py:97`.
 * The handler returns one order document with its items, its payment intents and
 * the transitions the state machine currently allows (commerce.py:110-142), so
 * this is a `record` surface rather than a table.
 */
const PATH = '/api/v1/commerce/orders/{order_id}';

type Payload = Record<string, unknown>;

/**
 * The commerce order record.
 *
 * `/market/orders/[id]` had no page of its own, so every `/market/orders/{id}`
 * request fell through to the marketplace catch-all, which resolved no group for
 * a bare identifier and returned 404 — the reader's own order was unreachable
 * while its `/track`, `/timeline` and `/evidence` children rendered. This is the
 * spine the brief names as real and mounted, so it is bound here.
 *
 * `require_user` is declared on the handler (commerce.py:98), so the response is
 * the authenticated reader's order or a 401. The error state says exactly that
 * rather than showing an empty table.
 */
export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}): Promise<Metadata> {
  const { locale, id } = await params;
  const t = await getTranslations('market.orderRecord');
  return {
    title: t('title'),
    description: t('lead'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/market/orders/${id}`,
      title: t('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, ROUTE),
      languages: languageAlternates(ROUTE),
    },
    robots: { index: false, follow: true },
  };
}

export default async function OrderRecordPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale, id } = await params;
  const t = await getTranslations('market.orderRecord');
  const labels = await resourceLabels();
  const endpoint = `${PATH.replace('{order_id}', encodeURIComponent(id))}`;
  const result = await fetchResource<Payload>(endpoint);

  return (
    <ResourcePage<Payload>
      slug={SLUG}
      locale={locale}
      title={t('title')}
      description={t('lead')}
      path={endpoint}
      result={result}
      mode="record"
      labels={labels}
    >
      {({ state }) => (
        <div className="space-y-2 text-sm text-[var(--color-ink-soft)]">
          {state === 'error' ? <p>{t('authHint')}</p> : null}
          <nav className="flex flex-wrap gap-4">
            <Link
              href={`/${locale}/market/orders/${id}/transitions`}
              className="text-[var(--color-forest)] underline"
            >
              {t('transitions')}
            </Link>
            <Link
              href={`/${locale}/market/orders/${id}/track`}
              className="text-[var(--color-forest)] underline"
            >
              {t('track')}
            </Link>
            <Link
              href={`/${locale}/market/orders/${id}/evidence`}
              className="text-[var(--color-forest)] underline"
            >
              {t('evidence')}
            </Link>
          </nav>
        </div>
      )}
    </ResourcePage>
  );
}
