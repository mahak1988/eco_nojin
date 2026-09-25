'use client';

import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { use, useCallback, useEffect, useState } from 'react';
import { type MarketDataState, MarketDataStateNotice } from '@/components/market/MarketDataState';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { useAuth } from '@/components/providers/AuthProvider';
import { StatusDot } from '@/components/StatusDot';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { type ApiFailureKind, addToCart, classifyApiFailure } from '@/lib/api/cart';
import { getProduct, type MarketProductDetail, PRODUCTS_SOURCE } from '@/lib/api/market';
import { isOnline, registerConnectivityListeners } from '@/lib/offline/connectivity';

function productSource(id: string): string {
  return `${PRODUCTS_SOURCE}/${encodeURIComponent(id)}`;
}

export default function ProductPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale: routeLocale, id } = use(params);
  const locale = routeLocale || 'fa';
  const t = useTranslations('market.product');
  const market = useTranslations('market');
  const common = useTranslations('common');
  const statusLine = useTranslations('statusLine');
  const authCommon = useTranslations('auth.common');
  const authSession = useTranslations('auth.session');
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();

  const [product, setProduct] = useState<MarketProductDetail | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [dataState, setDataState] = useState<MarketDataState>('loading');
  const [failureKind, setFailureKind] = useState<ApiFailureKind>('server');
  const [detail, setDetail] = useState('');
  const [addState, setAddState] = useState<'idle' | 'adding' | 'failed'>('idle');

  const source = productSource(id);

  const load = useCallback(async () => {
    if (!isOnline()) {
      setDataState('offline');
      return;
    }
    setDetail('');
    const result = await getProduct(id);
    if (!result.ok) {
      const kind = classifyApiFailure(result.status);
      setFailureKind(kind);
      setDetail(result.error);
      setDataState(kind === 'offline' ? 'offline' : 'error');
      return;
    }
    setProduct(result.data);
    setQuantity(
      result.data.minimumOrderKg && result.data.minimumOrderKg > 0 ? result.data.minimumOrderKg : 1,
    );
    setDataState('live');
  }, [id]);

  useEffect(() => {
    if (!id) return;
    setDataState('loading');
    void load();
  }, [id, load]);

  useEffect(() => {
    if (dataState !== 'offline') return;
    return registerConnectivityListeners((online) => {
      if (online) void load();
    });
  }, [dataState, load]);

  const available = product ? product.quantityAvailableKg : 0;
  const minimum =
    product?.minimumOrderKg && product.minimumOrderKg > 0 ? product.minimumOrderKg : 1;

  const handleAddToCart = async () => {
    if (!user || !product) {
      setAddState('failed');
      setDetail(authSession('signedOut'));
      return;
    }
    setAddState('adding');
    setDetail('');
    const result = await addToCart([{ productId: product.id, quantity }]);
    if (!result.ok) {
      setAddState('failed');
      setFailureKind(classifyApiFailure(result.status));
      setDetail(result.error);
      return;
    }
    setAddState('idle');
    router.push(`/${locale}/market/cart`);
  };

  const formatPrice = (price: number) =>
    new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(price);

  const hasEcoImpact =
    product?.carbonFootprintKgCo2 != null ||
    product?.waterFootprintLiters != null ||
    product?.batchNumber != null;

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-6xl px-6 pb-12 pt-6">
        <header className="mb-8">
          <nav className="mb-4 flex flex-wrap items-center gap-2 text-sm text-ink-soft">
            <button
              type="button"
              onClick={() => router.push(`/${locale}/market`)}
              className="text-ink-soft underline hover:text-ink"
            >
              {t('backToMarket')}
            </button>
            {product ? (
              <>
                <span aria-hidden="true">/</span>
                <span className="text-ink">{product.name}</span>
              </>
            ) : null}
          </nav>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h1 className="display text-3xl font-bold text-ink sm:text-4xl">
              {product?.name ?? ''}
            </h1>
            <ProvenanceStamp
              source={source}
              label={t('productProvenance')}
              method={dataState === 'live' ? statusLine('realData') : undefined}
            />
          </div>
          {product?.description ? (
            <p className="mt-3 text-ink-soft">{product.description}</p>
          ) : null}
        </header>

        {dataState !== 'live' && (
          <MarketDataStateNotice
            state={dataState}
            locale={locale}
            detail={dataState === 'error' ? detail : undefined}
            failureKind={failureKind}
            onRetry={() => void load()}
            emptyMessage={t('dataUnavailable')}
          />
        )}

        {product && dataState === 'live' && (
          <>
            {detail ? (
              <p role="alert" className="mb-6 rounded-md bg-clay/10 p-3 text-sm text-clay">
                {detail}
              </p>
            ) : null}

            <div className="grid gap-8 lg:grid-cols-2">
              <div className="space-y-4">
                {product.images.length > 0 ? (
                  <>
                    <div className="aspect-square w-full overflow-hidden rounded-lg border border-line bg-surface">
                      <Image
                        src={product.images[0]}
                        alt={product.name}
                        width={800}
                        height={800}
                        unoptimized
                        className="h-full w-full object-contain"
                      />
                    </div>
                    {product.images.length > 1 ? (
                      <div className="flex flex-wrap gap-2">
                        {product.images.slice(1).map((src) => (
                          <Image
                            key={src}
                            src={src}
                            alt={product.name}
                            width={128}
                            height={128}
                            unoptimized
                            className="h-16 w-16 rounded border border-line bg-surface object-cover"
                          />
                        ))}
                      </div>
                    ) : null}
                  </>
                ) : (
                  <div
                    role="status"
                    className="aspect-square w-full rounded-lg border border-line bg-surface p-6 text-sm text-ink-soft"
                  >
                    {statusLine('unavailable')}
                  </div>
                )}
              </div>

              <div className="space-y-6">
                <Card density="compact">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <StatusDot
                      state={available > 0 ? 'ok' : 'down'}
                      label={available > 0 ? t('inStock') : t('outOfStock')}
                    />
                    {product.organicCertified ? (
                      <span className="rounded-full border border-line px-2 py-0.5 text-[10px] text-forest">
                        {market('organicBadge')}
                      </span>
                    ) : null}
                  </div>
                  <dl className="mt-4 space-y-2">
                    <div className="flex justify-between">
                      <dt className="text-sm text-ink-soft">{t('unitPrice')}</dt>
                      <dd className="num font-medium text-ink">
                        {formatPrice(product.pricePerKg)}
                      </dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-sm text-ink-soft">{t('available')}</dt>
                      <dd className="num text-ink">{available}</dd>
                    </div>
                    {product.minimumOrderKg ? (
                      <div className="flex justify-between">
                        <dt className="text-sm text-ink-soft">{t('qty')}</dt>
                        <dd className="num text-ink">{product.minimumOrderKg}</dd>
                      </div>
                    ) : null}
                    {product.producerName || product.originLocation ? (
                      <div className="flex justify-between">
                        <dt className="text-sm text-ink-soft">{market('producers')}</dt>
                        <dd className="text-right text-ink">
                          {product.producerName}
                          {product.originLocation ? (
                            <span className="block text-xs text-ink-soft">
                              {product.originLocation}
                            </span>
                          ) : null}
                        </dd>
                      </div>
                    ) : null}
                    {product.harvestDate ? (
                      <div className="flex justify-between">
                        <dt className="text-sm text-ink-soft">{t('pricingHistory')}</dt>
                        <dd className="num text-ink">{product.harvestDate}</dd>
                      </div>
                    ) : null}
                    {product.traceabilityCode ? (
                      <div className="flex justify-between">
                        <dt className="text-sm text-ink-soft">{t('traceability')}</dt>
                        <dd className="num font-mono text-xs text-forest">
                          {product.traceabilityCode}
                        </dd>
                      </div>
                    ) : null}
                  </dl>
                </Card>

                <Card density="compact">
                  <h2 className="mb-3 font-medium text-ink">{t('quantity')}</h2>
                  <div className="flex items-center gap-4">
                    <button
                      type="button"
                      aria-label={t('qty')}
                      onClick={() => setQuantity((value) => Math.max(minimum, value - 1))}
                      disabled={quantity <= minimum || available === 0}
                      className="flex h-11 w-11 items-center justify-center rounded border border-line disabled:opacity-40"
                    >
                      −
                    </button>
                    <span className="num w-10 text-center font-medium text-ink">{quantity}</span>
                    <button
                      type="button"
                      aria-label={t('qty')}
                      onClick={() =>
                        setQuantity((value) => Math.min(Math.max(available, minimum), value + 1))
                      }
                      disabled={available === 0 || quantity >= Math.max(available, minimum)}
                      className="flex h-11 w-11 items-center justify-center rounded border border-line disabled:opacity-40"
                    >
                      +
                    </button>
                  </div>
                  <div className="mt-4 flex items-center justify-between border-t border-line pt-3">
                    <span className="font-medium text-ink">{common('total')}</span>
                    <span className="num text-xl font-bold text-forest">
                      {formatPrice(product.pricePerKg * quantity)}
                    </span>
                  </div>
                </Card>

                {authLoading ? null : user ? (
                  <Button
                    variant="primary"
                    size="lg"
                    className="w-full"
                    loading={addState === 'adding'}
                    disabled={available === 0}
                    onClick={() => void handleAddToCart()}
                  >
                    {t('addToCart')}
                  </Button>
                ) : (
                  <div
                    role="status"
                    className="rounded-[var(--radius-l)] border border-[var(--color-line)] bg-[var(--color-surface-2)] p-4"
                  >
                    <p className="text-sm text-[var(--color-ink-soft)]">
                      {authSession('signedOut')}
                    </p>
                    <a
                      href={`/${locale}/auth/login`}
                      className="mt-3 inline-flex rounded-[var(--radius-m)] border border-[var(--color-line)] px-3 py-2 text-sm font-semibold text-[var(--color-ink)]"
                    >
                      {authCommon('signIn')}
                    </a>
                  </div>
                )}
              </div>
            </div>

            <div className="mt-8 grid gap-8 lg:grid-cols-2">
              <Card density="compact">
                <h2 className="mb-3 font-medium text-ink">{t('productSpecs')}</h2>
                <p role="status" className="text-sm text-ink-soft">
                  {statusLine('unavailable')}
                </p>
              </Card>

              <Card density="compact">
                <h2 className="mb-3 font-medium text-ink">{t('ecoImpact')}</h2>
                {!hasEcoImpact ? (
                  <p role="status" className="text-sm text-ink-soft">
                    {statusLine('unavailable')}
                  </p>
                ) : (
                  <dl className="space-y-3">
                    {product.carbonFootprintKgCo2 != null ? (
                      <div className="flex justify-between">
                        <dt className="text-sm text-ink-soft">{t('carbonSequestration')}</dt>
                        <dd className="num font-medium text-ink">{product.carbonFootprintKgCo2}</dd>
                      </div>
                    ) : null}
                    {product.waterFootprintLiters != null ? (
                      <div className="flex justify-between">
                        <dt className="text-sm text-ink-soft">{t('waterSavings')}</dt>
                        <dd className="num font-medium text-ink">{product.waterFootprintLiters}</dd>
                      </div>
                    ) : null}
                    {product.batchNumber ? (
                      <div className="flex justify-between">
                        <dt className="text-sm text-ink-soft">{t('certifications')}</dt>
                        <dd className="num font-mono text-xs text-ink">{product.batchNumber}</dd>
                      </div>
                    ) : null}
                  </dl>
                )}
              </Card>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
