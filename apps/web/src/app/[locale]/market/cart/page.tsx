'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useCallback, useEffect, useState } from 'react';
import { type MarketDataState, MarketDataStateNotice } from '@/components/market/MarketDataState';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { useAuth } from '@/components/providers/AuthProvider';
import { StatusDot } from '@/components/StatusDot';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import {
  type ApiResult,
  CART_SOURCE,
  type CartLine,
  classifyApiFailure,
  getCart,
  removeFromCart,
  updateCartItem,
} from '@/lib/api/cart';
import { isOnline, registerConnectivityListeners } from '@/lib/offline/connectivity';

interface CartItem {
  id: string;
  product: string;
  quantity: number;
  unitPrice: number;
}

function toCartItem(line: CartLine): CartItem {
  return {
    id: line.product_id,
    product: line.product_name ?? line.product_id,
    quantity: line.quantity,
    unitPrice: line.price ?? 0,
  };
}

export default function CartPage() {
  const t = useTranslations('market.cart');
  const checkout = useTranslations('market.checkout');
  const stock = useTranslations('market.product');
  const common = useTranslations('common');
  const nav = useTranslations('nav');
  const statusLine = useTranslations('statusLine');
  const pathname = usePathname();
  const router = useRouter();
  const locale = pathname.split('/')[1] || 'fa';

  const { user, loading: authLoading } = useAuth();
  const [items, setItems] = useState<CartItem[]>([]);
  const [subtotal, setSubtotal] = useState(0);
  const [dataState, setDataState] = useState<MarketDataState>('loading');
  const [failureKind, setFailureKind] = useState<'auth' | 'offline' | 'server' | 'not-found'>(
    'server',
  );
  const [detail, setDetail] = useState('');
  const [pendingId, setPendingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!isOnline()) {
      setDataState('offline');
      return;
    }
    setDetail('');
    const result = await getCart();
    if (!result.ok) {
      const kind = classifyApiFailure(result.status);
      setFailureKind(kind);
      setDetail(result.error);
      setDataState(kind === 'offline' ? 'offline' : kind === 'auth' ? 'unauthenticated' : 'error');
      return;
    }
    const next = result.data.items.map(toCartItem);
    setItems(next);
    // The payable amount is the server subtotal; no client-side fee is invented.
    setSubtotal(result.data.subtotal);
    setDataState(next.length > 0 ? 'live' : 'empty');
  }, []);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      setDataState('unauthenticated');
      setItems([]);
      return;
    }
    setDataState('loading');
    void load();
  }, [authLoading, user, load]);

  useEffect(() => {
    if (dataState !== 'offline') return;
    return registerConnectivityListeners((online) => {
      if (online) void load();
    });
  }, [dataState, load]);

  const mutate = async (id: string, action: () => Promise<ApiResult<unknown>>) => {
    setPendingId(id);
    setDetail('');
    const result = await action();
    setPendingId(null);
    if (!result.ok) {
      setDetail(result.error);
      setFailureKind(classifyApiFailure(result.status));
      await load();
      return;
    }
    await load();
  };

  const changeQuantity = (item: CartItem, nextQuantity: number) => {
    const quantity = Math.max(1, nextQuantity);
    if (quantity === item.quantity) return;
    void mutate(item.id, () => updateCartItem(item.id, quantity));
  };

  const removeItem = (item: CartItem) => {
    void mutate(item.id, () => removeFromCart(item.id));
  };

  const formatPrice = (price: number) =>
    new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(price);

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-6">
        <header className="mb-8 flex flex-wrap items-center gap-3">
          <div className="flex-1">
            <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title')}</h1>
            {dataState === 'live' ? (
              <p className="mt-2 text-ink-soft">{statusLine('realData')}</p>
            ) : null}
          </div>
          <ProvenanceStamp
            source={CART_SOURCE}
            label={t('cartProvenance')}
            method={dataState === 'live' ? statusLine('realData') : undefined}
          />
        </header>

        {dataState !== 'live' && dataState !== 'loading' && (
          <MarketDataStateNotice
            state={dataState}
            locale={locale}
            detail={dataState === 'error' || dataState === 'unavailable' ? detail : undefined}
            failureKind={failureKind}
            onRetry={() => void load()}
            emptyMessage={t('empty')}
            emptyAction={
              <Button variant="primary" onClick={() => router.push(`/${locale}/market`)}>
                {nav('market')}
              </Button>
            }
          />
        )}

        {dataState === 'loading' && <MarketDataStateNotice state="loading" locale={locale} />}

        {detail && dataState === 'live' && (
          <p role="alert" className="mb-6 rounded-md bg-clay/10 p-3 text-sm text-clay">
            {detail}
          </p>
        )}

        {dataState === 'live' && (
          <div className="space-y-6">
            {items.map((item) => (
              <Card key={item.id} density="compact">
                <div className="flex flex-wrap gap-4">
                  <div className="min-w-0 flex-1">
                    <h2 className="font-medium text-ink">{item.product}</h2>
                    <div className="mt-2">
                      <StatusDot state="ok" label={stock('inStock')} />
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-3">
                    <span className="font-medium text-ink">{formatPrice(item.unitPrice)}</span>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        aria-label={`${t('decrease')}: ${item.product}`}
                        disabled={pendingId === item.id}
                        onClick={() => changeQuantity(item, item.quantity - 1)}
                        className="flex h-11 w-11 items-center justify-center rounded border border-line text-sm disabled:opacity-40"
                      >
                        −
                      </button>
                      <span className="num w-8 text-center text-sm font-medium text-ink">
                        {item.quantity}
                      </span>
                      <button
                        type="button"
                        aria-label={`${t('increase')}: ${item.product}`}
                        disabled={pendingId === item.id}
                        onClick={() => changeQuantity(item, item.quantity + 1)}
                        className="flex h-11 w-11 items-center justify-center rounded border border-line text-sm disabled:opacity-40"
                      >
                        +
                      </button>
                    </div>
                    <button
                      type="button"
                      aria-label={item.product}
                      title={item.product}
                      disabled={pendingId === item.id}
                      onClick={() => removeItem(item)}
                      className="text-sm text-copper disabled:opacity-40"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              </Card>
            ))}

            <Card density="compact">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="font-medium text-ink">{t('summary')}</h2>
                <span className="num text-sm text-ink-soft">{items.length}</span>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-ink-soft">{checkout('subtotal')}</span>
                  <span className="text-ink">{formatPrice(subtotal)}</span>
                </div>
                <div className="border-t border-line pt-3">
                  <div className="flex justify-between">
                    <span className="font-medium text-ink">{common('total')}</span>
                    <span className="num text-xl font-bold text-forest">
                      {formatPrice(subtotal)}
                    </span>
                  </div>
                </div>
              </div>
            </Card>

            <div className="flex flex-wrap gap-4">
              <Button variant="ghost" size="lg" onClick={() => router.push(`/${locale}/market`)}>
                {nav('market')}
              </Button>
              <Button
                variant="primary"
                size="lg"
                className="flex-1"
                onClick={() => router.push(`/${locale}/market/checkout`)}
              >
                {common('proceedToCheckout')}
              </Button>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
