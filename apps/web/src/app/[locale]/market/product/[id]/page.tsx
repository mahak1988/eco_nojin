'use client';

import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useEffect, useState } from 'react';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { StatusDot } from '@/components/StatusDot';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { getProduct } from '@/lib/api/market';
import type { ProductListing } from '@/types/market';

interface ProductSpec {
  label: string;
  value: string;
}

interface ProductVariant {
  unit: string;
  price: number;
  stock: number;
}

interface ProductData {
  id: string;
  name: string;
  producer: string;
  description: string;
  category: string;
  origin: string;
  impact: { carbon: number; water: number; soil: number };
  variants: ProductVariant[];
  specs: ProductSpec[];
  images: string[];
  inStock: boolean;
  rating: number;
}

const EMPTY_PRODUCT: ProductData = {
  id: '',
  name: '',
  producer: '',
  description: '',
  category: '',
  origin: '',
  impact: { carbon: 0, water: 0, soil: 0 },
  variants: [],
  specs: [],
  images: [],
  inStock: false,
  rating: 0,
};

const EMPTY_VARIANT: ProductVariant = { unit: '', price: 0, stock: 0 };

function productSource(id: string): string {
  return `/api/v1/marketplace/products/${encodeURIComponent(id)}`;
}

function mapProduct(item: ProductListing, locale: string): ProductData {
  return {
    id: item.id,
    name: item.name[locale] ?? item.name.en ?? item.id,
    producer: item.producer.name,
    description: item.description?.[locale] ?? item.description?.en ?? '',
    category: item.category.name[locale] ?? item.category.name.en ?? item.category.slug,
    origin: item.origin ?? item.location?.address ?? '',
    impact: { carbon: item.carbonFootprint ?? 0, water: item.waterFootprint ?? 0, soil: 0 },
    variants: [{ unit: item.unit, price: item.price, stock: item.stockQuantity ?? 0 }],
    specs: [],
    images: item.images,
    inStock: item.inStock,
    rating: item.producer.rating ?? 0,
  };
}

export default function ProductPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const t = useTranslations('market.product');
  const common = useTranslations('common');
  const { locale, id } = useParamsSafe(params);
  const router = useRouter();
  const [selectedVariant, setSelectedVariant] = useState(0);
  const [quantity, setQuantity] = useState(1);
  const [product, setProduct] = useState<ProductData>(EMPTY_PRODUCT);
  const [dataState, setDataState] = useState<'loading' | 'live' | 'unavailable'>('loading');
  const [error, setError] = useState('');
  const source = productSource(id);

  useEffect(() => {
    let active = true;
    if (!id)
      return () => {
        active = false;
      };
    void getProduct(id).then((result) => {
      if (!active) return;
      if (!result.ok) {
        setDataState('unavailable');
        setError(result.error);
        return;
      }
      if (result.data) {
        setProduct(mapProduct(result.data, locale || 'en'));
        setDataState('live');
      } else {
        setDataState('unavailable');
        setError(t('dataUnavailable'));
      }
    });
    return () => {
      active = false;
    };
  }, [id, locale, t]);

  const currentVariant = product.variants[selectedVariant] ?? EMPTY_VARIANT;

  const handleAddToCart = () => {
    const params = new URLSearchParams();
    params.set('product', product.id);
    params.set('variant', selectedVariant.toString());
    params.set('qty', quantity.toString());
    router.push(`/${locale}/market/cart?${params.toString()}`);
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(price);
  };

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-6xl px-6 pb-12 pt-6">
        <header className="mb-8">
          <nav className="mb-4 text-sm text-ink-soft">
            <button
              type="button"
              onClick={() => router.push(`/${locale}/market`)}
              className="text-ink-soft hover:text-ink underline"
            >
              {t('backToMarket')}
            </button>
            {' / '}
            <span className="text-ink">{product.name}</span>
          </nav>
          <div className="flex items-center justify-between">
            <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{product.name}</h1>
            <ProvenanceStamp source={source} verified={false} label={t('verifiedProduct')} />
          </div>
          <p className="mt-3 text-ink-soft">{product.description}</p>
        </header>

        {dataState === 'unavailable' && (
          <p
            role="status"
            className="mb-6 rounded-md border border-line bg-surface-alt p-3 text-sm text-ink-soft"
          >
            {t('dataUnavailable')}
          </p>
        )}
        {error && (
          <p role="alert" className="mb-6 rounded-md bg-red-50 p-3 text-sm text-red-800">
            {error}
          </p>
        )}

        <div className="grid gap-8 lg:grid-cols-2">
          <div className="space-y-4">
            <div className="aspect-square w-full overflow-hidden rounded-lg border border-line bg-surface">
              <div className="flex h-full items-center justify-center text-4xl text-ink-soft">
                📷
              </div>
            </div>
            <div className="flex gap-2">
              {product.images.map((src, idx) => (
                <button
                  type="button"
                  key={src}
                  onClick={() => setSelectedVariant(idx)}
                  className="h-16 w-16 rounded border border-line bg-surface"
                >
                  <span className="text-2xl text-ink-soft">📷</span>
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-6">
            <Card density="compact">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-ink-soft">{common('status')}</p>
                  <StatusDot
                    state={product.inStock ? 'ok' : 'down'}
                    label={product.inStock ? common('inStock') : common('outOfStock')}
                  />
                </div>
                <div className="text-right">
                  <p className="text-sm text-ink-soft">{common('rating')}</p>
                  <p className="font-medium text-ink">⭐ {product.rating}</p>
                </div>
              </div>
            </Card>

            <Card density="compact">
              <h2 className="font-medium text-ink mb-3">{t('pricing')}</h2>
              <div className="space-y-3">
                {product.variants.map((variant, idx) => (
                  <label
                    key={variant.unit}
                    className="flex items-center justify-between cursor-pointer"
                  >
                    <div className="flex items-center gap-3">
                      <input
                        type="radio"
                        name="variant"
                        checked={selectedVariant === idx}
                        onChange={() => setSelectedVariant(idx)}
                        className="h-4 w-4 text-forest focus:ring-forest"
                      />
                      <span className="text-ink">{variant.unit}</span>
                    </div>
                    <div className="text-right">
                      <span className="font-medium text-ink">
                        {formatPrice(variant.price)} ریال
                      </span>
                      <span className="text-xs text-ink-soft">
                        {' '}
                        ({variant.stock} {common('available')})
                      </span>
                    </div>
                  </label>
                ))}
              </div>
            </Card>

            <Card density="compact">
              <h2 className="font-medium text-ink mb-3">{t('quantity')}</h2>
              <div className="flex items-center gap-4">
                <button
                  type="button"
                  onClick={() => setQuantity(Math.max(1, quantity - 1))}
                  className="flex h-8 w-8 items-center justify-center rounded border border-line bg-surface"
                >
                  −
                </button>
                <span className="font-medium text-ink w-8 text-center">{quantity}</span>
                <button
                  type="button"
                  onClick={() => setQuantity(Math.min(currentVariant.stock, quantity + 1))}
                  className="flex h-8 w-8 items-center justify-center rounded border border-line bg-surface"
                >
                  +
                </button>
              </div>
            </Card>

            <Card density="compact">
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-ink-soft">{t('unitPrice')}</span>
                  <span className="font-medium text-ink">
                    {formatPrice(currentVariant.price)} ریال
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ink-soft">{t('qty')}</span>
                  <span className="font-medium text-ink">{quantity}</span>
                </div>
                <div className="flex justify-between border-t border-line pt-3">
                  <span className="font-medium text-ink">{common('total')}</span>
                  <span className="font-bold text-forest">
                    {formatPrice(currentVariant.price * quantity)} ریال
                  </span>
                </div>
              </div>
            </Card>

            <Button variant="primary" size="lg" className="w-full" onClick={handleAddToCart}>
              {common('addToCart')}
            </Button>

            <Button variant="secondary" size="lg" className="w-full">
              {t('escrowOption')}
            </Button>
          </div>
        </div>

        <div className="mt-8 grid gap-8 lg:grid-cols-2">
          <Card density="compact">
            <h2 className="font-medium text-ink mb-3">{t('productSpecs')}</h2>
            <div className="space-y-2">
              {product.specs.map((spec) => (
                <div key={spec.label} className="flex justify-between">
                  <span className="text-ink-soft">{spec.label}</span>
                  <span className="text-ink">{spec.value}</span>
                </div>
              ))}
            </div>
          </Card>

          <Card density="compact">
            <h2 className="font-medium text-ink mb-3">{t('ecoImpact')}</h2>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between">
                  <span className="text-ink-soft">{t('carbonSequestration')}</span>
                  <span className="font-medium text-ink">{product.impact.carbon} kg CO₂</span>
                </div>
                <div className="h-2 rounded-full bg-surface-alt mt-1">
                  <div
                    className="h-2 rounded-full bg-forest"
                    style={{ width: `${Math.min(product.impact.carbon * 5, 100)}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between">
                  <span className="text-ink-soft">{t('waterSavings')}</span>
                  <span className="font-medium text-ink">{product.impact.water} L</span>
                </div>
                <div className="h-2 rounded-full bg-surface-alt mt-1">
                  <div
                    className="h-2 rounded-full bg-forest"
                    style={{ width: `${Math.min(product.impact.water / 100, 100)}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between">
                  <span className="text-ink-soft">{t('soilRestoration')}</span>
                  <span className="font-medium text-ink">{product.impact.soil} t/ha</span>
                </div>
                <div className="h-2 rounded-full bg-surface-alt mt-1">
                  <div
                    className="h-2 rounded-full bg-forest"
                    style={{ width: `${Math.min(product.impact.soil * 20, 100)}%` }}
                  />
                </div>
              </div>
            </div>
          </Card>
        </div>

        <Card density="compact" className="mt-8">
          <ProvenanceStamp source={source} verified={false} label={t('productProvenance')} />
        </Card>
      </div>
    </main>
  );
}

function useParamsSafe(params: Promise<{ locale: string; id: string }>) {
  const [resolved, setResolved] = useState<{ locale: string; id: string } | null>(null);
  if (typeof window === 'undefined') {
    if (!resolved) {
      params.then(setResolved);
    }
    return { locale: '', id: '' };
  }
  return resolved || { locale: '', id: '' };
}
