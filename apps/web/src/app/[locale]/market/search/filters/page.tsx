'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useCallback, useEffect, useState } from 'react';
import { type MarketDataState, MarketDataStateNotice } from '@/components/market/MarketDataState';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { type ApiFailureKind, classifyApiFailure } from '@/lib/api/cart';
import {
  listProducts,
  PRODUCTS_SOURCE,
  type ProductFilterForm,
  type ProductFilterParam,
  parseProductFilterForm,
} from '@/lib/api/market';
import { isOnline, registerConnectivityListeners } from '@/lib/offline/connectivity';
import type { ProductListing, SearchFilters } from '@/types/market';

const EMPTY_FORM: ProductFilterForm = {
  category: '',
  organic: false,
  priceMin: '',
  priceMax: '',
  limit: '',
};

export default function SearchFiltersPage() {
  const product = useTranslations('market.product');
  const compare = useTranslations('market.compare');
  const market = useTranslations('market');
  const common = useTranslations('common');
  const nav = useTranslations('nav');
  const statusLine = useTranslations('statusLine');
  const pathname = usePathname();
  const router = useRouter();
  const locale = pathname.split('/')[1] || 'fa';

  const [form, setForm] = useState<ProductFilterForm>(EMPTY_FORM);
  const [filters, setFilters] = useState<SearchFilters | null>(null);
  const [applied, setApplied] = useState<ProductFilterParam[]>([]);
  const [issues, setIssues] = useState<string[]>([]);
  const [products, setProducts] = useState<ProductListing[]>([]);
  const [dataState, setDataState] = useState<MarketDataState>('unavailable');
  const [failureKind, setFailureKind] = useState<ApiFailureKind>('server');
  const [detail, setDetail] = useState('');

  const load = useCallback(async () => {
    if (!filters) {
      setProducts([]);
      setDataState('unavailable');
      return;
    }
    if (!isOnline()) {
      setDataState('offline');
      return;
    }
    setDetail('');
    const result = await listProducts(filters);
    if (!result.ok) {
      const kind = classifyApiFailure(result.status);
      setFailureKind(kind);
      setDetail(result.error);
      setProducts([]);
      setDataState(kind === 'offline' ? 'offline' : kind === 'auth' ? 'unauthenticated' : 'error');
      return;
    }
    setProducts(result.data.products);
    setDataState(result.data.products.length > 0 ? 'live' : 'empty');
  }, [filters]);

  useEffect(() => {
    void load();
  }, [load]);

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
              <h1 className="display text-3xl font-bold text-ink sm:text-4xl">
                {market('products')}
              </h1>
              <p className="mt-2 text-ink-soft">{market('lead')}</p>
            </div>
            <ProvenanceStamp
              source={PRODUCTS_SOURCE}
              label={product('productProvenance')}
              method={dataState === 'live' ? statusLine('realData') : undefined}
            />
          </div>
        </header>

        <form
          className="mb-8 space-y-4"
          onSubmit={(event) => {
            event.preventDefault();
            const parsed = parseProductFilterForm(form);
            if (!parsed.ok) {
              setIssues(parsed.issues);
              return;
            }
            setIssues([]);
            setFilters(parsed.filters);
            setApplied(parsed.applied);
          }}
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="filter-category" className="mb-1 block text-sm text-ink-soft">
                {compare('category')}
              </label>
              <input
                id="filter-category"
                type="text"
                value={form.category}
                onChange={(event) => setForm({ ...form, category: event.target.value })}
                className="w-full rounded border border-line bg-surface px-4 py-2 text-ink"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="filter-min" className="mb-1 block text-sm text-ink-soft">
                  {compare('price')}
                </label>
                <input
                  id="filter-min"
                  type="number"
                  inputMode="decimal"
                  min={0}
                  value={form.priceMin}
                  onChange={(event) => setForm({ ...form, priceMin: event.target.value })}
                  className="w-full rounded border border-line bg-surface px-4 py-2 text-ink"
                />
              </div>
              <div>
                <label htmlFor="filter-max" className="mb-1 block text-sm text-ink-soft">
                  {product('unitPrice')}
                </label>
                <input
                  id="filter-max"
                  type="number"
                  inputMode="decimal"
                  min={0}
                  value={form.priceMax}
                  onChange={(event) => setForm({ ...form, priceMax: event.target.value })}
                  className="w-full rounded border border-line bg-surface px-4 py-2 text-ink"
                />
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-4">
            <label className="flex items-center gap-3 text-sm text-ink">
              <input
                type="checkbox"
                checked={form.organic}
                onChange={(event) => setForm({ ...form, organic: event.target.checked })}
                className="h-4 w-4"
              />
              {compare('organic')}
            </label>
            <div>
              <label htmlFor="filter-limit" className="mb-1 block text-sm text-ink-soft">
                {product('quantity')}
              </label>
              <input
                id="filter-limit"
                type="number"
                inputMode="numeric"
                min={1}
                value={form.limit}
                onChange={(event) => setForm({ ...form, limit: event.target.value })}
                className="w-24 rounded border border-line bg-surface px-3 py-2 text-ink"
              />
            </div>
            <Button variant="primary" type="submit" className="ms-auto">
              {common('view')}
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

        {applied.length > 0 && (
          <div className="mb-6 flex flex-wrap items-center gap-2">
            <span className="text-sm text-ink-soft">{common('evidence')}:</span>
            {applied.map((param) => (
              <span key={param} className="num rounded border border-line px-2 py-0.5 text-xs">
                {param}
              </span>
            ))}
          </div>
        )}

        {dataState === 'loading' && <MarketDataStateNotice state="loading" locale={locale} />}

        {dataState !== 'live' && dataState !== 'loading' && (
          <MarketDataStateNotice
            state={dataState}
            locale={locale}
            detail={dataState === 'error' ? detail : undefined}
            failureKind={failureKind}
            onRetry={filters ? () => void load() : undefined}
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
            {products.map((item) => (
              <Card key={item.id} density="compact">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="min-w-0">
                    <h2 className="font-medium text-ink">{item.name.en}</h2>
                    <p className="mt-1 text-sm text-ink-soft">
                      {item.producer.name}
                      {item.origin ? ` · ${item.origin}` : ''}
                    </p>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="num text-sm text-ink">
                      {product('unitPrice')}: {formatPrice(item.price)}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => router.push(`/${locale}/market/product/${item.id}`)}
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
