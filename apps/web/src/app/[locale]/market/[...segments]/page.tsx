import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getTranslations, setRequestLocale } from 'next-intl/server';

import { MarketplaceTemplatePage } from '@/components/market/MarketplaceTemplatePage';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import {
  fillPathParams,
  resolveMarketplaceGroup,
  resolveMarketplaceSurface,
  surfaceParams,
} from '../surfaces';

export const dynamic = 'force-dynamic';

type Params = Promise<{ locale: string; segments: string[] }>;

/**
 * The catch-all resolves by lookup, not by pattern.
 *
 * It used to accept one shape — a group base followed by a `{prefix}-{index}`
 * slug — and `notFound()` for everything else, so every declared marketplace
 * surface that is not one of the 444 generated slugs was unreachable. The rule
 * now is:
 *
 *   1. a declared surface (`./surfaces`) answers the path, either as a capability
 *      with no published read contract or as a command endpoint;
 *   2. a group base with a `{prefix}-{index}` slug falls back to the generated
 *      template;
 *   3. anything else is a 404, because a path nobody declared is not a page.
 *
 * `robots` follows the same split. A surface with no read contract and the 444
 * generated slugs stay `noindex` — that is the MKT-G6 acceptance criterion for
 * an unconnected capability, and flipping it would be the same defect in the
 * other direction. A surface whose contract is published is a real document, but
 * it is a command or a capability, not an indexable record, so the whole
 * catch-all stays `noindex` and the dedicated pages carry the indexable
 * metadata.
 */
export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { locale, segments } = await params;
  setRequestLocale(locale);
  const surface = resolveMarketplaceSurface(segments);
  const t = await getTranslations(
    surface?.kind === 'action' ? 'market.surface' : 'market.template',
  );
  return {
    title: surface?.kind === 'action' ? t('actionTitle') : t('title'),
    description: surface?.kind === 'action' ? t('actionLead') : t('description'),
    robots: { index: false, follow: true },
  };
}

export default async function MarketplaceCatchAllPage({ params }: { params: Params }) {
  const { locale, segments } = await params;
  setRequestLocale(locale);

  const surface = resolveMarketplaceSurface(segments);
  const requested = `/${segments.join('/')}`;

  if (surface) {
    const bound = surfaceParams(surface, segments) ?? {};
    if (surface.kind === 'unavailable') {
      return (
        <MarketplaceTemplatePage
          locale={locale}
          group=""
          slug={requested.slice(1)}
          source={surface.sourceOfTruth}
        />
      );
    }

    const t = await getTranslations('market.surface');
    const read = surface.read ? fillPathParams(surface.read, bound) : null;

    return (
      <main id="main" className="min-h-dvh">
        <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
          <Link href={`/${locale}/market`} className="text-sm text-[var(--color-forest)] underline">
            {t('back')}
          </Link>

          <header className="mt-6">
            <div className="flex flex-wrap items-center gap-3">
              <StatusDot state="warn" label={t('actionStatus')} />
              <span className="num font-mono text-xs text-[var(--color-ink-soft)]">
                {requested}
              </span>
              <ProvenanceStamp
                source={surface.read ?? surface.sourceOfTruth}
                label={t('actionSource')}
                method={surface.method}
              />
            </div>
            <h1 className="display mt-4 text-3xl font-bold text-[var(--color-ink)]">
              {t('actionTitle')}
            </h1>
            <p className="mt-3 text-[var(--color-ink-soft)]">{t('actionLead')}</p>
          </header>

          <Card density="cozy" className="mt-6">
            <h2 className="font-semibold text-[var(--color-ink)]">{t('actionCommandTitle')}</h2>
            <p className="mt-2 text-sm text-[var(--color-ink-soft)]">
              {t('actionCommandDescription')}
            </p>
            <p className="num mt-3 font-mono text-sm text-[var(--color-ink)]">
              {surface.method} {surface.path}
            </p>
          </Card>

          <Card density="cozy" className="mt-4">
            <h2 className="font-semibold text-[var(--color-ink)]">{t('actionReadTitle')}</h2>
            {read ? (
              <>
                <p className="mt-2 text-sm text-[var(--color-ink-soft)]">
                  {t('actionReadDescription')}
                </p>
                <p className="num mt-3 font-mono text-sm break-all text-[var(--color-ink)]">
                  {read}
                </p>
                {/* `read` is `surface.read` with its path parameters filled in,
                      and it is non-null in this branch. `surface.read` itself is
                      `string | null` for a surface with no read contract, so
                      passing the property here re-widened the type the guard had
                      just narrowed. */}
                <ReadLink locale={locale} readTemplate={read} params={bound} />
              </>
            ) : (
              <p className="mt-2 text-sm text-[var(--color-ink-soft)]">{t('actionNoRead')}</p>
            )}
          </Card>

          <Card density="cozy" className="mt-4">
            <h2 className="font-semibold text-[var(--color-ink)]">{t('actionFormTitle')}</h2>
            <p className="mt-2 text-sm text-[var(--color-ink-soft)]">
              {t('actionFormDescription')}
            </p>
          </Card>

          <p className="mt-6 text-xs text-[var(--color-ink-soft)]">
            {t('actionDeclaredBy')}: <span className="num font-mono">{surface.sourceOfTruth}</span>
          </p>
        </div>
      </main>
    );
  }

  const group = resolveMarketplaceGroup(segments);
  if (group) {
    return <MarketplaceTemplatePage locale={locale} group={group.group.id} slug={group.slug} />;
  }

  notFound();
}

/**
 * Send the reader to the page that renders a surface's read contract.
 *
 * A gateway path is not a page path, so it cannot be linked directly. Only the
 * read contracts that a page in this tree already renders are linked; every other
 * read is named and left for the surface owner to route, rather than being
 * turned into a link to a page that does not exist.
 */
const PAGE_FOR_READ: Record<string, string> = {
  '/api/v1/commerce/orders': '/market/escrow/orders',
  '/api/v1/marketplace/cart': '/market/cart',
  '/api/v1/marketplace/marketplaces': '/market/bazaars',
  '/api/v1/marketplace/marketplaces/{marketplace_id}': '/market/marketplaces/{marketplace_id}',
  '/api/v1/marketplace/payments/{payment_id}/escrow': '/market/payments/{payment_id}/escrow',
  '/api/v1/marketplace/products/{product_id}': '/market/products/{product_id}',
  '/api/v1/marketplace/vendors/{vendor_id}': '/market/vendors/{vendor_id}',
};

async function ReadLink({
  locale,
  readTemplate,
  params,
}: {
  locale: string;
  readTemplate: string;
  params: Record<string, string>;
}) {
  const t = await getTranslations('market.surface');
  const page = PAGE_FOR_READ[readTemplate];
  if (!page) return null;
  return (
    <Link
      href={`/${locale}${fillPathParams(page, params)}`}
      className="mt-4 inline-block text-sm text-[var(--color-forest)] underline"
    >
      {t('actionReadLink')}
    </Link>
  );
}
