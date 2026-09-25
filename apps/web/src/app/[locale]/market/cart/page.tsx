'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useEffect, useState } from 'react';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { useAuth } from '@/components/providers/AuthProvider';
import { StatusDot } from '@/components/StatusDot';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { type CartLine, getCart, removeFromCart, updateCartItem } from '@/lib/api/cart';

interface CartItem {
  id: string;
  product: string;
  producer: string;
  variant: string;
  price: number;
  quantity: number;
  inStock: boolean;
}

function mapCartLine(line: CartLine): CartItem {
  return {
    id: line.product_id,
    product: line.product_name ?? line.product_id,
    producer: line.producer_name ?? '',
    variant: line.unit ?? '',
    price: line.price ?? 0,
    quantity: line.quantity,
    inStock: line.in_stock ?? true,
  };
}

const platformFeeRate = 0.05;
const escrowFeeRate = 0.02;

export default function CartPage() {
  const t = useTranslations('market.cart');
  const common = useTranslations('common');
  const statusLine = useTranslations('statusLine');
  const pathname = usePathname();
  const router = useRouter();
  const locale = pathname.split('/')[1] || 'fa';

  const { user, loading: authLoading } = useAuth();
  const [items, setItems] = useState<CartItem[]>([]);
  const [dataState, setDataState] = useState<
    'loading' | 'live' | 'unauthenticated' | 'unavailable'
  >('loading');
  const [error, setError] = useState('');

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      setDataState('unauthenticated');
      return;
    }
    let active = true;
    void getCart().then((result) => {
      if (!active) return;
      if (result.ok && result.data.items.length > 0) {
        setItems(result.data.items.map(mapCartLine));
        setDataState('live');
      } else {
        setDataState('unavailable');
        if (!result.ok) setError(result.error);
      }
    });
    return () => {
      active = false;
    };
  }, [authLoading, user]);

  const updateQuantity = async (id: string, qty: number) => {
    const quantity = Math.max(1, qty);
    setItems(items.map((item) => (item.id === id ? { ...item, quantity } : item)));
    if (dataState === 'live') {
      const result = await updateCartItem(id, quantity);
      if (!result.ok) setError(result.error);
    }
  };

  const removeItem = async (id: string) => {
    setItems(items.filter((item) => item.id !== id));
    if (dataState === 'live') {
      const result = await removeFromCart(id);
      if (!result.ok) setError(result.error);
    }
  };

  const subtotal = items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const platformFee = Math.round(subtotal * platformFeeRate);
  const escrowFee = Math.round(subtotal * escrowFeeRate);
  const total = subtotal + platformFee + escrowFee;

  const handleCheckout = () => {
    router.push(`/${locale}/market/checkout`);
  };

  const handleContinueShopping = () => {
    router.push(`/${locale}/market`);
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(price);
  };

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-6">
        <header className="mb-8">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title')}</h1>
          <p className="mt-2 text-ink-soft">
            {items.length} {items.length === 1 ? common('item') : common('items')}
          </p>
        </header>

        {dataState === 'unavailable' && (
          <p
            role="status"
            className="mb-6 rounded-md border border-line bg-surface-alt p-3 text-sm text-ink-soft"
          >
            {statusLine('unavailable')}
          </p>
        )}
        {error && (
          <p role="alert" className="mb-6 rounded-md bg-red-50 p-3 text-sm text-red-800">
            {error}
          </p>
        )}

        {items.length === 0 ? (
          <Card density="cozy" className="text-center py-12">
            <p className="text-ink-soft mb-4">{t('empty')}</p>
            <Button variant="primary" onClick={handleContinueShopping}>
              {common('continueShopping')}
            </Button>
          </Card>
        ) : (
          <div className="space-y-6">
            {items.map((item) => (
              <Card key={item.id} density="compact">
                <div className="flex gap-4">
                  <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded border border-line bg-surface">
                    📷
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between">
                      <h3 className="font-medium text-ink">{item.product}</h3>
                      <button
                        type="button"
                        onClick={() => removeItem(item.id)}
                        className="text-sm text-copper hover:text-copper/80"
                      >
                        {common('remove')}
                      </button>
                    </div>
                    <p className="text-sm text-ink-soft">{item.producer}</p>
                    <div className="mt-2 flex items-center gap-4">
                      <StatusDot
                        state={item.inStock ? 'ok' : 'down'}
                        label={item.inStock ? common('inStock') : common('outOfStock')}
                      />
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-3">
                    <span className="font-medium text-ink">{formatPrice(item.price)} ریال</span>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        aria-label={`${t('decrease')}: ${item.product}`}
                        onClick={() => updateQuantity(item.id, item.quantity - 1)}
                        className="flex h-11 w-11 items-center justify-center rounded border border-line text-sm"
                      >
                        −
                      </button>
                      <span className="text-sm font-medium text-ink w-6 text-center">
                        {item.quantity}
                      </span>
                      <button
                        type="button"
                        aria-label={`${t('increase')}: ${item.product}`}
                        onClick={() => updateQuantity(item.id, item.quantity + 1)}
                        className="flex h-11 w-11 items-center justify-center rounded border border-line text-sm"
                      >
                        +
                      </button>
                    </div>
                    <span className="text-sm text-ink-soft">{item.variant}</span>
                  </div>
                </div>
              </Card>
            ))}

            <Card density="compact">
              <h2 className="font-medium text-ink mb-4">{t('summary')}</h2>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-ink-soft">{t('subtotal')}</span>
                  <span className="text-ink">{formatPrice(subtotal)} ریال</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ink-soft">{t('platformFee')}</span>
                  <span className="text-ink">{formatPrice(platformFee)} ریال</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ink-soft">{t('escrowFee')}</span>
                  <span className="text-ink">{formatPrice(escrowFee)} ریال</span>
                </div>
                <div className="border-t border-line pt-3">
                  <div className="flex justify-between">
                    <span className="font-medium text-ink">{common('total')}</span>
                    <span className="font-bold text-forest text-xl">{formatPrice(total)} ریال</span>
                  </div>
                </div>
              </div>
            </Card>

            <div className="flex gap-4">
              <Button variant="ghost" size="lg" onClick={handleContinueShopping}>
                {common('continueShopping')}
              </Button>
              <Button
                variant="primary"
                size="lg"
                className="flex-1"
                disabled={dataState !== 'live'}
                onClick={handleCheckout}
              >
                {common('proceedToCheckout')}
              </Button>
            </div>
          </div>
        )}

        <Card density="compact" className="mt-8">
          <ProvenanceStamp
            source="/api/v1/marketplace/cart"
            verified={false}
            label={t('cartProvenance')}
          />
        </Card>
      </div>
    </main>
  );
}
