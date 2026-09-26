'use client';

import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useCallback, useEffect, useState } from 'react';
import { type MarketDataState, MarketDataStateNotice } from '@/components/market/MarketDataState';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { type ApiFailureKind, classifyApiFailure } from '@/lib/api/cart';
import {
  type ProductFilterForm,
  type ProductSearchHit,
  parseProductFilterForm,
  SEARCH_SOURCE,
  searchProducts,
} from '@/lib/api/market';
import { isOnline, registerConnectivityListeners } from '@/lib/offline/connectivity';

const PRICE_WINDOW: ProductFilterForm = {
  category: '',
  organic: false,
  priceMin: '',
  priceMax: '',
  limit: '',
};

interface PriceWindow {
  min: number | undefined;
  max: number | undefined;
}

/**
 * Filter dimensions a keyword search cannot apply. `GET /products/search` takes
 * only `q`, so they are reported as unavailable instead of being sent anyway.
 */
const UNSUPPORTED = ['category', 'organic_only', 'sort', 'radius'] as const;

export default function AdvancedSearchPage() {
  const product = useTranslations('market.product');
  const compare = useTranslations('market.compare');
  const market = useTranslations('market');
  const common = useTranslations('common');
  const nav = useTranslations('nav');
  const statusLine = useTranslations('statusLine');
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const router = useRouter();
  const locale = pathname.split('/')[1] || 'fa';

  const query = (searchParams.get('q') ?? '').trim();
  const [term, setTerm] = useState(query);
  const [draft, setDraft] = useState(PRICE_WINDOW);
  const [window, setWindow] = useState<PriceWindow>({ min: undefined, max: undefined });
  const [issues, setIssues] = useState<string[]>([]);
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
    // The price window is applied to the unit prices the gateway returned; no
    // value is estimated for a hit that carries none.
    const withinWindow = result.data.filter(
      (hit) =>
        (window.min === undefined || hit.pricePerKg >= window.min) &&
        (window.max === undefined || hit.pricePerKg <= window.max),
    );
    setHits(withinWindow);
    setDataState(withinWindow.length > 0 ? 'live' : 'empty');
  }, [query, window.min, window.max]);

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
              onClick={() => router.push(`/${locale}/market/search`)}
              className="text-sm text-ink-soft underline hover:text-ink"
            >
              {market('products')}
            </button>
          </nav>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h1 className="display text-3xl font-bold text-ink sm:text-4xl">
                {market('products')}
              </h1>
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
          className="mb-6 space-y-4"
          onSubmit={(event) => {
            event.preventDefault();
            const parsed = parseProductFilterForm(draft);
            if (!parsed.ok) {
              setIssues(parsed.issues);
              return;
            }
            setIssues([]);
            setWindow({
              min: parsed.filters.priceMin,
              max: parsed.filters.priceMax,
            });
            router.push(`/${locale}/market/search/advanced?q=${encodeURIComponent(term.trim())}`);
          }}
        >
          <div>
            <label htmlFor="advanced-term" className="mb-1 block text-sm text-ink-soft">
              {market('products')}
            </label>
            <input
              id="advanced-term"
              type="search"
              value={term}
              onChange={(event) => setTerm(event.target.value)}
              className="w-full rounded border border-line bg-surface px-4 py-2 text-ink"
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="advanced-min" className="mb-1 block text-sm text-ink-soft">
                {compare('price')}
              </label>
              <input
                id="advanced-min"
                type="number"
                inputMode="decimal"
                min={0}
                value={draft.priceMin}
                onChange={(event) => setDraft({ ...draft, priceMin: event.target.value })}
                className="w-full rounded border border-line bg-surface px-4 py-2 text-ink"
              />
            </div>
            <div>
              <label htmlFor="advanced-max" className="mb-1 block text-sm text-ink-soft">
                {product('unitPrice')}
              </label>
              <input
                id="advanced-max"
                type="number"
                inputMode="decimal"
                min={0}
                value={draft.priceMax}
                onChange={(event) => setDraft({ ...draft, priceMax: event.target.value })}
                className="w-full rounded border border-line bg-surface px-4 py-2 text-ink"
              />
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Button variant="primary" type="submit">
              {common('view')}
            </Button>
            <Button
              variant="ghost"
              type="button"
              onClick={() => router.push(`/${locale}/market/search/filters`)}
            >
              {product('productSpecs')}
            </Button>
          </div>
          {issues.length > 0 ? (
            <ul role="alert" className="space-y-1 text-sm text-clay">
              {issues.map((issue) => (
                <li key={issue}>{issue}</li>
              ))}
            </ul>
          ) : null}
        </form>

        <Card density="compact" className="mb-8">
          <h2 className="mb-3 font-medium text-ink">{common('limitsLabel')}</h2>
          <ul className="space-y-1">
            {UNSUPPORTED.map((param) => (
              <li key={param} className="flex items-center justify-between gap-3 text-sm">
                <span className="num font-mono text-xs text-ink-soft">{param}</span>
                <span className="text-ink-soft">{statusLine('unavailable')}</span>
              </li>
            ))}
          </ul>
        </Card>

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
