'use client';

import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useCallback, useEffect, useState } from 'react';
import { type MarketDataState, MarketDataStateNotice } from '@/components/market/MarketDataState';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { type ApiFailureKind, classifyApiFailure } from '@/lib/api/cart';
import { type ProductSearchHit, SEARCH_SOURCE, searchProducts } from '@/lib/api/market';
import { isOnline, registerConnectivityListeners } from '@/lib/offline/connectivity';

export default function SearchPage() {
  const product = useTranslations('market.product');
  const market = useTranslations('market');
  const common = useTranslations('common');
  const nav = useTranslations('nav');
  const statusLine = useTranslations('statusLine');
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const router = useRouter();
  const locale = pathname.split('/')[1] || 'fa';

  // `GET /products/search` requires `q`, so the term lives in the URL and the
  // request is only issued for a term the user actually submitted.
  const query = (searchParams.get('q') ?? '').trim();
  const [term, setTerm] = useState(query);
  const [hits, setHits] = useState<ProductSearchHit[]>([]);
  const [dataState, setDataState] = useState<MarketDataState>('unavailable');
  const [failureKind, setFailureKind] = useState<ApiFailureKind>('server');
  const [detail, setDetail] = useState('');

  const load = useCallback(async () => {
    if (!query) {
      setHits([]);
      setDataState('unavailable');
      return;
    }
    if (!isOnline()) {
      setDataState('offline');
      return;
    }
    setDetail('');
    const result = await searchProducts(query);
    if (!result.ok) {
      const kind = classifyApiFailure(result.status);
      setFailureKind(kind);
      setDetail(result.error);
      setHits([]);
      setDataState(kind === 'offline' ? 'offline' : kind === 'auth' ? 'unauthenticated' : 'error');
      return;
    }
    setHits(result.data);
    setDataState(result.data.length > 0 ? 'live' : 'empty');
  }, [query]);

  useEffect(() => {
    setTerm(query);
    void load();
  }, [query, load]);

  useEffect(() => {
    if (dataState !== 'offline') return;
    return registerConnectivityListeners((online) => {
      if (online) void load();
    });
  }, [dataState, load]);

  const formatPrice = (price: number) =>
    new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(price);

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-6">
        <header className="mb-8">
          <nav className="mb-4">
            <button
              type="button"
              onClick={() => router.push(`/${locale}/market`)}
              className="text-sm text-ink-soft underline hover:text-ink"
            >
              {nav('market')}
            </button>
          </nav>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{market('title')}</h1>
              <p className="mt-2 text-ink-soft">{market('lead')}</p>
            </div>
            <ProvenanceStamp
              source={SEARCH_SOURCE}
              label={product('productProvenance')}
              method={dataState === 'live' ? statusLine('realData') : undefined}
            />
          </div>
        </header>

        <form
          className="mb-8 flex flex-wrap items-end gap-3"
          onSubmit={(event) => {
            event.preventDefault();
            router.push(`/${locale}/market/search?q=${encodeURIComponent(term.trim())}`);
          }}
        >
          <div className="min-w-0 flex-1">
            <label htmlFor="market-search" className="mb-1 block text-sm text-ink-soft">
              {market('products')}
            </label>
            <input
              id="market-search"
              type="search"
              value={term}
              onChange={(event) => setTerm(event.target.value)}
              className="w-full rounded border border-line bg-surface px-4 py-2 text-ink"
            />
          </div>
          <Button variant="primary" type="submit">
            {common('view')}
          </Button>
        </form>

        {dataState === 'loading' && <MarketDataStateNotice state="loading" locale={locale} />}

        {dataState !== 'live' && dataState !== 'loading' && (
          <MarketDataStateNotice
            state={dataState}
            locale={locale}
            detail={dataState === 'error' ? detail : undefined}
            failureKind={failureKind}
            onRetry={query ? () => void load() : undefined}
            emptyMessage={market('empty')}
            emptyAction={
              <Button variant="primary" onClick={() => router.push(`/${locale}/market`)}>
                {nav('market')}
              </Button>
            }
          />
        )}

        {dataState === 'live' && (
          <div className="space-y-4">
            <p className="text-sm text-ink-soft">{query}</p>
            {hits.map((hit) => (
              <Card key={hit.id} density="compact">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="min-w-0">
                    <h2 className="font-medium text-ink">{hit.name}</h2>
                    <p className="num mt-1 font-mono text-xs text-ink-soft">{hit.id}</p>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="num text-sm text-ink">
                      {product('unitPrice')}: {formatPrice(hit.pricePerKg)}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => router.push(`/${locale}/market/product/${hit.id}`)}
                    >
                      {common('view')}
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
