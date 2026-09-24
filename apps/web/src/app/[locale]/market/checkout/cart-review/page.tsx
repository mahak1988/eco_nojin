import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface CartItem {
  id: string;
  product: string;
  producer: string;
  variant: string;
  price: number;
  quantity: number;
  organic: boolean;
  stock: number;
}

const MOCK_CART: CartItem[] = [
  { id: 'ci1', product: 'پسته ارگانیک آکبری', producer: 'Rafsanjan Organic Co', variant: '1 kg', price: 285000, quantity: 2, organic: true, stock: 18 },
  { id: 'ci2', product: 'زعفران سوپر نگین', producer: 'Khorasan Saffron', variant: '5 g', price: 8900000, quantity: 1, organic: true, stock: 8 },
];

const platformFeeRate = 0.05;
const escrowFeeRate = 0.02;

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'مرور سبد خرید', en: 'Cart Review' };
  const descriptions: Record<string, string> = { fa: 'مرور و تأیید اقلام سبد خرید', en: 'Review and confirm cart items' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/checkout/cart-review`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/checkout/cart-review`, languages: { fa: `${BASE_URL}/fa/market/checkout/cart-review`, en: `${BASE_URL}/en/market/checkout/cart-review` } },
  };
}

export default async function CartReviewPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.checkout.cartReview');
  const common = await getTranslations('common');

  const items = MOCK_CART;
  const subtotal = items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const platformFee = Math.round(subtotal * platformFeeRate);
  const escrowFee = Math.round(subtotal * escrowFeeRate);
  const total = subtotal + platformFee + escrowFee;

  const formatPrice = (price: number) => new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(price);

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-3xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Checkout Service" label={t('provenanceLabel')} verified={true} method="Session-signed" timestamp="2024-12-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title')}</h1>
        </ProvenanceStamp>
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-6">
        <FivePart
          title={t('whatTitle')}
          lead={t('whatLead')}
          what={t('whatDesc')}
          audience={t('audience')}
          evidence={['Real-time pricing', 'Fee transparency', 'Stock validation']}
          limits={['Prices may change', 'Stock not reserved yet', 'Promo codes not applied']}
          next={['Proceed to escrow', 'Apply promotions', 'Save for later']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-12">
        <Card density="compact">
          <h2 className="font-semibold text-ink mb-4">{t('cartItems')}</h2>
          <div className="space-y-3">
            {items.map(item => (
              <div key={item.id} className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-3 border border-line rounded">
                <div className="flex items-center gap-3">
                  <div className="w-16 h-16 flex items-center justify-center bg-slate/10 rounded">📷</div>
                  <div>
                    <h3 className="font-medium text-ink">{item.product}</h3>
                    <p className="text-sm text-ink-soft">{item.producer} · {item.variant}</p>
                    {item.organic && <span className="mt-1 inline-block text-xs bg-forest/10 text-forest px-2 py-1 rounded">{t('organic')}</span>}
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-ink-soft">× {item.quantity}</span>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-forest">{new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(item.price * item.quantity)} ریال</p>
                    <StatusDot state={item.stock > 0 ? 'ok' : 'down'} label={item.stock > 0 ? t('inStock') : t('outOfStock')} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card density="compact" className="mt-6">
          <h2 className="font-semibold text-ink mb-4">{t('priceSummary')}</h2>
          <div className="space-y-2">
            <div className="flex justify-between"><span className="text-ink-soft">{t('subtotal')}</span><span className="text-ink">{formatPrice(subtotal)} ریال</span></div>
            <div className="flex justify-between"><span className="text-ink-soft">{t('platformFee')}</span><span className="text-ink">{formatPrice(platformFee)} ریال</span></div>
            <div className="flex justify-between"><span className="text-ink-soft">{t('escrowFee')}</span><span className="text-ink">{formatPrice(escrowFee)} ریال</span></div>
            <div className="border-t border-line pt-3 flex justify-between"><span className="font-bold text-ink">{common('total')}</span><span className="font-bold text-forest text-xl">{formatPrice(total)} ریال</span></div>
          </div>
        </Card>

        <Button variant="primary" className="w-full mt-6" onClick={() => window.location.href = `/${locale}/market/checkout/escrow-setup`}>
          {t('proceedToEscrow')}
        </Button>
      </section>
    </main>
  );
}