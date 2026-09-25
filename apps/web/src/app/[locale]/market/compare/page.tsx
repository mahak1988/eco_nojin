'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useCallback, useEffect, useState } from 'react';
import { type MarketDataState, MarketDataStateNotice } from '@/components/market/MarketDataState';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { type ApiFailureKind, classifyApiFailure } from '@/lib/api/cart';
import { listProducts, PRODUCTS_SOURCE } from '@/lib/api/market';
import { isOnline, registerConnectivityListeners } from '@/lib/offline/connectivity';
import type { ProductListing } from '@/types/market';

const MAX_COMPARE = 4;

export default function ComparePage() {
  const t = useTranslations('market.compare');
  const stock = useTranslations('market.product');
  const market = useTranslations('market');
  const common = useTranslations('common');
  const statusLine = useTranslations('statusLine');
  const pathname = usePathname();
  const router = useRouter();
  const locale = pathname.split('/')[1] || 'fa';

  const [products, setProducts] = useState<ProductListing[]>([]);
  const [dataState, setDataState] = useState<MarketDataState>('loading');
  const [failureKind, setFailureKind] = useState<ApiFailureKind>('server');
  const [detail, setDetail] = useState('');
  const [selected, setSelected] = useState<string[]>([]);

  const load = useCallback(async () => {
    if (!isOnline()) {
      setDataState('offline');
      return;
    }
    setDetail('');
    const result = await listProducts({ pageSize: 50 });
    if (!result.ok) {
      const kind = classifyApiFailure(result.status);
      setFailureKind(kind);
      setDetail(result.error);
      setDataState(kind === 'offline' ? 'offline' : kind === 'auth' ? 'unauthenticated' : 'error');
      return;
    }
    setProducts(result.data.products);
    setDataState(result.data.products.length > 0 ? 'live' : 'empty');
  }, []);

  useEffect(() => {
    setDataState('loading');
    void load();
  }, [load]);

  useEffect(() => {
    if (dataState !== 'offline') return;
    return registerConnectivityListeners((online) => {
      if (online) void load();
    });
  }, [dataState, load]);

  const selectedProducts = products
    .filter((product) => selected.includes(product.id))
    .slice(0, MAX_COMPARE);

  const toggleProduct = (id: string) => {
    setSelected((current) =>
      current.includes(id)
        ? current.filter((value) => value !== id)
        : current.length < MAX_COMPARE
          ? [...current, id]
          : current,
    );
  };

  const formatPrice = (price: number) =>
    new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(price);

  const hasCarbon = selectedProducts.some((product) => product.carbonFootprint !== undefined);
  const hasWater = selectedProducts.some((product) => product.waterFootprint !== undefined);

  const fields = [
    {
      key: 'price',
      label: t('price'),
      render: (p: ProductListing) => `${formatPrice(p.price)} / ${p.unit}`,
    },
    { key: 'category', label: t('category'), render: (p: ProductListing) => p.category.name.en },
    { key: 'origin', label: t('origin'), render: (p: ProductListing) => p.origin ?? '' },
    { key: 'producer', label: t('producer'), render: (p: ProductListing) => p.producer.name },
    {
      key: 'availability',
      label: t('availability'),
      render: (p: ProductListing) =>
        p.stockQuantity !== undefined
          ? `${p.inStock ? stock('inStock') : stock('outOfStock')} · ${p.stockQuantity}`
          : statusLine('unavailable'),
    },
    {
      key: 'organic',
      label: t('organic'),
      render: (p: ProductListing) => (p.organic ? market('organicBadge') : ''),
    },
    ...(hasCarbon
      ? [
          {
            key: 'carbon',
            label: t('carbonImpact'),
            render: (p: ProductListing) =>
              p.carbonFootprint !== undefined ? `${p.carbonFootprint}` : statusLine('unavailable'),
          },
        ]
      : []),
    ...(hasWater
      ? [
          {
            key: 'water',
            label: t('waterImpact'),
            render: (p: ProductListing) =>
              p.waterFootprint !== undefined ? `${p.waterFootprint}` : statusLine('unavailable'),
          },
        ]
      : []),
  ];

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-6xl px-6 pb-12 pt-6">
        <header className="mb-8 flex flex-wrap items-center gap-3">
          <div className="flex-1">
            <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title')}</h1>
            <p className="mt-2 text-ink-soft">{t('lead')}</p>
          </div>
          <ProvenanceStamp
            source={PRODUCTS_SOURCE}
            label={t('compareProvenance')}
            method={dataState === 'live' ? statusLine('realData') : undefined}
          />
        </header>

        {dataState === 'loading' && <MarketDataStateNotice state="loading" locale={locale} />}

        {dataState !== 'live' && dataState !== 'loading' && (
          <MarketDataStateNotice
            state={dataState}
            locale={locale}
            detail={dataState === 'error' ? detail : undefined}
            failureKind={failureKind}
            onRetry={() => void load()}
            emptyMessage={t('noProductsSelected')}
          />
        )}

        {dataState === 'live' && (
          <>
            <Card density="compact" className="mb-8">
              <h2 className="mb-4 font-medium text-ink">{t('selectProducts')}</h2>
              <p className="mb-3 text-sm text-ink-soft">
                {t('maxFour')}: {selected.length}/{MAX_COMPARE}
              </p>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                {products.map((product) => (
                  <button
                    type="button"
                    key={product.id}
                    onClick={() => toggleProduct(product.id)}
                    aria-pressed={selected.includes(product.id)}
                    disabled={!selected.includes(product.id) && selected.length >= MAX_COMPARE}
                    className={`rounded-md border p-3 text-left disabled:opacity-40 ${
                      selected.includes(product.id)
                        ? 'border-forest bg-forest/5'
                        : 'border-line hover:border-ink/30'
                    }`}
                  >
                    <p className="font-medium text-ink">{product.name.en}</p>
                    <p className="text-sm text-ink-soft">{product.producer.name}</p>
                  </button>
                ))}
              </div>
            </Card>

            {selectedProducts.length === 0 ? (
              <Card density="cozy" className="py-8 text-center">
                <p className="text-ink-soft">{t('noProductsSelected')}</p>
              </Card>
            ) : (
              <Card density="compact">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-line">
                        <th className="px-3 py-3 text-left font-medium text-ink-soft">
                          {t('feature')}
                        </th>
                        {selectedProducts.map((product) => (
                          <th key={product.id} className="px-3 py-3 text-center">
                            <p className="font-medium text-ink">{product.name.en}</p>
                            <p className="text-xs text-ink-soft">{product.producer.name}</p>
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {fields.map((field) => (
                        <tr key={field.key} className="border-b border-line/50">
                          <td className="px-3 py-3 font-medium text-ink">{field.label}</td>
                          {selectedProducts.map((product) => (
                            <td key={product.id} className="num px-3 py-3 text-center">
                              {field.render(product)}
                            </td>
                          ))}
                        </tr>
                      ))}
                      <tr className="border-b border-line/50">
                        <td className="px-3 py-3 font-medium text-ink">{t('actions')}</td>
                        {selectedProducts.map((product) => (
                          <td key={product.id} className="px-3 py-3 text-center">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => router.push(`/${locale}/market/product/${product.id}`)}
                            >
                              {common('view')}
                            </Button>
                          </td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                </div>
                <p className="mt-4 text-center text-xs text-ink-soft">{t('antiFraudWarning')}</p>
              </Card>
            )}
          </>
        )}
      </div>
    </main>
  );
}
