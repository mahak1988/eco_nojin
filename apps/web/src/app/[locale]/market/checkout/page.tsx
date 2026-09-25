'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useEffect, useState } from 'react';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { useAuth } from '@/components/providers/AuthProvider';
import { StatusDot } from '@/components/StatusDot';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { createOrder, getCart } from '@/lib/api/cart';
import { createPayment } from '@/lib/api/escrow';

type CheckoutStep = 'cart' | 'escrow' | 'confirmation';

interface CartItem {
  id: string;
  product: string;
  producer: string;
  variant: string;
  price: number;
  quantity: number;
  inStock: boolean;
}

const platformFeeRate = 0.05;
const escrowFeeRate = 0.02;

export default function CheckoutPage() {
  const t = useTranslations('market.checkout');
  const common = useTranslations('common');
  const pathname = usePathname();
  const router = useRouter();
  const locale = pathname.split('/')[1] || 'fa';
  const { user, loading: authLoading } = useAuth();

  const [step, setStep] = useState<CheckoutStep>('cart');
  const [contractAccepted, setContractAccepted] = useState(false);
  const [walletSelected, setWalletSelected] = useState<'ecowallet' | 'card'>('ecowallet');
  const [transactionKey, setTransactionKey] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [items, setItems] = useState<CartItem[]>([]);
  const [dataState, setDataState] = useState<
    'loading' | 'ready' | 'empty' | 'unauthenticated' | 'error'
  >('loading');

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      setDataState('unauthenticated');
      return;
    }
    void getCart()
      .then((result) => {
        if (!result.ok) {
          setDataState('error');
          setError(result.error);
          return;
        }
        const nextItems = result.data.items.map((item) => ({
          id: item.product_id,
          product: item.product_name ?? item.product_id,
          producer: item.producer_name ?? '',
          variant: item.unit ?? 'kg',
          price: item.price ?? 0,
          quantity: item.quantity,
          inStock: item.in_stock ?? true,
        }));
        setItems(nextItems);
        setDataState(nextItems.length > 0 ? 'ready' : 'empty');
      })
      .catch((caught) => {
        setDataState('error');
        setError(caught instanceof Error ? caught.message : t('apiUnavailable'));
      });
  }, [authLoading, user, t]);
  const subtotal = items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const platformFee = Math.round(subtotal * platformFeeRate);
  const escrowFee = Math.round(subtotal * escrowFeeRate);
  const total = subtotal + platformFee + escrowFee;

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(price);
  };

  const handleEscrowStep = () => {
    if (!user || items.length === 0) {
      setError(t('apiUnavailable'));
      return;
    }
    setError('');
    setStep('escrow');
  };

  const handleConfirm = async () => {
    if (!user || items.length === 0) {
      setError(t('apiUnavailable'));
      return;
    }
    setIsSubmitting(true);
    setError('');
    try {
      const orders = await Promise.all(
        items.map((item) =>
          createOrder({
            productId: item.id,
            buyerName: user.full_name ?? user.email,
            quantityKg: item.quantity,
          }),
        ),
      );
      const failedOrder = orders.find((result) => !result.ok);
      if (failedOrder && !failedOrder.ok) {
        setError(failedOrder.error);
        return;
      }

      const payments = await Promise.all(
        orders.map((result, index) => {
          if (!result.ok) return Promise.resolve(result);
          return createPayment({
            orderId: result.data.order_id,
            amount: items[index].price * items[index].quantity,
            paymentMethod: walletSelected,
            description: 'Marketplace checkout',
          });
        }),
      );
      const failedPayment = payments.find((result) => !result.ok);
      if (failedPayment && !failedPayment.ok) {
        setError(failedPayment.error);
        return;
      }

      const firstPayment = payments.find((result) => result.ok);
      if (!firstPayment?.ok) {
        setError(t('apiUnavailable'));
        return;
      }
      setTransactionKey(firstPayment.data.id ?? firstPayment.data.payment_id ?? '');
      setStep('confirmation');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleBack = () => {
    if (step === 'cart') {
      router.push(`/${locale}/market/cart`);
    } else if (step === 'escrow') {
      setStep('cart');
    }
  };

  const StepIndicator = () => {
    const steps: { key: CheckoutStep; label: string }[] = [
      { key: 'cart', label: t('step1Cart') },
      { key: 'escrow', label: t('step2Escrow') },
      { key: 'confirmation', label: t('step3Confirm') },
    ];

    return (
      <div className="flex justify-between mb-8">
        {steps.map((s, idx) => {
          const isActive = step === s.key;
          const isComplete = steps.findIndex((st) => st.key === step) > idx;
          return (
            <div key={s.key} className="flex items-center">
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium ${
                  isActive
                    ? 'bg-forest text-paper'
                    : isComplete
                      ? 'bg-forest/10 text-forest'
                      : 'bg-surface-alt text-ink-soft'
                }`}
              >
                {idx + 1}
              </div>
              <span
                className={`mr-2 text-sm ${isActive ? 'font-medium text-ink' : 'text-ink-soft'}`}
              >
                {s.label}
              </span>
              {idx < steps.length - 1 && <div className="mx-2 h-px w-8 bg-line" />}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-3xl px-6 pb-12 pt-6">
        <StepIndicator />
        {step !== 'cart' && (
          <Button variant="ghost" size="sm" className="mb-6" onClick={handleBack}>
            {common('back')}
          </Button>
        )}

        {step === 'cart' && (
          <Card density="compact">
            <h2 className="font-medium text-ink mb-4">{t('cartReview')}</h2>
            <p className="mb-4 text-sm text-ink-soft">
              {dataState === 'ready' ? t('cartReview') : t('apiUnavailable')}
            </p>
            <div className="space-y-3 mb-6">
              {items.map((item) => (
                <div key={item.id} className="flex justify-between">
                  <span className="text-ink-soft">
                    {item.product} × {item.quantity} ({item.variant})
                  </span>
                  <span className="text-ink">{formatPrice(item.price * item.quantity)} ریال</span>
                </div>
              ))}
            </div>
            <div className="border-t border-line pt-4 space-y-2">
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
              <div className="flex justify-between pt-2 border-t border-line">
                <span className="font-bold text-ink">{common('total')}</span>
                <span className="font-bold text-forest text-xl">{formatPrice(total)} ریال</span>
              </div>
            </div>
            <Button
              variant="primary"
              className="w-full mt-6"
              disabled={dataState !== 'ready'}
              onClick={handleEscrowStep}
            >
              {common('proceedToCheckout')}
            </Button>
          </Card>
        )}

        {step === 'escrow' && (
          <Card density="compact">
            <h2 className="font-medium text-ink mb-4">{t('escrowSetup')}</h2>
            {error && (
              <p role="alert" className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-800">
                {error}
              </p>
            )}

            <div className="mb-6">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="radio"
                  name="payment"
                  checked={walletSelected === 'ecowallet'}
                  onChange={() => setWalletSelected('ecowallet')}
                  className="h-4 w-4 text-forest"
                />
                <span className="text-ink">{t('ecowallet')}</span>
              </label>
              <label className="mt-2 flex items-center gap-3 cursor-pointer">
                <input
                  type="radio"
                  name="payment"
                  checked={walletSelected === 'card'}
                  onChange={() => setWalletSelected('card')}
                  className="h-4 w-4 text-forest"
                />
                <span className="text-ink">{common('card')}</span>
              </label>
            </div>

            <div className="mb-6">
              <label className="flex items-start gap-3">
                <input
                  type="checkbox"
                  checked={contractAccepted}
                  onChange={(e) => setContractAccepted(e.target.checked)}
                  className="mt-1 h-4 w-4 text-forest"
                  required
                />
                <span className="text-sm text-ink-soft">{t('contractAcceptance')}</span>
              </label>
            </div>

            {transactionKey && (
              <div className="mb-6 p-4 rounded-md bg-surface-alt">
                <p className="text-sm text-ink-soft">{t('transactionKey')}</p>
                <code className="font-mono text-forest text-sm">{transactionKey}</code>
              </div>
            )}

            <div className="space-y-3">
              <Button
                variant="primary"
                className="w-full"
                disabled={isSubmitting || !contractAccepted || walletSelected !== 'ecowallet'}
                onClick={handleConfirm}
              >
                {isSubmitting
                  ? t('processing')
                  : contractAccepted && walletSelected === 'ecowallet'
                    ? t('confirmAndLock')
                    : t('acceptContractFirst')}
              </Button>
            </div>
          </Card>
        )}

        {step === 'confirmation' && (
          <Card density="compact">
            <h2 className="font-medium text-ink mb-4">{t('confirmation')}</h2>
            <div className="text-center py-8">
              <div className="text-6xl mb-4">✓</div>
              <p className="text-lg font-medium text-ink mb-2">{t('orderPlaced')}</p>
              {transactionKey && (
                <p className="text-sm text-ink-soft">
                  {t('transactionKey')}: <code className="text-forest">{transactionKey}</code>
                </p>
              )}
            </div>

            <div className="mt-6 pt-6 border-t border-line">
              <h3 className="font-medium text-ink mb-3">{t('escrowStatus')}</h3>
              <div className="space-y-3">
                {['Buyer', 'Seller', 'Arbitrator', 'Platform'].map((party, idx) => (
                  <div key={party} className="flex items-center justify-between">
                    <span className="text-ink">{party}</span>
                    <StatusDot
                      state={idx < 2 ? 'ok' : idx === 2 ? 'warn' : 'down'}
                      label={
                        idx < 2
                          ? common('signed')
                          : idx === 2
                            ? common('pending')
                            : common('pending')
                      }
                    />
                  </div>
                ))}
              </div>
            </div>

            <Button
              variant="primary"
              className="w-full mt-6"
              onClick={() => router.push(`/${locale}/market/orders`)}
            >
              {t('viewOrders')}
            </Button>
          </Card>
        )}

        <div className="mt-8">
          <ProvenanceStamp
            source="/api/v1/marketplace/orders"
            verified={false}
            label={t('checkoutProvenance')}
          />
        </div>
      </div>
    </main>
  );
}
