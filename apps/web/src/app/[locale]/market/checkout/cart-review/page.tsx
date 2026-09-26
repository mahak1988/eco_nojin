'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useCallback, useEffect, useState } from 'react';
import { type MarketDataState, MarketDataStateNotice } from '@/components/market/MarketDataState';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { useAuth } from '@/components/providers/AuthProvider';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import {
  type ApiFailureKind,
  CART_SOURCE,
  type CartLine,
  type CartResponse,
  classifyApiFailure,
  getCart,
} from '@/lib/api/cart';
import { isOnline, registerConnectivityListeners } from '@/lib/offline/connectivity';

export default function CartReviewPage() {
  const checkout = useTranslations('market.checkout');
  const product = useTranslations('market.product');
  const cart = useTranslations('market.cart');
  const common = useTranslations('common');
  const statusLine = useTranslations('statusLine');
  const pathname = usePathname();
  const router = useRouter();
  const locale = pathname.split('/')[1] || 'fa';
  const { user, loading: authLoading } = useAuth();

  const [review, setReview] = useState<CartResponse | null>(null);
  const [dataState, setDataState] = useState<MarketDataState>('loading');
  const [failureKind, setFailureKind] = useState<ApiFailureKind>('server');
  const [detail, setDetail] = useState('');

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
      setReview(null);
      setDataState(kind === 'offline' ? 'offline' : kind === 'auth' ? 'unauthenticated' : 'error');
      return;
    }
    setReview(result.data);
    setDataState(result.data.items.length > 0 ? 'live' : 'empty');
  }, []);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      setReview(null);
      setDataState('unauthenticated');
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

  const formatPrice = (price: number) =>
    new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(price);

  const unitPrice = (line: CartLine) => line.price ?? null;

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-3xl px-6 pb-12 pt-6">
        <header className="mb-8">
          <nav className="mb-4">
            <button
              type="button"
              onClick={() => router.push(`/${locale}/market/checkout`)}
              className="text-sm text-ink-soft underline hover:text-ink"
            >
              {common('back')}
            </button>
          </nav>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h1 className="display text-3xl font-bold text-ink sm:text-4xl">
              {checkout('cartReview')}
            </h1>
            <ProvenanceStamp
              source={CART_SOURCE}
              label={cart('cartProvenance')}
              method={dataState === 'live' ? statusLine('realData') : undefined}
            />
          </div>
        </header>

        {dataState !== 'live' && (
          <MarketDataStateNotice
            state={dataState}
            locale={locale}
            detail={dataState === 'error' ? detail : undefined}
            failureKind={failureKind}
            onRetry={() => void load()}
            emptyMessage={cart('empty')}
            emptyAction={
              <Button variant="primary" onClick={() => router.push(`/${locale}/market`)}>
                {common('view')}
              </Button>
            }
          />
        )}

        {dataState === 'live' && review && (
          <div className="space-y-6">
            <Card density="compact">
              <div className="space-y-3">
                {review.items.map((line) => (
                  <div
                    key={line.product_id}
                    className="flex flex-wrap justify-between gap-4 border-b border-line/50 pb-3 last:border-0"
                  >
                    <div className="min-w-0">
                      <p className="text-ink">{line.product_name ?? line.product_id}</p>
                      <p className="num mt-1 font-mono text-xs text-ink-soft">{line.product_id}</p>
                    </div>
                    <div className="text-end">
                      <p className="num text-sm text-ink">
                        {product('quantity')}: {line.quantity}
                      </p>
                      <p className="num text-sm text-ink-soft">
                        {product('unitPrice')}:{' '}
                        {unitPrice(line) === null
                          ? statusLine('unavailable')
                          : formatPrice(unitPrice(line) as number)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <Card density="compact">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-ink-soft">{product('quantity')}</span>
                  <span className="num text-ink">{review.total_items}</span>
                </div>
                <div className="flex justify-between border-t border-line pt-2">
                  <span className="font-medium text-ink">{common('total')}</span>
                  <span className="num text-xl font-bold text-forest">
                    {formatPrice(review.subtotal)}
                  </span>
                </div>
              </div>
            </Card>

            <div className="flex flex-wrap gap-3">
              <Button variant="ghost" onClick={() => router.push(`/${locale}/market/cart`)}>
                {common('back')}
              </Button>
              <Button
                variant="secondary"
                onClick={() => router.push(`/${locale}/market/checkout/escrow-setup`)}
              >
                {checkout('escrowSetup')}
              </Button>
              <Button variant="primary" onClick={() => router.push(`/${locale}/market/checkout`)}>
                {common('proceedToCheckout')}
              </Button>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
